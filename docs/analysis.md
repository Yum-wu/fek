# FEK 设计评估与黑客松 MVP 落地建议

> 配套仓库：根目录（已包含可运行代码，本文件是分析 + 建议部分）

---

## 一、对 FEK 设计的评估

### 1.1 设计合理性（亮点）

**核心抽象成立且清晰。** `Task → Strategy → Graph → Runtime → Fusion` 这条主链抓住了"执行智能"的本质——不是模型更聪明，而是**如何用模型**更聪明。相比 LangChain（工具编排）、AutoGen（对话式 Agent）、LiteLLM（模型路由），FEK 把"选计算策略"提升为一等公民（Policy Engine），这是有差异化的定位，也是评委最容易记住的"一句话卖点"。

**分层架构收敛得好。** v0→v4 演进路线从"静态流程"逐步走向"自演化系统"，最终收敛成一个统一架构图，说明作者对系统的边界有清晰思考，不是堆功能。分层（理解/策略/编译/运行时/融合/反思/遥测）职责单一、可独立替换，利于 demo 分阶段实现。

**"成本感知推理"是稀缺叙事。** 同时优化 cost / latency / quality 三要素，并且用 telemetry 量化，这在 Agent 框架里很少被当作一等目标。对黑客松评委来说，"能省钱的执行内核"比"又一个 Agent 框架"更有商业想象空间。

### 1.2 可行性风险（必须正视）

| 风险点 | 说明 | 对黑客松的影响 |
|--------|------|----------------|
| **v2–v4 偏"愿景"** | Policy Learning / Graph Mutation / 自主目标生成 在 48h 内无法真正验证，且"自我演化"容易沦为演示噱头 | 评委更看重 v0/v1 跑通，不要把故事讲满 |
| **Execution Runtime 写 (Go)** | 黑客松用 Go 写 Agent 编排性价比低，生态与开发速度不如 Python | Demo 用 Python，生产再切 Go，需说明 |
| **复杂度分类器未定义** | 文档只说"task complexity → strategy"，但没给量化方法，容易被质疑"不就是 if-else 吗" | 必须给出可解释、可展示的分类信号 |
| **MoA 融合方式模糊** | "简单 MoA 聚合"没说聚合策略（投票？LLM 融合？加权？） | Demo 里要给出确定性的融合定义 |
| **缺少可运行证据** | 纯设计文档，无代码无评测，难以取信 | 本仓库即补上 |

**结论：** 设计方向正确、定位清晰、分层合理；最大问题是"愿景过大 + 缺少量化定义 + 无代码"。黑客松 MVP 应**只做 v0/v1 的精华**，并把"策略如何选择 / 融合如何做 / 成本如何量化"这三件模糊事定义清楚。

---

## 二、项目结构与目录组织建议

**原则：** 目录结构直接映射 FEK 架构分层，让评委"看目录就懂系统"。核心层不依赖任何第三方库，确保零配置可跑。

```
fek-demo/
├── fek/                  # 内核包（核心层 = 纯标准库）
│   ├── core/             # 类型 + 执行图(DAG)
│   ├── classifier/       # 复杂度分类（Task → score）
│   ├── policy/           # 策略引擎（score → Strategy）★创新点
│   ├── compiler/         # 图编译器（Strategy,Task → DAG）
│   ├── runtime/          # DAG 执行器
│   ├── fusion/           # MoA 融合
│   ├── reflection/       # 质量评估
│   ├── models/           # LLM 后端抽象 + Mock(离线) + OpenAI
│   ├── telemetry/        # 追踪记录（学习层雏形）
│   └── kernel.py         # 编排入口
├── examples/             # CLI 演示（离线可跑）
├── web/                  # Streamlit 演示 UI
├── tests/                # 单测（unittest，零依赖）
├── docs/                 # 本文档
├── pyproject.toml
└── .env.example
```

**关键决策：**
- `models/` 用后端抽象（ABC），使得 **Mock 后端可完全离线运行**，评委无需 API key 就能看到完整行为——这是黑客松"能跑"的保险。
- 核心层只用标准库；Streamlit / openai / pytest 全部设为可选依赖。

---

## 三、核心功能模块划分

| 模块 | 输入 | 输出 | 必须可展示的点 |
|------|------|------|----------------|
| Classifier | 任务文本 | 复杂度分 [0,1] + band | 用了哪些关键词/长度信号，为什么是 high |
| Policy Engine | 复杂度分 | Strategy | 阈值决策 + 可解释 `explain()` |
| Graph Compiler | Strategy + Task | ExecutionGraph(DAG) | 三种策略编译出不同 DAG |
| Runtime | DAG | NodeResult 列表 | 拓扑执行、可并行 |
| Fusion | 多 agent 输出 | 融合答案 | 明确的聚合策略（本仓库用结构化合并） |
| Reflection | 文本 | 质量分 [0,1] | 透明启发式 + 可替换为 LLM 裁判 |
| Telemetry | ExecutionResult | trace | 三策略的 cost/latency/quality 对比 |

**给评委的"记忆点"**：Policy Engine 的 `explain()` 输出一句话说明"为什么选这个策略"，比任何架构图都更有说服力。

---

## 四、技术选型建议

