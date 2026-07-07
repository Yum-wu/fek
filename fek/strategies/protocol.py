"""策略协议与基类（RFC 0012 · Strategy Library）。

FEK 不发明推理策略，只负责在约束下**选择**最优策略。所有策略都实现统一契约：
``name`` / ``cost_tier`` / ``supports(profile)`` / ``build(task, constraints, models)``。

``Strategy`` 是 RFC 定义的协议（结构契约）；``BaseStrategy`` 提供共用实现，
具体策略（Single / MoA / Debate …）继承它并只关心 DAG 形状。
"""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from ..core.graph import ComputeGraph
from ..core.types import ConstraintProfile, Constraints, Strategy as StrategyKind, Task

# 默认模型（当 allowed_models 为空或不足时回退），与 MockBackend 对齐
_FALLBACK_MODELS = ["gpt-fast", "gpt-smart", "claude-x"]


@runtime_checkable
class Strategy(Protocol):
    """策略统一契约（RFC 0012）。"""

    name: str
    cost_tier: float

    def supports(self, profile: ConstraintProfile) -> bool: ...

    def build(
        self, task: Task, constraints: Constraints | None, models: List[str]
    ) -> ComputeGraph: ...


class BaseStrategy:
    """策略共用基类：固化 name/zh/cost_tier/quality_est/min_models 与兼容逻辑。"""

    name: str = "base"
    zh: str = "基础策略"
    cost_tier: float = 1.0          # 相对成本档（用于优化预估，越大越贵）
    quality_est: float = 0.85       # 启发式质量预期（研究路线 R3 会改进）
    min_models: int = 1             # 该策略最少需要的模型数（隐私约束据此剪枝）
    node_count: int = 1             # 估算成本/延迟用

    # ---- 与核心 Strategy 枚举的兼容映射（ExecutionResult / 遥测依赖枚举）----
    def kind(self) -> StrategyKind:
        if self.name == "moa":
            return StrategyKind.MOA
        if self.name == "single":
            return StrategyKind.SINGLE
        return StrategyKind.MULTI_AGENT

    def supports(self, profile: ConstraintProfile) -> bool:
        """硬约束闸门：画像不可行、或可用模型少于所需，则该策略不可用。"""
        if not profile.feasible:
            return False
        return len(profile.allowed_models) >= self.min_models

    def _models(self, models: List[str], default: List[str] | None = None) -> List[str]:
        """解析实际使用的模型列表，不足时循环复用以保证 build 始终合法。"""
        models = list(models) if models else list(default or _FALLBACK_MODELS)
        if len(models) < self.min_models:
            base = models or ["local-model"]
            models = [base[i % len(base)] for i in range(self.min_models)]
        return models

    def estimate(self, model_profiles: dict[str, tuple[float, float]]) -> tuple[float, float]:
        """启发式成本/延迟估算（node_count × 代表模型单次开销）。

        仅用于 Policy Optimizer 的预算/延迟剪枝，属估算而非实测（RFC 明确标注为启发式）。
        """
        rep = next(iter(model_profiles.keys()), "gpt-fast")
        cost_per, lat_per = model_profiles.get(rep, (0.0001, 70.0))
        return self.node_count * cost_per, self.node_count * lat_per

    def build(self, task: Task, constraints: Constraints | None, models: List[str]) -> ComputeGraph:
        raise NotImplementedError
