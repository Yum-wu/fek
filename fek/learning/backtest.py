"""离线回测基准 —— 对比「学习后策略」与「固定阈值策略」。

确定性、可复现、零依赖。CI 用它证明「学习后不劣于固定阈值」（见 tests/test_backtest.py）。
逻辑提炼自 examples/learning_replay.py（该示例现改为调用本模块，单一事实来源）。

环境模型（_ENV）给定 (复杂度档, 策略) 的质量/成本/延迟，体现 FEK 叙事：
- 简单任务：SINGLE 质量已很高且最便宜；MOA 在这里是浪费。
- 困难任务：SINGLE 质量低；MOA 质量最高但最贵；MULTI 居中。
在强成本惩罚下，MOA 的「贵 + 慢」使其奖励反而最低，于是学习器会学会
「够好的质量 + 更低成本」的 MULTI，而非盲目堆最贵的 MOA。
"""

from __future__ import annotations

from ..core.types import Complexity, Strategy
from ..learning import create_learner
from ..learning.reward import compute_reward
from ..policy import PolicyEngine


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

# 交错数据集：确保训练集覆盖三个档位，否则验证阶段遇冷启动档会退化为第一臂
_DATASET = [b for _ in range(10) for b in (Complexity.LOW, Complexity.MEDIUM, Complexity.HIGH)]

# 固定阈值规则用的分数映射（驱动阈值，避免恒定 0.5 永远落在 MEDIUM 档导致比较失真）
_BAND_SCORE = {Complexity.LOW: 0.1, Complexity.MEDIUM: 0.5, Complexity.HIGH: 0.9}


def _evaluate(policy: PolicyEngine, train_n: int, use_learning: bool, lam: float, mu: float) -> dict:
    """在数据集上评估：前 train_n 条训练，其余验证。验证阶段关闭探索（纯利用）。"""
    policy.learning = use_learning
    costs, quals, rewards = [], [], []
    for i, band in enumerate(_DATASET):
        strategy = policy.select(_BAND_SCORE[band], band)
        q, c, l = _ENV[band][strategy]
        if i < train_n:
            # 训练阶段：用真实反馈更新学习层
            policy.learn(_BAND_SCORE[band], band, strategy, q, c, l)
        else:
            # 验证阶段：关闭探索，纯利用已学到的偏好（否则随机探索污染指标）
            if use_learning:
                policy.bandit.epsilon = 0.0
            costs.append(c)
            quals.append(q)
            rewards.append(compute_reward(q, c, l, lam=lam, mu=mu))
    n = max(1, len(costs))
    return {
        "avg_cost": sum(costs) / n,
        "avg_quality": sum(quals) / n,
        "avg_reward": sum(rewards) / n,
        "efficiency": (sum(quals) / n) / max(1e-9, (sum(costs) / n)),
    }


def run_backtest(
    train_n: int = 20,
    lam: float = 1.5,
    mu: float = 0.5,
    warmup: int = 4,
    epsilon: float = 0.1,
    seed: int = 42,
    state_path: str | None = None,
) -> dict:
    """运行离线回测，返回固定阈值 vs 学习后 的指标对比。

    返回结构：
        {
          "train_n": int, "val_n": int,
          "fixed": {avg_cost, avg_quality, avg_reward, efficiency},
          "learned": {...同},
          "learned_no_worse": bool,  # learned.avg_reward >= fixed.avg_reward - 1e-9
        }

    ``seed`` 固定以保证 CI 可复现：训练阶段探索被 seed 锁定，验证阶段 ε=0 纯利用。
    ``state_path=None`` 确保每次回测从冷启动学起，不被外部存盘污染。
    """
    fixed = PolicyEngine(learning=False)
    fixed_res = _evaluate(fixed, train_n, use_learning=False, lam=lam, mu=mu)

    # 学习策略：用种子锁定探索，保证确定性与可复现
    learned = PolicyEngine(
        learning=True,
        warmup=warmup,
        epsilon=epsilon,
        reward_lambda=lam,
        reward_mu=mu,
        state_path=state_path,
        bandit=create_learner("epsilon_greedy", epsilon=epsilon, seed=seed),
    )
    learned_res = _evaluate(learned, train_n, use_learning=True, lam=lam, mu=mu)

    learned_no_worse = learned_res["avg_reward"] >= fixed_res["avg_reward"] - 1e-9
    return {
        "train_n": train_n,
        "val_n": len(_DATASET) - train_n,
        "fixed": fixed_res,
        "learned": learned_res,
        "learned_no_worse": learned_no_worse,
    }
