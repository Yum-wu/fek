import os
import tempfile
import unittest

from fek.core.types import Complexity, Strategy
from fek.learning.bandit import ContextualBandit
from fek.learning.persist import load, save
from fek.learning.reward import compute_reward
from fek.policy import PolicyEngine


class TestReward(unittest.TestCase):
    def test_quality_monotonic(self):
        # 质量越高，奖励越高（其余不变）
        self.assertGreater(
            compute_reward(0.9, 0.001, 100), compute_reward(0.5, 0.001, 100)
        )

    def test_cost_penalty(self):
        # 成本越高，奖励越低（体现"贵策略必须证明自己"）
        self.assertLess(
            compute_reward(0.9, 0.01, 100), compute_reward(0.9, 0.001, 100)
        )

    def test_latency_penalty(self):
        self.assertLess(
            compute_reward(0.9, 0.001, 2000), compute_reward(0.9, 0.001, 100)
        )

    def test_reward_in_reasonable_range(self):
        r = compute_reward(0.8, 0.002, 500)
        self.assertTrue(-2.0 < r < 2.0)


class TestBandit(unittest.TestCase):
    def test_update_mean(self):
        b = ContextualBandit()
        b.update("high", Strategy.MOA, 1.0)
        b.update("high", Strategy.MOA, 0.0)
        self.assertEqual(b.count("high", Strategy.MOA), 2)
        self.assertAlmostEqual(b.mean_reward("high", Strategy.MOA), 0.5, places=6)

    def test_greedy_selects_best(self):
        b = ContextualBandit(epsilon=0.0, seed=1)
        b.update("high", Strategy.MOA, 0.8)
        b.update("high", Strategy.SINGLE, 0.3)
        arms = [Strategy.SINGLE, Strategy.MULTI_AGENT, Strategy.MOA]
        self.assertEqual(b.select("high", arms, epsilon=0.0), Strategy.MOA)
        self.assertEqual(b.best_arm("high", arms), Strategy.MOA)

    def test_explore_returns_valid_arm(self):
        b = ContextualBandit(epsilon=1.0, seed=2)
        arms = [Strategy.SINGLE, Strategy.MULTI_AGENT, Strategy.MOA]
        for _ in range(20):
            self.assertIn(b.select("low", arms, epsilon=1.0), arms)

    def test_persist_roundtrip(self):
        b = ContextualBandit(epsilon=0.2)
        b.update("high", Strategy.MOA, 0.7)
        d = b.to_dict()
        b2 = ContextualBandit.from_dict(d)
        self.assertEqual(b2.total_feedback, 1)
        self.assertAlmostEqual(b2.mean_reward("high", Strategy.MOA), 0.7, places=6)

    def test_separate_contexts(self):
        # 不同复杂度档位独立统计（上下文感知的核心）
        b = ContextualBandit(epsilon=0.0)
        b.update("low", Strategy.SINGLE, 0.9)
        b.update("high", Strategy.MOA, 0.9)
        arms = [Strategy.SINGLE, Strategy.MULTI_AGENT, Strategy.MOA]
        self.assertEqual(b.best_arm("low", arms), Strategy.SINGLE)
        self.assertEqual(b.best_arm("high", arms), Strategy.MOA)


class TestPersistFile(unittest.TestCase):
    def test_save_load_file(self):
        path = tempfile.mktemp(suffix=".json")
        try:
            save({"epsilon": 0.15, "total_feedback": 3}, path)
            self.assertEqual(load(path), {"epsilon": 0.15, "total_feedback": 3})
            # 文件不存在时返回 None（冷启动安全回退）
            self.assertIsNone(load(path + ".nope"))
        finally:
            if os.path.exists(path):
                os.remove(path)


class TestPolicyLearning(unittest.TestCase):
    def test_fallback_when_no_learning(self):
        p = PolicyEngine(learning=False)
        self.assertEqual(p.select(0.1, Complexity.LOW), Strategy.SINGLE)
        self.assertEqual(p.select(0.9, Complexity.HIGH), Strategy.MOA)

    def test_fallback_before_warmup(self):
        p = PolicyEngine(learning=True, warmup=100)
        # 反馈为 0 < warmup -> 仍走规则（保证冷启动可跑、行为可预期）
        self.assertEqual(p.select(0.1, Complexity.LOW), Strategy.SINGLE)

    def test_uses_bandit_after_warmup(self):
        p = PolicyEngine(learning=True, warmup=2, epsilon=0.0)
        band = Complexity.HIGH
        for _ in range(4):
            p.learn(0.9, band, Strategy.MOA, 0.9, 0.002, 200.0)
        self.assertEqual(p.select(0.9, band), Strategy.MOA)
        self.assertIn("学习层已热身", p.explain(0.9, band))

    def test_policy_save_load(self):
        p = PolicyEngine(learning=True, warmup=2, state_path=None)
        for _ in range(4):
            p.learn(0.9, Complexity.HIGH, Strategy.MOA, 0.9, 0.002, 200.0)
        path = tempfile.mktemp(suffix=".json")
        try:
            p.save(path)
            p2 = PolicyEngine(learning=True, state_path=path)
            self.assertEqual(p2.bandit.total_feedback, p.bandit.total_feedback)
            self.assertEqual(p2.select(0.9, Complexity.HIGH), Strategy.MOA)
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main()
