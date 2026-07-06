"""FEK 内核 —— 唯一的编排入口。

流水线（与 FEK 统一架构一致）：
    Task -> Classifier -> Policy Engine -> Graph Compiler -> Runtime -> Fusion -> Reflection
并将每次运行结果送入遥测层，以支撑"成本感知"的叙事。

用法：
    from fek import FEKKernel
    kernel = FEKKernel()           # 默认 mock 模式，零 API key
    result = kernel.run("对比 Python 和 Go 做后端服务")
    print(result.summary())
"""

from __future__ import annotations

import uuid

from .classifier import ComplexityClassifier
from .compiler import GraphBuilder
from .core.types import Complexity, ExecutionResult, Strategy, Task
from .models import LLMBackend, MockBackend, from_env
from .policy import PolicyEngine
from .runtime import Executor
from .telemetry import TelemetryRecorder


class FEKKernel:
    def __init__(
        self,
        backend: LLMBackend | None = None,
        policy: PolicyEngine | None = None,
        telemetry: TelemetryRecorder | None = None,
        telemetry_log: str | None = None,
    ):
        self.classifier = ComplexityClassifier()
        self.policy = policy or PolicyEngine()
        self.builder = GraphBuilder()
        self.backend = backend or from_env()
        self.executor = Executor(self.backend)
        self.telemetry = telemetry or TelemetryRecorder(log_path=telemetry_log)

    def run(self, prompt: str, task_id: str | None = None) -> ExecutionResult:
        # 自动模式：由系统根据复杂度自主选择策略
        task = Task(id=task_id or uuid.uuid4().hex[:8], prompt=prompt)
        score = self.classifier.score(prompt)
        band = self.classifier.classify(prompt)
        strategy = self.policy.select(score)
        graph = self.builder.build(strategy, task)
        node_results, final_output, fused = self.executor.run(task, graph)

        total_lat = sum(n.latency_ms for n in node_results)
        total_cost = sum(n.cost_usd for n in node_results)
        avg_q = sum(n.quality for n in node_results) / max(1, len(node_results))

        result = ExecutionResult(
            task_id=task.id,
            prompt=prompt,
            strategy=strategy,
            complexity=band,
            complexity_score=score,
            node_results=node_results,
            final_output=final_output,
            fused=fused,
            total_latency_ms=total_lat,
            total_cost_usd=total_cost,
            avg_quality=avg_q,
        )
        self.telemetry.record(result)
        self.policy.learn(score, avg_q)  # 用本次结果微调策略偏移
        return result

    def run_all_strategies(self, prompt: str) -> dict[Strategy, ExecutionResult]:
        """对战模式：用全部三种策略执行同一个任务。"""
        return {s: self._run_fixed(s, prompt) for s in Strategy}

    def _run_fixed(self, strategy: Strategy, prompt: str) -> ExecutionResult:
        # 强制使用指定策略执行（绕过自动选择）
        task = Task(id=uuid.uuid4().hex[:8], prompt=prompt)
        score = self.classifier.score(prompt)
        band = self.classifier.classify(prompt)
        graph = self.builder.build(strategy, task)
        node_results, final_output, fused = self.executor.run(task, graph)
        total_lat = sum(n.latency_ms for n in node_results)
        total_cost = sum(n.cost_usd for n in node_results)
        avg_q = sum(n.quality for n in node_results) / max(1, len(node_results))
        result = ExecutionResult(
            task_id=task.id, prompt=prompt, strategy=strategy, complexity=band,
            complexity_score=score, node_results=node_results, final_output=final_output,
            fused=fused, total_latency_ms=total_lat, total_cost_usd=total_cost, avg_quality=avg_q,
        )
        self.telemetry.record(result)
        return result
