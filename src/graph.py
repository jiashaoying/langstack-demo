"""
graph.py —— LangGraph 有状态研究工作流

定位：演示 LangGraph 的核心价值 —— 用「状态图」编排多步、可循环、可分支的流程。

状态机：
    plan → retrieve → reflect → (需要更多？retrieve : write) → END
                              ↺ 反思后可再检索（循环）

State 是跨节点共享的「黑板」。Checkpointer 提供持久化（断点恢复/人机协同）。
"""
from typing import TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.llm import RESEARCHER_SYSTEM_PROMPT, get_llm
from src.retriever import build_index_from_dir, format_context, get_retriever


class ResearchState(TypedDict, total=False):
    query: str
    plan: str
    context: str
    reflection: str
    answer: str
    iterations: int
    messages: list  # 对话消息列表


# ---- 节点函数 ----
def plan_node(state: ResearchState) -> dict:
    """步骤1：把问题拆成研究计划。"""
    llm = get_llm()
    msg = llm.invoke(
        [
            SystemMessage(content="把用户问题拆成 3-5 条研究要点，用换行分隔。"),
            HumanMessage(content=state["query"]),
        ]
    )
    return {"plan": msg.content}


def retrieve_node(state: ResearchState) -> dict:
    """步骤2：依据问题检索资料。"""
    try:
        idx = build_index_from_dir()
        retriever = get_retriever(idx)
        context = format_context(retriever, state["query"])
    except Exception as e:
        context = f"（检索失败，退化为无资料模式：{e}）"
    return {"context": context, "iterations": state.get("iterations", 0) + 1}


def reflect_node(state: ResearchState) -> dict:
    """步骤3：反思资料是否足够。"""
    llm = get_llm()
    msg = llm.invoke(
        [
            SystemMessage(content=("判断当前资料是否足以回答。若足够回复『OK』；" "否则回复『MORE: <还需要什么>』。")),
            HumanMessage(
                content=f"问题：{state['query']}\n资料：\n{state.get('context', '')}"
            ),
        ]
    )
    return {"reflection": msg.content}


def write_node(state: ResearchState) -> dict:
    """步骤4：综合写出最终答案。"""
    llm = get_llm(temperature=0.2)
    msg = llm.invoke(
        [
            SystemMessage(content=RESEARCHER_SYSTEM_PROMPT),
            HumanMessage(
                content=f"问题：{state['query']}\n\n资料：\n{state.get('context', '')}"
            ),
        ]
    )
    return {"answer": msg.content, "messages": [AIMessage(content=msg.content)]}


def should_continue(state: ResearchState) -> str:
    """条件边：控制是否再循环一次。"""
    if "MORE" in state.get("reflection", "") and state.get("iterations", 0) < 2:
        return "retrieve"
    return "write"


# ---- 组装图 ----
def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("plan", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("reflect", reflect_node)
    graph.add_node("write", write_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "reflect")
    graph.add_conditional_edges(
        "reflect", should_continue, {"retrieve": "retrieve", "write": "write"}
    )
    graph.add_edge("write", END)

    # MemorySaver：进程内持久化；生产可换 PostgresSaver
    return graph.compile(checkpointer=MemorySaver())


def run_research(query: str) -> str:
    """便捷入口：跑一次研究流程，返回最终答案字符串。"""
    app = build_graph()
    config = {"configurable": {"thread_id": "default"}}
    final = app.invoke(
        {"query": query, "messages": [HumanMessage(content=query)]}, config=config
    )
    return final.get("answer", "")
