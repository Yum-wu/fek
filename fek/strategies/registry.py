"""策略注册表（Strategy Library）。

把内置策略集中管理，Policy Optimizer 从中按约束筛选与选择。
新增策略 = 新增一个实现文件并在 :data:`BUILTIN_STRATEGIES` 注册，不动引擎核心
（满足 RFC 0012「策略无关」）。v3 的 Strategy Marketplace（外部注册）将复用此接口。
"""

from __future__ import annotations

from ..core.types import ConstraintProfile
from .builtin import BUILTIN_STRATEGIES
from .protocol import BaseStrategy


class StrategyLibrary:
    def __init__(self, strategies: list[BaseStrategy] | None = None):
        self._all = list(strategies) if strategies is not None else list(BUILTIN_STRATEGIES)

    def all(self) -> list[BaseStrategy]:
        return list(self._all)

    def names(self) -> list[str]:
        return [s.name for s in self._all]

    def get(self, name: str) -> BaseStrategy | None:
        return next((s for s in self._all if s.name == name), None)

    def filter(self, profile: ConstraintProfile) -> list[BaseStrategy]:
        """返回在给定约束画像下 ``supports()`` 为真的策略（硬约束闸门）。"""
        return [s for s in self._all if s.supports(profile)]


# 默认库（内置 8 策略）
DEFAULT_LIBRARY = StrategyLibrary()
