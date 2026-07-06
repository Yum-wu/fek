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


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Task:
    id: str
    prompt: str
    metadata: Dict[str, Any] = field(default_factory=dict)


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

    def summary(self) -> str:
        return (
            f"[{self.strategy.value}] complexity={self.complexity.value} "
            f"({self.complexity_score:.2f}) | "
            f"nodes={len(self.node_results)} fused={self.fused} | "
            f"latency={self.total_latency_ms:.0f}ms cost=${self.total_cost_usd:.4f} "
            f"quality={self.avg_quality:.2f}"
        )
