#!/usr/bin/env python3
"""
ci_local.py —— 本地模拟 CI 流程（不依赖 GitHub Actions）

依次跑：lint(bash) → verify_pure → verify_full → evaluate
用法：python scripts/ci_local.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def step(name: str, fn) -> bool:
    print(f"\n{'=' * 50}\n▶ {name}\n{'=' * 50}")
    try:
        fn()
        print(f"✅ {name} 通过")
        return True
    except Exception as e:
        print(f"❌ {name} 失败: {e}")
        return False


def run_cmd(cmd: str):
    result = subprocess.run(cmd, shell=True, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"命令退出码 {result.returncode}: {cmd}")


def main():
    results = {}

    # 1. Lint（ruff 可选，未装则跳过）
    def lint():
        try:
            import ruff  # noqa
        except ImportError:
            print("ruff 未安装，跳过（CI 中会自动安装）")
            return
        run_cmd("ruff check src scripts")

    results["lint"] = step("Lint (ruff)", lint)

    # 2. verify_pure
    results["verify_pure"] = step(
        "Verify Pure", lambda: run_cmd("python scripts/verify_pure.py")
    )

    # 3. verify_full（依赖缺失会自动降级）
    results["verify_full"] = step(
        "Verify Full", lambda: run_cmd("python scripts/verify.py")
    )

    # 4. evaluate（离线）
    results["evaluate"] = step(
        "Evaluate (offline)", lambda: run_cmd("python scripts/evaluate.py")
    )

    # 汇总
    print(f"\n{'=' * 50}\n📊 汇总\n{'=' * 50}")
    for k, v in results.items():
        print(f"  {'✅' if v else '❌'} {k}")
    failed = [k for k, v in results.items() if not v]
    if failed:
        print(f"\n❌ 失败: {failed}")
        sys.exit(1)
    print("\n🎉 本地 CI 全部通过，可放心推送")


if __name__ == "__main__":
    main()
