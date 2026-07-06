# FEK 架构评审报告（2026-07）

> 评审人视角：Principal AI Infrastructure Architect
> 评审对象：`Yum-wu/fek` 仓库（commit 881547f 状态）
> 目标：将 FEK 从一个"黑客松 Demo"重构为"世界级 AI Infrastructure 项目"的文档与定位基线
> 范围：README.md / docs/analysis.md / docs/learn-design.md / pyproject.toml / fek/ 包结构 / web/

---

## 0. 一句话结论

FEK 的**架构主线是对的、分层是收敛的、零依赖可跑是稀缺优势**；但它当前被一个**错误的名字（"融合执行内核"）、一套不一致的术语、以及把研究愿景包装成近期交付**三件事拖累了。本评审给出修正清单，并在后续文档中落地。

---

## 1. 逐文档 / 模块评审

### 1.1 README.md —— 定位误导，需重写
- **问题**：开篇即 "⚡ FEK · Fusion Execution Kernel（融合执行内核）"。`Kernel` 在系统软件里指"管理硬件资源的特权核心层"（OS kernel / CUDA kernel）。FEK 不管理任何资源，它是一个**编排/执行引擎**。"Kernel" 是危险隐喻，会让基础设施工程师本能地皱眉。
- **问题**：把 v2–v4（图变异 / 自主目标 / Go 运行时）与已实现功能并列在 "MVP 范围与路线图" 里，且 v2 标 ✅、v3/v4 标 🔜，暗示它们是"即将到来"的近期交付。实际 v3/v4 是纯研究愿景，v2 学习层在 mock 下只是方法演示。
- **亮点**：30 秒能看懂（一句话定义 + 3 步跑起来 + 架构图 + Battle Mode），这要保留。
- **动作**：见 `README.md` 重写（Part 7）与 `docs/roadmap.md`。

### 1.2 docs/analysis.md —— 黑客松评估，应归档
- 这是一份**黑客松 MVP 落地建议**，价值在于记录了"为什么只做 v0/v1 精华"。但它已被实现超越（v2 已落地），且语气是"评委视角"。
- **动作**：保留为历史文档，顶部加横幅指向 `docs/architecture.md`（新权威架构文档），不再作为主架构引用。

### 1.3 docs/learn-design.md —— 诚实，但边界要更显眼
- 设计质量高（Contextual Bandit 框架、奖励函数、冷启动 fallback、离线回测）。
- **问题**：第 7 节"mock 下的学习是演示性质"这个关键诚实声明，在当前 README 里被弱化了（v2 标 ✅ 且无 caveat）。
- **动作**：在 `README.md` / `VISION.md` 中明确 "学习层在 mock 模式是方法演示，真实模式才有真实信号"。

### 1.4 pyproject.toml —— 元数据过时
- `description` 仍写 "Fusion Execution Kernel"；`keywords` 含 `execution-kernel`、`hackathon`。
- **动作**：更新为 "Adaptive AI Execution Engine" 定位，移除 `hackathon`、移除 `execution-kernel`（或改为 `execution-engine`）。

### 1.5 代码结构（fek/）—— 分层好，命名需对齐新术语
| 当前模块 | 评审 | 建议 |
|---|---|---|
| `classifier/` | 名不副实：它是**启发式评分器**，不是 ML "分类器" | 概念名 **Task Profiler** |
| `policy/` | 真正的创新点，保留 | **Policy Engine**（核心） |
| `compiler/` | "编译器"略重，但可辩护（策略→图） | 保留，明确 = Compute Graph Builder |
| `core/graph.py` `ExecutionGraph` | 与运行时"执行"混淆 | 改名 **Compute Graph**；运行时产物叫 **Execution Trace** |
| `runtime/` | OK | **Runtime** |
| `fusion/` | FEK 名字来源，但只是子组件 | **Fusion Engine**（子组件，不是项目名） |
| `reflection/` | 名不副实：它只是质量打分，不是 LLM 自反思循环 | **Evaluation** |
| `telemetry/` | OK | **Telemetry** |
| `learning/` | OK，是 Policy Engine 的可学习实现 | 归入 Policy Engine 的能力，不单独成"层" |
| `kernel.py` | 编排入口，OK | 保留为 `FEKKernel`（唯一入口） |

**注意**：本评审**只改文档与元数据，不重命名代码模块**（代码重构见 `docs/migration-plan.md`，遵循 RFC 流程后再动）。

---

## 2. 重复 / 不一致概念

