"""约束分析（Constraint Analysis，RFC 0011）。

把 ``(Task, Constraints)`` 归一化为 ``ConstraintProfile``：
- 规范化质量下限到 [0,1]；
- 按 **隐私 / 本地开关 / 模型偏好** 过滤候选模型集合；
- 做可行性校验（若过滤后无可用模型则标记不可行并给出原因）。

该层是纯标准库实现，不依赖任何后端，便于独立测试与复用。
FEK 的"优化思维"由此起点：先把用户诉求变成可计算的硬约束与软目标。
"""

from __future__ import annotations

from ..core.types import ConstraintProfile, Constraints, Task

# 隐私档位 -> 整数级别（越高越严格）
PRIVACY_LEVELS: dict[str, int] = {
    "none": 0,
    "no_external": 1,
    "local_only": 2,
}

# 被判定为"本地模型"的名称集合（隐私约束由此过滤）
LOCAL_MODELS: set[str] = {"local-model"}

# 默认可用模型集合（与 MockBackend 对齐；真实后端可传入自己的模型列表）
DEFAULT_AVAILABLE_MODELS: list[str] = [
    "gpt-fast",
    "gpt-smart",
    "claude-x",
    "local-model",
]


def _infeasible_reason(constraints: Constraints, available: list[str]) -> str:
    """构造不可行原因，帮助 explain 与用户诊断。"""
    if constraints.preferred_models:
        missing = [m for m in constraints.preferred_models if m not in available]
        if missing and not (set(available) & set(constraints.preferred_models)):
            return f"偏好模型 {missing} 不在可用模型集合中：{available}"
    if constraints.privacy in ("local_only", "no_external") and not (
        set(available) & LOCAL_MODELS
    ):
        return f"隐私要求 {constraints.privacy}，但可用模型 {available} 中无本地模型"
    if (
        constraints.privacy in ("local_only", "no_external")
        and not constraints.allow_local_models
    ):
        return f"隐私={constraints.privacy} 但 allow_local_models=False，无可用模型"
    return "无满足硬约束的可用模型"


def analyze(
    task: Task,
    constraints: Constraints | None = None,
    available_models: list[str] | None = None,
) -> ConstraintProfile:
    """将任务与约束归一化为约束画像。

    过滤顺序（后者不推翻前者，逐步收窄候选集）：
      1. 偏好模型交集；
      2. 隐私档（local_only / no_external -> 仅留本地模型）；
      3. 本地模型开关（allow_local_models=False 时剔除本地模型）。

    参数
    ----
    task: 当前任务（用于扩展，如未来按任务语义约束模型）。
    constraints: 用户约束；为 None 时退化为默认画像（无约束，全部可用模型）。
    available_models: 后端实际可用模型；缺省用 :data:`DEFAULT_AVAILABLE_MODELS`。
    """
    constraints = constraints or Constraints()
    avail = list(available_models or DEFAULT_AVAILABLE_MODELS)

    allowed = set(avail)

    # 1. 偏好模型交集
    if constraints.preferred_models:
        allowed &= set(constraints.preferred_models)

    # 2. 隐私档过滤
    privacy_level = PRIVACY_LEVELS.get(constraints.privacy, 0)
    if constraints.privacy in ("local_only", "no_external"):
        allowed &= LOCAL_MODELS

    # 3. 本地模型开关
    if not constraints.allow_local_models:
        allowed -= LOCAL_MODELS

    # 保持 avail 中的顺序，结果稳定可复现
    allowed_models = [m for m in avail if m in allowed]

    feasible = bool(allowed_models)
    reason: str | None = None
    if not feasible:
        reason = _infeasible_reason(constraints, avail)

    return ConstraintProfile(
        normalized_quality=constraints.min_quality,
        budget=constraints.max_cost_usd,
        latency=constraints.max_latency_ms,
        privacy_level=privacy_level,
        allowed_models=allowed_models,
        feasible=feasible,
        infeasibility_reason=reason,
    )
