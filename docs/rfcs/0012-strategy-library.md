# RFC 0012 · Strategy Library（可插拔策略库）

- 状态：Accepted
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：关联 0010 positioning-pivot, 0011 constraint-policy-optimizer

## Background（背景）

旧 FEK 把 SINGLE / MULTI_AGENT / MOA 硬编码为 `Strategy` 枚举，由 `PolicyEngine` 与 `GraphCompiler` 特判。新定位要求 **MoA / Debate / ToT 等都是可插拔 Strategy**，FEK 不发明策略、只负责选。

## Problem（问题）

1. 策略与引擎核心耦合：新增一个策略（如 Debate）要改 PolicyEngine、GraphCompiler、types 多处。
2. MoA 被当核心宣传，与 Hermes 直接竞争；实则 MoA 只是众多策略之一。
3. 无法吸收社区新推理策略（Self-Consistency / Graph-of-Thoughts …）而不动核心。

## Proposal（提案）

### 定义 Strategy 协议
```python
class Strategy(Protocol):
    name: str                      # "moa" / "debate" / "tot" / ...
    cost_tier: float              # 相对成本档（用于优化预估）
    def supports(self, profile: ConstraintProfile) -> bool
    def build(self, task: Task, constraints: Constraints,
              models: list[str]) -> ComputeGraph
```

### 新增 Strategy Library 模块（`fek/strategies/`）
内置策略实现（**均来自已有论文/项目，FEK 适配而非发明**）：
- `Single` — 单模型一次调用
- `PlannerPlusReviewer` — 规划 + 批判
- `Reflection` — 自反思循环（Reflexion）
- `Debate` — 多角色辩论
- `TreeOfThoughts` — 树搜索（ToT）
- `MoA` — 混合专家（Hermes/Together 风格；FEK 适配，不重造）
- `Parallel` — 并行多模型投票/融合
- `Hierarchical` — 层级分解

### Policy Optimizer 改为从 Library 选
- Policy Optimizer 在约束下从 Library 中筛选 `supports(profile)` 的策略，再优化选择。
- 新增策略 = 新增一个实现文件，不动引擎核心。

### MoA 立场
- MoA 只是 `StrategyLibrary` 中的一个 `Strategy`。文档与对外沟通**不大讲 MoA**；它与其他策略平权。

## Alternatives（备选）

- **A. 保留 Strategy 枚举 + 工厂**：拒绝。枚举扩展仍需改核心，不满足"策略无关"。
- **B. 用注册表但仍是固定类**：部分采纳；协议 + 注册表优于纯枚举，采纳为本次实现。
- **C. 外部插件包（独立 repo）**：推迟到 v3 Strategy Marketplace；v1 先内置可插拔实现。

## Tradeoffs（权衡）

- ✅ 策略与引擎解耦，新推理策略即插即用，FEK 永远吸收新能力而不被绑定。
- ✅ MoA 退场为普通策略，避免与 Hermes 正面竞争。
- ⚠️ 需要定义清晰的 Strategy 协议与 ComputeGraph 契约；v1 先以 mock 实现多数策略，真实实现后续接入。
- ⚠️ 策略质量（如 ToT 展开深度）本身是研究问题，不在 FEK 核心范围内。

## Future Work（未来工作）

- v1：内置策略的 mock 实现 + 注册表。
- v3：外部 Strategy 注册（Strategy Marketplace，社区新论文即插即用）。
- R5：Strategy Library 自动扩张（从论文/项目吸收）。
