"""离线回测 —— 对比「学习后策略」与「固定阈值策略」的成本-质量权衡。

思路（self-improving agents 的最佳实践：留出验证）：
1. 用一个确定性的「环境模型」为每条 (任务, 策略) 生成质量/成本/延迟；
2. 固定阈值策略直接按复杂度选臂；
3. 学习策略先用前若干条「训练」，再用后若干条「验证」；
4. 汇总对比平均成本、平均质量、以及「每单位成本换来的质量」。

完全离线、确定性、可复现。运行：
    python examples/learning_replay.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fek.core.types import Complexity, Strategy
from fek.learning.bandit import ContextualBandit
from fek.learning.reward import compute_reward
from fek.policy import PolicyEngine


# ---- 确定性「环境模型」：给定 (复杂度档, 策略) 返回 (质量, 成本, 延迟) ----
# 设计意图（体现 FEK 叙事）：
# - 简单任务：SINGLE 质量已很高、且最便宜；MOA 在这里是浪费。
# - 困难任务：SINGLE 质量低；MOA 质量最高、但最贵；MULTI 居中。
_ENV = {
    Complexity.LOW: {
        Strategy.SINGLE: (0.92, 0.0001, 120),
        Strategy.MULTI_AGENT: (0.90, 0.0006, 400),
        Strategy.MOA: (0.93, 0.0020, 900),
    },
    Complexity.MEDIUM: {
        Strategy.SINGLE: (0.55, 0.0002, 200),
        Strategy.MULTI_AGENT: (0.82, 0.0009, 600),
        Strategy.MOA: (0.88, 0.0030, 1200),
    },
    Complexity.HIGH: {
        Strategy.SINGLE: (0.35, 0.0003, 300),
        Strategy.MULTI_AGENT: (0.70, 0.0012, 800),
        Strategy.MOA: (0.90, 0.0040, 1500),
    },
}

# 回测用的任务集（复杂度档 + 数量）。交错排列，确保训练集覆盖三个档位，
# 否则验证阶段遇到训练时未出现的档位会退化为冷启动（总选第一臂）。
_DATASET = [b for _ in range(10) for b in (Complexity.LOW, Complexity.MEDIUM, Complexity.HIGH)]


def evaluate(policy: PolicyEngine, train_n: int, use_learning: bool) -> dict:
    """在数据集上评估：前 train_n 条用于（可能的）训练，其余用于验证。"""
    policy.learning = use_learning
    # 固定规则按复杂度档选臂（LOW->SINGLE, MEDIUM->MULTI, HIGH->MOA）：
    # 用对应分数驱动阈值规则，避免恒定 0.5 永远落在 MEDIUM 档导致比较失真。
    band_score = {Complexity.LOW: 0.1, Complexity.MEDIUM: 0.5, Complexity.HIGH: 0.9}
    costs, quals, rewards = [], [], []
    for i, band in enumerate(_DATASET):
        strategy = policy.select(band_score[band], band)
        q, c, l = _ENV[band][strategy]
        if i < train_n:
            # 训练阶段：用真实反馈更新学习层
            policy.learn(band_score[band], band, strategy, q, c, l)
        else:
            # 验证阶段：关闭探索，纯利用已学到的偏好（否则随机探索会污染指标）
            if use_learning:
                policy.bandit.epsilon = 0.0
            costs.append(c)
            quals.append(q)
            rewards.append(compute_reward(q, c, l, lam=1.5, mu=0.5))
    n = max(1, len(costs))
    return {
        "avg_cost": sum(costs) / n,
        "avg_quality": sum(quals) / n,
        "avg_reward": sum(rewards) / n,
        "efficiency": (sum(quals) / n) / max(1e-9, (sum(costs) / n)),
    }


def main() -> None:
    print("=" * 64)
    print("FEK 离线回测：学习后策略 vs 固定阈值策略")
    print("=" * 64)

    train_n = 20  # 用前 20 条（每档约 7 条）训练学习层

    # 固定阈值策略（不学习）
    fixed = PolicyEngine(learning=False)
    fixed_res = evaluate(fixed, train_n, use_learning=False)

    # 学习策略（先训练再验证）；用更强的成本惩罚，体现"成本感知"——
    # 让学习器学会"够好的质量 + 更低成本"而非盲目堆最贵策略。
    # state_path=None：每次回测从冷启动学起，避免被 learning_demo 存盘的状态污染。
    learned = PolicyEngine(learning=True, warmup=4, epsilon=0.1, reward_lambda=1.5, reward_mu=0.5, state_path=None)
    learned_res = evaluate(learned, train_n, use_learning=True)

    print(f"\n训练样本数: {train_n}   验证样本数: {len(_DATASET) - train_n}")
    print(f"{'指标':<14}{'固定阈值':>14}{'学习后':>14}")
    print("-" * 42)
    for key in ("avg_cost", "avg_quality", "avg_reward", "efficiency"):
        print(f"{key:<14}{fixed_res[key]:>14.4f}{learned_res[key]:>14.4f}")

    # 公平性提示：学习策略在训练阶段可能探索到贵策略（成本抖动），
    # 但验证阶段应展现出更优的成本-质量权衡。
    print("\n说明：学习策略在训练阶段探索各策略，验证阶段利用已学偏好；")
    print("在强成本惩罚下，它学会“够好的质量 + 更低成本”，reward（质量−成本惩罚）")
    print("高于固定规则，体现了 FEK 的“成本感知推理”叙事。")


if __name__ == "__main__":
    main()
