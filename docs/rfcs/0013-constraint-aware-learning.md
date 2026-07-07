# RFC 0013 · 约束感知学习优化器（Constraint-aware Learning Optimizer）

- 状态：Accepted
- 作者：FEK Chief Architect
- 日期：2026-07-07
- 关联：0011 constraint-policy-optimizer、0009 learning-optimizer、0012 strategy-library

---

## Background（背景）

阶段 6（对应 0011 / 0012）落地了 **Constraint Analysis + Policy Optimizer + Strategy Library**，
组成 v1「约束感知优化器」。但当前 `PolicyOptimizer.select()` 是**纯静态**的：

- 用固定的 `quality_est / estimate()` 启发式做软目标择优；
- 用硬约束（预算/延迟/隐私）做剪枝；
- **没有任何从执行反馈中学习的能力**。

与此同时，学习层（RFC 0009 的 `ContextualBandit`）只接在**旧** `PolicyEngine` 上，
其上下文是「复杂度档（low/medium/high）」、臂是「SINGLE / MULTI_AGENT / MOA」三枚举——
与新世界（上下文=ConstraintProfile、臂=8 个 Strategy Library 策略）完全不匹配。

FEK 的真正护城河是「**约束感知、策略无关、可学习的策略优化闭环**」
（见 VISION / 0010 / competitive-analysis）。若新管线没有学习，护城河就缺了最关键的一截。

## Problem（问题）

1. **新管线不学习**：`PolicyOptimizer` 无法从真实执行轨迹改进，`quality_est` 是写死的启发式。
2. **学习层上下文/臂错配**：旧 learner 的 complexity-bucket 上下文与 3 枚举臂，不适用于约束世界。
3. **奖励不含约束违规**：一个把预算/延迟/隐私全炸穿的策略，只要质量高仍能拿到「好」奖励，
   学习器没有动机去避开它——与「约束优先」叙事自相矛盾。
4. **无回测保障**：没有断言「约束下学习后不劣于固定阈值」的基准（roadmap v2 交付标准之一）。

## Proposal（提案）

把学习层正式接入新约束管线，不破坏零依赖、不破坏存量测试：

### 1. 约束感知奖励（改 reward 模型，需 RFC）
在 `fek/learning/` 新增 `constraint_aware_reward(quality, cost_usd, latency_ms, constraints, used_models)`，
在 `compute_reward`（质量 − λ·成本 − μ·延迟）基础上叠加硬约束惩罚：
- 超 `max_cost_usd` → 惩罚 +1.0
- 超 `max_latency_ms` → 惩罚 +1.0
- `privacy == local_only` 但 `used_models` 含非本地模型 → 惩罚 +2.0
- `quality < min_quality` → 惩罚差值
`constraints is None` 时退化为原 `compute_reward`（向后兼容）。

### 2. 上下文键（ConstraintProfile → context key）
新增 `profile_context_key(profile) -> str`，把连续的约束离散化为可复用的 bandit 上下文：
`p{privacy_level}|q{lo/mid/hi}|b{none/tight/loose}|l{none/tight/loose}|m{0/1}`。
（m=1 表示候选模型≤1，即强隐私受限场景。）上下文空间可控、可解释。

### 3. PolicyOptimizer 接入 learner（改公共决策接口，需 RFC）
`PolicyOptimizer.__init__` 增加 `learner: Learner | None = None` 与 `warmup: int = 8`：
- 静态择优逻辑**原样保留**为回退路径；
- 当 `learner` 存在、`learner.total_feedback >= warmup`、且该上下文已有样本时，
  用 `learner.best_arm(ctx, feasible_names)` 在可行策略名中选臂，经 `library.get()` 映射回策略对象；
- 若学习选中的策略不在可行集（理论上不该发生，做安全校验），回退静态；
- `explain()` 标注本轮来源（`learned` / `static`）。

### 4. 内核回写学习（kernel 接线）
`FEKKernel._run_constrained` 执行后，若 `optimizer.learner` 已挂载，
用 `profile_context_key(profile)` + `constraint_aware_reward(...)` 回写
`learner.update(ctx, strategy.name, reward)`。
默认 `learner=None`（静态、确定性），由构造参数可选开启——保证存量 demo / 测试零改动。

### 5. 复用既有学习基础设施
沿用 RFC 0009 的 `ContextualBandit`（已是通用 ε-greedy，上下文键与臂均为任意 Hashable）、
`Learner` 协议、`create_learner`、`persist.py`（跨运行累积）。**不引入新依赖**。

## Alternatives（备选方案）

- **完整 MDP / 强化学习**：对 Demo 过重、需 numpy/torch，破坏零依赖；且状态空间大、样本少难收敛。驳回。
- **沿用复杂度档作为新管线上下文**：丢失约束信号（预算/延迟/隐私），与 pivot 主旨冲突。驳回。
- **仅做全局（无上下文）在线优化**：无法针对不同约束自适应，等价于退化成单一全局均值。驳回。
- **把 learner 直接塞进 Constraint Analysis**：职责错位，分析层应保持纯确定性。驳回。

## Tradeoffs（权衡）

- ✅ 护城河补齐：新管线真正「可学习」；奖励显式惩罚违规，行为自洽。
- ✅ 零依赖保持：仍用 ε-greedy + 纯标准库；LinUCB 仍是 v2.1 预留（RFC 0009）。
- ✅ 向后兼容：默认关闭 learner，存量 `run(prompt)` / `run(prompt, constraints)` 行为不变，32 存量测试无回归。
- ⚠️ 多一处状态：learner 需被构造/持久化；示例与可选 Web 面板负责展示，不影响核心路径。
- ⚠️ 臂用策略 `name`（字符串）映射，需 `library.get()` 回查；策略名稳定性成为隐式契约（可接受，RFC 0012 已锁定）。

## Future Work（未来工作）

- **v2.1 LinUCB**（RFC 0009 预留）：用连续约束特征（归一化质量/预算/延迟）做上下文，提升小样本效率。
- **约束冲突协商**（R1）：当 `profile.feasible == False` 时主动提案 Pareto 折中并请求确认。
- **真实成本信号**：可选 `tiktoken` 按 token 计费接入 `constraint_aware_reward`（已具备懒加载）。
- **Web 洞察面板**：展示每策略在各类约束上下文下的平均奖励/样本数/可行性（roadmap v2）。
