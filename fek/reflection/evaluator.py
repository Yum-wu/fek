"""反思 / 评估层。

用透明的启发式方法（结构标记、推理标记、长度）将答案质量评为 [0, 1]，
并加入确定性抖动，使 mock 运行结果稳定但略有差异。在生产环境中，该节点
应改为调用一个 LLM 裁判来打分。
"""

from __future__ import annotations

import hashlib

_STRUCTURE_MARKERS = ["because", "therefore", "first", "step", "1.", "2.", "->", "conclude"]
_REASON_MARKERS = ["why", "trade", "risk", "assume", "however", "but"]


def score_quality(text: str) -> float:
    t = text.lower()
    s = 0.0
    s += min(len(text) / 800.0, 0.4)  # 越长、越充实的答案得分越高（带上限）
    s += 0.05 * sum(1 for m in _STRUCTURE_MARKERS if m in t)
    s += 0.05 * sum(1 for m in _REASON_MARKERS if m in t)
    # 融合 / 综合类输出加分：体现"更多算力 -> 更高质量"的叙事
    if "fused from" in t or "consolidated" in t or "synthesi" in t:
        s += 0.12
    # 确定性抖动，范围 [-0.1, 0.1]
    h = hashlib.sha256(text.encode()).hexdigest()
    jitter = (int(h[:8], 16) % 200 - 100) / 1000.0
    return max(0.0, min(1.0, s + jitter + 0.3))
