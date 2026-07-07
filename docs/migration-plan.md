# FEK 迁移计划（Actionable Migration Plan）

> 把"黑客松 Demo（Fusion Execution Kernel）"迁移到"Adaptive AI Execution Engine + RFC 驱动开发"（阶段 0–5，已全部完成 ✅）。
> 后续战略定位重构（Pivot，RFC 0010/0011/0012）将定位演进为 **Adaptive AI Compute Optimizer**，其代码落地见 **阶段 6**（当前未执行，待 RFC 合并后按计划推进）。
> 本文档是**可执行清单**，按阶段排序。所有代码重命名必须先有对应 RFC 合并。

---

## 阶段 0 · 文档与定位（本批次已完成 ✅）

目标：先让对外叙事正确，再动代码。

- [x] 写架构评审 `docs/reviews/architecture-review-2026.md`
- [x] 写 `VISION.md`（新愿景 + 非目标）
- [x] 写 `docs/architecture.md`（重构架构 + 核心创新）
- [x] 写 `docs/ecosystem/ai-infra-landscape.md`（生态分层）
- [x] 写 `docs/competitive-analysis.md`（10 项目对比）
- [x] 写 `docs/roadmap.md`（Product/Research 分离）
- [x] 写 `docs/terminology.md`（命名审计）
- [x] 建立 `docs/rfcs/`（流程 + 8 篇 RFC）
- [x] 重写 `README.md`（新定位 + 新结构）
- [x] 更新 `pyproject.toml` description/keywords
- [x] `docs/analysis.md` 加历史横幅，指向 `docs/architecture.md`

**本阶段零代码改动，纯文档/元数据，已交付。**

---

## 阶段 1 · 建立 RFC 流程（已完成 ✅）

- [x] 在 `CONTRIBUTING.md` 增加 "RFC-Driven Development" 章节，链接 `docs/rfcs/README.md`。
- [x] 任何后续"重大设计"（新增策略类型、新增模块、改 Policy Engine 接口、改 Compute Graph 结构）**必须先开 RFC PR**，评审合并后再写代码。
- [x] 在 PR 模板（`.github/PULL_REQUEST_TEMPLATE.md`）加勾选项："本 PR 是否需 RFC？如是，RFC 链接？"
- [x] 代码评审时，无 RFC 的重大设计 PR 打回。

**Rationale**：FEK 现在代码量小但概念多，早立 RFC 流程可避免术语/抽象再次漂移。

---

## 阶段 2 · 代码命名对齐（已完成 ✅）

> ⚠️ 下列为**计划**，执行前需对应 RFC 评审通过。不要在无 RFC 情况下批量重命名（会破坏 CI 与 import）。

| 动作 | 对应 RFC | 影响文件 |
|---|---|---|
| `classifier/` → 概念对齐 Task Profiler（包重命名 `profiler/`） | 0003 policy-engine | `fek/classifier/*`、`fek/__init__.py`、`kernel.py` |
| `ExecutionGraph` 类 → `ComputeGraph` | 0004 compute-graph | `fek/core/graph.py`、`fek/__init__.py`、compiler/runtime |
| `reflection/` → `evaluation/` | 0007 evaluation | `fek/reflection/*`、`fek/__init__.py`、`kernel.py`、`reflection.evaluator` → `evaluation.scorer` |
| `fek/__init__.py` / `kernel.py` 文档字符串去掉"融合执行内核" | 0001 project-vision | docstrings |
| 引入 `Execution Trace` 术语（Runtime 返回结构补充） | 0005 runtime | `core/types.py` 注释 |

**执行顺序建议**：先 0004（Compute Graph，影响面最大但纯重命名）→ 0007（Evaluation）→ 0003（Task Profiler）。
每步：开 RFC → 合并 → 一个 PR 完成重命名 + 全量 `python -m unittest` 通过 + 更新文档引用。

---

## 阶段 3 · 诚实化（已完成 ✅）

- [x] README "已实现" 区给 `Evaluation` 标 "启发式占位"，给 mock 学习标 "方法演示"。
- [x] `docs/learn-design.md` 第 7 节诚实声明在 README 顶部附近可见。
- [x] `Task Profiler` 最弱一环写入 README "已知限制"。
- [x] 移除 pyproject `hackathon` keyword。

---

## 阶段 4 · Product v2（Learning Optimizer，已完成 ✅）

见 `docs/roadmap.md` v2 与 RFC 0009（已 Accepted 并实现）。
- [x] 真实成本信号（tokenizer，可选依赖 tiktoken，懒加载，未装回退固定估算）
- [x] 学习可开关 + 回测进 CI（`fek/learning/backtest.py` + `tests/test_backtest.py`）
- [x] 学习洞察面板（Web 侧栏开关 + 每臂平均奖励/样本数）

---

## 阶段 5 · 研究路线（不排期）

- R3 更好 Task Profiling（嵌入/检索/LLM 自评）—— 优先级高于炫技
- R4 真实 LLM 裁判
- R1 自演化执行 / R2 自主内核 —— 仅研究，不承诺交付

