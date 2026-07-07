"""离线回测 —— 对比「学习后策略」与「固定阈值策略」的成本-质量权衡。

逻辑现由 fek/learning/backtest.py 提供（单一事实来源），本脚本只做可视化展示。
完全离线、确定性、可复现。运行：
    python examples/learning_replay.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fek.learning.backtest import run_backtest


def main() -> None:
    print("=" * 64)
    print("FEK 离线回测：学习后策略 vs 固定阈值策略")
    print("=" * 64)

    res = run_backtest()
    fixed, learned = res["fixed"], res["learned"]

    print(f"\n训练样本数: {res['train_n']}   验证样本数: {res['val_n']}")
    print(f"{'指标':<14}{'固定阈值':>14}{'学习后':>14}")
    print("-" * 42)
    for key in ("avg_cost", "avg_quality", "avg_reward", "efficiency"):
        print(f"{key:<14}{fixed[key]:>14.4f}{learned[key]:>14.4f}")

    print("\n说明：学习策略在训练阶段探索各策略，验证阶段利用已学偏好；")
    print("在强成本惩罚下，它学会“够好的质量 + 更低成本”，reward（质量−成本惩罚）")
    print("高于固定规则，体现了 FEK 的“成本感知推理”叙事。")
    print(f"\n结论：学习后不劣于固定阈值 = {res['learned_no_worse']}")


if __name__ == "__main__":
    main()
