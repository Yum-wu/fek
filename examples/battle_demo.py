"""对战演示 —— 用全部三种策略并排执行同一个困难任务。

展示 FEK 的核心价值：由*系统*选择计算策略，也可以强制对比三种策略，
直观看到成本 / 质量 / 延迟之间的权衡。

运行：
    python examples/battle_demo.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from fek import FEKKernel, Strategy


def main() -> None:
    kernel = FEKKernel()
    prompt = (
        "对比并辩论微服务与单体架构在高速成长型初创公司中的取舍，"
        "需考虑延迟、成本与团队结构。"
    )
    print("=" * 70)
    print("FEK 对战模式")
    print("任务：", prompt)
    print("=" * 70)

    results = kernel.run_all_strategies(prompt)
    for strategy in (Strategy.SINGLE, Strategy.MULTI_AGENT, Strategy.MOA):
        r = results[strategy]
        print(f"\n### 策略：{strategy.value.upper()}")
        print("  " + r.summary())
        print("  最终输出（前 240 字）：")
        print("  " + r.final_output[:240].replace("\n", "\n  "))

    print("\n" + "=" * 70)
    print("结论：SINGLE 最省最快；MOA / MULTI_AGENT 在复杂任务上投入更多算力，")
    print("换取更高质量、更多视角的答案。")
    print("=" * 70)


if __name__ == "__main__":
    main()
