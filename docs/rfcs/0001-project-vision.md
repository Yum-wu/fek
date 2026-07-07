# RFC 0001 · Project Vision

- 状态：Superseded（被 0010 positioning-pivot 取代）
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：VISION.md, docs/architecture.md, 0010 positioning-pivot

## Background

FEK 源于一份私人设计文档（FEK.MD），最初以 "Fusion Execution Kernel / 融合执行内核" 命名，作为黑客松 Demo 实现。Demo 已落地：零依赖内核、自动策略选择（SINGLE/MULTI_AGENT/MOA）、Compute Graph 执行、Telemetry、mock 学习层。

但 "Fusion Execution Kernel" 是错误隐喻（Kernel 暗示资源管理层），且把研究愿景（图变异/自主目标）与已实现功能并列，对外叙事混乱。

## Problem

1. 项目名误导：不是内核，是执行引擎。
2. 定位重叠风险：容易被认为是又一个 Agent Framework / Gateway / MoA 库。
3. 研究愿景被包装成近期交付，损害可信度。
4. 缺少权威愿景文档，术语与定位各自漂移。

## Proposal

- 项目定位改为 **Adaptive AI Execution Engine（自适应 AI 执行引擎）**，缩写 FEK 仅作品牌，不再展开为 "Fusion Execution Kernel"。
- 核心职责一句话：**为每个 AI 任务自动决定最优执行策略。**
- 发布 `VISION.md` 作为权威愿景，明确非目标（不是 Gateway / 不是 Agent Framework / 不是 MoA 库 / 不是 RAG）。
- 生态分层定位：FEK 属于 **Execution Layer**，跑在 Gateway 之上、可嵌入 Agent Framework 之内（见 docs/ecosystem/ai-infra-landscape.md）。

## Alternatives

- **保留 "Fusion Execution Kernel"**：否决——隐喻错误，且 "Fusion" 仅是子组件。
- **改名 "FEK Router"**：否决——"Router" 暗示 Gateway 层，不对。
- **改名 "FEK Orchestrator"**：部分可行，但 "Orchestrator" 偏数据管道语义；"Execution Engine" 更贴 AI 执行。

## Tradeoffs

- 保留 `fek` 包名：重命名 import 成本过高，接受缩写不再展开。
- "Engine" 仍偏重，但比 "Kernel" 准确得多，且业界（如规则引擎、推理引擎）可接受。

## Future Work

- 在对外沟通（README/博客/演讲）统一口径。
- 若社区要求，未来可讨论 `fek` 是否改为更有语义的 PyPI 名（不影响 import）。
