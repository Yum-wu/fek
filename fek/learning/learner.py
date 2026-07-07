"""Learner 协议 + 工厂 —— 策略学习层的统一契约（可切换算法的基石）。

任何 learner（ε-greedy / LinUCB / ...）都必须实现这些方法，`PolicyEngine` 只依赖此
协议，不依赖具体算法。这样换算法无需改 `PolicyEngine` 内部，满足 RFC 0009「可切换」。

约定：
- 上下文 `ctx`（context_key）：通常是复杂度档（"low" / "medium" / "high"）。
- 臂 `arm`：Strategy 枚举值（"single" / "multi_agent" / "moa"）。
- 奖励 `reward`：由 `fek.learning.reward.compute_reward` 给出（质量 − 成本/延迟惩罚）。
"""

from __future__ import annotations

from typing import Hashable, List, Protocol, runtime_checkable


@runtime_checkable
class Learner(Protocol):
    """策略学习器契约：上下文老虎机的统一接口。"""

    total_feedback: int

    def select(
        self, context_key: Hashable, arms: List[Hashable], epsilon: float | None = None
    ) -> Hashable: ...

    def update(self, context_key: Hashable, arm: Hashable, reward: float) -> None: ...

    def mean_reward(self, context_key: Hashable, arm: Hashable) -> float: ...

    def count(self, context_key: Hashable, arm: Hashable) -> int: ...

    def best_arm(self, context_key: Hashable, arms: List[Hashable]) -> Hashable: ...

    def to_dict(self) -> dict: ...

    @classmethod
    def from_dict(cls, d: dict) -> "Learner": ...

    def snapshot(self): ...


def create_learner(name: str = "epsilon_greedy", **kwargs) -> Learner:
    """learner 工厂：可切换算法，零依赖核心默认 ε-greedy。

    - ``"epsilon_greedy"`` → 现有 ``ContextualBandit``（默认，零依赖，最易演示）。
    - ``"linucb"`` → v2.1 预留，需引入 numpy；当前明确抛 ``NotImplementedError``，
      作为可扩展点但不破坏零依赖核心（见 RFC 0009）。

    返回对象在结构上满足 ``Learner`` 协议。
    """
    if name == "epsilon_greedy":
        # 延迟导入避免循环：bandit 已实现 Learner 契约
        from .bandit import ContextualBandit

        return ContextualBandit(**kwargs)
    if name == "linucb":
        raise NotImplementedError(
            "LinUCB 为 v2.1 预留，需引入 numpy（可选依赖）。当前默认 epsilon_greedy。"
        )
    raise ValueError(f"未知 learner：{name!r}（可选：epsilon_greedy）")
