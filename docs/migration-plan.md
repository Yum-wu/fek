# FEK 迁移计划（Actionable Migration Plan）

> 把"黑客松 Demo（Fusion Execution Kernel）"迁移到"Adaptive AI Execution Engine + RFC 驱动开发"。
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

## 阶段 1 · 建立 RFC 流程（立即，治理动作）

- [ ] 在 `CONTRIBUTING.md` 增加 "RFC-Driven Development" 章节，链接 `docs/rfcs/README.md`。
- [ ] 任何后续"重大设计"（新增策略类型、新增模块、改 Policy Engine 接口、改 Compute Graph 结构）**必须先开 RFC PR**，评审合并后再写代码。
- [ ] 在 PR 模板（`.github/PULL_REQUEST_TEMPLATE.md`）加勾选项："本 PR 是否需 RFC？如是，RFC 链接？"
- [ ] 代码评审时，无 RFC 的重大设计 PR 打回。

**Rationale**：FEK 现在代码量小但概念多，早立 RFC 流程可避免术语/抽象再次漂移。

---

## 阶段 2 · 代码命名对齐（待 RFC 合并后执行）

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

## 阶段 3 · 诚实化（与阶段 2 并行，低成本）

- [ ] README "已实现" 区给 `Evaluation` 标 "启发式占位"，给 mock 学习标 "方法演示"。
- [ ] `docs/learn-design.md` 第 7 节诚实声明在 README 顶部附近可见。
- [ ] `Task Profiler` 最弱一环写入 README "已知限制"。
- [ ] 移除 pyproject `hackathon` keyword。

---

## 阶段 4 · Product v2（Learning Optimizer，下一个真实里程碑）

见 `docs/roadmap.md` v2。需 RFC 补充：0003 policy-engine 学习部分扩展（LinUCB 切换）、可选 tokenizer 依赖 RFC。
- [ ] 真实成本信号（tokenizer，可选依赖）
- [ ] 学习可开关 + 回测进 CI
- [ ] 学习洞察面板

---

## 阶段 5 · 研究路线（不排期）

- R3 更好 Task Profiling（嵌入/检索/LLM 自评）—— 优先级高于炫技
- R4 真实 LLM 裁判
- R1 自演化执行 / R2 自主内核 —— 仅研究，不承诺交付

---

## 验收标准（Definition of Done）

迁移完成当：
1. 仓库对外统一称 "Adaptive AI Execution Engine"，无 "Fusion Execution Kernel" 残留（除历史文档横幅）。
2. 代码术语与 `docs/terminology.md` 一致（Compute Graph / Evaluation / Task Profiler）。
3. 任何新重大设计均有 RFC。
4. README 30 秒能讲清：问题 → 方案 → Demo → 架构 → 路线图。
5. 30 测试全过、CI 绿。

---

*本计划不修改代码，仅记录待办。代码改动在对应 RFC 合并后由本计划驱动执行。*