1. **"Execution Graph" vs "Compute Graph"**：代码叫 `ExecutionGraph`，本文档草案与 RFC 用 "Compute Graph"。→ 统一为 **Compute Graph**（静态计划），运行时记录叫 **Execution Trace**。
2. **"Reflection" vs "Evaluation"**：`reflection/` 实际做的是质量评分。→ 统一为 **Evaluation**。
3. **"核心创新" 被稀释**：README、analysis、多处都把 Policy Engine 称为"核心创新"，但从未精确定义**它到底新在哪**。→ 在 `docs/architecture.md` Part 4 给出精确论断：**新在"闭环"**（Task Profile → Policy Engine → Compute Graph → Runtime → Telemetry → Policy 更新），而非其中任一孤立组件。
4. **"Fusion" 既是项目名又是子组件**：→ 项目名不再是 "Fusion ..."，Fusion 降级为 Fusion Engine 子组件。

---

## 3. 过度工程 / 研究-only 识别

| 项目 | 状态 | 判定 |
|---|---|---|
| v3 图变异 / 自演化角色 | 未实现 | **研究路线**（Research Roadmap） |
| v4 自主目标生成 / 目标分解 | 未实现 | **研究路线** |
| Go 运行时 / 分布式执行 | 未实现 | **研究路线**（且与 MVP 零依赖优势冲突） |
| mock 学习层 | 已实现（演示） | **产品功能，但须诚实标注为方法演示** |
| Reflection 自反思循环 | 未实现（仅打分） | **研究路线**（或并入 Evaluation 的未来工作） |

**原则**：任何未实现、依赖未来研究突破的能力，**不得**出现在 Product Roadmap，只能进 Research Roadmap（见 `docs/roadmap.md`）。

---

## 4. 定位重叠识别（与现有项目）

- **与 LiteLLM / OpenRouter（Gateway）重叠？** 部分：FEK 也做"成本/延迟"统计。但 FEK **不代理 token 级 API 调用、不做 key 管理、不做统一 API**。FEK 在 Gateway **之上**：它决定"用哪种执行策略"，而具体模型调用可走 Gateway。→ FEK **不是 Gateway**（见 `docs/ecosystem/ai-infra-landscape.md`）。
- **与 LangGraph / AutoGen / CrewAI（Agent Framework）重叠？** 部分：FEK 也能跑多智能体模式。但用户**不写 Agent、不组合工作流**；FEK **自动**选策略并执行。→ FEK **不是 Agent Framework**，而是可嵌入其内的"执行决策层"。
- **与 MoA（Together AI）重叠？** MoA 是一种融合技术；FEK 把 MoA 当作**众多策略之一**。→ FEK **不只是 MoA**。

---

## 5. 对假设的挑战（Critical Evaluation）

- **假设"策略选择是核心创新"——成立，但需精确化**。孤立看，bandit 路由（RouteLLM）、MoA 路由都不新。FEK 的差异是**把"按任务自动选执行策略 + 成本感知 + 从遥测学习"做成一个可嵌入的闭环引擎**。这是真实但"中等"的创新，应诚实地这么讲，不要吹成"自演化内核"。
- **"零依赖"是双刃剑**：它是 Demo 可跑的保险，但也阻碍了接真实 tokenizer 计费、真实 LLM 裁判。应在 Roadmap 里规划"可选依赖层"，而非永远零依赖。
- **"复杂度分类器"是最弱的一环**：纯关键词启发式，容易被质疑"不就是 if-else 吗"。这是已知短板，应作为 **Research / 近期改进项** 显式列出（更好的 task profiling：嵌入相似度、历史任务检索、LLM 自评复杂度）。
- **"反思/评估"目前是玩具启发式**：质量分不可信。必须标注为占位，规划接入 LLM 裁判（LLM-as-judge）。

---

## 6. 修正清单（指向后续文档）

| # | 问题 | 落地文档 |
|---|---|---|
| 1 | "Kernel" 错误隐喻 + 定位 | README.md, VISION.md, pyproject.toml |
| 2 | 术语不一致 | docs/terminology.md, docs/architecture.md |
| 3 | 研究愿景伪装成近期交付 | docs/roadmap.md |
| 4 | 创新点未精确定义 | docs/architecture.md (Part 4) |
| 5 | 缺少生态定位 | docs/ecosystem/ai-infra-landscape.md |
| 6 | 缺少竞争分析 | docs/competitive-analysis.md |
| 7 | 缺少愿景文档 | VISION.md |
| 8 | 缺少 RFC 流程（所有重大设计先写 RFC） | docs/rfcs/* |
| 9 | 无迁移计划 | docs/migration-plan.md |

---

*本评审不修改任何代码，仅作为文档重构与后续 RFC 的基线。代码层重命名将在对应 RFC 合并后由迁移计划执行。*
