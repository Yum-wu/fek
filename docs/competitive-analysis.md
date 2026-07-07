# 竞争分析 · FEK vs AI Infrastructure 生态

> 配套：VISION.md（非目标）、docs/ecosystem/ai-infra-landscape.md（分层）
> **本次重构的口径变化**：不比较"功能清单"，只比较**每个项目解决什么问题、FEK 解决什么问题、是否存在重叠、FEK 位于哪一层**。
> 关键立场：FEK 不与任何 Agent Framework / Gateway **正面竞争**，而是做它们之上的 **AI Compute Optimization Layer**。

---

## 总表速览（按"解决什么问题"分）

| 项目 | 它解决什么问题 | FEK 位于哪层 | 关系 |
|---|---|---|---|
| LiteLLM | 统一 100+ 模型 API / key / 成本计量 | Gateway（FEK 之下） | 互补，FEK 的后端 |
| OpenRouter | 模型聚合市场 + 路由 | Gateway（FEK 之下） | 互补 |
| LangGraph | 提供图让开发者**编排** Agent 工作流 | Agent Framework（FEK 之上） | FEK 可嵌入其节点 |
| AutoGen | 多 Agent 对话框架（开发者定义角色） | Agent Framework | FEK 可嵌入其会话 |
| CrewAI | 角色化多智能体协作（产品叙事） | Agent Framework | 边界最近，但 FEK 自动化 |
| Mastra | TS Agents 框架（工作流/记忆/评估） | Agent Framework | 跨语言互补 |
| OpenAI Agents SDK | 轻量 Agent 原语（Agent/Handoff/Tracing） | Agent Framework | FEK 可包其外 |
| Claude Code | 终端编码 Agent（自动生成 workflow、动态选执行流） | Agentic 应用/IDE | **部分重叠风险，见下** |
| Hermes | 开放模型 + 对齐数据（Nous Research） | 模型/数据侧 | FEK 的潜在后端 |
| OpenHands | 自主软件工程 Agent | Agentic 应用 | 不同场景 |

---

## 1. LiteLLM / OpenRouter（Gateway）

- **解决什么问题**：模型接入的基础设施——统一 API、key 管理、fallback、成本计量、路由到最便宜/最快的模型。
- **FEK 解决什么问题**：在模型之上，给定任务 + 约束，决定"用哪种执行策略（单模型/MoA/Debate…）"并运行、学习。
- **重叠**：都做"成本统计"。LiteLLM 在单次调用粒度，FEK 在跨策略、跨约束粒度。
- **FEK 的层**：Gateway **之上**。FEK 的 `LLMBackend` 直接把 LiteLLM/OpenRouter 当后端。
- **结论**：**强互补，零竞争。**

## 2. LangGraph / AutoGen / CrewAI / Mastra / OpenAI Agents SDK（Agent Framework）

- **解决什么问题**：给开发者一套**编程模型**来组合 Agent / 工作流 / 状态机 / 记忆 / 工具。
- **FEK 解决什么问题**：开发者**不写**任何编排；只提交任务 + 约束，FEK 自动选策略并执行。
- **重叠**："都能跑多步/多智能体"。但 Framework 的每一步形态由开发者定；FEK 的步骤形态由引擎按约束自动定。
- **FEK 的层**：Agent Framework **之内/之上**的可嵌入优化层。例如 LangGraph 某节点内部用 FEK 决策"这步在约束下用单模型还是 MoA"。
- **结论**：**层级不同，可嵌入，不竞争。** FEK 主动把"编排"让给 Framework，自己只做"约束 → 策略优化"。

## 3. Claude Code / Cursor（Agentic IDE / 应用）

- **解决什么问题**：终端/编辑器里的编码 Agent——**已能按任务自动生成 workflow、动态选择执行流程、多模型协同**。
- **FEK 解决什么问题**：通用任务的约束优化（不绑定编码场景）；强调约束（预算/延迟/隐私）作为一等输入与可解释、可回测的学习。
- **重叠（须正视）**：Claude Code 的"动态选执行流"与 FEK 的"自动选策略"在**能力表象**上重叠。这正是本次 pivot 的动因——若 FEK 也强调"自动 workflow"，就直接与 Claude Code 撞车。
- **FEK 的差异化**：FEK 不绑定编码场景、不提供 Agent 产品，而是把"约束下的策略优化"做成**可嵌入、可学习、可解释的计算优化层**；Claude Code 是具体 Agent 产品，不会把"约束优化"抽象成独立层对外开放。
- **结论**：**避免正面竞争。** FEK 的护城河是"约束感知的策略优化闭环"，不是"能自动写 workflow"（那已是商品）。

## 4. Hermes（模型 / 数据侧）

- **解决什么问题**：开放模型权重 + 工具调用/对齐数据集。
- **FEK 解决什么问题**：与模型无关的执行优化层。
- **重叠**：无（不同层）。
- **FEK 的层**：Hermes 可作为 FEK 的 `LLMBackend`（尤其隐私约束要求本地/开放模型时）。
- **结论**：**互补（后端）。** 顺带：Hermes 的 MoA 能力，FEK 作为 Strategy Library 中的一个 Strategy 适配，而非重造。

## 5. OpenHands（自主软件工程 Agent）

- **解决什么问题**：写代码、修 bug、跑命令的自主 Agent 产品。
- **FEK 解决什么问题**：通用任务的约束优化，不绑定软件工程。
- **重叠**：弱（同属自主 Agent 大类）。
- **FEK 的层**：可嵌入——OpenHands 内部某步可用 FEK 决策"这步在约束下要不要多模型"。
- **结论**：**不同场景，潜在嵌入。**

---

## 结论：FEK 的防守位与进攻位

**防守位（不与之下场）**：Agent Framework、Gateway、MoA 库、具体 Agent 产品——这些要么已商品化，要么在别人主场。

**进攻位（FEK 真正的长期位置）**：**AI Compute Optimization Layer**——
在质量/成本/延迟/隐私约束下，自动选最优执行策略，并把所有新推理策略吸收为可插拔 Strategy。

**护城河不是单个组件，而是"约束感知、策略无关、可学习的策略优化闭环"**（详见 VISION.md 与 architecture.md Part 4）。

对外沟通永远先讲："我们跑在 Gateway 之上、可嵌入 Agent Framework / IDE 之内，做的是约束下的策略优化。"把竞争变成集成。
