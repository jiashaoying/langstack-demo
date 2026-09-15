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
        if use_deep:
            from deepagents import create_deep_agent

            steps.append("🚀 使用 DeepAgents 满配模式")
            agent = create_deep_agent(
                model="openai:gpt-4o-mini",
                tools=[],
                system_prompt="你是研究助手，先列计划再检索，最后出带引用的报告。",
            )
            result = agent.invoke({"messages": [{"role": "user", "content": query}]})
            final_answer = result["messages"][-1].content
            steps.append("✅ 完成")
        else:
            steps.append("🚀 开始研究...")
            thread_id = "ui-session"
            for step_name, state in graph.stream(
                {"query": query, "messages": [HumanMessage(content=query)]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="values",
            ):
                steps.append(f"📍 执行节点: **{step_name}**")
                if step_name == "plan" and state.get("plan"):
                    steps.append(f"   📋 计划: {state['plan']}")
                elif step_name == "retrieve" and state.get("context"):
                    ctx = state["context"]
                    steps.append(f"   🔍 检索到资料（{len(str(ctx))} 字符）")
                elif step_name == "reflect":
                    steps.append("   🤔 反思中...")
                elif step_name == "write":
                    steps.append("   ✍️ 生成最终答案...")
            final_state = graph.get_state({"configurable": {"thread_id": thread_id}})
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
