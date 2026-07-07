"""Strategy Library（可插拔策略库，RFC 0012）。"""
from .protocol import BaseStrategy, Strategy
from .builtin import (
    BUILTIN_STRATEGIES,
    Debate,
    Hierarchical,
    MoA,
    Parallel,
    PlannerPlusReviewer,
    Reflection,
    Single,
    TreeOfThoughts,
)
from .registry import DEFAULT_LIBRARY, StrategyLibrary

__all__ = [
    "Strategy",
    "BaseStrategy",
    "Single",
    "PlannerPlusReviewer",
    "Reflection",
    "Debate",
    "TreeOfThoughts",
    "MoA",
    "Parallel",
    "Hierarchical",
    "BUILTIN_STRATEGIES",
    "StrategyLibrary",
    "DEFAULT_LIBRARY",
]
