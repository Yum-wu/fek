"""FEK —— 自适应 AI 计算优化器（Adaptive AI Compute Optimizer）。

在质量、成本、延迟、隐私等约束下，自动选择最优的 AI 计算策略，并持续从运行反馈中学习。
本仓库是 FEK 的 v1 内核实现：约束作为一等输入，策略来自可插拔 Strategy Library，
FEK 自身只负责"在约束下选到最划算的策略"（Optimization Thinking，而非 Framework Thinking）。

快速开始（零 API key，mock 模式）：
    from fek import FEKKernel
    kernel = FEKKernel()
    result = kernel.run("对比 Python 和 Go 做后端服务")
    print(result.summary())

约束感知执行：
    from fek.core.types import Constraints
    r = kernel.run("写一份隐私报告", constraints=Constraints(privacy="local_only"))
"""

from __future__ import annotations

from .core import (
    Completion,
    Complexity,
    ComputeGraph,
    ConstraintProfile,
    Constraints,
    ExecutionResult,
    GraphNode,
    NodeResult,
    Strategy,
    Task,
)
from .constraint import analyze
from .profiler import TaskProfiler
from .policy import PolicyEngine, PolicyOptimizer
from .compiler import GraphBuilder
from .runtime import Executor
from .fusion import fuse
from .evaluation import score_quality
from .telemetry import TelemetryRecorder
from .models import LLMBackend, MockBackend, OpenAIBackend, from_env
from .strategies import DEFAULT_LIBRARY, StrategyLibrary
from .kernel import FEKKernel

__version__ = "0.1.0"

__all__ = [
    "Completion",
    "Complexity",
    "ComputeGraph",
    "ConstraintProfile",
    "Constraints",
    "ExecutionResult",
    "GraphNode",
    "NodeResult",
    "Strategy",
    "Task",
    "analyze",
    "TaskProfiler",
    "PolicyEngine",
    "PolicyOptimizer",
    "GraphBuilder",
    "Executor",
    "fuse",
    "score_quality",
    "TelemetryRecorder",
    "LLMBackend",
    "MockBackend",
    "OpenAIBackend",
    "from_env",
    "StrategyLibrary",
    "DEFAULT_LIBRARY",
    "FEKKernel",
]
