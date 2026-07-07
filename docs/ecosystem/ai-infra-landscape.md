# AI Infrastructure 生态分层与 FEK 定位

> 配套：VISION.md（非目标）、docs/competitive-analysis.md（问题空间对比）、docs/architecture.md（模块边界）
> 本次重构把 FEK 重定位为 **AI Compute Optimization Layer（AI 计算优化层）**，
> 关键词是 **Optimization Thinking**，不是 Framework Thinking。

---

## 1. 生态分层（自底向上）

```
┌──────────────────────────────────────────────────────────────┐
│  Applications / IDE / Agent Frameworks                          │
│  聊天机器人 / Copilot / RAG / 工作流 / Claude Code / LangGraph  │
├──────────────────────────────────────────────────────────────┤
│  ▶ AI Compute Optimization Layer ◀  FEK                        │
│    Task + Constraints → 约束分析 → 策略优化 → 选策略 → 执行 → 学 │
├──────────────────────────────────────────────────────────────┤
│  Gateway Layer        LiteLLM / OpenRouter                      │
│  （统一 API、key 管理、fallback、用量计费）                      │
├──────────────────────────────────────────────────────────────┤
│  SDK Layer            OpenAI SDK / Anthropic SDK                │
├──────────────────────────────────────────────────────────────┤
│  Model Layer          GPT / Claude / Llama / Qwen / 本地模型    │
└──────────────────────────────────────────────────────────────┘
```

FEK 是 **应用/框架与 Gateway 之间** 的一层：它**消费**任务与约束，**产出**最优执行结果，
底层通过 Gateway 调用模型。它既不向上取代 Agent Framework（那是编程模型层），
也不向下取代 Gateway（那是模型接入层）。

---

## 2. 每层解决什么

| 层 | 解决的核心问题 | 典型项目 |
|---|---|---|
| **Model** | "智能从哪来" | GPT-4o, Claude, Llama, Qwen, 本地模型 |
| **SDK** | "怎么调用模型" | OpenAI SDK, Anthropic SDK |
| **Gateway** | "怎么管一堆模型"——统一接口、key、fallback、成本计量 | LiteLLM, OpenRouter |
| **AI Compute Optimization** | "**在约束下怎么算最划算**"——选策略、编译计划、跑、学 | **FEK** |
| **Agent Framework / IDE** | "怎么**让用户组合**智能体/工作流"——编程模型 | LangGraph, AutoGen, CrewAI, Claude Code, Cursor |
| **Application** | "解决最终用户问题" | 各类产品 |

---

## 3. 为什么 FEK 属于 AI Compute Optimization Layer

这一层回答的问题是：**给定一个任务及其约束（质量/成本/延迟/隐私/模型偏好），用哪种执行策略（单模型 / 规划+批判 / 反思 / 辩论 / 思维树 / MoA / 并行 …）能在约束下最优？**

FEK 的输入是"任务 + 约束"，输出是"执行结果 + 执行轨迹 + 选择解释"。它：
- **不暴露编程模型**给最终用户（那是 Agent Framework / IDE 的事）；
- **不代理模型 API**（那是 Gateway 的事）；
- 坐在两者之间的"**决策 + 优化**"位置。

---

## 4. 为什么 FEK 不是 Gateway

| 维度 | Gateway（LiteLLM/OpenRouter） | FEK |
|---|---|---|
| 输入 | 模型调用请求（messages） | 任务 + 约束 |
| 核心动作 | 路由到某个模型、管理 key | **在约束下优化策略选择** |
| 是否代理 token API | 是 | 否（可**调用** Gateway 作后端） |
| 成本粒度 | 单次调用账单 | 跨策略的 cost/quality/latency/privacy 权衡 |

**关系**：FEK 跑在 Gateway **之上**，Runtime 调用模型时把 LiteLLM/OpenRouter 当 `LLMBackend`。互补，不竞争。

---

## 5. 为什么 FEK 不是 Agent Framework

| 维度 | Agent Framework（LangGraph 等） | FEK |
|---|---|---|
| 用户做什么 | **写** Agent / 状态机 / 工作流 | **提交任务 + 约束**，不写任何编排 |
| 策略来源 | 开发者硬编码 | 引擎**自动**在约束下选 |
| 抽象层级 | 提供构建块（节点/边/记忆/工具） | 提供"约束 → 最优策略"优化，内部用图 |
| 学习 | 通常无 | 从轨迹自优化选择 |

**关系**：FEK 可**嵌入** Agent Framework——例如 LangGraph 的某个节点内部用 FEK 决定"这一步在约束下用单模型还是 MoA"。FEK 是"优化层"，Agent Framework 是"编程模型层"，层级不同。

---

## 6. 为什么 FEK 不只是 MoA（以及为什么这很重要）

MoA 只是 **Strategy Library 里的一个策略**。FEK 还会选 Single / Planner+Reviewer / Reflection / Debate / ToT / Parallel ……

**战略含义**：把 MoA 当核心 = 在 Hermes 的主场作战；把 MoA 当可插拔策略 = FEK 永远吸收新能力而不被绑定。这正是 Optimization Thinking 的精髓——**FEK 的价值在"按约束选"，不在"发明了某个策略"**。

---

## 7. 一句话定位（对外统一口径）

> **FEK 是 AI 基础设施的 AI Compute Optimization Layer：在质量、成本、延迟、隐私等约束下，自动为任务选择并运行最优的执行策略，并持续学习优化。它跑在 Gateway 之上、可嵌入 Agent Framework / IDE 之内，既不是网关、也不是 Agent 框架、更不是 MoA 库。**
