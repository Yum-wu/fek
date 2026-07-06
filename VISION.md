# VISION · FEK

> **FEK = Adaptive AI Execution Engine（自适应 AI 执行引擎）**
> 核心职责一句话：**为每个 AI 任务自动决定"用哪种执行策略最划算"。**

---

## 1. FEK 是什么

FEK 是一个**执行引擎**：你提交一个任务（一段自然语言指令），它自动判断该任务的复杂度，选择一个执行策略——单模型一次调用、规划+批判的多智能体、还是混合专家（MoA）融合——把这个策略编译成一张计算图（Compute Graph），交给运行时执行，并从每次执行的成本/延迟/质量遥测中持续学习、优化未来的策略选择。

FEK 不要求你写 Agent、不要求你编排工作流、不要求你选模型。你只提交任务，它决定**怎么执行**。

---

## 2. 为什么存在

今天构建一个"会思考的 AI 系统"，开发者被迫在两条路里选：

- **自己手写 Agent / 工作流**（LangGraph / AutoGen / CrewAI）：灵活，但每个任务都用"重"策略，成本和延迟失控，且新手很容易过度设计。
- **直接调一个强模型**（GPT / Claude）：简单，但对简单任务浪费钱，对困难任务又不够。

两条路都缺一个东西：**一个能"看任务下菜碟"的执行层**——简单任务用便宜的单次调用，困难任务才上多智能体/MoA，并且能**量化地证明"多花的算力确实换来了更好的结果"**。

FEK 填补的就是这一层。

---

## 3. 解决什么问题

| 问题 | FEK 的解法 |
|---|---|
| "这个任务到底该用单模型还是多智能体？" | Policy Engine 按复杂度自动选 |
| "多智能体/MoA 是不是在瞎花钱？" | Telemetry 把 cost/latency/quality 并排，决策可解释 |
| "系统能不能越用越聪明？" | 从执行遥测学习策略偏好（成本感知 contextual bandit） |
| "换模型/换后端麻烦吗？" | Backend 抽象层，mock 离线可跑，OpenAI 兼容可插拔 |
| "新人能一眼看懂吗？" | 零依赖内核 + `explain()` 把每个决策讲清楚 |

---

## 4. 刻意不解决什么（Non-Goals）

为避免功能蔓延，FEK **明确不做**以下事：

- **不是 LLM Gateway**：不代理 token 级 API 调用、不做 key 管理、不做统一 API 封装。FEK 跑在 Gateway **之上**（可用 LiteLLM/OpenRouter 当后端）。
- **不是 Agent Framework**：不提供让你组合 Agent / 写工作流的 SDK。FEK 的策略是**内部自动**决定的，用户不写 Agent。
- **不是模型训练/微调框架**。
- **不是 RAG / 向量数据库**。
- **不是又一个 MoA 库**：MoA 只是 FEK 的多种策略之一。
- **不是通用编排器**（如 Airflow）：FEK 只编排"AI 执行"，不编排数据管道。

---

## 5. 长期愿景

> **让"如何执行一个 AI 任务"成为一个可被优化、可被学习、可被解释的一等公民。**

远期，FEK 希望成为 AI 应用与底层模型之间的**默认执行层**：

- 应用只描述"任务"，FEK 负责"怎么跑最划算"。
- 执行策略从硬编码三选一，演进到**由系统从海量执行轨迹中自演化**出来的策略空间。
- 成本/质量/延迟的帕累托前沿，由引擎自动在每次任务上求解。

---

## 6. 设计原则（Principles）

1. **决策可解释（Explainable by default）**：每一个策略选择都必须能用 `explain()` 讲清楚"为什么"，不接受黑箱。
2. **成本感知（Cost-aware）**：成本/延迟/质量三者同等重要，决策必须显式权衡，不默认"越多算力越好"。
3. **零配置可跑（Zero-config runnable）**：mock 模式无需任何 API key 即可完整演示，降低一切采用摩擦。
4. **分层可替换（Composable layers）**：Task Profiler / Policy Engine / Graph Compiler / Runtime / Fusion / Evaluation / Telemetry 各层职责单一、接口稳定、可独立替换。
5. **学习可回测（Learnable & auditable）**：学习层的改动必须能离线回测对比，否则只是噱头。
6. **诚实（Honest）**：演示性质的能力（如 mock 学习）必须明确标注，不夸大。

---

## 7. 非目标边界（与路线图的关系）

- **Product Roadmap**（见 `docs/roadmap.md`）：v1 Adaptive Runtime、v2 Learning Optimizer——近期、可交付、可验证。
- **Research Roadmap**（见 `docs/roadmap.md`）：Self-Evolving Execution、Autonomous Kernel——探索性、依赖研究突破、**不承诺交付时间**。

---

## 8. 未来演进（方向，非承诺）

- 更好的 Task Profiling（嵌入相似度 / 历史任务检索 / LLM 自评复杂度）。
- 真实 LLM 裁判（LLM-as-judge）替代玩具质量启发式。
- 真实 token 计费（接 tokenizer），让成本信号可信。
- 策略空间从三选一扩展到可组合的策略原语（debate / reflection / branching）。
- 可选依赖层：在保持内核零依赖的同时，允许"进阶能力"按需安装。

---

*本文件是 FEK 的权威愿景文档。任何重大设计变更，先写 RFC（见 `docs/rfcs/`），再改代码。*
