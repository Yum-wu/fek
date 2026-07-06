# FEK `learn()` 真实最小实现 —— 设计与规划

> 目标：把 `fek/policy/engine.py` 里目前只是"质量阈值漂移"的 `learn()` 桩，升级为**真正能从执行轨迹学习的自适应策略层**，让路线图 v2（策略学习）不再是空头支票。
> 原则（沿用 Rapid Prototyper 作风）：零依赖、mock 可离线演示、可解释、可量化、不碰过度工程。

---

## 一、调研结论：四个最佳实践方向

| 方向 | 代表工作 | 核心思想 | 对 FEK 的借鉴 |
|---|---|---|---|
| **自适应路由** | RouteLLM (arXiv 2406.18665)、FrugalGPT | 在强/弱模型间**动态路由**，用偏好数据训练轻量路由器，优化"成本-质量"权衡 | FEK 的"策略选择"本质就是路由问题：上下文→选臂（SINGLE/MULTI/MoA）→奖励（质量−成本惩罚） |
| **MoA 路由与聚合** | Together AI Mixture of Agents (2024) | 分层 Proposer 生成多样候选 + Aggregator 综合 | FEK 已有 MoA 融合层，学习层应据此**奖励"融合带来质量提升"的轨迹** |
| **上下文老虎机** | Contextual Bandit for LLM selection (arXiv 2506.17670)、bandit-controlled-agentic-LLM | 把"多策略/多 agent 链路选择"建模为 contextual bandit：上下文=任务特征，臂=策略，奖励=质量−成本/延迟惩罚 | **最贴合 FEK 的数学框架**。复杂度评分即上下文，三种策略即三臂 |
| **自改进 Agent** | Self-improving agents from traces (ClawBench/AxLearn) | baseline → 轨迹诊断 → 单变量变更 → 留出验证 → promotion | FEK 的 telemetry 已是天然训练数据；学习应可**离线回测对比**（学习后 vs 固定策略） |

**提炼出的可借鉴要点：**
1. 策略选择 = **Contextual Bandit**（不是 if-else 阈值，而是带探索的学习器）。
2. 必须显式定义**奖励函数**：质量越高越好，但成本/延迟要作为惩罚项 —— 这正是 FEK "成本感知推理"叙事的引擎。
3. **冷启动必须回退到规则**，保证评委零配置可跑；有数据后再逐步接管。
4. 学习要**可累积、可回测、可解释**，否则只是噱头。

---

## 二、FEK 现状与缺口

**已有（可直接复用）：**
- `PolicyEngine.select/explain/learn` —— 阈值规则 + 简单的 `_drift` 微调（桩）。
- `ComplexityClassifier.score` —— 已是 `[0,1]` 的归一化复杂度上下文。
- `TelemetryRecorder` —— **完整记录每次轨迹**（strategy / complexity / cost / latency / quality），是学习层的天然数据集。
- `kernel.run` 已在末尾调用 `self.policy.learn(score, avg_q)` —— 反馈通道已打通。

**缺口（本次要补）：**
1. `learn()` 只看 `quality` 一个标量做 ±0.05 漂移，**没有显式奖励函数**，也没利用 cost/latency。
2. 学习**不可累积**（内存 `_drift`，重启清零）、**不可解释**（说不清"为什么偏移"）。
3. 没有**离线回测**能力，无法证明"学习后比固定策略好"。

---

## 三、设计方案

### 3.1 核心抽象：策略选择 = Contextual Bandit
- **上下文 `x`**：`[complexity_score, complexity_band_onehot(3), length_norm, signal_strength]`（MVP 至少用 `complexity_score`）。
- **臂 `a`** ∈ `{SINGLE, MULTI_AGENT, MOA}`（即 `Strategy` 枚举）。
- **奖励 `r`** = `quality − λ·cost_norm − μ·latency_norm`（见 3.3）。

### 3.2 算法选型（见文末提问，请拍板）
- **A. ε-greedy 朴素版**：每臂维护经验均值奖励，以 ε 概率强制探索。零依赖、最易演示。
- **B. LinUCB**：线性上下文老虎机，用特征加权预测每臂得分，更"聪明"但需数值稳定处理。
- **C. 两者都做**：默认 ε-greedy，预留 LinUCB 可切换。

