# RFC 0007 · Evaluation

- 状态：Accepted
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：0005-runtime, docs/terminology.md, docs/roadmap.md (R4)

## Background

当前 `reflection/evaluator.py` 的 `score_quality()` 是质量启发式打分（玩具级），却被包名 "reflection" 暗示为 LLM 自反思。

## Problem

1. **命名误导**：`reflection` 在 LLM 圈指"自反思循环"，但实际只做打分。
2. **质量分不可信**：启发式分不能当真，却进 Telemetry 驱动学习，可能污染奖励信号。
3. 与未来策略类型 `REFLECTION`（自反思循环）术语冲突。

## Proposal

- 重命名 `reflection/` → **`evaluation/`**，函数 `score_quality` → `evaluate`。
- **接口**：`evaluate(output, task) -> float`（[0,1] 质量分）。
- 当前实现：启发式占位，**文档明确标注为占位**。
- 未来：LLM-as-judge 替代启发式（R4 研究）。

## Alternatives

- **保留 reflection 包名**：否决——误导且冲突。
- **删除 Evaluation，直接用学习奖励**：不可，质量信号是奖励函数输入，必须有。

## Tradeoffs

- 启发式质量分驱动学习，在 mock 下只是方法演示（诚实标注）；真实模式必须接 LLM 裁判才可信。
- 重命名影响 import（__init__、kernel、tests），随迁移计划执行。

## Future Work

- R4：LLM-as-judge 多维度评分（正确性/完整性/安全性）。
- 评估与学习的耦合解耦：评估只打分，奖励函数（learning/reward.py）决定如何用它。
