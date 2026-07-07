"""FEK 基础演示 —— 完全离线运行于 mock 模式（无需 API key）。

运行：
    python examples/basic_demo.py
"""

import pathlib
import sys

# 将项目根目录加入导入路径，使脚本在任意目录都能直接运行
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from fek import FEKKernel


def main() -> None:
    kernel = FEKKernel()
    tasks = [
        "法国的首都是哪里？",
        "为新入职的后端工程师制定一份 3 天入职计划。",
        "对比并辩论 SQL 与 NoSQL 在实时分析看板中的取舍，"
        "需兼顾一致性、延迟与运维成本。",
    ]
    print("=" * 70)
    print("FEK —— 自适应 AI 执行引擎  （mock 模式，离线）")
    print("=" * 70)
    for prompt in tasks:
        print(f"\n任务：{prompt}")
        result = kernel.run(prompt)
        print("  ->", result.summary())
        print("  策略说明：", kernel.policy.explain(result.complexity_score))
        print("  --- 最终输出 ---")
        print("  " + result.final_output.replace("\n", "\n  "))
    print("\n" + "=" * 70)
    print("遥测（成本感知推理叙事）")
    print("=" * 70)
    print(kernel.telemetry.summary())


if __name__ == "__main__":
    main()
