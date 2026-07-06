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
            f"[{self.strategy.zh}（{self.strategy.value}）] "
            f"复杂度={self.complexity.zh}（{self.complexity.value}）"
            f"({self.complexity_score:.2f}) | "
            f"节点数={len(self.node_results)} 融合={self.fused} | "
            f"延迟={self.total_latency_ms:.0f}ms 成本=${self.total_cost_usd:.4f} "
            f"质量={self.avg_quality:.2f}"
        )
