# RFC 0011 · Constraint-Aware Policy Optimizer

- 状态：Accepted
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：Supersedes 0003 policy-engine；关联 0010 positioning-pivot, 0012 strategy-library

## Background（背景）

旧 `PolicyEngine` 的输入是"任务复杂度评分"，输出是 SINGLE / MULTI_AGENT / MOA 三选一。这把 FEK 的价值绑在"按复杂度选策略"，而复杂度只是约束的一个维度。

新定位要求**约束（质量/预算/延迟/隐私/模型偏好）作为一等输入**，FEK 在约束下优化策略选择。

## Problem（问题）

1. 旧输入模型缺少预算/延迟/隐私/模型偏好，无法表达"预算 $0.2 且质量 High"这类真实诉求。
2. 旧目标只是"按复杂度选"，不是"在约束下最大化质量"，无法处理硬约束（如隐私要求本地模型）。
3. 策略集合固定三选一，新增策略需改引擎核心，违反"策略无关"原则。

## Proposal（提案）

### 新增 Constraints 与 ConstraintProfile
```python
@dataclass
class Constraints:
    min_quality: float = 0.0        # 期望质量下限
    max_cost_usd: float | None = None
    max_latency_ms: float | None = None
    privacy: str = "none"           # none | local_only | no_external
    allow_local_models: bool = True
    preferred_models: list[str] = field(default_factory=list)

@dataclass
class ConstraintProfile:
    normalized_quality: float
    budget: float | None
    latency: float | None
    privacy_level: int
    allowed_models: list[str]
    feasible: bool
    infeasibility_reason: str | None
```

### 新增 Constraint Analysis 模块
- `analyze(task, constraints) -> ConstraintProfile`
- 规范化约束、做可行性检查、按隐私/本地/偏好过滤可用模型集合。

### Policy Optimizer（重构 PolicyEngine）
- 输入从 `score: float` 改为 `profile: ConstraintProfile`。
- 目标：`maximize quality` subject to `cost ≤ budget`, `latency ≤ latency_cap`, `privacy` 硬约束。
- 多目标奖励（保留 `质量 − λ·成本 − μ·延迟`），并带可行性/隐私硬约束。
- 策略集合来自 **Strategy Library**（见 0012），不再硬编码三选一。
- `explain()` 输出"在哪些约束下、为何选此策略、预期权衡"。
- 学习层（`learning/`）保留，奖励改为约束感知。

### Task 扩展
`Task` 增加 `constraints: Constraints` 字段（旧 `metadata` 仍可用作补充）。

## Alternatives（备选）

- **A. 仅扩展 PolicyEngine 输入加 budget/latency 字段**：部分采纳，但仍需 Constraint Analysis 做规范化与可行性。
- **B. 把约束塞进 Task.metadata 由 PolicyEngine 自己解析**：拒绝。解析与可行性检查应独立成层，便于测试与复用。
- **C. 本次提案（Constraint Analysis + Policy Optimizer + Strategy Library）**：采纳。

## Tradeoffs（权衡）

- ✅ 约束成为一等公民，FEK 能回答真正稳定的优化问题。
- ✅ 硬约束（隐私/预算）可被显式处理，而非静默降级。
- ⚠️ 公共接口变化（PolicyEngine.select 签名变），需 RFC 驱动 + 迁移计划执行，且 breaking。
- ⚠️ Constraint Analysis 当前只能是启发式；更好理解是 Research（路线图 R3）。

## Future Work（未来工作）

- v1 实现 Constraint Analysis + Policy Optimizer 重构 + Strategy Library 基础（见迁移计划 pivot 阶段）。
- v2 约束感知奖励与冲突协商原型（路线图 R1）。
- 更好的约束理解（嵌入/检索/LLM 自评）作为 R3 研究。
