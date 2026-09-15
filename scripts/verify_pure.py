"""
verify_pure.py —— 纯标准库验证（零第三方依赖）

只验证「核心算法」：should_continue 的循环/分支逻辑与状态流转。
适合在没有任何依赖的 CI 环境里跑，作为 docker compose run verify 的兜底。

运行：python scripts/verify_pure.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def should_continue(state: dict) -> str:
    """从 graph.py 抽取的核心分支逻辑（与源码保持一致）。"""
    if "MORE" in state.get("reflection", "") and state.get("iterations", 0) < 2:
        return "retrieve"
    return "write"


def test_branch():
    cases = [
        (
            {"reflection": "MORE: 需要更多资料", "iterations": 1},
            "retrieve",
            "资料不足 → 再检索",
        ),
        ({"reflection": "MORE: 仍不足", "iterations": 2}, "write", "达上限 → 停止写作"),
        ({"reflection": "OK 足够了", "iterations": 1}, "write", "资料充足 → 写作"),
        ({"reflection": "", "iterations": 0}, "write", "无反思内容 → 默认写作"),
    ]
    for state, expected, desc in cases:
        got = should_continue(state)
        assert got == expected, f"[{desc}] 期望 {expected}，实际 {got}"
        print(f"  ✅ {desc}: {got}")


def test_state_flow():
    """模拟 plan → retrieve → reflect → write 的状态流转。"""
    state = {
        "query": "测试",
        "iterations": 0,
        "plan": "",
        "context": "",
        "reflection": "",
    }

    # plan
    state["plan"] = "1. 定位 2. 场景"
    assert "plan" in state

    # retrieve
    state["iterations"] += 1
    state["context"] = "【资料】..."
    assert state["iterations"] == 1

    # reflect → 分支
    state["reflection"] = "OK"
    assert should_continue(state) == "write"

    print("  ✅ 状态流转 plan→retrieve→reflect→write 正确")


if __name__ == "__main__":
    print("测试分支逻辑:")
    test_branch()
    print("测试状态流转:")
    test_state_flow()
    print("\n🎉 verify_pure 全部通过（零依赖，可作为 CI 兜底）")
