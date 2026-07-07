# FEK 路线图（战略 Pivot 版）

> 原则（见 VISION.md）：**Product 与 Research 严格分离。**
> Product = 近期、可交付、可验证；Research = 探索性、**不承诺交付时间**。
> 所有重大设计先写 RFC（`docs/rfcs/`），再动代码。
> 本次重构（pivot）把 FEK 从"Adaptive AI Execution Engine"转为"Adaptive AI Compute Optimizer"——
> 核心是 **Optimization Thinking**：约束作为一等输入，策略可插拔。

---

## 一、Product Roadmap

### v1 · Constraint-aware Optimizer（当前基线 → 近期）
**目标**：把"在约束下自动选策略"做成可信赖的默认能力。

- [x] 执行内核：Policy Optimizer + Graph Compiler + Compute Graph + Runtime + Fusion + Evaluation + Telemetry（已落地，前称"Adaptive Runtime"）
- [x] 学习层：约束感知 bandit（已落地，前称"Learning Optimizer"）
- [x] Mock 后端：零 API key 可跑；OpenAI 兼容可插拔
- [ ] **新增 Constraint Analysis**：把 `Task + Constraints` 规范化为 `ConstraintProfile`（质量/预算/延迟/隐私/模型偏好），做可行性检查与模型过滤
- [ ] **新增 Strategy Library**：把 SINGLE / MULTI_AGENT / MOA 重构为可插拔 Strategy；新增 Planner+Reviewer / Reflection / Debate / ToT / Parallel / Hierarchical 的原型（多来自已有论文，先 mock 实现）
- [ ] **Policy Optimizer 重构**：输入从"复杂度评分"改为 `ConstraintProfile`，目标改为"约束下最大化质量"
- [ ] **诚实标注**：mock 学习层是方法演示；Evaluation 是玩具启发式；MoA 只是 Strategy 之一

**交付标准**：`FEKKernel.run(task, constraints)` 在约束下选策略并 `explain()`；离线 demo 可对比"同一任务在不同预算/延迟约束下的策略选择"。

### v2 · Constraint-aware Policy Learning（近期，下一个里程碑）
**目标**：让"在约束下学习选策略"从 demo 升级为可信产品能力。

- [ ] 约束感知奖励：学习目标显式带硬约束（预算/延迟/隐私）与多目标权重（质量−成本−延迟）
- [ ] 约束冲突协商原型：当约束不可行（如 $0.01 + 高质量 + <1s）时，主动提案并请求确认
- [ ] 真实成本信号：可选 `tiktoken` 按 token 计费（已具备，接入约束优化目标）
- [ ] 学习可开关 + 可回测：CI 基准断言"约束下学习后不劣于固定阈值"
- [ ] Web 洞察面板：展示每策略在各类约束下的平均奖励/样本数/可行性

**交付标准**：真实模式下，约束下学习后的策略在 cost-quality-latency Pareto 上优于固定阈值（有基准证明）；约束冲突可被检测并解释。

### v3 · Strategy Marketplace（更远期）
- [ ] Strategy Library 支持外部注册（社区新推理策略即插即用）
- [ ] 约束协商 UI：用户用自然语言描述约束，FEK 解析并协商
- [ ] 策略自动基准：新策略接入时自动跑约束化回测，给出适用边界

---

## 二、Research Roadmap

> ⚠️ 探索方向，**不进入交付排期**，不向用户承诺"即将到来"。

### R1 · 约束协商与可行性（Constraint Negotiation）
- 当约束冲突/不可行时，自动提出 Pareto 提案（如"预算 +50% 可达高质量"）。
- 风险：易做成玩具；需可量化收益才晋级 Product。

### R2 · 策略自组合（Strategy Composition）
- 把策略当原语，系统从轨迹中演化出组合策略（如 Debate + Reflection + branching）。
- 风险：与"可解释"原则冲突；须先解决可解释性。

### R3 · 更好的约束/任务理解（最高优先级）
- 嵌入相似度 / 历史任务检索 / LLM 自评，替代关键词启发式（原 Task Profiler 短板升级版）。
- **优先级高于 R1/R2 的"炫技"**——理解错了约束，优化毫无意义。

### R4 · 真实 Evaluation
- LLM-as-judge 替代玩具质量启发式；多维度评分（正确性/完整性/安全性）。

### R5 · Strategy Library 自动扩张
- 自动从论文/项目吸收新策略（MoA / Debate / ToT / Self-Consistency / Graph-of-Thoughts …）为可插拔 Strategy。

---

## 三、明确不做（Non-Goals，见 VISION.md）

- **不是 LLM Gateway**（key 管理 / 统一 API）——交给 LiteLLM/OpenRouter
- **不是 Agent 编程框架 / Workflow Builder**——交给 LangGraph/AutoGen/CrewAI
- **不是 MoA Framework**——MoA 只是 Strategy 之一
- **不是模型训练 / 微调**
- **不是 RAG / 向量数据库**
- **不是 AI OS**

---

## 四、RFC 与路线图的关系

| 里程碑 | 相关 RFC |
|---|---|
| 定位 pivot | **0010 positioning-pivot（新增，Supersede 0001/0002）** |
| Constraint + Policy Optimizer | **0011 constraint-policy-optimizer（新增，Supersede 0003）** |
| Strategy Library | **0012 strategy-library（新增）** |
| v1 基线 | 原 0004 compute-graph, 0005 runtime, 0006 fusion-engine, 0007 evaluation（仍有效） |
| v2 Learning Optimizer | 0009 learning-optimizer（仍有效，目标并入约束优化） |
| R3/R4 研究 | 待新 RFC（如 0013 task-constraint-profiling, 0014 llm-judge） |