### 3.3 奖励函数（`fek/learning/reward.py`）
```
cost_norm   = cost_usd   / COST_BUDGET      # 例如 COST_BUDGET=0.01 USD
latency_norm= latency_ms / LATENCY_BUDGET   # 例如 LATENCY_BUDGET=2000 ms
reward      = quality − λ * cost_norm − μ * latency_norm
# 默认 λ=0.5, μ=0.3（偏质量，但让"更贵的策略"必须拿出更高 quality 才划算）
```
- 在 mock 模式下，cost/latency 由 `MockBackend` 给出（确定性、可复现），学习曲线稳定可演示。
- 在真实模式下，奖励信号来自真实账单，学习更可信。

### 3.4 冷启动与 fallback
- `PolicyEngine.select()`：若 bandit 已积累足够样本（`n_feedback >= WARMUP`，默认 8），用 bandit 决策；否则回退现有阈值规则。**保证评委零配置可跑，且行为可预期。**
- 新增 `policy.use_learning: bool` 开关，可在 Web UI / 示例里对比"纯规则 vs 学习后"。

### 3.5 持久化（可选，见文末提问）
- `fek/learning/persist.py`：把 bandit 参数（臂均值、计数、漂移）存/载本地 JSON（默认 `fek_policy.json`）。
- 重启后加载 → **学习可累积**，贴合 self-improving 叙事；也方便"训练一次、到处用"。

### 3.6 可解释
- `explain()` 同时输出：① 规则依据（阈值/上下文）；② 学习偏好（"基于 N 条历史，MOA 在该复杂度区间平均奖励更高"）。
- Web UI 新增"学习洞察"面板：每臂的平均奖励/样本数/成本-质量散点。

---

## 四、MVP 范围（明确边界）

**做（本次交付）：**
- `fek/learning/`：bandit + reward + persist（纯标准库）。
- 改造 `PolicyEngine` 集成 bandit，保留 fallback。
- `examples/learning_demo.py`：跑一批任务 → 展示学习曲线（成本/质量随反馈收敛）。
- `examples/learning_replay.py`：离线回测，对比"学习后 vs 固定阈值"的 Pareto。
- `tests/test_learning.py`：≥10 个测试（bandit 探索、奖励单调性、持久化往返、fallback）。
- README roadmap 更新（v2 落地）、`docs/analysis.md` 补一节。

**不做（诚实标注为未来工作，不承诺）：**
- 神经网络路由器 / 用真实 LLM 裁判蒸馏偏好（RouteLLM 式）。
- 多目标 Pareto 优化、贝叶斯优化超参。
- 分布式训练、在线服务化。
- 跨会话联邦学习。

---

## 五、文件级实施计划

| 文件 | 动作 | 说明 |
|---|---|---|
| `fek/learning/__init__.py` | 新建 | 包导出 |
| `fek/learning/bandit.py` | 新建 | `ContextualBandit`（ε-greedy 或 LinUCB） |
| `fek/learning/reward.py` | 新建 | `compute_reward(quality, cost, latency, λ, μ)` |
| `fek/learning/persist.py` | 新建 | `save/load` JSON |
| `fek/policy/engine.py` | 改造 | 集成 bandit，保留阈值 fallback + explain 增强 |
| `fek/kernel.py` | 微调 | `learn()` 反馈传更丰富轨迹（含 cost/latency） |
| `examples/learning_demo.py` | 新建 | 学习曲线演示 |
| `examples/learning_replay.py` | 新建 | 离线回测对比 |
| `tests/test_learning.py` | 新建 | 学习层测试 |
| `README.md` / `docs/analysis.md` | 更新 | v2 落地说明 |

---

## 六、验证方式（mock 模式即可全跑）
1. `python examples/learning_demo.py`：观察 ε 探索 → 奖励收敛 → 策略偏好稳定。
2. `python examples/learning_replay.py`：回测证明学习后策略在成本-质量上不劣于（通常优于）固定阈值。
3. `python -m unittest discover -s tests`：学习层测试全过。
4. Web UI 勾选"启用学习"，实时看三臂奖励柱状图随运行变化。

## 七、风险与诚实声明
- **mock 下的"学习"是演示性质**：quality/cost 是启发式，学习曲线展示的是*方法*而非*真实智能*。真实模式才有真实信号——这点必须在 README 讲清楚。
- 不做"学习让效果暴涨"的夸大承诺；只承诺"系统能从轨迹自适应调整策略选择，并量化权衡"。
- 若选 ε-greedy，初期探索会选到"贵但质量一般"的策略（成本抖动），这是 bandit 的正常代价，演示时需解释。
