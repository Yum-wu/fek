# RFC 0002 · Execution Model

- 状态：Superseded（被 0010 positioning-pivot 取代）
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：docs/architecture.md, 0003-policy-engine, 0004-compute-graph, 0010 positioning-pivot

## Background

FEK 的执行模型是一条约定的流水线：Task → Classifier → Policy Engine → Graph Compiler → Runtime → Fusion → Reflection → Telemetry。这个主线抓住了"执行智能"的本质，但术语随实现漂移（"Execution Graph" vs "Compute Graph"、"Reflection" 实为打分）。

## Problem

1. 缺少对"执行模型"的精确定义，外界不清楚 FEK 到底自动做了什么。
2. 术语不一致导致模块边界模糊。
3. 真正创新点（闭环）未被显式命名。

## Proposal

定义 FEK 的执行模型为**闭环**：

```
Task Profile → Policy Engine → Compute Graph → Runtime → Telemetry →（学习）→ Policy Engine
```

- **输入**：任务（自然语言）。
- **决策**：Policy Engine 按 Task Profile 选 Strategy（SINGLE/MULTI_AGENT/MOA）。
- **规划**：Graph Compiler 把 Strategy 编译成 Compute Graph。
- **执行**：Runtime 跑图，Fusion Engine 聚合、Evaluation 打分。
- **观测**：Telemetry 记录 trace，回流 Policy Engine 学习。

明确**核心创新 = 这个成本感知、可解释、可学习的闭环**，而非任一孤立组件（见 docs/architecture.md Part 4）。

## Alternatives

- **无闭环（每次独立决策）**：简单但无法"越用越聪明"，否决。
- **让用户显式选策略**：变成 Agent Framework，违背"自动"定位，否决。

## Tradeoffs

- 闭环引入状态（学习参数），需处理冷启动（fallback 规则）与可复现性（JSON 持久化）。已通过 warmup + ε-greedy 缓解。

## Future Work

- 策略空间从三选一扩展为可组合原语（DEBATE/REFLECTION/branching）。
- 学习从 ε-greedy 升级到 LinUCB（见 0003）。
