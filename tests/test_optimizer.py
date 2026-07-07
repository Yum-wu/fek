"""Policy Optimizer 单测（RFC 0011 / 迁移计划阶段 6.3）。"""
import unittest

from fek.core.types import ConstraintProfile, Constraints, Task
from fek.policy.optimizer import PolicyOptimizer
from fek.strategies import MoA, Single


def _task() -> Task:
    return Task(id="t", prompt="示例任务")


_NORMAL = ConstraintProfile(
    normalized_quality=0.0, budget=None, latency=None, privacy_level=0,
    allowed_models=["gpt-fast", "gpt-smart", "claude-x"], feasible=True,
)
_LOCAL = ConstraintProfile(
    normalized_quality=0.0, budget=None, latency=None, privacy_level=2,
    allowed_models=["local-model"], feasible=True,
)


class TestPolicyOptimizer(unittest.TestCase):
    def setUp(self):
        self.opt = PolicyOptimizer()

    def test_normal_profile_picks_reasonably(self):
        chosen = self.opt.select(_NORMAL)
        self.assertIsNotNone(chosen)
        # 无预算/延迟约束时，高质量预期（MoA）应被选中
        self.assertIsInstance(chosen, MoA)

    def test_local_only_never_picks_multi_model(self):
        chosen = self.opt.select(_LOCAL)
        self.assertIsNotNone(chosen)
        # 隐私 local_only 下多模型策略被 supports() 剪枝，优化器只能在单模型类里择优
        self.assertEqual(chosen.min_models, 1)
        self.assertNotIsInstance(chosen, MoA)

    def test_tight_budget_prunes_expensive(self):
        # 极紧预算：MoA 必被剪枝，退回到最便宜可行策略
        profile = ConstraintProfile(
            normalized_quality=0.0, budget=0.0002, latency=None, privacy_level=0,
            allowed_models=["gpt-fast", "gpt-smart", "claude-x"], feasible=True,
        )
        chosen = self.opt.select(profile)
        self.assertIsNotNone(chosen)
        self.assertNotIsInstance(chosen, MoA)

    def test_infeasible_returns_none(self):
        infeasible = ConstraintProfile(
            normalized_quality=0.0, budget=None, latency=None, privacy_level=0,
            allowed_models=[], feasible=False, infeasibility_reason="无模型",
        )
        self.assertIsNone(self.opt.select(infeasible))

    def test_explain_mentions_constraints(self):
        out = self.opt.explain(_NORMAL)
        self.assertIn("约束画像", out)
        self.assertIn("候选模型", out)
        self.assertIn("<- 选中", out)

    def test_explain_reports_infeasible(self):
        infeasible = ConstraintProfile(
            normalized_quality=0.0, budget=None, latency=None, privacy_level=0,
            allowed_models=[], feasible=False, infeasibility_reason="无可用模型",
        )
        out = self.opt.explain(infeasible)
        self.assertIn("不可行", out)

    def test_constraints_to_profile_end_to_end(self):
        # 从 Constraints 经 analyze -> optimizer 的端到端选择
        from fek.constraint import analyze

        profile = analyze(_task(), Constraints(privacy="local_only"))
        chosen = self.opt.select(profile)
        self.assertEqual(chosen.min_models, 1)
        self.assertNotIsInstance(chosen, MoA)


if __name__ == "__main__":
    unittest.main()
