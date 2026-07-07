"""约束感知学习（RFC 0013 · v2）测试。

覆盖：
- ``constraint_aware_reward`` 对预算/延迟/隐私/min_quality 违规的硬惩罚；
- ``profile_context_key`` 离散化稳定且随约束变化；
- ``PolicyOptimizer`` 挂载 learner 后：冷启动回退静态、热身后会学到可行偏好、
  且绝不会选中不可行（如隐私受限下的多模型）策略。
"""

import unittest

from fek.core.types import ConstraintProfile, Constraints
from fek.learning import (
    create_learner,
    constraint_aware_reward,
    profile_context_key,
)
from fek.learning.reward import compute_reward
from fek.policy.optimizer import PolicyOptimizer
from fek.strategies import DEFAULT_LIBRARY


def _profile(
    privacy_level: int = 0,
    allowed=("gpt-fast", "gpt-smart", "claude-x"),
    budget=None,
    latency=None,
    quality: float = 0.8,
    feasible: bool = True,
) -> ConstraintProfile:
    """构造测试用 ConstraintProfile（避免走 analyze，聚焦优化器/学习逻辑）。"""
    return ConstraintProfile(
        normalized_quality=quality,
        budget=budget,
        latency=latency,
        privacy_level=privacy_level,
        allowed_models=list(allowed),
        feasible=feasible,
    )


class TestConstraintReward(unittest.TestCase):
    def test_no_constraints_equals_base(self):
        base = compute_reward(0.9, 0.001, 100)
        self.assertAlmostEqual(
            constraint_aware_reward(0.9, 0.001, 100, None, None), base
        )

    def test_budget_violation_penalized(self):
        ok = constraint_aware_reward(0.9, 0.0005, 100, Constraints(max_cost_usd=0.001))
        bad = constraint_aware_reward(0.9, 0.005, 100, Constraints(max_cost_usd=0.001))
        self.assertLess(bad, ok)

    def test_latency_violation_penalized(self):
        ok = constraint_aware_reward(0.9, 0.001, 100, Constraints(max_latency_ms=200))
        bad = constraint_aware_reward(0.9, 0.001, 500, Constraints(max_latency_ms=200))
        self.assertLess(bad, ok)

    def test_privacy_violation_heavy_penalty(self):
        ok = constraint_aware_reward(
            0.9, 0.001, 100, Constraints(privacy="local_only"), used_models=["local-model"]
        )
        bad = constraint_aware_reward(
            0.95, 0.001, 100, Constraints(privacy="local_only"), used_models=["gpt-fast"]
        )
        # 隐私红线至少 -2.0，明显压过质量收益
        self.assertLess(bad, ok - 1.0)

    def test_min_quality_underdelivery_penalized(self):
        ok = constraint_aware_reward(0.9, 0.001, 100, Constraints(min_quality=0.8))
        bad = constraint_aware_reward(0.5, 0.001, 100, Constraints(min_quality=0.8))
        self.assertLess(bad, ok)


class TestContextKey(unittest.TestCase):
    def test_stable(self):
        self.assertEqual(profile_context_key(_profile()), profile_context_key(_profile()))

    def test_varies_by_privacy(self):
        self.assertNotEqual(
            profile_context_key(_profile(privacy_level=0)),
            profile_context_key(_profile(privacy_level=2)),
        )

    def test_varies_by_budget(self):
        self.assertNotEqual(
            profile_context_key(_profile(budget=None)),
            profile_context_key(_profile(budget=0.0003)),
        )


class TestOptimizerLearning(unittest.TestCase):
    def _opt(self, warmup: int = 4):
        return PolicyOptimizer(
            DEFAULT_LIBRARY,
            learner=create_learner("epsilon_greedy", epsilon=0.0, seed=1),
            warmup=warmup,
        )

    def test_cold_no_learner_is_static(self):
        opt = PolicyOptimizer(DEFAULT_LIBRARY)  # 默认无 learner
        self.assertIsNone(opt.learner)
        self.assertIsNotNone(opt.select(_profile()))

    def test_cold_learner_falls_back_static(self):
        opt = self._opt()
        p = _profile(privacy_level=2, allowed=["local-model"])
        # 没有任何反馈 -> 静态回退（不挑不可行策略）
        self.assertEqual(opt._last_mode, "static")
        chosen = opt.select(p)
        self.assertIn(chosen.min_models, (1,))  # 单模型类（隐私 local_only）

    def test_learns_feasible_preference(self):
        opt = self._opt(warmup=4)
        p = _profile(privacy_level=2, allowed=["local-model"])
        ctx = profile_context_key(p)
        for _ in range(6):
            opt.learner.update(ctx, "reflection", 0.9)  # 该上下文反复偏爱 reflection
        chosen = opt.select(p)
        self.assertEqual(opt._last_mode, "learned")
        self.assertEqual(chosen.name, "reflection")

    def test_never_selects_infeasible_multi_model(self):
        opt = self._opt(warmup=2)
        p = _profile(privacy_level=2, allowed=["local-model"])  # moa/debate/parallel/tot 不可行
        # 历史在"别处" moa 很好，但本上下文 moa 不在可行集
        for _ in range(4):
            opt.learner.update(profile_context_key(p), "moa", 0.99)
        chosen = opt.select(p)
        self.assertNotEqual(chosen.name, "moa")
        self.assertEqual(chosen.min_models, 1)  # 必为可行（单模型）策略

    def test_learns_cheaper_under_tight_budget(self):
        opt = self._opt(warmup=4)
        p = _profile(budget=0.0003)  # 紧预算
        ctx = profile_context_key(p)
        # 真实世界：moa 贵且超预算被惩罚，single 够用且省 -> 学出 single
        for _ in range(5):
            opt.learner.update(ctx, "single", 0.80)
            opt.learner.update(ctx, "moa", -1.2)  # 超预算惩罚
        chosen = opt.select(p)
        self.assertEqual(chosen.name, "single")


if __name__ == "__main__":
    unittest.main()
