# RFC 0008 · Roadmap

- 状态：Accepted
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：VISION.md, docs/roadmap.md, docs/reviews/architecture-review-2026.md

## Background

原 README 把 v2（学习层，已实现但 mock 演示）、v3（图变异）、v4（自主目标/Go 运行时）并列在"路线图"下，v2 标 ✅、v3/v4 标 🔜，暗示研究愿景是近期交付。

## Problem

1. 研究愿景伪装成近期交付，损害可信度。
2. 无 Product/Research 分离，开发者无法判断什么能指望。
3. "Scheduler" 在路线图中出现但未定义，易与模块混淆。

## Proposal

- **严格分离 Product Roadmap 与 Research Roadmap**（见 docs/roadmap.md）。
- **Product**：
  - v1 Adaptive Runtime（当前基线，含已落地能力 + 诚实标注）。
  - v2 Learning Optimizer（学习升级、真实成本信号、可回测）。
- **Research**（不排期、不承诺）：
  - R1 Self-Evolving Execution（图变异/角色自演化）。
  - R2 Autonomous Kernel（自主目标分解）。
  - R3 更好 Task Profiling（最高优先级改进）。
  - R4 真实 LLM 裁判。
- **术语**：路线图 v2 的"学习"归入 Policy Engine 能力，称 **Learning Optimizer**，不用模糊的 "Scheduler"。

## Alternatives

- **保留单层路线图**：否决——正是当前问题根源。
- **把研究全删**：否决——研究是长期方向，只是不承诺排期。

## Tradeoffs

- 分离后"看起来功能少"，但更诚实、更专业，符合世界级基础设施项目标准。

## Future Work

- 每个 Product 里程碑对应 RFC 索引（见 docs/roadmap.md 第四节）。
- 研究路线若验证可行，晋级 Product 需新 RFC + 基准证明。
