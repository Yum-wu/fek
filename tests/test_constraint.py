"""Constraint Analysis 单测（RFC 0011 / 迁移计划阶段 6.2）。"""
import unittest

from fek.constraint import analyze, DEFAULT_AVAILABLE_MODELS, LOCAL_MODELS
from fek.core.types import Constraints, Task


def _task() -> Task:
    return Task(id="t1", prompt="示例任务")


class TestConstraintAnalysis(unittest.TestCase):
    def test_no_constraints_falls_back_to_default(self):
        # 不传约束 -> 默认画像：全部可用模型、无隐私限制、可行
        prof = analyze(_task(), None)
        self.assertTrue(prof.feasible)
        self.assertEqual(prof.allowed_models, DEFAULT_AVAILABLE_MODELS)
        self.assertEqual(prof.privacy_level, 0)
        self.assertIsNone(prof.budget)
        self.assertIsNone(prof.latency)
        self.assertIsNone(prof.infeasibility_reason)

    def test_quality_clamped_to_unit(self):
        prof = analyze(_task(), Constraints(min_quality=5.0))
        self.assertEqual(prof.normalized_quality, 1.0)
        prof2 = analyze(_task(), Constraints(min_quality=-3.0))
        self.assertEqual(prof2.normalized_quality, 0.0)

    def test_privacy_local_only_keeps_only_local_models(self):
        prof = analyze(_task(), Constraints(privacy="local_only"))
        self.assertTrue(prof.feasible)
        self.assertEqual(prof.allowed_models, ["local-model"])
        self.assertEqual(prof.privacy_level, 2)
        self.assertTrue(set(prof.allowed_models) <= LOCAL_MODELS)

    def test_privacy_no_external_keeps_only_local_models(self):
        prof = analyze(_task(), Constraints(privacy="no_external"))
        self.assertEqual(prof.allowed_models, ["local-model"])
        self.assertEqual(prof.privacy_level, 1)

    def test_preferred_models_intersection(self):
        prof = analyze(_task(), Constraints(preferred_models=["gpt-smart"]))
        self.assertTrue(prof.feasible)
        self.assertEqual(prof.allowed_models, ["gpt-smart"])

    def test_preferred_models_empty_intersection_infeasible(self):
        prof = analyze(_task(), Constraints(preferred_models=["no-such-model"]))
        self.assertFalse(prof.feasible)
        self.assertIsNotNone(prof.infeasibility_reason)
        self.assertIn("no-such-model", prof.infeasibility_reason)

    def test_local_only_but_local_disallowed_infeasible(self):
        prof = analyze(
            _task(),
            Constraints(privacy="local_only", allow_local_models=False),
        )
        self.assertFalse(prof.feasible)
        self.assertIn("allow_local_models", prof.infeasibility_reason)

    def test_budget_and_latency_recorded_not_pruned_here(self):
        # 预算/延迟是优化层（Policy Optimizer）的剪枝依据，分析层只记录、不裁模型
        prof = analyze(
            _task(),
            Constraints(max_cost_usd=0.0001, max_latency_ms=100),
        )
        self.assertEqual(prof.budget, 0.0001)
        self.assertEqual(prof.latency, 100)
        self.assertTrue(prof.feasible)
        self.assertEqual(prof.allowed_models, DEFAULT_AVAILABLE_MODELS)

    def test_task_constraints_consistent(self):
        # Task.constraints 与 analyze 一致：不传约束走默认
        task = Task(id="t2", prompt="x", constraints=None)
        prof = analyze(task, task.constraints)
        self.assertEqual(prof.allowed_models, DEFAULT_AVAILABLE_MODELS)


if __name__ == "__main__":
    unittest.main()
