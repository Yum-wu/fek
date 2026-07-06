"""学习层演示 —— 展示 FEK 如何从执行轨迹中自适应调整策略选择。

完全离线（mock 模式，无需 API key）。运行后你会看到：
1. 冷启动阶段：策略由阈值规则决定（可预期）。
2. 随着反馈积累：bandit 逐步接管，开始探索并形成偏好。
3. 学习洞察面板：每个复杂度档下三臂的平均奖励与样本数。

运行：
    python examples/learning_demo.py
"""

import os
import sys

# 路径引导：保证从任意目录都能 import fek
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fek import FEKKernel
from fek.core.types import Complexity


# 一批覆盖不同复杂度档的任务（英文，便于复杂度分类器命中信号词；
# 会重复多轮以积累反馈）。注意：分类器信号词为英文（compare/debate/versus/
# trade-off/plan/step by step 等），中文任务会全部被判为低复杂度，因此这里
# 用英文以正确触发低/中/高三档的自适应学习。
TASKS = [
    ("Simple: what is 2+2?", Complexity.LOW),
    ("Simple: explain what an API is in one sentence.", Complexity.LOW),
    ("Medium: plan a 3-day Tokyo trip with a budget.", Complexity.MEDIUM),
    ("Medium: explain why the sky is blue, step by step.", Complexity.MEDIUM),
    ("Hard: compare and debate the trade-offs of microservices versus monoliths for a high-growth startup, considering latency, cost, and team structure.", Complexity.HIGH),
    ("Hard: evaluate three caching strategies (LRU / LFU / ARC) and their trade-offs under high read throughput.", Complexity.HIGH),
]


def main() -> None:
    print("=" * 64)
    print("FEK 学习层演示（mock 模式，离线可跑）")
    print("=" * 64)

    kernel = FEKKernel(learning=True)
    rounds = 3  # 每轮把全部任务跑一遍，共 18 条反馈（> warmup）

    for rnd in range(rounds):
        print(f"\n--- 第 {rnd + 1} 轮 ---")
        for text, _band in TASKS:
            res = kernel.run(text)
            print(
                f"  [{res.complexity.value:<6}] {res.strategy.value:<12} "
                f"质量 {res.avg_quality:.2f}  成本 ${res.total_cost_usd:.5f}  "
                f"{res.total_latency_ms:>6.0f}ms"
            )

    print("\n" + "=" * 64)
    print("学习洞察（各复杂度档下三臂平均奖励 / 样本数）")
    print("=" * 64)
    for band in (Complexity.LOW, Complexity.MEDIUM, Complexity.HIGH):
        print(f"\n复杂度档 {band.value}:")
        print(kernel.policy.explain(0.5, band))

    # 持久化：学到的参数存盘，下次运行可累积
    kernel.policy.save()
    print(f"\n已保存学习状态到 {kernel.policy.state_path}（重启后偏好不丢失）")


if __name__ == "__main__":
    main()
