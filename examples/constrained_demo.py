"""约束感知演示 —— 在质量 / 成本 / 延迟 / 隐私等约束下自动选择最优策略（Pivot 落地）。

展示 FEK 新定位的核心价值：
- 约束（Constraints）是一等输入，由 Constraint Analysis 归一化；
- Policy Optimizer 在 Strategy Library 中按硬约束剪枝、软目标择优；
- 同一任务在不同约束下会路由到不同策略。

运行（零 API key，mock 模式）：
    python examples/constrained_demo.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from fek import FEKKernel
from fek.constraint import analyze
from fek.core.types import Constraints
from fek.policy.optimizer import PolicyOptimizer


def _hr(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    kernel = FEKKernel()
    optimizer = PolicyOptimizer()
    prompt = "写一份关于用户隐私数据处理的内部评估报告，需兼顾合规与可读性。"

    # 1) 默认（无约束）—— 向后兼容旧管线
    _hr("① 默认执行（无约束，向后兼容）")
    r0 = kernel.run(prompt)
    print(r0.summary())

    # 2) 隐私约束：local_only —— 只能使用本地模型
    _hr("② 约束：隐私 = local_only（仅本地模型）")
    cons_local = Constraints(privacy="local_only", min_quality=0.8)
    r1 = kernel.run(prompt, constraints=cons_local)
    print(r1.summary())
    print("说明：多模型策略被 supports() 剪枝，优化器在单模型类策略中择优。")

    # 3) 预算约束：极紧预算 —— 退回最便宜的可行策略
    _hr("③ 约束：预算 ≤ $0.0002（极紧）")
    cons_budget = Constraints(max_cost_usd=0.0002)
    r2 = kernel.run(prompt, constraints=cons_budget)
    print(r2.summary())
    print("说明：MoA 等昂贵策略超预算被剪枝，退回最便宜可行策略。")

    # 4) 不可行约束 —— 偏好模型不在可用集合中
    _hr("④ 不可行约束：偏好模型不存在")
    try:
        kernel.run(prompt, constraints=Constraints(preferred_models=["no-such-model"]))
    except ValueError as e:
        print("捕获到不可行：", e)

    # 5) 可解释性：展示 Policy Optimizer 的决策依据
    _hr("⑤ Policy Optimizer 可解释决策（local_only）")
    profile = analyze(
        __import__("fek.core.types", fromlist=["Task"]).Task("t", prompt),
        cons_local,
        available_models=getattr(kernel.backend, "models", None),
    )
    print(optimizer.explain(profile))


if __name__ == "__main__":
    main()