---

## 阶段 6 · 战略定位重构（Pivot）代码落地（已执行 ✅）

> 对应 RFC：**0010** positioning-pivot（取代 0001/0002）、**0011** constraint-policy-optimizer（取代 0003）、**0012** strategy-library。
> 以下**计划已全部执行**（2026-07-07）。当前内核已演进为"约束感知 + Policy Optimizer + Strategy Library"，旧管线（`run(prompt)` 无约束）完全保留作向后兼容。

### 6.1 新增 `Constraints` / `ConstraintProfile` 数据模型（RFC 0011）
- [x] `fek/core/types.py` 新增 `Constraints`（quality / budget / latency / privacy / preferred_models 字段）与 `ConstraintProfile`（归一化后的约束画像）。
- [x] `Task` 增加可选 `constraints: Constraints | None` 字段（向后兼容，旧调用不传约束走默认）。
- [x] 影响：`fek/__init__.py`、`kernel.py` 的 `run()` 签名与文档字符串；`ExecutionResult` 增加可选 `constraints` 字段。

### 6.2 新增 Constraint Analysis 模块（RFC 0011）
- [x] 新建 `fek/constraint/`：`analyzer.py` 实现 `(Task, Constraints) -> ConstraintProfile`，含归一化、可行性校验（约束冲突告警）、模型筛选（按 privacy / preferred_models 过滤候选后端）。
- [x] 单测 `tests/test_constraint.py`：覆盖"无约束回退默认画像""预算+延迟硬约束裁剪""隐私=local 仅留本地模型"等路径。

### 6.3 Policy Engine → Policy Optimizer 演进（RFC 0011）
- [x] 新增 `fek/policy/optimizer.py`：`PolicyOptimizer` 输入 `ConstraintProfile`；硬约束（budget/latency/privacy）作为不可违反的剪枝条件，软目标（quality）作为优化目标。`PolicyEngine` 原样保留（向后兼容）。
- [x] 保留可解释 `explain()`，输出新增"约束满足情况""候选策略成本/延迟/质量""剪枝原因"维度。
- [x] `PolicyEngine` 类名保留为别名，对外引导至 `PolicyOptimizer`（向后兼容，未破坏现有 demo）。

### 6.4 新增 Strategy Library 模块（RFC 0012）
- [x] 新建 `fek/strategies/`：定义 `Strategy` 协议（`name` / `cost_tier` / `supports(profile)` / `build(task, constraints, models) -> ComputeGraph`）。
- [x] 内置 8 个策略（均源自已有论文 / 项目，FEK 适配不重造）：`Single` / `PlannerPlusReviewer` / `Reflection` / `Debate` / `TreeOfThoughts` / `MoA` / `Parallel` / `Hierarchical`。
- [x] `MoA` 由"核心叙事"降为 Strategy Library 中一个普通策略；现有 `fek/fusion/` 逻辑下沉为其 `build()` 的实现细节。
- [x] 单测 `tests/test_strategies.py`：每个策略 `supports()` 与 `build()` 产出合法 Compute Graph。

### 6.5 接线与文档
- [x] `kernel.py`：pipeline 改为（有约束时）`Task+Constraints → Constraint Analysis → Policy Optimizer → Strategy Library → Compute Graph → Runtime → Telemetry`（默认无约束管线不变，学习层在其生效）。
- [x] 更新 `examples/constrained_demo.py` 增加带约束的调用示例；`web/app.py` 增加约束输入控件（默认不启用，向后兼容）。
- [x] 更新 `docs/architecture.md` / `docs/terminology.md` 中的代码路径映射表。

**执行顺序建议**：6.1（数据模型）→ 6.2（Constraint Analysis）→ 6.3（Policy Optimizer）→ 6.4（Strategy Library）→ 6.5（接线）。
每步：一个 PR 完成 + 全量 `python -m unittest` 通过 + 更新文档引用。**不破坏零依赖核心**（约束分析/策略库均为纯标准库实现）。

---

## 验收标准（Definition of Done）

迁移完成当：
1. 仓库对外统一称 "Adaptive AI Compute Optimizer"（Pivot 后，RFC 0010），无 "Fusion Execution Kernel" 残留（除历史文档横幅）；"Adaptive AI Execution Engine" 视为过渡定位，不主动使用。
2. 代码术语与 `docs/terminology.md` 一致（Compute Graph / Evaluation / Task Profiler / Constraint Analysis / Policy Optimizer / Strategy Library）。
3. 任何新重大设计均有 RFC。
4. README 30 秒能讲清：问题 → 方案 → Demo → 架构 → 路线图。
5. 32 测试全过（含回测基准 `test_backtest`）、CI 绿（Python 3.10–3.13 矩阵 + 冒烟测试）。

---

*本计划不修改代码，仅记录待办。代码改动在对应 RFC 合并后由本计划驱动执行。*
