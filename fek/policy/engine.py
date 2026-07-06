"""策略引擎 —— FEK 的核心创新点。

将复杂度评分映射为具体的计算策略。阈值是可变的，以便未来的学习层（v2）
能根据观察到的执行轨迹对阈值进行微调。正是这个唯一决策点，使 FEK 成为
"执行智能"而非一段写死的固定流水线。
"""

from __future__ import annotations

from ..core.types import Complexity, Strategy


class PolicyEngine:
    def __init__(self, low_threshold: float = 0.33, high_threshold: float = 0.66):
        self.low = low_threshold
        self.high = high_threshold
        # 根据执行轨迹反馈产生的、可学习的偏移量
        self._drift = 0.0

    def select(self, complexity_score: float) -> Strategy:
        s = complexity_score + self._drift
        if s < self.low:
            return Strategy.SINGLE
        if s < self.high:
            return Strategy.MULTI_AGENT
        return Strategy.MOA

    def explain(self, complexity_score: float) -> str:
        # 返回一句可解释的决策说明，便于演示时向评委展示"为什么这样选"
        s = complexity_score + self._drift
        if s < self.low:
            return f"评分 {s:.2f} < {self.low:.2f} -> SINGLE（单模型已足够）"
        if s < self.high:
            return f"{self.low:.2f} <= 评分 {s:.2f} < {self.high:.2f} -> MULTI_AGENT（角色拆分更有帮助）"
        return f"评分 {s:.2f} >= {self.high:.2f} -> MOA（高不确定性，并行多模型 + 融合）"

    def learn(self, complexity_score: float, quality: float) -> None:
        """带有 v2 味道的微小自适应：若所选策略质量偏低，则略微扩大该档位，
        使更困难的任务下次获得更多算力。"""
        if quality < 0.5:
            # 向下偏移，使该评分下次路由到更"重"的策略
            self._drift -= 0.05
        elif quality > 0.9:
            self._drift += 0.01
        self._drift = max(-0.3, min(0.3, self._drift))
