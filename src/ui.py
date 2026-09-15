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
    """执行研究流程，返回逐步过程 + 最终答案。"""
    if not query.strip():
        return "请输入问题", ""

    steps = []
    final_answer = ""

    try:
        # ---- 进阶：DeepAgents ----
        # 复用 src.deep_research，而不是在这里自己 create_deep_agent：
        # 那边用的是 get_llm()，会跟随 .env 的 LLM_PROVIDER / LLM_MODEL；
        # 若在此硬编码 model="openai:gpt-4o-mini"，配了方舟的用户一切到满配模式就会
        # 因缺少 OpenAI 官方 Key 而失败。
        if use_deep:
            steps.append("🚀 使用 DeepAgents 满配模式")
            try:
                from src.deep_research import run_deep_research

                final_answer = run_deep_research(query)
                steps.append("✅ 完成")
                return "\n".join(steps), final_answer
            except (ImportError, RuntimeError) as e:
                steps.append(f"⚠️ DeepAgents 不可用：{e}")
                steps.append("   已自动回退到 LangGraph 标准模式\n")

        # ---- 标准：LangGraph 工作流 ----
        steps.append("🚀 开始研究...")
        thread_id = "ui-session"
        cfg = {"configurable": {"thread_id": thread_id}}

        # stream_mode 必须用 "updates"：
        #   updates → 每个 chunk 是 {节点名: 该节点返回的增量}，能拿到节点名
        #   values  → 每个 chunk 是「完整 state」这个 dict，把它解包成
        #             (节点名, state) 两个值会直接抛 "too many values to unpack"
        for chunk in graph.stream(
            {"query": query, "messages": [HumanMessage(content=query)]},
            cfg,
            stream_mode="updates",
        ):
            for step_name, update in chunk.items():
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

        final_state = graph.get_state(cfg)
        if final_state and final_state.values.get("messages"):
            final_answer = final_state.values["messages"][-1].content
        else:
            final_answer = "未能生成答案"

        return "\n".join(steps), final_answer

    except Exception as e:
        return f"❌ 错误: {e!s}", ""


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
                    label="执行过程（实时）", lines=15, max_lines=25, interactive=False
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

    demo.launch(server_name=args.server_name, server_port=args.server_port, share=False)


if __name__ == "__main__":
    main()
