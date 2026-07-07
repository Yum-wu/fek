# FEK 架构（重构版 · 战略 Pivot）

> 权威架构文档。本次重构把 FEK 从"Adaptive AI Execution Engine"重新定位为
> **"Adaptive AI Compute Optimizer / AI Compute Optimization Layer"**。
> 核心转向 **Optimization Thinking**：FEK 的价值是"在约束下选最优策略"，
> 而非"支持多少 workflow / 多少 MoA"。
> 配套：VISION.md（愿景）、docs/roadmap.md（路线图）、docs/rfcs/*（各模块 RFC）。

---

## Part 4 · 核心创新到底是什么

FEK 里每个孤立组件都不是新东西，而且**很多已经商品化**：

- **Workflow / Agent 编排**——LangGraph、AutoGen、CrewAI 成熟；Claude Code 已能自动生成 workflow。
- **MoA 融合**——Hermes、Together AI 已做成成熟能力。
- **推理策略**（Debate / Reflection / ToT / Self-Consistency）——大量论文验证，已成"标配积木"。
- **策略路由（bandit）**——RouteLLM、FrugalGPT 早就在做。
- **Compute Graph（DAG）**——LangGraph、AutoGen 都有图。

**那 FEK 新在哪？**

> FEK 的新，在于它是一个**约束感知、策略无关、可学习的策略优化闭环**：
>
> **Task + Constraints → Constraint Analysis → Policy Optimizer → Strategy Selection → Execution Plan → Runtime → Telemetry →（学习）→ Policy Optimizer**
>
> 并且这个闭环对使用者是**全自动**的：你提交"任务 + 约束"，引擎自己决定"用哪个策略（MoA / Debate / ToT / 单模型 …）"，执行、度量、再优化。

更精确地说，FEK 的真正创新点是一个**产品化的优化闭环**，而非任一组件：

1. **约束作为一等输入**：不是"先选策略再过滤"，而是"质量 / 成本 / 延迟 / 隐私 / 模型偏好"一开始就进入优化目标。
2. **策略无关（Strategy-agnostic）**：MoA、Debate、ToT 都是可插拔 Strategy，引擎不绑定任一；新策略即插即用。
3. **约束感知的奖励信号**：优化目标显式是"在约束下最大化质量"（如 `质量 − λ·成本 − μ·延迟`，并带可行性/隐私硬约束），不是"效果最好"。
4. **可解释 + 可回测的学习**：每个决策能 `explain()`，每次学习能离线回测对比。

单独看都不新；**组合成"约束驱动、策略无关、可嵌入、可解释的策略优化层"**才是 FEK 的差异化。对外沟通必须这么讲。

---

## Part 5 · 重构后的模块边界

### 5.1 分层总览

```
┌──────────────────────────────────────────────────────────────────┐
│  Application / Agent Framework / IDE                               │
│  （调用 FEKKernel.run(task, constraints)，不关心内部策略）          │
└───────────────┬──────────────────────────────────────────────────┘
                │ Task + Constraints（任务 + 约束）
                ▼
┌──────────────────────────────────────────────────────────────────┐
│  Constraint Analysis  （输入层）  (Task, Constraints) → ConstraintProfile │
│     ├─ 约束规范化 / 可行性检查                                        │
│     └─ 模型过滤（隐私/本地/偏好）                                     │
├──────────────────────────────────────────────────────────────────┤
│  Policy Optimizer     （决策层 · FEK 心脏）                         │
│     (ConstraintProfile, Telemetry) → StrategyDecision              │
│     └─ Learning（约束感知 bandit，可学习、可解释）                   │
├──────────────────────────────────────────────────────────────────┤
│  Strategy Library     （策略层 · 可插拔）                           │
│     Single │ Planner+Reviewer │ Reflection │ Debate │ ToT │         │
│     MoA │ Parallel │ Hierarchical │ …（均来自论文/项目，非 FEK 发明）│
│     每个 Strategy: (task, constraints, models) → ComputeGraph      │
├──────────────────────────────────────────────────────────────────┤
│  Graph Compiler       （规划层）  StrategyDecision → ComputeGraph   │
│  Compute Graph        （数据结构）  节点 + 依赖的 DAG               │
├──────────────────────────────────────────────────────────────────┤
│  Runtime              （执行层）  ComputeGraph → ExecutionResult    │
│     ├─ Fusion Engine   （子组件）多输出 → 融合答案（MoA/Parallel 用）│
│     └─ Evaluation      （子组件）输出 → 质量分 [0,1]                │
├──────────────────────────────────────────────────────────────────┤
│  Telemetry            （观测层）  ExecutionResult → Trace           │
│     └──────────────── 反馈给 Policy Optimizer（学习闭环）──────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 模块职责 / 接口 / 依赖

#### Constraint Analysis（新模块）
- **职责**：把 `(Task, Constraints)` 转成 `ConstraintProfile`（规范化质量/预算/延迟目标、隐私级别、允许的模型集合、可行性标志）。
- **接口**：`analyze(task: Task, constraints: Constraints) -> ConstraintProfile`
- **依赖**：无（当前启发式；未来可接嵌入/检索/LLM 自评）。
- **为何新增**：旧 `Task Profiler` 只看"任务复杂度"，新定位要求"约束"也是一等输入；可行性检查与模型过滤必须在优化前完成。

#### Policy Optimizer（原 Policy Engine，核心，扩展）
- **职责**：根据 `ConstraintProfile` 选择（或组合）执行策略，输出 `StrategyDecision` 含 `explain()`。
- **接口**：`select(profile: ConstraintProfile) -> StrategyDecision`；`learn(trace)`；`explain(decision) -> str`
- **依赖**：读取 ConstraintProfile；写入 Telemetry（经 Kernel）；从 Telemetry 学习。
- **与旧版差异**：旧版输入是"复杂度评分"，输出是三选一策略；新版输入是"约束画像"，目标是在约束下优化（带硬约束与多目标），策略集合来自 Strategy Library，可扩展。

#### Strategy Library（新模块 · 可插拔）
- **职责**：维护一组**策略实现**。每个 Strategy 是一个组件，给定 `(task, constraints, models)` 产出一张 `ComputeGraph`。
- **接口**：`Strategy` 协议：`build(task, constraints, models) -> ComputeGraph`；`name`、`cost_tier`、`supports_constraints()`。
- **内置策略（均来自已有论文/项目，FEK 不发明）**：
  - `Single`（单模型一次调用）
  - `PlannerPlusReviewer`（规划 + 批判）
  - `Reflection`（自反思循环，Reflexion）
  - `Debate`（多角色辩论）
  - `TreeOfThoughts`（树搜索，ToT）
  - `MoA`（混合专家，Hermes/Together 风格——FEK 适配，不重造）
  - `Parallel`（并行多模型投票/融合）
  - `Hierarchical`（层级分解）
- **依赖**：Compute Graph 结构；可被 Policy Optimizer 调用。
- **关键立场**：MoA 只是其中一个 Strategy；FEK 不负责创造策略，只负责选。

#### Graph Compiler（原 compiler/，不变语义）
- **职责**：把 `StrategyDecision` 实例化为具体 `ComputeGraph`（必要时组合多个策略原语）。
- **接口**：`compile(decision, task, constraints, models) -> ComputeGraph`

#### Compute Graph（原 core/graph，不变）
- **职责**：纯数据结构，描述节点（角色/类型/依赖）与边。
- **接口**：`ComputeGraph`：`nodes`、`edges`、`topological_order()`

#### Runtime（原 runtime/，不变）
- **职责**：拓扑序执行 Compute Graph，处理并行、重试，产出 `ExecutionResult`（含 Execution Trace）。
- **接口**：`execute(graph, backend, constraints) -> ExecutionResult`

#### Fusion Engine（原 fusion/，子组件）
- **职责**：把多个节点输出聚合成一个融合答案（加权 / LLM 融合 / 结构化合并）。
- **说明**：仅作为 MoA / Parallel 策略的实现细节，不是项目级概念。

#### Evaluation（原 reflection/，改名）
- **职责**：给输出打质量分 [0,1]（当前启发式；未来 LLM-as-judge）。

#### Telemetry（原 telemetry/，不变）
- **职责**：记录每次 `ExecutionResult` 为 trace（strategy / constraints / cost / latency / quality / privacy），聚合统计，供 Policy Optimizer 学习。

### 5.3 依赖方向（必须单向）

```
Application → Constraint Analysis → Policy Optimizer → Strategy Library
                                                   ↓
                              Graph Compiler → Compute Graph
                                                   ↓
                              Runtime → (Fusion Engine, Evaluation) → ExecutionResult
                                                   ↓
                                              Telemetry ──┐
                                                         ↓
                                           Policy Optimizer（学习）
```

- 上层依赖下层，下层**绝不**反向 import 上层。
- Telemetry 是唯一的"回边"，只通过数据（trace）回流，不形成代码环。
- `FEKKernel`（`kernel.py`）是唯一编排入口。

### 5.4 与当前代码的映射（pivot 阶段 6 + v2 约束学习阶段 7 已落地）

| 新模块 | 当前路径 | pivot 动作 |
|---|---|---|
| Constraint Analysis | `fek/constraint/analyzer.py`（已新增） | 新增 `fek/constraint/`；`Task` 扩展 `constraints` 字段；`Constraints` / `ConstraintProfile` 落地于 `fek/core/types.py` |
| Policy Optimizer | `fek/policy/optimizer.py`（`PolicyOptimizer`，新）+ `fek/policy/engine.py`（`PolicyEngine`，保留兼容） | 输入从复杂度评分改为 `ConstraintProfile`；硬约束剪枝 + 软目标优化；旧 `PolicyEngine` 作向后兼容别名。**v2（RFC 0013）：`PolicyOptimizer` 可挂载 `learner`，热身后在可行策略中用学习偏好决策，否则回退静态** |
| Strategy Library | `fek/strategies/`（已新增，8 策略） | 新增 `fek/strategies/`；`Strategy` 协议 + 8 个可插拔实现；SINGLE/MULTI_AGENT/MOA 改为 Strategy 实现，MoA 降为普通策略 |
| 约束感知学习 | `fek/learning/constraint_learning.py`（已新增，RFC 0013） | `constraint_aware_reward`（违规硬惩罚）+ `profile_context_key`（约束→bandit 上下文）；`FEKKernel` 可选挂载 learner，约束管线执行后回写 |
| Graph Compiler | `fek/compiler/` | 不变（明确语义） |
| Compute Graph | `fek/core/graph.py` `ComputeGraph` | 不变 |
| Runtime | `fek/runtime/` | 不变（传 constraints 给 Evaluation/Fusion） |
| Fusion Engine | `fek/fusion/` | 不变（降级为 MoA/Parallel 策略细节） |
| Evaluation | `fek/evaluation/` | 不变 |
| Telemetry | `fek/telemetry/` | 不变（增加 constraints 维度） |

> pivot + v2 代码均已落地（见 `docs/migration-plan.md` 阶段 6 / 阶段 7）；旧管线（`run(prompt)` 无约束）完全保留，确保既有 Demo 与测试零改动。本文档为架构权威来源。
