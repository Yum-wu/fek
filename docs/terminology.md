# 术语审计 · FEK Naming Audit（战略 Pivot 版）

> 原则（见 VISION.md）：**一致性优先于新颖性。** 选一个清晰的词，全仓库（代码+文档）统一使用。
> 本文档是命名决策的权威来源，供 RFC 与迁移计划引用。
> 本次 pivot 重大变更：定位从"Adaptive AI Execution Engine"改为 **"Adaptive AI Compute Optimizer"**；
> 新增 **Constraints / Constraint Analysis / Policy Optimizer / Strategy Library**；**MoA 降级为一个 Strategy**。

---

## 1. 项目级命名

| 术语 | 上一版 | 本次决定 | 理由 |
|---|---|---|---|
| 项目定位 | Adaptive AI Execution Engine（自适应 AI 执行引擎） | **Adaptive AI Compute Optimizer（自适应 AI 计算优化器）** | 从"执行"转向"优化"；价值是约束下选最优策略，不是"能执行" |
| 所处层 | Execution Layer | **AI Compute Optimization Layer（AI 计算优化层）** | 更准确表达"优化"本质 |
| 一句话定位 | "为每个任务自动决定最优执行策略" | **"在质量/成本/延迟/隐私等约束下，自动为任务选择最优的 AI 计算策略"** | 约束是一等输入 |
| 包名 `fek` | `fek` | **保留 `fek`** | 已是 GitHub 品牌与 import 名；`fek` 不再展开为 "Fusion Execution Kernel" |

---

## 2. 模块级命名（pivot 新增/调整）

| 概念 | 当前代码 | 本次建议 | 是否改动 | 理由 |
|---|---|---|---|---|
| 约束分析 | `fek/constraint/analyzer.py` | **Constraint Analysis** | 已新增（v1 落地） | 约束是一等输入，需在优化前规范化/过滤 |
| 约束画像 | `fek/core/types.py` | **ConstraintProfile** | 新增数据结构（已落地） | Task + Constraints → 规范化后的约束画像 |
| 策略优化 | `policy/engine.py`（`PolicyEngine`，保留兼容）+ `policy/optimizer.py`（`PolicyOptimizer`，新） | **Policy Optimizer** | 已重构（新增 PolicyOptimizer；旧 PolicyEngine 作向后兼容别名） | 输入从复杂度评分改为 ConstraintProfile；目标改为约束优化 |
| 策略库 | `fek/strategies/` | **Strategy Library** | 已新增（v1 落地） | 把 MoA/Debate/ToT 等做成可插拔 Strategy |
| 策略实现 | `Strategy` 枚举（保留作 ExecutionResult 兼容）+ `fek/strategies/`（协议+8 实现） | **Strategy（协议）+ 多个实现** | 已重构（新增 StrategyLibrary，8 策略可插拔） | 每个策略是一个组件，可插拔；枚举保留用于遥测兼容 |
| 复杂度估计 | `profiler/` `TaskProfiler` | **Task Profiler（仍保留，归 Constraint Analysis 用）** | 否 | 复杂度仍是有用信号，但只是 Constraint Analysis 的一部分 |
| 图编译器 | `compiler/` | **Graph Compiler** | 否 | 不变 |
| 图结构 | `core/graph.py` `ComputeGraph` | **Compute Graph** | 否 | 不变 |
| 运行时产物 | — | **Execution Trace** | 术语保留 | 运行时记录，区别于静态 Compute Graph |
| 执行器 | `runtime/` | **Runtime** | 否 | 不变 |
| 多输出聚合 | `fusion/` | **Fusion Engine（子组件）** | 降级叙事 | 仅 MoA/Parallel 策略的实现细节 |
| 质量打分 | `evaluation/` | **Evaluation** | 否 | 不变 |
| 轨迹记录 | `telemetry/` | **Telemetry** | 否（增加 constraints 维度） | 不变 |
| 编排入口 | `kernel.py` `FEKKernel` | **FEKKernel** | 否 | 不变 |

---

## 3. 策略（Strategy）命名 —— MoA 只是一个 Strategy

| 策略 | 来源 | 在 FEK 中的定位 | 说明 |
|---|---|---|---|
| Single | 基础 | Strategy | 单模型一次调用 |
| Planner+Reviewer | 规划+批判范式 | Strategy |  |
| Reflection | Reflexion 论文 | Strategy | 自反思循环 |
| Debate | 多角色辩论 | Strategy |  |
| Tree of Thoughts | ToT 论文 | Strategy | 树搜索 |
| MoA | Hermes/Together | **Strategy（仅此而已）** | FEK 适配已有 MoA，不重造；**不是核心** |
| Parallel | 并行多模型 | Strategy | 投票/融合 |
| Hierarchical | 层级分解 | Strategy |  |
| Future | 社区新论文 | **即插即用** | Self-Consistency / Graph-of-Thoughts 等 |

> **核心立场**：FEK 不负责发明这些策略；FEK 负责**在约束下选择**它们。对外绝不大讲"我们支持 MoA"。

---

## 4. 中英文对照（统一）

| 中文 | English | 使用场景 |
|---|---|---|
| 自适应 AI 计算优化器 | Adaptive AI Compute Optimizer | 项目定位 |
| AI 计算优化层 | AI Compute Optimization Layer | 生态层 |
| 约束 | Constraints | 一等输入 |
| 约束分析器 | Constraint Analysis | 模块 |
| 约束画像 | ConstraintProfile | 数据结构 |
| 策略优化器 | Policy Optimizer | 模块（核心） |
| 策略库 | Strategy Library | 模块 |
| 策略 | Strategy | 可插拔执行策略 |
| 任务画像器 | Task Profiler | 模块（归 Constraint Analysis） |
| 图编译器 | Graph Compiler | 模块 |
| 计算图 | Compute Graph | 数据结构 |
| 执行轨迹 | Execution Trace | 运行时记录 |
| 运行时 | Runtime | 模块 |
| 融合引擎 | Fusion Engine | 子组件 |
| 评估器 | Evaluation | 模块 |
| 遥测 | Telemetry | 模块 |

技术专有名词（DAG / MoA / SINGLE / Strategy / Policy Optimizer / Compute Graph / LLMBackend）保留英文。

---

## 5. 禁止使用的旧术语（pivot 后）

- ❌ "自适应 AI 执行引擎" 作首要定位（改"自适应 AI 计算优化器"）
- ❌ "Execution Layer" 作首要层名（改"AI Compute Optimization Layer"）
- ❌ "Fusion Execution Kernel" / "融合执行内核"（项目标题）
- ❌ "Execution Graph"（统一为 Compute Graph）
- ❌ 把 MoA 当核心卖点（MoA 只是 Strategy 之一）

---

*命名变更经 `docs/rfcs/0010-positioning-pivot.md`（定位）、`0011-constraint-policy-optimizer.md`（Policy Optimizer）、`0012-strategy-library.md`（Strategy Library）评审后，由 `docs/migration-plan.md` 的 pivot 阶段执行。本文件不修改代码。*
