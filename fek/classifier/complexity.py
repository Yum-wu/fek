"""复杂度分类器（v1：启发式；v2 起可接入学习权重）。

将一段自由文本任务转化为 [0, 1] 区间内的归一化复杂度评分。启发式信号包括：
提示词长度、推理类关键词、对比/"vs" 措辞、多步骤类词汇。刻意保持简单且透明，
让评委能直观看到某个任务*为什么*被路由到某种策略。
"""

from __future__ import annotations

import re

from ..core.types import Complexity

# 带权重的词法信号
_SIGNALS = {
    "compare": 0.18,
    "versus": 0.15,
    "vs": 0.12,
    "debate": 0.20,
    "perspective": 0.15,
    "trade-off": 0.18,
    "tradeoff": 0.18,
    "analyze": 0.12,
    "design": 0.14,
    "optimize": 0.16,
    "plan": 0.10,
    "why": 0.08,
    "multiple": 0.12,
    "step by step": 0.10,
    "evaluate": 0.12,
    "strategy": 0.12,
    "reason": 0.10,
}


class ComplexityClassifier:
    def __init__(self, length_weight: float = 0.0008):
        self.length_weight = length_weight

    def score(self, prompt: str) -> float:
        p = prompt.lower()
        s = 0.0
        for token, w in _SIGNALS.items():
            if token in p:
                s += w
        # 长度贡献（带饱和上限）
        s += min(len(prompt) * self.length_weight, 0.35)
        # 问号数量
        s += min(p.count("?") * 0.04, 0.12)
        return max(0.0, min(1.0, s))

    def classify(self, prompt: str) -> Complexity:
        return band(self.score(prompt))


def band(score: float) -> Complexity:
    # 将连续评分映射到离散档位
    if score < 0.33:
        return Complexity.LOW
    if score < 0.66:
        return Complexity.MEDIUM
    return Complexity.HIGH
