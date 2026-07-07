"""约束感知学习演示（RFC 0013 · v2）。

展示 FEK 的"可学习策略优化闭环"：
- 给 ``FEKKernel`` 挂一个 learner，在**同一约束**下反复执行同一类任务；
- 冷启动时走静态择优，热身（warmup）后转为"用真实反馈学到的偏好"决策；
- 由于 ``constraint_aware_reward`` 对超预算/超延迟/隐私违规重重惩罚，
  学习器会自然收敛到"够用且省钱"的策略，而非盲目堆最贵的 MoA。

全部走 mock 后端，零 API key、确定性可复现。
"""

from __future__ import annotations

from fek import FEKKernel
from fek.constraint import analyze
from fek.core.types import Constraints
from fek.learning import create_learner


def main() -> None:
    print("=" * 64)
    print("FEK · 约束感知学习演示（v2 Constraint-aware Learning）")
    print("=" * 64)

    # 紧预算：单次执行成本上限 0.0004 美元
    constraints = Constraints(max_cost_usd=0.0004, min_quality=0.8)
    task = "用一句话解释为什么天空是蓝色的"

    # 挂载 learner（ε-greedy，种子锁定保证可复现）
    kernel = FEKKernel(learner=create_learner("epsilon_greedy", epsilon=0.2, seed=7))

    # 用于 explain 的约束画像
    available = getattr(kernel.backend, "models", None)
    profile = analyze(task, constraints, available_models=available)

    print(f"\n约束：预算≤${constraints.max_cost_usd:.4f}  质量≥{constraints.min_quality:.2f}")
    from fek.learning import profile_context_key

    ctx_key = profile_context_key(profile)
    print(f"学习上下文键：{ctx_key}")
    print("-" * 64)
    print(f"{'轮次':>4} | {'选中策略(name)':<24} | {'成本':>8} | {'预算内':>4} | {'决策来源'}")
    print("-" * 64)

    episodes = 14
    for i in range(1, episodes + 1):
        result = kernel.run(task, constraints=constraints)
        within = "✓" if result.total_cost_usd <= constraints.max_cost_usd else "✗"
        sname = kernel.optimizer._last_strategy.name if kernel.optimizer._last_strategy else "-"
        print(
            f"{i:>4} | {sname:<24} | "
            f"${result.total_cost_usd:.5f} | {within:>4} | {kernel.optimizer._last_mode}"
        )

    print("-" * 64)
    print("\n[最终 explain]")
    print(kernel.optimizer.explain(profile))

    print("\n[learner 快照：该约束上下文下各策略的平均奖励]")
    snap = [
        (arm, n, round(mean, 3))
        for (c, arm, n, mean) in kernel.optimizer.learner.snapshot()
        if c == ctx_key
    ]
    for arm, n, mean in sorted(snap, key=lambda x: -x[2]):
        print(f"  {arm:<22} 样本={n:<3} 平均奖励={mean}")

    print("\n结论：热身后，优化器在约束下学会避开'贵且超预算'的策略，")
    print("收敛到质量够用、成本更低的策略——这正是 FEK 的护城河：可学习的约束优化闭环。")


if __name__ == "__main__":
    main()
