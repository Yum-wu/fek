# FEK 架构（重构版）

> 权威架构文档。取代 `docs/analysis.md` 中的架构部分（analysis.md 归档为历史评审）。
> 配套：VISION.md（愿景）、docs/roadmap.md（路线图）、docs/rfcs/*（各模块 RFC）。

---

## Part 4 · 核心创新到底是什么

FEK 里每个孤立组件都不是新东西：

- **Compute Graph（DAG）**——LangGraph、AutoGen 都有图。
- **策略路由（bandit）**——RouteLLM、FrugalGPT 早就在做。
- **MoA 融合**——Together AI 2024 年就发布了。
- **从轨迹学习**——Self-improving agents from traces 是活跃研究方向。

**那 FEK 新在哪？**

> FEK 的新，在于把上述组件组织成一个**闭环的、成本感知的、可解释的执行引擎**：
>
> **Task Profile → Policy Engine → Compute Graph → Runtime → Telemetry →（学习）→ Policy Engine**
>
> 并且这个闭环对使用者是**全自动**的：你提交任务，引擎自己决定"单模型 / 多智能体 / MoA"，执行、度量、再优化。

更精确地说，FEK 的真正创新点是三个组合的**产品化闭环**：

1. **Per-task 策略选择**：不是全局配一个 Agent 模板，而是每个任务独立选执行策略。
2. **成本感知的奖励信号**：决策优化目标显式是 `质量 − λ·成本 − μ·延迟`，不是"效果最好"。
3. **可解释 + 可回测的学习**：每个决策能 `explain()`，每次学习能离线回测对比。

单独看都不新；**组合成"可嵌入、可解释、成本感知的执行闭环"**才是 FEK 的差异化。文档和对外沟通必须这么讲，不要吹成"自演化内核"。

---

## Part 5 · 重构后的模块边界

### 5.1 分层总览

```
┌─────────────────────────────────────────────────────────────┐
│                         Application                           │
│         （调用 FEKKernel.run(task)，不关心内部策略）            │
└───────────────┬─────────────────────────────────────────────┘
                │ Task（自然语言指令）
                ▼
┌─────────────────────────────────────────────────────────────┐
│  Task Profiler      （输入层）   prompt → TaskProfile          │
├─────────────────────────────────────────────────────────────┤
│  Policy Engine      （决策层）  TaskProfile → StrategyDecision │
│     └─ Learning / Optimizer（成本感知 bandit，可学习）         │
├─────────────────────────────────────────────────────────────┤
│  Graph Compiler     （规划层）  (Strategy, Task) → ComputeGraph│
│  Compute Graph      （数据结构） 节点 + 依赖的 DAG             │
├─────────────────────────────────────────────────────────────┤
│  Runtime            （执行层）  ComputeGraph → ExecutionResult │
│     ├─ Fusion Engine  （子组件）多输出 → 融合答案              │
│     └─ Evaluation    （子组件）输出 → 质量分 [0,1]             │
├─────────────────────────────────────────────────────────────┤
│  Telemetry          （观测层）  ExecutionResult → Trace        │
│     └────────────── 反馈给 Policy Engine（学习闭环）──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 模块职责 / 接口 / 依赖

#### Task Profiler（原 classifier/）
- **职责**：把任务文本转成 `TaskProfile`（复杂度评分 [0,1]、离散档位、信号分解）。
- **接口**：`profile(prompt: str) -> TaskProfile`
- **依赖**：无（当前为启发式；未来可接嵌入/检索/LLM 自评）。
- **为什么改名**：它不是 ML 分类器，是估计器。"Profiler" 更准确地表达"给任务画像"。

#### Policy Engine（原 policy/，核心）
- **职责**：根据 `TaskProfile` 选择执行策略（`SINGLE` / `MULTI_AGENT` / `MOA` / 未来 `DEBATE` / `REFLECTION`），输出 `StrategyDecision` 含 `explain()`。
- **接口**：`select(profile: TaskProfile) -> StrategyDecision`；`learn(trace)` 接收遥测更新内部模型；`explain(decision) -> str`
- **依赖**：读取 TaskProfile；写入 Telemetry（间接，经 Kernel）。
- **包含**：阈值 fallback（冷启动）+ 成本感知 contextual bandit（学习后接管）。这是 FEK 的心脏。

#### Graph Compiler（原 compiler/）
- **职责**：把 `(StrategyDecision, Task)` 实例化为具体 `ComputeGraph`。
- **接口**：`compile(decision: StrategyDecision, task: Task) -> ComputeGraph`
- **依赖**：Policy Engine 的输出；Compute Graph 结构。
- **说明**："编译器"略重但可辩护——它把"决策"编译成"可执行的图"。

#### Compute Graph（原 core/graph `ExecutionGraph`）
- **职责**：纯数据结构，描述节点（角色/类型/依赖）与边。不含执行逻辑。
- **接口**：`ComputeGraph` 提供 `nodes`、`edges`、`topological_order()`。
- **依赖**：无。
- **改名理由**：与运行时"执行（execution）"区分。静态计划 = Compute Graph；运行时记录 = Execution Trace。

#### Runtime（原 runtime/，不变）
- **职责**：拓扑序执行 Compute Graph，处理并行、重试，产出 `ExecutionResult`（节点结果 + 最终输出 + Execution Trace）。
- **接口**：`execute(graph: ComputeGraph, backend: LLMBackend) -> ExecutionResult`
- **依赖**：Compute Graph、LLMBackend、Fusion Engine、Evaluation。

#### Fusion Engine（原 fusion/，子组件）
- **职责**：把多个节点输出聚合成一个融合答案（加权 / LLM 融合 / 结构化合并）。
- **接口**：`fuse(outputs: list[NodeOutput]) -> FusedOutput`
- **依赖**：Runtime 在 MoA/MULTI_AGENT 策略下调用。
- **说明**：FEK 名字里的 "Fusion" 仅指这一子组件，不是整个项目。

#### Evaluation（原 reflection/，改名）
- **职责**：给输出打质量分 [0,1]（当前启发式；未来 LLM-as-judge）。
- **接口**：`evaluate(output, task) -> float`
- **依赖**：Runtime 调用；结果进 Telemetry。
- **改名理由**：`reflection` 在 LLM 圈指"自反思循环"，容易误导。这里只是打分，叫 Evaluation。

#### Telemetry（原 telemetry/，不变）
- **职责**：记录每次 `ExecutionResult` 为 trace（strategy / complexity / cost / latency / quality），聚合统计，供 Policy Engine 学习。
- **接口**：`record(result)`、`aggregate()`、`export_traces()`
- **依赖**：被 Kernel 在每次运行后调用；输出喂给 Policy Engine.learn()。

### 5.3 依赖方向（必须单向）

```
Application → Task Profiler → Policy Engine → Graph Compiler → Compute Graph
                                                       ↓
                              Runtime → (Fusion Engine, Evaluation) → ExecutionResult
                                                       ↓
                                                   Telemetry ──┐
                                                              ↓
                                                        Policy Engine（学习）
```

- 上层依赖下层，下层**绝不**反向 import 上层。
- Telemetry 是唯一的"回边"，且只通过数据（trace）回流，不形成代码环。
- `FEKKernel`（`kernel.py`）是唯一编排入口，负责把上述模块串成流水线。

### 5.4 与当前代码的映射（供迁移参考，不立即改代码）

| 新模块名 | 当前路径 | 改名动作 |
|---|---|---|
| Task Profiler | `fek/classifier/` | 概念对齐，RFC 后重命名 |
| Policy Engine | `fek/policy/` | 不变 |
| Graph Compiler | `fek/compiler/` | 不变（明确语义） |
| Compute Graph | `fek/core/graph.py` `ExecutionGraph` | 重命名类 |
| Runtime | `fek/runtime/` | 不变 |
| Fusion Engine | `fek/fusion/` | 不变（降级为子组件叙事） |
| Evaluation | `fek/reflection/` | 重命名包 |
| Telemetry | `fek/telemetry/` | 不变 |

> 所有代码重命名遵循 RFC 流程（`docs/rfcs/0004-compute-graph.md` 等），经评审合并后由 `docs/migration-plan.md` 执行。本架构文档不修改代码。
