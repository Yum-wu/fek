import unittest

from fek.core.types import Strategy
from fek.policy import PolicyEngine


class TestPolicy(unittest.TestCase):
    def test_default_bands(self):
        p = PolicyEngine()
        self.assertEqual(p.select(0.1), Strategy.SINGLE)
        self.assertEqual(p.select(0.5), Strategy.MULTI_AGENT)
        self.assertEqual(p.select(0.9), Strategy.MOA)

    def test_explain_returns_string(self):
        p = PolicyEngine()
        self.assertIn("SINGLE", p.explain(0.1))
        self.assertIn("MOA", p.explain(0.9))

    def test_learn_drift_bounded(self):
        p = PolicyEngine()
        for _ in range(50):
            p.learn(0.8, 0.2)  # consistently low quality
        self.assertGreaterEqual(p._drift, -0.3)
        self.assertLessEqual(p._drift, 0.3)


if __name__ == "__main__":
    unittest.main()
