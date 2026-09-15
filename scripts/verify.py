"""
verify.py —— 离线验证脚本（不消耗真实 API）

用 unittest.mock 替换 LLM 与检索器，验证：
1. LangGraph 工作流能被正确编译
2. 状态在各节点间正确流转
3. 条件分支（反思→再检索 / 反思→写作）逻辑正确

运行：python scripts/verify.py

依赖策略：
- 装齐 langgraph + langchain_core 时，跑「完整验证」（真实 LangGraph API + mock LLM）；
- 缺失依赖时，自动降级为 verify_pure.py 的纯逻辑校验，保证任何环境都能跑。
"""

import importlib.util
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch


def _has(module_name: str) -> bool:
    """依赖是否真实可导入（注意：与「是否已 import」无关）。"""
    return importlib.util.find_spec(module_name) is not None


HAS_LANGGRAPH = _has("langgraph")
HAS_LANGCHAIN_CORE = _has("langchain_core")
# 仅当真实依赖齐全时才跑完整验证，否则降级
FULL_MODE = HAS_LANGGRAPH and HAS_LANGCHAIN_CORE


# ---------------------------------------------------------------
# 惰性依赖桩：让 src.graph / src.retriever 在 import 时不报错
# （真实运行时这些包需通过 requirements.txt 安装）
# ---------------------------------------------------------------
def _install_langgraph_stub():
    if "langgraph" in sys.modules:
        return
    stub = types.ModuleType("langgraph")

    class _StateGraph:
        def __init__(self, state_cls=None):
            self.nodes = {}
            self.edges = []
            self.cond_edges = []

        def add_node(self, name, fn):
            self.nodes[name] = fn
            return self

        def set_entry_point(self, name):
            self.entry = name
            return self

        def add_edge(self, src, tgt):
            self.edges.append((src, tgt))
            return self

        def add_conditional_edges(self, src, router, mapping):
            self.cond_edges.append((src, router, mapping))
            return self

        def compile(self, checkpointer=None):
            # 返回一个最小可调用对象，invoke/stream 会被 mock 替换
            compiled = MagicMock()
            compiled.nodes = self.nodes
            compiled.edges = self.edges
            compiled.cond_edges = self.cond_edges
            return compiled

    stub.StateGraph = _StateGraph
    stub.END = "END"

    # checkpoint.memory.MemorySaver
    mem = types.ModuleType("langgraph.checkpoint.memory")
    mem.MemorySaver = MagicMock
    sys.modules["langgraph.checkpoint"] = types.ModuleType("langgraph.checkpoint")
    sys.modules["langgraph.checkpoint.memory"] = mem

    sys.modules["langgraph"] = stub
    sys.modules["langgraph.graph"] = stub


def _install_llama_index_stub():
    if "llama_index" in sys.modules:
        return
    core = types.ModuleType("llama_index.core")
    core.Document = object
    core.VectorStoreIndex = object
    LlamaSettings = MagicMock()
    LlamaSettings.embed_model = None
    core.Settings = LlamaSettings
    sys.modules["llama_index"] = types.ModuleType("llama_index")
    sys.modules["llama_index.core"] = core
    sys.modules["llama_index.embeddings"] = types.ModuleType("llama_index.embeddings")
    sys.modules["llama_index.embeddings.openai"] = MagicMock()
    sys.modules["llama_index.readers"] = types.ModuleType("llama_index.readers")
    sys.modules["llama_index.readers.file"] = MagicMock()


# 仅在依赖缺失的降级路径下注入桩，避免污染真实环境
if not FULL_MODE:
    if not HAS_LANGGRAPH:
        _install_langgraph_stub()
    _install_llama_index_stub()


# ===============================================================
# 测试用例
# ===============================================================
def test_graph_structure():
    """验证图能编译、节点/条件边齐全（基于真实 LangGraph API）。"""
    from src.graph import build_graph

    app = build_graph()
    assert app is not None

    graph = app.get_graph()
    node_names = set(graph.nodes.keys())
    expected = {"plan", "retrieve", "reflect", "write"}
    assert expected.issubset(node_names), f"缺少节点: {expected - node_names}"

    # 条件边（reflect → retrieve/write）在 Graph.edges 上以 conditional=True 标记
    cond_edges = [e for e in graph.edges if getattr(e, "conditional", False)]
    assert cond_edges, "应有至少一条条件边"
    print("✅ 图编译成功，节点:", sorted(node_names))
    print("✅ 条件边数量:", len(cond_edges))


