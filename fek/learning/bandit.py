"""上下文老虎机（ε-greedy，朴素但利用上下文）。

为什么是"上下文"：FEK 的策略选择本质是 —— 不同复杂度的任务，最优策略不同。
纯全局均值会忽略上下文（比如 MOA 全局质量高但贵，会导致所有任务都选 MOA，
失去自适应）。因此本实现按**复杂度档位（band）分桶**，每个桶内独立维护三臂均值。

为什么是"朴素 ε-greedy"：零依赖、最易演示、最快落地，符合黑客松 Demo 调性。
未来可在同一接口上替换为 LinUCB（见 docs/learn-design.md），不影响调用方。

核心 API：
- select(context_key, arms, epsilon) -> 选中的臂
- update(context_key, arm, reward)    -> 用反馈更新该桶下该臂的均值
"""

from __future__ import annotations

import random
from typing import Dict, Hashable, List, Tuple


class ContextualBandit:
    def __init__(self, epsilon: float = 0.15, seed: int | None = None):
        self.epsilon = epsilon
        self._rng = random.Random(seed)
        # stats[context_key][arm] = {"n": 样本数, "mean": 平均奖励}
        self.stats: Dict[Hashable, Dict[Hashable, dict]] = {}
        self.total_feedback = 0

    # ---- 查询 ----
    def _ensure(self, context_key: Hashable, arms: List[Hashable]) -> Dict[Hashable, dict]:
        bucket = self.stats.setdefault(context_key, {})
        for a in arms:
            bucket.setdefault(a, {"n": 0, "mean": 0.0})
        return bucket

    def mean_reward(self, context_key: Hashable, arm: Hashable) -> float:
        b = self.stats.get(context_key, {})
        return b.get(arm, {}).get("mean", 0.0)

    def count(self, context_key: Hashable, arm: Hashable) -> int:
        b = self.stats.get(context_key, {})
        return b.get(arm, {}).get("n", 0)

    def best_arm(self, context_key: Hashable, arms: List[Hashable]) -> Hashable:
        """该上下文下当前平均奖励最高的臂（用于 ε=0 的贪婪决策）。"""
        b = self._ensure(context_key, arms)
        return max(arms, key=lambda a: b[a]["mean"])

    # ---- 决策 ----
    def select(self, context_key: Hashable, arms: List[Hashable], epsilon: float | None = None) -> Hashable:
        """按 ε-greedy 选择臂。

        - 以 ε 概率随机探索（保证能发现当前看似次优、实则更优的臂）；
        - 否则选该上下文下平均奖励最高的臂。
        """
        eps = self.epsilon if epsilon is None else epsilon
        self._ensure(context_key, arms)
        if self._rng.random() < eps:
            return self._rng.choice(arms)
        return self.best_arm(context_key, arms)

    # ---- 学习 ----
    def update(self, context_key: Hashable, arm: Hashable, reward: float) -> None:
        """用一条 (上下文, 臂, 奖励) 反馈更新该桶下该臂的滑动均值。"""
        b = self._ensure(context_key, [arm])
        st = b[arm]
        st["n"] += 1
        # 增量更新均值，避免存储全部历史
        st["mean"] += (reward - st["mean"]) / st["n"]
        self.total_feedback += 1

    # ---- 持久化支持 ----
    def to_dict(self) -> dict:
        return {
            "epsilon": self.epsilon,
            "total_feedback": self.total_feedback,
            "stats": {str(k): v for k, v in self.stats.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContextualBandit":
        obj = cls(epsilon=d.get("epsilon", 0.15))
        obj.total_feedback = d.get("total_feedback", 0)
        # JSON 键只能是字符串，加载时按字符串还原（band 本身就是字符串，OK）
        obj.stats = {k: {arm: {"n": s["n"], "mean": s["mean"]} for arm, s in v.items()}
                     for k, v in d.get("stats", {}).items()}
        return obj

    def snapshot(self) -> List[Tuple[str, str, int, float]]:
        """便于演示/测试：返回 [(上下文, 臂, 样本数, 平均奖励)] 扁平列表。"""
        rows = []
        for ctx, bucket in self.stats.items():
            for arm, st in bucket.items():
                rows.append((str(ctx), str(arm), st["n"], round(st["mean"], 4)))
        return rows
