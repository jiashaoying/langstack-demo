"""
deep_research.py —— DeepAgents 满配自主研究（进阶入口）

定位：演示 DeepAgents 的核心价值 —— 几行代码拿到
「规划 + 文件系统 + 子代理 + 上下文压缩 + 记忆」的满配 Agent。

注意：需要 Python 3.11+ 且已 `pip install deepagents`。
本模块做了惰性导入，环境不满足时自动跳过，不影响其它模块运行。
"""
from src.llm import get_llm


def _build_agent():
    """惰性导入 DeepAgents，避免硬依赖。"""
    try:
        from deepagents import create_deep_agent
    except ImportError:
        raise RuntimeError("DeepAgents 未安装。请 `pip install deepagents`（需 Python 3.11+）")

    # 把 LlamaIndex 检索器包装成工具，演示产品协作
    def search_knowledge_base(query: str) -> str:
        """检索本地知识库（基于 LlamaIndex）。"""
        try:
            from src.retriever import (
                build_index_from_dir,
                format_context,
                get_retriever,
            )

            idx = build_index_from_dir()
            return format_context(get_retriever(idx), query)
        except Exception as e:
            return f"检索失败：{e}"

    # 用 DeepAgents 自带工具 + 我们自定义的检索工具
    return create_deep_agent(
        model=get_llm(),
        tools=[search_knowledge_base],
        system_prompt="你是深度研究助手：先列计划，再检索/调研，最后出带引用的结构化报告。",
    )


def run_deep_research(question: str) -> str:
    """用 DeepAgents 跑一次自主研究。"""
    agent = _build_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    # 取最后一条 AI 消息
    for msg in reversed(result.get("messages", [])):
        if getattr(msg, "type", "") == "ai":
            return msg.content
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            return msg.get("content", "")
    return str(result)


if __name__ == "__main__":
    print(run_deep_research("对比 LangGraph 与 DeepAgents 的适用场景"))
