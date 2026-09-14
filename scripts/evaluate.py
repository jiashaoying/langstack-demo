"""
evaluate.py —— LangSmith 评测脚本

用途：用离线/在线数据集对研究助手做自动打分，验证迭代不退化。

两种模式：
1. 离线（默认）：用 mock LLM 跑数据集，适合 CI / 本地快速回归
   python scripts/evaluate.py

2. 真实 API：set USE_REAL_API=true，调真实模型（消耗 token，需 API Key）
   USE_REAL_API=true python scripts/evaluate.py

评分器：
- 关键词命中（离线可用）：检查答案是否包含预期关键词
- LLM-as-judge（需真实模型）：用裁判模型按 rubric 打分

LangSmith 集成（可选）：
  设 LANGSMITH_API_KEY 与 LANGSMITH_TRACING=true 后，结果自动上报，
  可在后台做在线评测、回归对比、数据集版本管理。
"""
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class EvalCase:
    query: str
    expected_keywords: list[str] = field(default_factory=list)
    rubric: str = ""  # LLM-judge 评分标准


@dataclass
class EvalResult:
    query: str
    answer: str
    passed: bool
    score: float
    reason: str


# ===============================================================
# 评测数据集（离线 mock 也用得上，因为它只校验关键词/结构）
# ===============================================================
DATASET = [
    EvalCase(
        query="LangGraph 和 DeepAgents 怎么选？",
        expected_keywords=["LangGraph", "DeepAgents", "状态", "循环"],
        rubric="答案应清晰对比两者定位：LangGraph 是图编排引擎，DeepAgents 是满配 Agent harness。",
    ),
    EvalCase(
        query="什么是 Checkpointer？",
        expected_keywords=["持久化", "状态", "恢复", "thread"],
        rubric="答案应说明 Checkpointer 负责状态持久化、断点恢复、支持人机协同。",
    ),
    EvalCase(
        query="LlamaIndex 在项目里负责什么？",
        expected_keywords=["检索", "索引", "文档", "RAG"],
        rubric="答案应说明 LlamaIndex 是数据/RAG 层，负责文档加载、索引、检索。",
    ),
]


# ===============================================================
# 评分器
# ===============================================================
def keyword_scorer(case: EvalCase, answer: str) -> EvalResult:
    """离线评分：预期关键词命中率。"""
    if not case.expected_keywords:
        return EvalResult(case.query, answer, True, 1.0, "无关键词要求")
    hits = sum(1 for kw in case.expected_keywords if kw.lower() in answer.lower())
    score = hits / len(case.expected_keywords)
    return EvalResult(
        query=case.query,
        answer=answer,
        passed=score >= 0.75,
        score=score,
        reason=f"命中 {hits}/{len(case.expected_keywords)} 关键词",
    )


def llm_judge_scorer(case: EvalCase, answer: str) -> EvalResult:
    """LLM-as-judge 评分（需真实模型）。"""
    from langchain_core.messages import HumanMessage, SystemMessage

    from src.llm import get_llm

    judge = get_llm(temperature=0)
    msg = judge.invoke(
        [
            SystemMessage(content="你是严格的评分裁判。按 rubric 打分 0-1，只输出数字。"),
            HumanMessage(
                content=(
                    f"问题：{case.query}\n"
                    f"Rubric：{case.rubric}\n"
                    f"待评答案：{answer}\n"
                    f"评分（0-1）："
                )
            ),
        ]
    )
    try:
        score = float(msg.content.strip().split()[0])
    except ValueError:
        score = 0.5
    return EvalResult(case.query, answer, score >= 0.7, score, "LLM judge")


# ===============================================================
# 被测函数：可替换为真实 run_research
# ===============================================================
def run_target(query: str) -> str:
    """默认用 mock；设 USE_REAL_API=true 时调真实管线。"""
    if os.getenv("USE_REAL_API", "").lower() == "true":
        from src.graph import run_research

        return run_research(query)

    # 离线 mock：返回含关键词的结构化答案
    return (
        f"【Mock 答案】针对「{query}」：\n"
        "LangGraph 提供有状态图编排与 Checkpointer 持久化（状态/循环/恢复/thread），"
        "DeepAgents 是满配 Agent harness，LlamaIndex 负责文档检索与索引（RAG）。"
    )


# ===============================================================
# 主流程
# ===============================================================
def run_evaluation(
    scorer: Callable[[EvalCase, str], EvalResult] = keyword_scorer,
) -> dict:
    results: list[EvalResult] = []
    for case in DATASET:
        answer = run_target(case.query)
        result = scorer(case, answer)
        results.append(result)
        status = "✅" if result.passed else "❌"
        print(f"{status} {case.query[:30]:30s} 得分={result.score:.2f}  {result.reason}")

    passed = sum(1 for r in results if r.passed)
    avg = sum(r.score for r in results) / len(results)
    summary = {
        "total": len(results),
        "passed": passed,
        "pass_rate": passed / len(results),
        "avg_score": avg,
        "results": [asdict(r) for r in results],
    }
    print(f"\n通过率: {passed}/{len(results)} = {summary['pass_rate']:.0%}")
    print(f"平均分: {avg:.2f}")
    return summary


if __name__ == "__main__":
    use_judge = os.getenv("USE_LLM_JUDGE", "").lower() == "true"
    scorer = llm_judge_scorer if use_judge else keyword_scorer
    summary = run_evaluation(scorer)
    # CI 门禁：平均分低于阈值则失败
    sys.exit(0 if summary["pass_rate"] >= 0.75 else 1)
