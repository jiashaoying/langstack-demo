"""
main.py —— 统一 CLI 入口

用法：
    python src/main.py "你的问题"            # 用 LangGraph 工作流
    python src/main.py "你的问题" --deep     # 用 DeepAgents（需安装）

环境变量：
    LANGSMITH_TRACING=true  开启后可在 LangSmith 后台看完整 trace
"""
import argparse

from src.config import settings


def main():
    parser = argparse.ArgumentParser(description="LangStack 深度研究助手 Demo")
    parser.add_argument("question", nargs="?", help="研究问题")
    parser.add_argument("--deep", action="store_true", help="使用 DeepAgents 满配模式")
    parser.add_argument("--no-rag", action="store_true", help="跳过 RAG 检索，纯模型回答")
    args = parser.parse_args()

    question = args.question or "LangChain、LangGraph、DeepAgents、LlamaIndex 各自适合什么场景？"

    print("=" * 60)
    print(f"问题：{question}")
    print(f"模型：{settings.LLM_PROVIDER}/{settings.LLM_MODEL}")
    print(f"LangSmith 追踪：{'开启' if settings.LANGSMITH_TRACING else '关闭'}")
    print("=" * 60)

    if args.deep:
        # ---- 进阶：DeepAgents ----
        from src.deep_research import run_deep_research

        answer = run_deep_research(question)
    else:
        # ---- 默认：LangGraph 工作流 ----
        from src.graph import run_research

        answer = run_research(question)

    print("\n📝 最终答案：\n")
    print(answer)


if __name__ == "__main__":
    main()