| 维度 | 建议 | 理由 |
|------|------|------|
| 语言 | **Python 3.10+** | LLM 生态成熟、评委熟悉、开发最快 |
| 内核依赖 | **0 第三方库** | 零配置可跑，降低评审摩擦 |
| LLM 后端 | Mock + OpenAI 兼容双后端 | 离线演示 + 真实效果无缝切换 |
| 图结构 | 自写轻量 DAG（拓扑排序） | 避免重量级依赖，逻辑透明 |
| Web UI | **Streamlit** | 10 行起一个可视化界面，最适合 demo |
| 图可视化 | graphviz（可选）+ mermaid 兜底 | 展示执行图 |
| 测试 | unittest（stdlib） | 评委 `python -m unittest` 即跑 |
| 部署 | 本地 / HuggingFace Spaces | 无 DB、无鉴权、无构建，1 分钟上线 |

**不推荐：** Go 运行时、分布式队列、向量数据库、前端框架（React 等）——这些在 48h 内是负收益，且偏离"能演示执行智能"的主线。

---

## 五、README 文档要点（评委 30 秒看懂）

1. **一句话定义**（直接引用 FEK 终局定义，但标注"本仓库实现 v0/v1 精华"）。
2. **3 步跑起来**：clone → `python examples/basic_demo.py` →（可选）`streamlit run web/app.py`。**强调零 API key**。
3. **架构图 + 目录映射表**：把目录和 FEK 分层一一对应，证明"不是说说的"。
4. **核心创新一句话**：系统自动选计算策略，并给出 `explain()` 示例。
5. **Battle Mode 截图/说明**：三策略成本质量对比，是商业价值的直观证据。
6. **明确 MVP 范围**：已实现 vs 推迟到 v2–v4，体现诚实与规划能力。
7. **部署 3 选项**：本地 / 云 Spaces，无 DB 无鉴权。

---

## 六、黑客松 MVP 功能范围设定

**必须做（v0+v1 精华，48h 内可完成且可演示）：**
- [x] 复杂度分类器（可解释信号）
- [x] 策略引擎（SINGLE / MULTI_AGENT / MOA 自动选择 + 解释）
- [x] 图编译器（三种策略 → 三种 DAG）
- [x] DAG 执行运行时
- [x] MoA 融合层（确定性聚合）
- [x] 反思/质量评分 + Telemetry（cost/latency/quality）
- [x] 离线 Mock 后端 + 可插拔真实 LLM
- [x] Web UI：实时执行图 + Battle Mode
- [x] 测试套件

**加分但不强求：**
- [x] Policy 从 trace 学习（fek/learning：上下文老虎机，mock 可演示、JSON 持久化、可离线回测）
- [ ] 把"成本"做成真实 token 计费（接 tokenizer）
- [ ] 导出执行 trace 为可分享的 JSON/图表

**明确不做（避免 Demo 翻车）：**
- [ ] 真实自演化 / 图变异（v3）
- [ ] 自主目标生成（v4）
- [ ] Go 运行时、分布式执行

**演示脚本建议（评委动线）：**
1. 打开 Web UI，输入一个简单问题 → 展示自动选 SINGLE，快且便宜。
2. 输入一个"compare / debate / trade-off"的复杂问题 → 展示自动选 MOA，并展开融合答案。
3. 点 Battle Mode → 同一难题三策略并排，指给评委看：MOA 质量最高但成本/延迟也最高，SINGLE 最省但质量一般。
4. 打开 Telemetry 侧栏，强调"成本感知推理" = FEK 的差异化价值。

---

## 七、本仓库与 FEK 的映射

| FEK 概念 | 本仓库实现 |
|-------------|-----------|
| Task Understanding | `fek/classifier` |
| Policy Engine（核心创新） | `fek/policy` |
| Graph Compiler | `fek/compiler` |
| Execution Runtime | `fek/runtime`（Python；文档目标为 Go） |
| MoA Fusion | `fek/fusion` |
| Reflection | `fek/reflection` |
| Telemetry & Learning | `fek/telemetry`（含 `learn()` 漂移桩） |
| v0 验证可行性 | ✅ 全部 v0 能力已可运行 |
| v1 动态图 + 策略调度 | ✅ 已实现 |
| v2 学习策略 | ✅ 已实现（上下文老虎机最小真实版，详见 docs/learn-design.md） |
| v3/v4 自演化 | ⏳ 文档标注为未来工作 |

## 八、learn() 真实最小实现（已落地）

把 v2 的"从轨迹学习策略"从桩升级为真实最小实现，设计细节见 `docs/learn-design.md`。

- **建模**：策略选择 = 上下文老虎机（contextual bandit）。上下文 = 复杂度档位（LOW/MEDIUM/HIGH），臂 = {SINGLE, MULTI_AGENT, MOA}，奖励 = 质量 − λ·成本 − μ·延迟。
- **算法**：ε-greedy（朴素版，零依赖、可解释），按复杂度档位分桶独立统计三臂均值。
- **冷启动**：反馈不足时（warmup 默认 8 条）回退阈值规则，保证零配置可跑。
- **持久化**：学到的参数存本地 JSON（`fek_policy.json`），重启累积，贴合 self-improving 叙事。
- **验证**：`examples/learning_demo.py`（学习曲线）、`examples/learning_replay.py`（离线回测对比学习 vs 固定阈值）、`tests/test_learning.py`（奖励单调性 / bandit / 持久化 / fallback）。
- **诚实边界**：mock 下"学习"是方法演示（质量/成本为启发式），真实模式才有真实信号；未做神经网络路由器、Pareto 优化等。

**一句话总结：** FEK 的设计值得做，但黑客松版本必须把"自动选策略"这一件事做到**可运行、可解释、可量化**，其余愿景诚实标注为 roadmap。本仓库即按此原则落地（并补上了 v2 学习层的真实最小实现）。
