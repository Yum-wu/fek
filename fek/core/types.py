"""FEK 核心类型定义。

所有核心抽象均只依赖标准库，使内核能在**零**外部依赖下运行
（对黑客松 Demo 至关重要：评委必须能 `pip install` 后立刻跑起来）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Strategy(str, Enum):
    """FEK 可自动选择的三种计算策略。

    这正是 FEK 相对 LangChain / AutoGen 的价值所在：由*系统*决定
    "如何思考"，而不是由开发者写死。
    """

    SINGLE = "single"            # 单模型，一次调用
    MULTI_AGENT = "multi_agent"  # 基于角色的智能体（规划/执行/批判）
    MOA = "moa"                  # 混合智能体：并行多模型 + 融合

    @property
    def zh(self) -> str:
        """中文显示名（页面与日志使用）。"""
        _MAP = {
            "single": "单模型",
            "multi_agent": "多智能体",
            "moa": "混合专家（MoA）",
        }
        return _MAP[self.value]


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def zh(self) -> str:
        """中文显示名（页面与日志使用）。"""
        _MAP = {"low": "低", "medium": "中", "high": "高"}
        return _MAP[self.value]


@dataclass
class Constraints:
    """约束（一等输入，RFC 0011）。

    FEK 的核心问题从"按复杂度选策略"升级为"在约束下最大化质量"。
    约束是 FEK 对外叙事的主角：质量 / 预算 / 延迟 / 隐私 / 模型偏好。
    """

    min_quality: float = 0.0          # 期望质量下限（[0,1]，越界自动夹紧）
    max_cost_usd: float | None = None  # 单次执行成本上限（美元）；None 表示不限制
    max_latency_ms: float | None = None  # 单次执行延迟上限（毫秒）；None 表示不限制
    privacy: str = "none"             # none | no_external | local_only
    allow_local_models: bool = True   # 是否允许使用本地模型
    preferred_models: list[str] = field(default_factory=list)  # 偏好模型（非空则仅从这些里选）

    def __post_init__(self) -> None:
        # 质量下限归一化到 [0,1]，避免非法输入破坏下游
        self.min_quality = max(0.0, min(1.0, float(self.min_quality)))


@dataclass
class ConstraintProfile:
    """归一化后的约束画像，由 Constraint Analysis 产出，供 Policy Optimizer 消费。"""

    normalized_quality: float
    budget: float | None
    latency: float | None
    privacy_level: int              # 0=none, 1=no_external, 2=local_only
    allowed_models: list[str]       # 经隐私/本地/偏好过滤后的候选模型
    feasible: bool                  # 是否存在满足硬约束的模型集合
    infeasibility_reason: str | None = None  # 不可行时的原因（用于 explain）


@dataclass
class Task:
    id: str
    prompt: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    constraints: "Constraints | None" = None  # 可选约束；不传则走默认画像（向后兼容）


@dataclass
class Completion:
    """单次模型调用的结果，附带成本与延迟信息。"""

    content: str
    model: str
    latency_ms: float
    cost_usd: float


@dataclass
class NodeResult:
    node_id: str
    role: str
    kind: str
    model: str
    content: str
    latency_ms: float
    cost_usd: float
    quality: float


# ExecutionResult 是运行时的 Execution Trace（执行轨迹）：记录一次执行的所有节点结果、
# 最终输出与聚合指标。它与静态的 Compute Graph（计算图）区分——图是“计划”，轨迹是“记录”。
@dataclass
class ExecutionResult:
    task_id: str
    prompt: str
    strategy: Strategy
    complexity: Complexity
    complexity_score: float
    node_results: List[NodeResult]
    final_output: str
    fused: bool
    total_latency_ms: float
    total_cost_usd: float
    avg_quality: float
    constraints: "Constraints | None" = None  # 本次执行所用的约束（如经约束感知管线）；无则 None

    def summary(self) -> str:
        parts = [
            f"[{self.strategy.zh}（{self.strategy.value}）] "
            f"复杂度={self.complexity.zh}（{self.complexity.value}）"
            f"({self.complexity_score:.2f}) | "
            f"节点数={len(self.node_results)} 融合={self.fused} | "
            f"延迟={self.total_latency_ms:.0f}ms 成本=${self.total_cost_usd:.4f} "
            f"质量={self.avg_quality:.2f}"
        ]
        if self.constraints is not None:
            parts.append(
                f" | 约束：质量≥{self.constraints.min_quality:.2f} "
                f"预算={self.constraints.max_cost_usd} 延迟={self.constraints.max_latency_ms} "
                f"隐私={self.constraints.privacy}"
            )
        return "".join(parts)
