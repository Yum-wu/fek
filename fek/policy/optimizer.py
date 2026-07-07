"""策略优化器（Policy Optimizer，RFC 0011）。

输入从旧 ``PolicyEngine`` 的"复杂度评分"升级为 ``ConstraintProfile``：
- 硬约束（隐私 / 预算 / 延迟）作为不可违反的剪枝条件，由 ``supports()`` + 预算/延迟预估把关；
- 软目标（质量）作为优化目标，用 ``质量 − λ·成本 − μ·延迟`` 在可行策略中择优；
- 策略集合来自 **Strategy Library**（RFC 0012），引擎核心不再硬编码。

``PolicyEngine`` 原样保留作向后兼容（见 ``policy/engine.py``）；本类是新定位下的首选决策器。
学习层（约束感知奖励）为 v2 范畴（RFC 0011 Future Work），此处先提供确定、可解释的选择。
"""

from __future__ import annotations

from ..core.types import ConstraintProfile
from ..learning.constraint_learning import profile_context_key
from ..learning.learner import Learner
from ..learning.reward import (
    COST_BUDGET_USD,
    DEFAULT_LAMBDA,
    DEFAULT_MU,
    LATENCY_BUDGET_MS,
)
from ..models.mock import _MODEL_PROFILE
from ..strategies.protocol import BaseStrategy
from ..strategies.registry import DEFAULT_LIBRARY, StrategyLibrary

# 模型 -> (单次成本, 单次延迟) 的估算表（与 MockBackend 对齐，仅用于剪枝预估）
_MODEL_PROFILES: dict[str, tuple[float, float]] = {
    m: (v["cost"], v["latency"]) for m, v in _MODEL_PROFILE.items()
}


class PolicyOptimizer:
    def __init__(
        self,
        library: StrategyLibrary | None = None,
        reward_lambda: float = DEFAULT_LAMBDA,
        reward_mu: float = DEFAULT_MU,
        model_profiles: dict[str, tuple[float, float]] | None = None,
        learner: "Learner | None" = None,
        warmup: int = 8,
    ):
        self.library = library or DEFAULT_LIBRARY
        self.lam = reward_lambda
        self.mu = reward_mu
        # 用首个可用模型作为估算代表（启发式；v2 可换更精细的逐模型估算）
        self.model_profiles = model_profiles or _MODEL_PROFILES
        # v2 约束学习：可选 learner（默认 None = 纯静态、确定、向后兼容）
        self.learner = learner
        self.warmup = warmup
        self._last_mode = "static"  # 最近一次 select 的决策来源（learned/static），供 explain
        self._last_strategy = None  # 最近一次 select 选中的策略对象，供观察/面板

    def _pruned_reasons(self, strategy: BaseStrategy, profile: ConstraintProfile) -> list[str]:
        cost, lat = strategy.estimate(self.model_profiles)
        reasons: list[str] = []
        if profile.budget is not None and cost > profile.budget:
            reasons.append("超预算")
        if profile.latency is not None and lat > profile.latency:
            reasons.append("超延迟")
        return reasons

    def select(self, profile: ConstraintProfile) -> BaseStrategy | None:
        """在约束下选出最优策略；无任何可行策略时返回 None（由调用方报告不可行）。

        决策来源（见 ``explain`` / ``self._last_mode``）：
        - 若挂载了 learner 且已热身、且当前上下文已有样本，则优先采用学习到的偏好；
        - 否则（含学习器选中的策略仍违反硬约束时）回退纯静态择优。
        """
        feasible = self.library.filter(profile)
        if not feasible:
            self._last_strategy = None
            return None

        feasible_names = [s.name for s in feasible]

        # —— 学习路径（v2 约束学习，RFC 0013）——
        learned: BaseStrategy | None = None
        if self.learner is not None and self.learner.total_feedback >= self.warmup:
            ctx = profile_context_key(profile)
            if any(self.learner.count(ctx, a) > 0 for a in feasible_names):
                chosen_arm = self.learner.best_arm(ctx, feasible_names)
                cand = self.library.get(chosen_arm)
                # 安全校验：学习选中的策略必须仍在可行集且未违反硬约束
                if cand is not None and cand in feasible and not self._pruned_reasons(cand, profile):
                    learned = cand

        if learned is not None:
            self._last_mode = "learned"
            self._last_strategy = learned
            return learned

        # —— 静态回退（v1）——
        self._last_mode = "static"
        chosen = self._static_select(feasible, profile)
        self._last_strategy = chosen
        return chosen

    def _static_select(self, feasible: list[BaseStrategy], profile: ConstraintProfile) -> BaseStrategy | None:
        """纯静态择优：硬约束剪枝 + 软目标（质量 − 成本 − 延迟）最大化。"""
        chosen: BaseStrategy | None = None
        best_score: float | None = None
        for s in feasible:
            if self._pruned_reasons(s, profile):
                continue  # 硬约束剪枝
            cost, lat = s.estimate(self.model_profiles)
            score = (
                s.quality_est
                - self.lam * (cost / COST_BUDGET_USD)
                - self.mu * (lat / LATENCY_BUDGET_MS)
            )
            if best_score is None or score > best_score:
                best_score = score
                chosen = s

        # 硬约束把全部剪光时，退回最便宜的可行策略（尽量给出结果，并在 explain 中说明）
        if chosen is None:
            chosen = min(feasible, key=lambda s: s.estimate(self.model_profiles)[0])
        return chosen

    def explain(self, profile: ConstraintProfile) -> str:
        """可解释输出：展示约束、候选策略的成本/延迟/质量，以及剪枝与选中原因。"""
        lines = [
            f"约束画像：质量≥{profile.normalized_quality:.2f} "
            f"预算={profile.budget} 延迟={profile.latency} 隐私级别={profile.privacy_level}"
        ]
        if not profile.feasible:
            lines.append(f"  ⚠ 不可行：{profile.infeasibility_reason}")
            return "\n".join(lines)

        lines.append(f"  候选模型：{profile.allowed_models}")
        chosen = self.select(profile)
        lines.append(
            f"  决策来源：{self._last_mode}（learner={'已挂载' if self.learner else '未挂载'}）"
        )
        for s in self.library.filter(profile):
            cost, lat = s.estimate(self.model_profiles)
            pruned = self._pruned_reasons(s, profile)
            tag = " <- 选中" if s is chosen else ""
            mark = f" [剪枝: {','.join(pruned)}]" if pruned else ""
            lines.append(
                f"  {s.zh}（{s.name}） 成本≈${cost:.5f} 延迟≈{lat:.0f}ms "
                f"质量预期≈{s.quality_est:.2f}{mark}{tag}"
            )
        return "\n".join(lines)
