"""学习层 —— FEK 的策略学习模块（纯标准库，零依赖）。

把"为每个任务自动选最优策略"从固定阈值规则，升级为能从执行轨迹学习的
上下文老虎机。详见 docs/learn-design.md。
"""

from __future__ import annotations

from .bandit import ContextualBandit
from .persist import load, reset, save
from .reward import (
    DEFAULT_LAMBDA,
    DEFAULT_MU,
    COST_BUDGET_USD,
    LATENCY_BUDGET_MS,
    compute_reward,
)

__all__ = [
    "ContextualBandit",
    "compute_reward",
    "save",
    "load",
    "reset",
    "DEFAULT_LAMBDA",
    "DEFAULT_MU",
    "COST_BUDGET_USD",
    "LATENCY_BUDGET_MS",
]
