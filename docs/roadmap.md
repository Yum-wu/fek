# FEK 路线图

> 原则（见 VISION.md / 架构评审）：**Product 与 Research 严格分离。**
> Product = 近期、可交付、可验证；Research = 探索性、依赖研究突破、**不承诺交付时间**。
> 所有重大设计先写 RFC（`docs/rfcs/`），再动代码。

---

## 一、Product Roadmap

### v1 · Adaptive Runtime（当前 → 近期）
**目标**：把"自动选策略 + 成本感知执行"做成可信赖的默认能力。

- [x] Task Profiler：可解释复杂度估计（启发式）
- [x] Policy Engine：SINGLE / MULTI_AGENT / MOA 自动选择 + `explain()`
- [x] Graph Compiler + Compute Graph：三策略 → 三种 DAG
- [x] Runtime：拓扑执行、可并行
- [x] Fusion Engine：确定性融合（结构化合并）
- [x] Evaluation：质量启发式打分（**占位，须标注**）
- [x] Telemetry：cost/latency/quality 记录 + 对战模式
- [x] Mock 后端：零 API key 可跑；OpenAI 兼容可插拔
- [ ] **诚实标注**：mock 学习层是方法演示；Evaluation 是玩具启发式
- [ ] 把"复杂度分类器是最弱一环"作为已知限制写入文档

**交付标准**：开发者 `pip install fek`（mock 模式）一条命令跑通；每个决策可 `explain()`；遥测能并排三策略成本/质量。

### v2 · Learning Optimizer（近期，下一个里程碑）—— 已实现 ✅
**目标**：把"从轨迹学习"从 demo 升级为可信产品能力。

- [x] Policy Engine 学习从 ε-greedy 升级到可切换（默认 ε-greedy；`create_learner` 工厂 + `Learner` 协议；LinUCB 预留为 v2.1）
- [x] 真实成本信号：可选 `tiktoken` 按 token 计费（`fek/cost`，未装则回退固定估算；核心仍零依赖）
- [x] 学习可开关 + 可回测：Web UI 勾选「启用学习」对比"纯规则 vs 学习后"
- [x] 学习洞察面板：Web 展示每臂平均奖励 / 样本数
- [x] 离线回测成为 CI 可跑的基准（`tests/test_backtest.py` 断言学习后不劣于固定阈值）

> 实现细节见 RFC 0009 · Learning Optimizer。

**交付标准**：真实模式下学习后策略在 cost-quality Pareto 上优于固定阈值（有基准证明）；学习行为可解释、可关闭。

---

## 二、Research Roadmap

> ⚠️ 以下为**探索方向**，依赖研究突破或重大投入，**不进入交付排期**，不向用户承诺"即将到来"。

### R1 · Self-Evolving Execution（自演化执行）
- 图变异 / 角色自演化：系统从轨迹中演化出新的 Compute Graph 形状，而非固定三策略。
- 策略原语空间：从"三选一"扩展到可组合原语（debate / reflection / branching / voting）。
- 风险：易沦为演示噱头；需可量化收益才考虑晋级 Product。

### R2 · Autonomous Kernel（自主内核）
- 自主目标分解：给定高层目标，自动拆为子任务并调度。
- 长期记忆 / 跨会话经验累积。
- 风险：与"零依赖、可解释"原则冲突；须先解决可解释性再谈自主。

### R3 · 更好的 Task Profiling
- 嵌入相似度 / 历史任务检索 / LLM 自评复杂度，替代关键词启发式。
- 这是当前最弱一环，优先级高于 R1/R2 的"炫技"。

### R4 · 真实 Evaluation
- LLM-as-judge 替代玩具质量启发式；多维度评分（正确性/完整性/安全性）。

---

## 三、明确不做（Non-Goals，见 VISION.md）

- Go 运行时 / 分布式执行（与零依赖优势冲突，且非 MVP 价值）
- 模型训练 / 微调
- LLM Gateway（key 管理 / 统一 API）——交给 LiteLLM/OpenRouter
- Agent 编程框架——交给 LangGraph/AutoGen/CrewAI
- RAG / 向量数据库

---

## 四、RFC 与路线图的关系

每个 Product 里程碑对应若干 RFC（见 `docs/rfcs/`）：

| 里程碑 | 相关 RFC |
|---|---|
| v1 基线 | 0001 project-vision, 0002 execution-model, 0003 policy-engine, 0004 compute-graph, 0005 runtime, 0006 fusion-engine, 0007 evaluation |
| v2 Learning Optimizer | 0003 policy-engine（学习部分）, 0008 roadmap |
| R3/R4 研究 | 待新 RFC（如 0009 task-profiling, 0010 llm-judge） |
