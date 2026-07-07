# VISION · FEK

> **FEK = Adaptive AI Compute Optimizer（自适应 AI 计算优化器）**
> 一句话定位：**在质量、成本、延迟、隐私等约束下，自动为任务选择最优的 AI 计算策略。**

---

## 1. FEK 是什么

FEK 是一个 **AI 计算优化层（AI Compute Optimization Layer）**。

你提交一个**任务**和一组**约束**（期望质量、预算上限、延迟上限、隐私要求、可接受的模型清单），FEK 自动：

1. **分析约束**（Constraint Analysis）——把约束规范化、做可行性检查、按隐私/偏好过滤可用模型；
2. **优化策略选择**（Policy Optimizer）——在约束下从策略库中选出（或组合出）最优执行策略；
3. **生成执行计划**（Execution Plan）——把选中的策略编译成计算图；
4. **执行并度量**（Runtime + Telemetry）——跑、打分、记录成本/质量/延迟/隐私；
5. **学习回流**——从每次轨迹中优化未来的选择。

FEK **不要求你写 Agent、不编排工作流、不挑模型、也不发明推理策略**。你只描述"要什么"和"限制是什么"，FEK 决定"怎么算最划算"。

MoA、Debate、Reflection、Tree of Thoughts 等，在 FEK 里都只是**可插拔的策略（Strategy）**，不是 FEK 自己的创新，也不是 FEK 的卖点。

---

## 2. 为什么存在（第一性原理）

过去两年，AI 基础设施快速商品化，**以下能力已不再是差异化护城河**：

- **自动 Workflow / 动态执行流**：Claude Code 已能按任务自动生成 workflow、动态选执行流程；Cursor、Claude Code 社区已大量采用多模型协同。
- **MoA（混合专家）**：Hermes、Together AI 已做成成熟能力。
- **推理策略**（Debate / Reflection / Tree of Thoughts / Self-Consistency …）：已被大量论文验证，正在变成"标配积木"。

> **结论**：继续围绕"自动 workflow"或"支持 MoA"设计 FEK，等于在 Claude Code / Hermes 的主场作战。这些能力会随新框架、新策略的出现而过时。

FEK 应该回答一个**更上游、更稳定**的问题：

> **给定任务和约束，如何在质量 / 成本 / 延迟 / 隐私之间取得最优权衡？**

这个问题不会因某个新 Agent 框架或新推理策略的出现而消失。相反，FEK 可以把所有新能力都吸收为**可插拔的策略**，自身始终停留在更高的"策略优化"抽象上。

这就是从 **Framework Thinking → Optimization Thinking** 的根本转向，也是 FEK 最有长期竞争力的方向。

---

## 3. 解决什么问题

| 问题 | FEK 的解法 |
|---|---|
| "这个任务该用单模型、多智能体还是 MoA？" | Policy Optimizer 在约束下自动选 |
| "预算只有 $0.2，但质量要 High，怎么选？" | 约束感知优化：在预算内最大化质量 |
| "数据不能出本地，能用哪些模型？" | Constraint Analysis 过滤模型、强制隐私策略 |
| "多花的算力真的值得吗？" | Telemetry 并排对比，决策可解释、可回测 |
| "新出的推理策略（如 ToT）怎么用上？" | 作为 Strategy 插进 Strategy Library，无需改引擎 |

---

## 4. 刻意不解决什么（Non-Goals）

为避免功能蔓延，FEK **明确不做**：

- **不是 LLM Gateway**：不做 key 管理 / 统一 API 封装；FEK 跑在 Gateway 之上。
- **不是 Agent Framework / Workflow Builder**：不提供让你组合 Agent / 写工作流的 SDK；策略是内部自动决定的。
- **不是 MoA Framework**：MoA 只是 Strategy Library 里的一个策略，FEK 不发明 MoA。
- **不是模型训练 / 微调框架**。
- **不是 RAG / 向量数据库**。
- **不是 AI OS**：不做通用调度 / 资源虚拟化。

---

## 5. 长期愿景

> **让"如何在约束下最优化 AI 计算"成为一等公民：应用描述任务与约束，FEK 负责选策略、跑、学。**

远期，FEK 希望成为 AI 应用与模型之间的**默认计算优化层**：

- 应用只描述"任务 + 约束"，FEK 负责"怎么算最划算"。
- 策略库自动吸收社区新推理方法（MoA / Debate / ToT / Self-Consistency …）。
- 约束 → 策略的帕累托前沿，由引擎在每次任务上求解。

---

## 6. 设计原则（Principles）

1. **Optimization-first**：对外沟通讲"在约束下优化"，不讲"支持多少 Agent / 多少 MoA / 多少 Workflow"。
2. **Constraint-aware**：约束是一等输入，不是事后过滤；冲突时主动协商，而非静默降级。
3. **Strategy-agnostic**：MoA / Debate / ToT 都是可插拔 Strategy，引擎不绑定任一；新策略即插即用。
4. **可解释（Explainable）**：每个选择都能讲清"为什么、在哪些约束下、预期权衡是什么"。
5. **零配置可跑（Zero-config）**：mock 模式无需 API key 即可完整演示。
6. **学习可回测（Learnable & auditable）**：学习改动必须能离线回测对比，否则只是噱头。
7. **诚实（Honest）**：演示性质能力必须明确标注，不夸大。

---

## 7. 非目标边界（与路线图关系）

- **Product Roadmap**（见 `docs/roadmap.md`）：v1 Constraint-aware Optimizer、v2 Constraint-aware Policy Learning——近期、可交付、可验证。
- **Research Roadmap**（见 `docs/roadmap.md`）：约束协商、策略自组合、更好约束理解、LLM 裁判——探索性、**不承诺交付时间**。

---

## 8. 未来演进（方向，非承诺）

- Strategy Library 自动吸收新论文（MoA / Debate / ToT / Self-Consistency / Graph-of-Thoughts …）。
- 约束可行性检测与协商（预算 / 质量 / 延迟冲突时主动提案）。
- 真实 LLM 裁判（LLM-as-judge）替代玩具质量启发式。
- 真实 token 计费（接 tokenizer），让成本信号可信。
- 约束理解从关键词启发式升级到嵌入 / 检索 / LLM 自评。

---

*本文件是 FEK 的权威愿景文档。任何重大设计变更，先写 RFC（见 `docs/rfcs/`），再改代码。*
