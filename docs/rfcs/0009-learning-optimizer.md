# RFC 0009 · Learning Optimizer

- 状态：Accepted
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：0003-policy-engine, 0008-roadmap, docs/learn-design.md

## Background

v1 已落地上下文老虎机学习层（`fek/learning/`：bandit + reward + persist），
`PolicyEngine` 在反馈达 warmup 后由 ε-greedy 接管决策，并保留阈值规则 fallback。
`examples/learning_replay.py` 已有的离线回测证明：在强成本惩罚下，学习后策略的
reward（质量 − 成本惩罚）高于固定阈值。

但 v1 学习层仍有三处产品级缺口，使 v2 不能被称为"可信产品能力"：

1. **算法不可切换**：只有 ε-greedy 一种实现，无法在不改代码的情况下替换 learner。
2. **真实成本信号缺失**：奖励函数里的 `cost` 在 mock 下是启发式、在真实模式下是
   每次调用固定估算，未用真实 token 数计费，导致真实模式下奖励仍不可信。
3. **回测未进 CI**：`learning_replay.py` 只是示例脚本，没有自动化断言，
   无法在每次改动后证明"学习后不劣于固定阈值"。

## Problem

1. "可切换 learner" 只是口头预留，没有接口契约与工厂，换算法要改 `PolicyEngine` 内部。
2. 真实模式下 `cost_usd` 来自 `OpenAIBackend._pricing`（每次调用固定价），
   与真实账单偏差大，使"成本感知"叙事在真实后端下站不住脚。
3. 离线回测是手动脚本，CI 无回归保护；学习层一旦回归，无人知晓。
4. Web UI 没有学习开关与洞察面板，用户无法直观对比"纯规则 vs 学习后"、
   也无法看到学习到了什么。

## Proposal

### 1. 可切换 Learner 接口
- 新增 `fek/learning/learner.py`：定义 `Learner` 协议（运行时检查），
  契约 = `select / update / mean_reward / count / best_arm / to_dict / from_dict / snapshot / total_feedback`。
- `fek/learning/__init__.py` 新增工厂 `create_learner(name="epsilon_greedy", **kwargs)`：
  - `"epsilon_greedy"` → 现有 `ContextualBandit`（零依赖，默认）。
  - `"linucb"` → 抛 `NotImplementedError`，明确标注"v2.1 预留，需引入 numpy"，
    作为可扩展点但不破坏零依赖核心。
- `PolicyEngine` 新增 `learner_name: str = "epsilon_greedy"` 参数；
  未显式传入 `bandit` 时通过工厂构建。保留 `bandit` 注入接口（测试/自定义用）。

### 2. 可选 tokenizer 真实成本
- 新增 `fek/cost/`（纯标准库 + 懒加载 `tiktoken`）：
  - `count_tokens(text, model)` → 有 `tiktoken` 时返回 token 数，否则 `None`。
  - `estimate_cost_usd(prompt, completion, model, price_per_1k)` → 有 `tiktoken` 时
    按 token 计费，否则 `None`。
- `OpenAIBackend.complete`：若 `estimate_cost_usd` 返回非 `None`，用真实 token 成本；
  否则回退现有每次调用固定估算。**Mock 后端完全不动**（保持零配置可跑）。

### 3. 回测成为 CI 基准
- 新增 `fek/learning/backtest.py`：`run_backtest(train_n, lam, mu, seed, warmup, epsilon)`
  返回 `{fixed: {...}, learned: {...}, learned_no_worse: bool}`。
  逻辑从 `examples/learning_replay.py` 提炼（确定性环境模型 + 交错数据集）。
- `examples/learning_replay.py` 改为调用该模块（单一事实来源，避免漂移）。
- 新增 `tests/test_backtest.py`：断言 `learned["avg_reward"] >= fixed["avg_reward"] - 1e-9`
  （证明学习后不劣于固定阈值；验证阶段 ε=0，确定性）。

### 4. Web 学习开关 + 洞察面板
- `web/app.py` 侧栏新增「启用学习（Learning Optimizer）」勾选，实时切换
  `kernel.policy.learning`（满足"学习可开关"）。
- 自动页运行后新增「学习洞察」折叠区，展示 `policy.explain(...)` 的每臂平均奖励/样本数
  （满足"学习洞察面板"）。

## Alternatives

- **直接实现 LinUCB**：更聪明，但需 numpy，破坏零依赖核心，且数值稳定复杂；
  本次只预留接口，不实现。否决。
- **把回测塞进 PolicyEngine**：职责混淆（PolicyEngine 不该知道"离线环境模型"）；
  独立 `backtest.py` 更干净。采纳独立模块。
- **真实成本用 LLM 提供商 usage 字段**：更准但需要解析各厂商响应结构，
  且与"可选 tiktoken"重复；tiktoken 通用且零厂商耦合，优先。采纳 tiktoken。

## Tradeoffs

- `tiktoken` 是**可选依赖**：未安装时真实模式回退到每次调用固定估算，
  功能不退化，核心保持零依赖。
- `linucb` 预留为 `NotImplementedError`：明确"未做"而非"假装做了"，符合诚实原则。
- 回测用确定性环境模型（非真实 LLM）：保证 CI 快、可复现、无 API 成本；
  代价是它验证的是"学习回路正确"，不是"真实质量提升"。已在测试注释说明。

## Future Work

- v2.1：LinUCB 实现（引入 numpy 作为可选依赖，或纯标准库线性代数小实现）。
- v2.1：回测扩展到多环境模型 + Pareto 前沿可视化。
- 研究 R4：用 LLM-as-judge 替代玩具质量启发式，让回测奖励来自真实评判。
