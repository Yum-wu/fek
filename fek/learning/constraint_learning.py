"""约束感知学习工具（RFC 0013 · v2 约束学习）。

把"约束"真正接入学习闭环：
- ``profile_context_key``：把连续的 ``ConstraintProfile`` 离散化为 bandit 可用的上下文键；
- ``constraint_aware_reward``：在 ``compute_reward`` 基础上，对预算/延迟/隐私/min_quality
  违规叠加硬惩罚，使学习器有动机主动避开"质量高但炸穿约束"的策略。

仅依赖标准库 + ``fek.core.types``，不破坏零依赖核心。
"""

from __future__ import annotations

from ..core.types import ConstraintProfile, Constraints
from .reward import compute_reward


def profile_context_key(profile: ConstraintProfile) -> str:
    """把约束画像离散化为稳定的上下文键，供 bandit 分桶。

    维度：隐私级别 / 质量档 / 预算档 / 延迟档 / 是否强模型受限（候选≤1）。
    上下文空间可控且可解释，例如 ``p0|qmid|bnone|lnone|m0``。
    """
    q = profile.normalized_quality
    q_bucket = "lo" if q < 0.7 else ("mid" if q < 0.85 else "hi")

    if profile.budget is None:
        b_bucket = "none"
    else:
        b_bucket = "tight" if profile.budget <= 0.0005 else "loose"

    if profile.latency is None:
        l_bucket = "none"
    else:
        l_bucket = "tight" if profile.latency <= 300 else "loose"

    # m=1 表示候选模型≤1（强隐私 / 单模型受限场景）
    m_flag = "1" if profile.allowed_models and len(profile.allowed_models) <= 1 else "0"

    return f"p{profile.privacy_level}|q{q_bucket}|b{b_bucket}|l{l_bucket}|m{m_flag}"


def constraint_aware_reward(
    quality: float,
    cost_usd: float,
    latency_ms: float,
    constraints: Constraints | None = None,
    used_models: list[str] | None = None,
) -> float:
    """约束感知奖励：基础奖励减去硬约束违规惩罚。

    - 基础：``compute_reward(quality, cost, latency)`` = 质量 − λ·成本 − μ·延迟；
    - 超预算 / 超延迟：各 +1.0（明确"不可接受"量级，盖过质量收益）；
    - ``local_only`` 却用了非本地模型：+2.0（最严重，隐私红线）；
    - 质量未达 ``min_quality``：补差值惩罚。
    ``constraints is None`` 时退化为原 ``compute_reward``（向后兼容）。
    """
    r = compute_reward(quality, cost_usd, latency_ms)
    if constraints is None:
        return r

    penalty = 0.0
    if constraints.max_cost_usd is not None and cost_usd > constraints.max_cost_usd:
        penalty += 1.0
    if constraints.max_latency_ms is not None and latency_ms > constraints.max_latency_ms:
        penalty += 1.0
    if constraints.privacy == "local_only" and used_models:
        if any(m != "local-model" for m in used_models):
            penalty += 2.0
    if quality < constraints.min_quality:
        penalty += constraints.min_quality - quality

    return r - penalty
