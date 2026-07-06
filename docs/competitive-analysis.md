# 竞争分析 · FEK vs AI Infrastructure 生态

> 配套：VISION.md（非目标）、docs/ecosystem/ai-infra-landscape.md（分层）
> 口径：每个项目先讲它解决什么，再讲 FEK 解决什么，最后给重叠/差异/集成建议。

---

## 总表速览

| 项目 | 层 | 与 FEK 关系 |
|---|---|---|
| LiteLLM | Gateway | FEK 可当其上游调用方 |
| OpenRouter | Gateway | 同上 |
| LangGraph | Agent Framework | FEK 可嵌入其节点 |
| AutoGen | Agent Framework | FEK 可嵌入其会话 |
| CrewAI | Agent Framework | 定位最近似（多智能体），但 FEK 自动化 |
| Mastra | Agent Framework (TS) | FEK 是 Python 引擎，可互补 |
| OpenAI Agents SDK | Agent Framework | FEK 是"策略决策"层，可包其外 |
| Claude Code | Agentic CLI | 不同场景（编码代理），不直接竞争 |
| Hermes | 模型/对齐 | 不同层（模型侧），潜在后端 |
| OpenHands | Agentic 应用 | 不同场景（软件工程代理），不直接竞争 |

---

## 1. LiteLLM

- **解决**：统一 100+ 模型 API、key 管理、fallback、用量与成本计量。是"模型调用的基础设施"。
- **FEK 解决**：给定任务，自动选执行策略并运行，成本感知地权衡质量/延迟。
- **重叠**：都做"成本统计"。但 LiteLLM 在单次调用粒度，FEK 在跨策略粒度。
- **差异**：LiteLLM 不决定"怎么执行任务"，只决定"调哪个模型"。FEK 决定的是更高层的执行 shape。
- **集成**：FEK 的 `LLMBackend` 可直接用 LiteLLM 作为统一后端。**互补，强集成。**

## 2. OpenRouter

- **解决**：模型聚合市场 + 统一 API + 路由到最便宜/最快的可用模型。
- **FEK 解决**：见上。
- **重叠**：模型路由。OpenRouter 路由"模型"，FEK 路由"执行策略"。
- **差异**：OpenRouter 是服务/市场；FEK 是本地可嵌入引擎。
- **集成**：FEK 可通过 `OPENAI_BASE_URL` 指向 OpenRouter 作为后端。**互补。**

## 3. LangGraph

- **解决**：用图（节点/边/状态/记忆）让开发者**显式编排** Agent 工作流。
- **FEK 解决**：自动决定并用图执行策略，用户不写图。
- **重叠**：都有"图"概念。FEK 的 Compute Graph 是引擎内部产物；LangGraph 的图是用户编程接口。
- **差异**：LangGraph 的每个任务都用开发者写死的图；FEK 按任务复杂度**自动**选不同的图。
- **集成**：FEK 可作为 LangGraph 某个节点的内部执行器（"这一步用 FEK 决策"）。**可嵌入。**

## 4. AutoGen

- **解决**：多 Agent 对话框架，开发者定义 Agent 角色与对话拓扑。
- **FEK 解决**：自动选多智能体/MoA 策略并跑，不要求定义角色。
- **重叠**：都能跑多智能体。
- **差异**：AutoGen 要你设计对话；FEK 内置角色模板，按策略自动实例化。
- **集成**：FEK 的 MULTI_AGENT 策略内部可用 AutoGen 风格的对话。**潜在集成。**

## 5. CrewAI

- **解决**：以"角色（Crew）+ 流程"组织多智能体协作，偏产品/业务叙事。
- **FEK 解决**：同上自动决策。CrewAI 是 FEK 的**最近似竞争者**（都涉及按角色组织多智能体）。
- **重叠**：角色化多智能体执行。
- **差异**：CrewAI 是"你定义 Crew，它跑"；FEK 是"你给任务，它决定要不要 Crew、还是单模型更划算"。
- **集成**：FEK 的 MULTI_AGENT 策略可内置 CrewAI 风格的角色。**潜在集成 / 竞争边界。**

## 6. Mastra

- **解决**：TypeScript  Agents 框架（工作流、记忆、评估、部署一体化），面向 JS/TS 全栈。
- **FEK 解决**：Python 执行引擎，语言无关的决策层。
- **重叠**：Agent 编排。
- **差异**：语言栈不同（TS vs Py）；Mastra 是框架，FEK 是引擎。
- **集成**：Mastra 应用可把"复杂步骤"委托给 FEK 的 Python 服务。**互补（跨语言）。**

## 7. OpenAI Agents SDK

- **解决**：轻量 Agent 原语（Agent / Handoff / Guardrails / Tracing），官方生态。
- **FEK 解决**：策略级自动决策。
- **重叠**：都能跑多步 Agent。
- **差异**：Agents SDK 是你组合 Agent；FEK 是引擎替你选"。
- **集成**：FEK 外层包 Agents SDK，自动决定某任务用单 Agent 还是 handoff 链。**可嵌入。**

## 8. Claude Code

- **解决**：终端里的编码 Agent（读/写/跑代码、工具调用）。
- **FEK 解决**：通用任务执行决策，不限定编码场景。
- **重叠**：弱（都是"智能体"大类）。
- **差异**：Claude Code 是具体产品（编码 Copilot）；FEK 是通用执行引擎，不绑定场景。
- **集成**：FEK 的某策略节点可调用 Claude Code 风格的编码子代理。**潜在（作为 backend/工具）。**

## 9. Hermes

- **解决**：开放模型 + 对齐/工具调用数据集（Nous Research），偏模型与数据侧。
- **FEK 解决**：执行层，与模型无关。
- **重叠**：无（不同层）。
- **差异**：Hermes 是模型/数据；FEK 是执行引擎。
- **集成**：FEK 可把 Hermes 系列模型当作 `LLMBackend`。**互补（后端）。**

## 10. OpenHands (原 OpenDevin)

- **解决**：自主软件工程 Agent（写代码、修 bug、跑命令）。
- **FEK 解决**：通用执行决策。
- **重叠**：弱（都是自主 Agent 大类）。
- **差异**：OpenHands 是具体领域 Agent 产品；FEK 是通用引擎。
- **集成**：OpenHands 内部某步可用 FEK 决策"这步要不要用多智能体"。**潜在（嵌入）。**

---

## 结论：FEK 的防守位

FEK 不应与任何 Agent Framework 或 Gateway **正面竞争**——那是在别人的主场作战。它的护城河是：

1. **自动化决策**（用户不写 Agent / 不配 Gateway 路由，只交任务）。
2. **成本感知闭环**（决策可被 cost/latency/quality 量化优化并学习）。
3. **可解释**（每个决策 `explain()`）。

对外沟通永远先讲"我们跑在 Gateway 之上、可嵌入 Agent Framework 之内"，把竞争变成集成。