def test_full_flow():
    """mock 掉 LLM 与检索，跑一次完整流程。"""
    from src.graph import run_research

    fake_context = "【Mock 资料】LangChain=编排, LangGraph=图编排, DeepAgents=满配"

    def fake_format_context(*a, **kw):
        return fake_context

    call_log = []

    def fake_invoke(messages, **kw):
        sys_msg = next(
            (m for m in messages if getattr(m, "type", "") == "system"), None
        )
        text = sys_msg.content if sys_msg else ""
        if "研究要点" in text:
            call_log.append("plan")
            return MagicMock(content="1. 定位\n2. 场景")
        if "是否足以回答" in text:
            call_log.append("reflect")
            return MagicMock(content="OK")
        call_log.append("write")
        return MagicMock(content="【Mock 最终答案】基于资料得出结论。")

    with patch("src.graph.format_context", fake_format_context), patch(
        "src.graph.build_index_from_dir", return_value=None
    ), patch("src.graph.get_llm") as mock_get:
        mock_get.return_value = MagicMock(invoke=fake_invoke)
        answer = run_research("测试问题")

    assert "Mock 最终答案" in answer, f"意外输出：{answer}"
    assert {"plan", "reflect", "write"}.issubset(
        set(call_log)
    ), f"调用顺序异常: {call_log}"
    print(f"✅ 完整流程通过，调用顺序：{' → '.join(call_log)}")
    print(f"   输出：{answer}")


def test_reflect_loop():
    """验证『资料不足 → 再检索一轮』的循环逻辑。"""
    from src.graph import should_continue

    state1 = {"reflection": "MORE: 需要更多资料", "iterations": 1}
    assert should_continue(state1) == "retrieve"

    state2 = {"reflection": "MORE: 仍不足", "iterations": 2}
    assert should_continue(state2) == "write"

    state3 = {"reflection": "OK 足够了", "iterations": 1}
    assert should_continue(state3) == "write"

    print("✅ 循环/分支逻辑正确（再检索 / 停止写作）")


def test_ui_stream_flow():
    """UI 的逐步过程依赖 stream_mode='updates'。

    这里曾经误用 'values'：该模式下每个 chunk 是「完整 state」（一个 dict），
    解包成 (节点名, state) 会直接抛
    `too many values to unpack (expected 2)` —— 即 Web UI 上那个报错。
    旧测试只覆盖 run_research()（invoke 路径），从没走到 stream，故 bug 溜过 CI。
    本用例把这条路径固化下来，避免回归。
    """
    if not _has("gradio"):
        print("⚠️ 跳过 UI stream 用例：未安装 gradio")
        return

    import src.ui as ui

    def fake_invoke(messages, **kw):
        sys_msg = next(
            (m for m in messages if getattr(m, "type", "") == "system"), None
        )
        text = sys_msg.content if sys_msg else ""
        if "研究要点" in text:
            return MagicMock(content="1. 定位\n2. 场景")
        if "是否足以回答" in text:
            return MagicMock(content="OK")
        return MagicMock(content="【Mock 最终答案】来自 UI 的答复。")

    with patch("src.graph.build_index_from_dir", return_value=None), patch(
        "src.graph.format_context", return_value="【Mock 资料】"
    ), patch("src.graph.get_llm") as mock_get:
        mock_get.return_value = MagicMock(invoke=fake_invoke)
        # run_research 是生成器：必须先消费完，最后一次 yield 才是最终结果
        updates = list(ui.run_research("测试问题", use_deep=False))

    steps, answer = updates[-1]
    # 流式要求：过程须按节点分批产出；若退回「一次性返回」，这里会先挂
    assert len(updates) >= 4, f"过程应逐步 yield，实际仅 {len(updates)} 次"
    assert "❌" not in steps, f"UI 执行失败：{steps}"
    assert "执行节点" in steps, f"未展示节点过程：{steps}"
    assert "Mock 最终答案" in answer, f"答案异常：{answer}"
    print(f"✅ UI stream 流程通过（共 yield {len(updates)} 次，逐步产出）")


if __name__ == "__main__":
    if not FULL_MODE:
        missing = [
            name
            for name, ok in (
                ("langgraph", HAS_LANGGRAPH),
                ("langchain_core", HAS_LANGCHAIN_CORE),
            )
            if not ok
        ]
        # 无依赖环境：跑纯逻辑兜底验证
        print(f"⚠️ 未安装 {missing}，自动降级运行 verify_pure.py 的纯逻辑校验")
        from scripts.verify_pure import test_branch, test_state_flow

        test_branch()
        test_state_flow()
        print("\n🎉 降级验证通过（安装依赖后可跑完整版：python scripts/verify.py）")
    else:
        test_graph_structure()
        test_full_flow()
        test_reflect_loop()
        test_ui_stream_flow()
        print("\n🎉 全部验证通过！项目结构无语法/导入错误。")
        print("   下一步：填入真实 API Key 后运行  python -m src.main '你的问题'")
