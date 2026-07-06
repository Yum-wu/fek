# AI Infrastructure 生态分层与 FEK 定位

> 配套：VISION.md（非目标）、docs/competitive-analysis.md（逐项目对比）、docs/architecture.md（模块边界）

---

## 1. 生态分层（自底向上）

```
┌──────────────────────────────────────────────────────────┐
│  Applications        聊天机器人 / Copilot / RAG / 工作流    │
├──────────────────────────────────────────────────────────┤
│  Agent Frameworks    LangGraph / AutoGen / CrewAI /         │
│                       OpenAI Agents SDK / Mastra            │
├──────────────────────────────────────────────────────────┤
│  ▶ Execution Layer ◀  FEK（自适应 AI 执行引擎）             │
│    Task Profiler → Policy Engine → Graph Compiler →        │
│    Runtime → (Fusion, Evaluation) → Telemetry → 学习        │
├──────────────────────────────────────────────────────────┤
│  Gateway Layer        LiteLLM / OpenRouter                  │
│  （统一 API、key 管理、fallback、用量计费）                  │
├──────────────────────────────────────────────────────────┤
│  SDK Layer            OpenAI SDK / Anthropic SDK            │
├──────────────────────────────────────────────────────────┤
│  Model Layer          GPT / Claude / Llama / 本地模型       │
└──────────────────────────────────────────────────────────┘
```

---

## 2. 每层解决什么

| 层 | 解决的核心问题 | 典型项目 |
|---|---|---|
| **Model** | "智能从哪来"——提供基础能力 | GPT-4o, Claude, Llama, Qwen |
| **SDK** | "怎么调用模型"——统一客户端 API | OpenAI SDK, Anthropic SDK |
| **Gateway** | "怎么管一堆模型"——统一接口、key、fallback、成本计量 | LiteLLM, OpenRouter |
| **Execution** | "这个任务**怎么执行最划算**"——自动选策略、编译计算图、跑、学 | **FEK** |
| **Agent Framework** | "怎么**让用户组合**智能体/工作流"——编程模型 | LangGraph, AutoGen, CrewAI |
| **Application** | "解决最终用户问题" | 各类产品 |

---

## 3. 为什么 FEK 属于 Execution Layer

Execution Layer 回答的问题是：**给定一个任务，用哪种执行方式（单次调用 / 多智能体 / MoA）能在成本-质量-延迟上最优？** 这正是 FEK 的 Policy Engine + Compute Graph + Runtime 闭环在做的事。

FEK 的输入是"任务"，输出是"执行结果 + 执行轨迹"。它**不暴露给最终用户编程模型**（那是 Agent Framework 的事），也**不代理模型 API**（那是 Gateway 的事）。它坐在两者之间的"决策+执行"位置。

---

## 4. 为什么 FEK 不是 Gateway

| 维度 | Gateway（LiteLLM/OpenRouter） | FEK |
|---|---|---|
| 输入 | 模型调用请求（messages） | 任务（自然语言指令） |
| 核心动作 | 路由到某个模型、管理 key、重试 | **决定执行策略**（单模型/多智能体/MoA） |
| 是否代理 token API | 是 | 否（可**调用** Gateway 作为后端） |
| 是否编排多步执行 | 否 | 是（Compute Graph 多节点） |
| 成本感知粒度 | 单次调用账单 | 跨策略的 cost/latency/quality 权衡 |

**关系**：FEK 跑在 Gateway **之上**。FEK 的 Runtime 调用模型时，可把 LiteLLM/OpenRouter 当作 `LLMBackend` 使用。二者互补，不竞争。

---

## 5. 为什么 FEK 不是 Agent Framework

| 维度 | Agent Framework（LangGraph 等） | FEK |
|---|---|---|
| 用户做什么 | **写** Agent / 状态机 / 工作流 | **提交任务**，不写任何编排 |
| 策略来源 | 开发者硬编码 | 引擎**自动**按复杂度选 |
| 抽象层级 | 提供构建块（节点/边/记忆/工具） | 提供"执行决策"，内部用图 |
| 学习 | 通常无 | 从遥测自优化策略选择 |

**关系**：FEK 可**嵌入** Agent Framework——例如 LangGraph 的某个节点内部用 FEK 决定"这一步用单模型还是 MoA"。FEK 是"决策层"，Agent Framework 是"编程模型层"，层级不同。

---

## 6. 为什么 FEK 不只是 MoA

MoA（Together AI）是一种**融合技术**：多个模型生成候选，再由 aggregator 综合。在 FEK 里，MoA 只是 `Strategy` 枚举中的一个值（`MOA`）。FEK 还会选 `SINGLE`（简单任务）和 `MULTI_AGENT`（规划+批判），未来可加 `DEBATE` / `REFLECTION`。FEK 的价值在"**按任务选**"，MoA 只是候选之一。

---

## 7. 一句话定位（对外统一口径）

> **FEK 是 AI 基础设施的 Execution Layer：为每个任务自动选择并运行最优执行策略，并在成本/质量/延迟上持续学习优化。它跑在 Gateway 之上、可嵌入 Agent Framework 之内，既不是网关也不是 Agent 框架。**
