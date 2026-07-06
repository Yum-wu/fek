"""混合智能体（MoA）融合层。

将多个并行智能体的输出合并为一个统一的答案。在 mock 模式下，这是一个确定性的
结构化合并；接入真实后端时，可改为调用 LLM 来融合。对 Demo 而言，重要的是
这一结构本身——它展示了 FEK 是主动*组合*多个模型视角，而非简单取第一个。
"""

from __future__ import annotations

from typing import List


def fuse(perspectives: List[str], labels: List[str] | None = None) -> str:
    labels = labels or [f"视角 {i + 1}" for i in range(len(perspectives))]
    parts = []
    for label, text in zip(labels, perspectives):
        clean = text.strip()
        parts.append(f"### {label}\n{clean}")
    consolidated = (
        "### 综合答案\n"
        + _consolidate(perspectives)
    )
    return "\n\n".join(parts + [consolidated])


def _consolidate(perspectives: List[str]) -> str:
    # 确定性综合：以最长的视角作为主干，再附上一句引用其余视角的说明
    # （对 mock 安全，无需调用 LLM）
    if not perspectives:
        return ""
    backbone = max(perspectives, key=len).strip()
    n = len(perspectives)
    return (
        f"{backbone}\n\n"
        f"[由 FEK MoA 融合自 {n} 个独立模型视角。]"
    )
