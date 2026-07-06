import unittest

from fek.core.types import Complexity, Strategy
from fek.policy import PolicyEngine


class TestPolicy(unittest.TestCase):
    def test_default_bands(self):
        # 无 band 时走阈值规则（冷启动路径）
        p = PolicyEngine()
        self.assertEqual(p.select(0.1), Strategy.SINGLE)
        self.assertEqual(p.select(0.5), Strategy.MULTI_AGENT)
        self.assertEqual(p.select(0.9), Strategy.MOA)

    def test_explain_returns_string(self):
        p = PolicyEngine()
        self.assertIn("SINGLE", p.explain(0.1))
        self.assertIn("MOA", p.explain(0.9))

    def test_learn_drift_bounded(self):
        # _drift 对阈值规则路径的微小自适应仍应有界（[-0.3, 0.3]）
        p = PolicyEngine()
        band = Complexity.HIGH
        strat = Strategy.MOA
        for _ in range(50):
            # 持续低质量 -> _drift 向下但有界
            p.learn(0.8, band, strat, 0.2, 0.001, 100.0)
        self.assertGreaterEqual(p._drift, -0.3)
        self.assertLessEqual(p._drift, 0.3)
        for _ in range(50):
            # 持续高质量 -> _drift 向上但有界
            p.learn(0.8, band, strat, 0.95, 0.001, 100.0)
        self.assertLessEqual(p._drift, 0.3)

    def test_learning_warms_up_then_uses_bandit(self):
        # 反馈足够后应切换到 bandit 决策，并能在 explain 中展示学习偏好
        p = PolicyEngine(warmup=4, epsilon=0.0, state_path=None)
        band = Complexity.HIGH
        # 在高复杂度档，反复用 MOA 且给高质量 -> 该臂均值最高
        for _ in range(6):
            p.learn(0.9, band, Strategy.MOA, 0.9, 0.002, 200.0)
        chosen = p.select(0.9, band)
        self.assertEqual(chosen, Strategy.MOA)
        self.assertIn("学习层已热身", p.explain(0.9, band))
