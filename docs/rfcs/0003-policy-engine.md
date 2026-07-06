# RFC 0003 · Policy Engine

- 状态：Accepted
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：0002-execution-model, docs/architecture.md, docs/learn-design.md

## Background

Policy Engine 是 FEK 的心脏：`policy/engine.py` 当前用阈值规则选策略，并在反馈足（warmup=8）后由上下文老虎机（ε-greedy）接管。已落地 v2 学习层（reward/ bandit/ persist），mock 可演示。

## Problem

1. **Task Profiler 概念错位**：当前 `classifier/` 是启发式评分器，不叫"分类器"更准确应称 Task Profiler（见 docs/terminology.md）。
2. **学习在 mock 下是方法演示**：quality/cost 为启发式，须在文档诚实标注。
3. **算法单一**：仅 ε-greedy，未预留更聪明的 bandit（LinUCB）。
4. **复杂度过弱**：关键词启发式易被质疑"不就是 if-else"。

## Proposal

- **接口稳定**：`select(profile: TaskProfile) -> StrategyDecision`（含 `explain()`）；`learn(trace)` 接收遥测更新；`explain(decision) -> str`。
- **冷启动**：反馈不足时回退阈值规则，保证零配置可跑。
- **可学习**：成本感知 contextual bandit，奖励 = `质量 − λ·成本 − μ·延迟`。
- **可切换**：默认 ε-greedy，预留 LinUCB 接口（v2 升级）。
- **概念**：上游称为 **Task Profiler**（不重命名代码包，待迁移计划执行）。

## Alternatives

- **纯规则（无学习）**：可解释但无法优化，否决（违背"学习闭环"）。
- **神经网络路由器（RouteLLM 式）**：强大但需训练数据、破坏零依赖，推迟到研究。
- **LinUCB 直接上**：更聪明但数值稳定复杂，先 ε-greedy 默认 + 预留接口。

## Tradeoffs

- ε-greedy 初期探索会选"贵但一般"的策略（成本抖动），是 bandit 正常代价，须演示时解释。
- mock 学习是演示：真实信号需真实后端，文档须诚实。

## Future Work

- v2：LinUCB 切换 + 真实 token 计费（可选依赖）+ 学习可开关/回测进 CI。
- R3：更好 Task Profiling（嵌入/检索/LLM 自评）替代关键词启发式——这是最高优先级改进。
