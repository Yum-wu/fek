# 术语审计 · FEK Naming Audit

> 原则（见 VISION.md）：**一致性优先于新颖性。** 选一个清晰的词，全仓库（代码+文档）统一使用。
> 本文档是命名决策的权威来源，供 RFC 与迁移计划引用。

---

## 1. 项目级命名

| 术语 | 当前 | 决定 | 理由 |
|---|---|---|---|
| 项目名 | Fusion Execution Kernel / 融合执行内核 | **FEK = Adaptive AI Execution Engine（自适应 AI 执行引擎）** | "Kernel" 隐喻错误（不管理资源）；"Fusion" 只是子组件，不应代表全局 |
| 包名 `fek` | `fek` | **保留 `fek`** | 已是 GitHub 品牌与 import 名，重命名成本过高；`fek` 作为缩写不再展开为 "Fusion Execution Kernel" |
| 一句话定位 | "把任务编译成最优计算图" | **"为每个任务自动决定最优执行策略"** | 更准确：FEK 决定"策略"，图只是策略的载体 |

---

## 2. 模块级命名

| 概念 | 当前代码 | 建议 | 是否重命名 | 理由 |
|---|---|---|---|---|
| 复杂度估计 | `classifier/` `ComplexityClassifier` | **Task Profiler** | ✅ 是 | 它不是 ML 分类器，是估计/画像器 |
| 策略选择 | `policy/` `PolicyEngine` | **Policy Engine** | 否 | 核心创新，名称准确 |
| 策略→图 | `compiler/` `GraphBuilder` | **Graph Compiler** | 否（语义明确） | 把决策编译成图，可辩护 |
| 图结构 | `core/graph.py` `ExecutionGraph` | **Compute Graph** | ✅ 是（类重命名） | 与运行时"执行"区分；静态计划 vs 执行轨迹 |
| 运行时产物 | （无独立名） | **Execution Trace** | 新增术语 | 区分"图（计划）"与"执行记录（轨迹）" |
| 执行器 | `runtime/` `Executor` | **Runtime** | 否 | 准确 |
| 多输出聚合 | `fusion/` `fuse` | **Fusion Engine** | 否（降级叙事） | 仅子组件；"Fusion" 不再代表项目 |
| 质量打分 | `reflection/` `score_quality` | **Evaluation** | ✅ 是（包重命名） | "Reflection" 在 LLM 圈指自反思循环，误导 |
| 轨迹记录 | `telemetry/` | **Telemetry** | 否 | 准确 |
| 学习/优化 | `learning/` `PolicyEngine.learn` | **Policy Optimizer**（Policy Engine 的能力） | 否（概念归并） | 学习是 Policy Engine 的可学习实现，不单独成"层" |
| 编排入口 | `kernel.py` `FEKKernel` | **FEKKernel** | 否 | 保留；但 "Kernel" 此处仅为类名，不对外称为"内核" |

---

## 3. 策略枚举命名

| 策略 | 当前 | 决定 | 说明 |
|---|---|---|---|
| 单模型 | `SINGLE` | **SINGLE** | 保留 |
| 多智能体 | `MULTI_AGENT` | **MULTI_AGENT** | 保留 |
| 混合专家 | `MOA` | **MOA** | 保留（术语保留英文 MoA） |
| 辩论（未来） | — | **DEBATE** | 候选策略 |
| 自反思（未来） | — | **REFLECTION** | 候选策略（注意：此处 REFLECTION 是策略类型，与 Evaluation 模块无关） |

> 注意：未来 `REFLECTION` 作为**策略类型**时，指"执行中引入自反思循环"；而 `Evaluation` 模块是"打完分"。两者不冲突，但文档须讲清。

---

## 4. 中英文对照（统一）

| 中文 | English | 使用场景 |
|---|---|---|
| 任务画像器 | Task Profiler | 模块 |
| 策略引擎 | Policy Engine | 模块 |
| 图编译器 | Graph Compiler | 模块 |
| 计算图 | Compute Graph | 数据结构 |
| 执行轨迹 | Execution Trace | 运行时记录 |
| 运行时 | Runtime | 模块 |
| 融合引擎 | Fusion Engine | 模块 |
| 评估器 | Evaluation | 模块 |
| 遥测 | Telemetry | 模块 |
| 策略决策 | Strategy Decision | Policy Engine 输出 |
| 任务画像 | Task Profile | Task Profiler 输出 |
| 自适应 AI 执行引擎 | Adaptive AI Execution Engine | 项目定位 |

技术专有名词（DAG / MoA / SINGLE / MULTI_AGENT / Policy Engine / Compute Graph / LLMBackend）保留英文，不翻译。

---

## 5. 禁止使用的旧术语（迁移后）

- ❌ "融合执行内核" / "Fusion Execution Kernel"（项目标题）
- ❌ "Execution Graph"（统一为 Compute Graph）
- ❌ "反思"（作模块名；仅可作未来策略类型 REFLECTION）
- ❌ "分类器"（作模块名；改 Task Profiler）

---

*命名变更经 `docs/rfcs/0004-compute-graph.md`（Compute Graph 重命名）、`docs/rfcs/0003-policy-engine.md`（Task Profiler 概念）、`docs/rfcs/0007-evaluation.md`（Evaluation 改名）评审后，由 `docs/migration-plan.md` 执行代码重命名。本文件不修改代码。*
