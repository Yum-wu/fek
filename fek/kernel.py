"""FEK —— 唯一的编排入口（Adaptive AI Compute Optimizer）。

默认（无约束）流水线保持旧行为，确保既有 Demo / 测试零改动：
    Task -> Task Profiler -> Policy Engine -> Graph Compiler -> Runtime -> Fusion -> Evaluation

传入约束时切换到新定位流水线（RFC 0010/0011/0012）：
    Task + Constraints -> Constraint Analysis -> Policy Optimizer -> Strategy Library
    -> Compute Graph -> Runtime -> Telemetry

用法：
    from fek import FEKKernel
    kernel = FEKKernel()           # 默认 mock 模式，零 API key
    result = kernel.run("对比 Python 和 Go 做后端服务")
    print(result.summary())

    # 约束感知执行
    from fek.core.types import Constraints
    r2 = kernel.run("写一份隐私报告", constraints=Constraints(privacy="local_only"))
"""

from __future__ import annotations

import uuid

from .compiler import GraphBuilder
from .constraint import analyze
from .core.types import Complexity, Constraints, ExecutionResult, Strategy, Task
from .learning.constraint_learning import constraint_aware_reward, profile_context_key
from .learning.learner import Learner
from .models import LLMBackend, MockBackend, from_env
from .policy import PolicyEngine
from .policy.optimizer import PolicyOptimizer
from .profiler import TaskProfiler
from .runtime import Executor
from .strategies import DEFAULT_LIBRARY
from .telemetry import TelemetryRecorder


class FEKKernel:
    def __init__(
        self,
        backend: LLMBackend | None = None,
        policy: PolicyEngine | None = None,
        telemetry: TelemetryRecorder | None = None,
        telemetry_log: str | None = None,
        learning: bool = True,
        strategy_library=DEFAULT_LIBRARY,
        learner: "Learner | None" = None,
        constraint_warmup: int = 8,
    ):
        self.profiler = TaskProfiler()
        self.policy = policy or PolicyEngine(learning=learning)
        self.builder = GraphBuilder()
        self.backend = backend or from_env()
        self.executor = Executor(self.backend)
        self.telemetry = telemetry or TelemetryRecorder(log_path=telemetry_log)
        # 新定位：约束感知优化器 + 策略库（向后兼容：无约束时仍走 PolicyEngine）
        self.strategy_library = strategy_library
        # v2 约束学习：optimizer 可挂载 learner（默认 None = 纯静态、确定）
        self.optimizer = PolicyOptimizer(
            self.strategy_library, learner=learner, warmup=constraint_warmup
        )

    def run(
        self,
        prompt: str,
        task_id: str | None = None,
        constraints: Constraints | None = None,
    ) -> ExecutionResult:
        # 传入约束 -> 新定位流水线（Constraint Analysis -> Policy Optimizer -> Strategy Library）
        if constraints is not None:
            return self._run_constrained(prompt, task_id, constraints)

        # 默认自动模式（向后兼容）：由系统根据复杂度自主选择策略
        task = Task(id=task_id or uuid.uuid4().hex[:8], prompt=prompt)
        score = self.profiler.score(prompt)
        band = self.profiler.classify(prompt)
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
        self.policy.learn(score, band, strategy, avg_q, total_cost, total_lat)  # 用本次执行轨迹更新学习层
        return result

    def _run_constrained(
        self, prompt: str, task_id: str | None, constraints: Constraints
    ) -> ExecutionResult:
        # 新定位流水线：约束作为一等输入，由优化器在策略库中择优
        task = Task(id=task_id or uuid.uuid4().hex[:8], prompt=prompt, constraints=constraints)
        available = getattr(self.backend, "models", None)
        profile = analyze(task, constraints, available_models=available)
        if not profile.feasible:
            raise ValueError(f"约束不可行：{profile.infeasibility_reason}")

        strategy = self.optimizer.select(profile)
        if strategy is None:
            raise ValueError("无满足约束的可行策略（硬约束过紧）")

        # 复杂度画像仍保留，供 ExecutionResult / 遥测兼容
        score = self.profiler.score(prompt)
        band = self.profiler.classify(prompt)
        graph = strategy.build(task, constraints, profile.allowed_models)
        node_results, final_output, fused = self.executor.run(task, graph)

        total_lat = sum(n.latency_ms for n in node_results)
        total_cost = sum(n.cost_usd for n in node_results)
        avg_q = sum(n.quality for n in node_results) / max(1, len(node_results))

        result = ExecutionResult(
            task_id=task.id,
            prompt=prompt,
            strategy=strategy.kind(),  # 映射到核心 Strategy 枚举，保持兼容
            complexity=band,
            complexity_score=score,
            node_results=node_results,
            final_output=final_output,
            fused=fused,
            total_latency_ms=total_lat,
            total_cost_usd=total_cost,
            avg_quality=avg_q,
            constraints=constraints,
        )
        self.telemetry.record(result)
        # v2 约束学习：把真实执行轨迹作为反馈回写 learner（仅当已挂载）
        if self.optimizer.learner is not None:
            ctx = profile_context_key(profile)
            used_models = [n.model for n in node_results]
            reward = constraint_aware_reward(
                avg_q, total_cost, total_lat, constraints=constraints, used_models=used_models
            )
            self.optimizer.learner.update(ctx, strategy.name, reward)
        return result

    def run_all_strategies(self, prompt: str) -> dict[Strategy, ExecutionResult]:
        """对战模式：用全部三种策略执行同一个任务（向后兼容）。"""
        return {s: self._run_fixed(s, prompt) for s in Strategy}

    def _run_fixed(self, strategy: Strategy, prompt: str) -> ExecutionResult:
        # 强制使用指定策略执行（绕过自动选择）
        task = Task(id=uuid.uuid4().hex[:8], prompt=prompt)
        score = self.profiler.score(prompt)
        band = self.profiler.classify(prompt)
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
