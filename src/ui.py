"""
ui.py —— Gradio Web UI（给非技术同事演示）

运行:  python -m src.ui
访问:  http://localhost:7860

可通过命令行参数覆盖默认 host/port：
    python -m src.ui --server-name 0.0.0.0 --server-port 7860

注意：必须用 `-m` 方式运行（原因见 src/main.py 顶部说明）。
"""

import argparse

import gradio as gr
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from src.graph import build_graph

load_dotenv()

graph = build_graph()


def run_research(query: str, use_deep: bool = False):
    """流式执行研究流程。

    这是一个生成器：每完成一个节点就 yield 一次，Gradio 会把每次 yield 刷新到
    界面上，所以「执行过程」是逐步出现的，而不是全部跑完后一次性显示。
    """
    steps: list[str] = []

    def emit(line: str | None = None) -> str:
        """追加一行过程日志（可选），返回当前完整的步骤文本。"""
        if line is not None:
            steps.append(line)
        return "\n".join(steps)

    if not query.strip():
        yield "请输入问题", ""
        return

    try:
        # ---- 进阶：DeepAgents ----
        # 复用 src.deep_research，而不是在这里自己 create_deep_agent：
        # 那边用的是 get_llm()，会跟随 .env 的 LLM_PROVIDER / LLM_MODEL；
        # 若在此硬编码 model="openai:gpt-4o-mini"，配了方舟的用户一切到满配模式
        # 就会因缺少 OpenAI 官方 Key 而失败。
        if use_deep:
            steps.append("🚀 使用 DeepAgents 满配模式")
            yield emit(), ""
            try:
                from src.deep_research import run_deep_research

                yield emit("✅ 完成"), run_deep_research(query)
                return
            except (ImportError, RuntimeError) as e:
                steps.append(f"⚠️ DeepAgents 不可用：{e}")
                steps.append("   已自动回退到 LangGraph 标准模式\n")

        # ---- 标准：LangGraph 工作流 ----
        yield emit("🚀 开始研究..."), ""
        cfg = {"configurable": {"thread_id": "ui-session"}}
        answer = ""

        # stream_mode 传 list 是为了同时拿到两类事件：
        #   updates  → payload 为 {节点名: 该节点返回的增量}，用来刷新「执行过程」
        #   messages → payload 为 (消息块, metadata)，用来让答案逐字流出
        # 只用 updates 的话，答案只能等 write 节点整个跑完才拿得到。
        for mode, payload in graph.stream(
            {"query": query, "messages": [HumanMessage(content=query)]},
            cfg,
            stream_mode=["updates", "messages"],
        ):
            if mode == "updates":
                for step_name, update in payload.items():
                    update = update if isinstance(update, dict) else {}
                    steps.append(f"📍 执行节点: **{step_name}**")
                    if step_name == "plan" and update.get("plan"):
                        steps.append(f"   📋 计划: {update['plan']}")
                    elif step_name == "retrieve":
                        ctx_len = len(str(update.get("context", "")))
                        steps.append(f"   🔍 检索到资料（{ctx_len} 字符）")
                    elif step_name == "reflect":
                        steps.append("   🤔 反思中...")
                    elif step_name == "write":
                        steps.append("   ✍️ 生成最终答案...")
                    yield emit(), answer
            elif mode == "messages":
                # 只拼接 write 节点的输出：plan / reflect 的内部思考不该流进答案
                try:
                    msg_chunk, metadata = payload
                except (TypeError, ValueError):
                    continue
                meta = metadata if isinstance(metadata, dict) else {}
                content = getattr(msg_chunk, "content", "")
                if meta.get("langgraph_node") == "write" and isinstance(content, str):
                    if content:
                        answer += content
                        yield emit(), answer

        # 兜底：mock / 非流式 LLM 不会产生 messages 事件，答案从最终 state 取
        final_state = graph.get_state(cfg)
        if final_state and final_state.values.get("messages"):
            answer = final_state.values["messages"][-1].content
        elif not answer:
            answer = "未能生成答案"
        yield emit(), answer

    except Exception as e:
        yield f"❌ 错误: {e!s}", ""


def main():
    parser = argparse.ArgumentParser(description="LangStack Gradio Web UI")
    parser.add_argument("--server-name", default="0.0.0.0")
    parser.add_argument("--server-port", type=int, default=7860)
    args = parser.parse_args()

    with gr.Blocks(title="深度研究助手 Demo", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            "# 🔬 深度研究助手 Demo\n"
            "基于 **LangChain + LlamaIndex + LangGraph + DeepAgents**"
        )

        with gr.Row():
            with gr.Column(scale=3):
                query_input = gr.Textbox(
                    label="研究问题",
                    placeholder="例如：LangGraph 和 DeepAgents 的取舍？",
                    lines=2,
                )
                use_deep = gr.Checkbox(label="使用 DeepAgents 满配模式", value=False)
                run_btn = gr.Button("🚀 开始研究", variant="primary")
            with gr.Column(scale=7):
                steps_output = gr.Textbox(
                    label="执行过程（实时）",
                    lines=15,
                    max_lines=25,
                    interactive=False,
                    autoscroll=True,  # 流式追加时自动滚到最新一行
                )
                answer_output = gr.Markdown(label="最终答案")

        run_btn.click(
            fn=run_research,
            inputs=[query_input, use_deep],
            outputs=[steps_output, answer_output],
            show_progress="full",
        )

        gr.Markdown(
            "--- \n"
            "**技术栈**: LangChain (模型层) · LlamaIndex (数据层) · "
            "LangGraph (编排层) · DeepAgents (自主层) · LangSmith (观测)"
        )

    # 生成器式的流式输出依赖 queue：未启用时，中间结果不会逐步刷新到前端，
    # 界面会退化成「跑完后一次性显示」。
    demo.queue()
    demo.launch(server_name=args.server_name, server_port=args.server_port, share=False)


if __name__ == "__main__":
    main()
