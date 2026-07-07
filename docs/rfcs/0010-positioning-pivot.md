# RFC 0010 · Positioning Pivot: Execution Engine → Compute Optimizer

- 状态：Accepted
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：Supersedes 0001 project-vision, 0002 execution-model；关联 0011 constraint-policy-optimizer, 0012 strategy-library

## Background（背景）

FEK 前一版定位为"Adaptive AI Execution Engine（自适应 AI 执行引擎）"，核心叙事是"自动选执行策略 + 成本感知执行"。

但经过对 AI Infra 生态的重新调研，发现以下能力**已快速商品化、不再是差异化护城河**：

- **自动 Workflow / 动态执行流**：Claude Code 已能按任务自动生成 workflow、动态选执行流；Cursor、Claude Code 社区已大量采用多模型协同。
- **MoA**：Hermes、Together AI 已做成成熟能力。
- **推理策略**（Debate / Reflection / ToT / Self-Consistency）：大量论文验证，正在变成"标配积木"。

继续围绕"自动 workflow"或"支持 MoA"设计 FEK，等于在 Claude Code / Hermes 的主场作战。

## Problem（问题）

1. 旧定位把 FEK 的价值绑定在"自动执行 / 支持 MoA"上——这些正被快速商品化，FEK 会随新框架/新策略出现而过时。
2. 旧定位的输入只有 Task，没有把"约束"作为一等公民，导致 FEK 无法回答"预算只有 $0.2 且质量要 High 怎么选"这类真正稳定的问题。
3. MoA 在旧定位里被当核心策略之一宣传，与 Hermes 直接竞争。

## Proposal（提案）

把 FEK 重新定位为 **Adaptive AI Compute Optimizer（自适应 AI 计算优化器）**，位于 **AI Compute Optimization Layer（AI 计算优化层）**。

核心转向 **Optimization Thinking**：

- **输入 = Task + Constraints**（质量 / 预算 / 延迟 / 隐私 / 可接受模型）。
- **FEK 解决的问题 = 在约束下，自动为任务选择（或组合）最优执行策略。**
- **MoA / Debate / ToT 等全部降级为可插拔 Strategy**；FEK 不发明策略，只负责选。
- 真正护城河 = **约束感知、策略无关、可学习的策略优化闭环**（Constraint Analysis → Policy Optimizer → Strategy Selection → Execution → Telemetry → Learning）。

对外沟通第一句讲"在约束下优化"，不讲"支持多少 Agent / 多少 MoA / 多少 Workflow"。

## Alternatives（备选方案）

- **A. 维持 Execution Engine 定位**：拒绝。护城河会随时间被商品化能力侵蚀。
- **B. 做成 MoA Framework**：拒绝。直接与 Hermes 竞争，且 MoA 只是策略之一。
- **C. 做成 Agent Framework**：拒绝。与 LangGraph/AutoGen 正面竞争，偏离 FEK 优势。
- **D. 本次提案（Compute Optimizer）**：采纳。更稳定、可吸收一切新策略、不与任何现有项目撞车。

## Tradeoffs（权衡）

- ✅ 定位更稳定，不会因新框架/新策略出现而过时。
- ✅ 与生态所有项目形成"集成而非竞争"关系。
- ⚠️ 放弃了"自动 workflow / MoA"的易传播卖点，需要重新教育用户"优化"价值（更长线的叙事成本）。
- ⚠️ 需要新增 Constraint Analysis 与 Strategy Library 两个模块的抽象成本（见 0011 / 0012）。

## Future Work（未来工作）

- 由 0011 落地 Constraint Analysis + Policy Optimizer 重构。
- 由 0012 落地 Strategy Library（可插拔策略）。
- 路线图见 docs/roadmap.md（v1 Constraint-aware Optimizer / v2 Constraint-aware Policy Learning）。
- 旧 RFC 0001、0002 标记 Superseded，本文档为新的定位权威来源。
