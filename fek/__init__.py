"""FEK —— 自适应 AI 执行引擎（Adaptive AI Execution Engine）。

一个自适应 AI 执行引擎，为每个任务自动选择最优执行策略并编译为计算图。本仓库是 FEK 的
v0/v1 架构的黑客松 Demo 实现。

快速开始（零 API key，mock 模式）：
    from fek import FEKKernel
    kernel = FEKKernel()
    result = kernel.run("对比 Python 和 Go 做后端服务")
    print(result.summary())
"""

from __future__ import annotations

from .core import (
    Completion,
    Complexity,
    ComputeGraph,
    ExecutionResult,
    GraphNode,
    NodeResult,
    Strategy,
    Task,
)
from .profiler import TaskProfiler
from .policy import PolicyEngine
from .compiler import GraphBuilder
from .runtime import Executor
from .fusion import fuse
from .evaluation import score_quality
from .telemetry import TelemetryRecorder
from .models import LLMBackend, MockBackend, OpenAIBackend, from_env
from .kernel import FEKKernel

__version__ = "0.1.0"

__all__ = [
    "Completion",
    "Complexity",
    "ComputeGraph",
    "ExecutionResult",
    "GraphNode",
    "NodeResult",
    "Strategy",
    "Task",
    "TaskProfiler",
    "PolicyEngine",
    "GraphBuilder",
    "Executor",
    "fuse",
    "score_quality",
    "TelemetryRecorder",
    "LLMBackend",
    "MockBackend",
    "OpenAIBackend",
    "from_env",
    "FEKKernel",
]
