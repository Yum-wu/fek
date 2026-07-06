"""奖励函数 —— FEK "成本感知推理" 的引擎。

把一次执行轨迹转化为一个标量奖励，供学习层（contextual bandit）优化。
设计原则：
- 质量越高，奖励越高；
- 成本 / 延迟作为惩罚项 —— 这正是 FEK 区别于"无脑堆算力"的核心叙事：
  "更贵的策略必须拿出更高的质量才划算"。

在 mock 模式下，quality / cost / latency 由 MockBackend 给出（确定性、可复现），
因此学习曲线稳定可演示；在真实模式下，奖励信号来自真实账单，学习更可信。
"""

from __future__ import annotations

# 预算上限（用于把绝对成本/延迟归一化到 ~[0,1]）
COST_BUDGET_USD = 0.01       # 单次执行的成本预算（美元）
LATENCY_BUDGET_MS = 2000.0   # 单次执行的延迟预算（毫秒）

# 默认惩罚权重（偏质量，但让"贵策略"必须证明自己）
DEFAULT_LAMBDA = 0.5         # 成本惩罚系数
DEFAULT_MU = 0.3             # 延迟惩罚系数


def compute_reward(
    quality: float,
    cost_usd: float,
    latency_ms: float,
    lam: float = DEFAULT_LAMBDA,
    mu: float = DEFAULT_MU,
) -> float:
    """计算单次执行的奖励。

    reward = quality - λ * (cost / 预算) - μ * (latency / 预算)

    返回值通常落在 [-1, 1] 附近，便于跨策略横向比较。
    """
    cost_norm = cost_usd / COST_BUDGET_USD
    latency_norm = latency_ms / LATENCY_BUDGET_MS
    return quality - lam * cost_norm - mu * latency_norm
