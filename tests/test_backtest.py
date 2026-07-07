import unittest

from fek.learning.backtest import run_backtest


class TestBacktest(unittest.TestCase):
    def test_learned_no_worse_than_fixed(self):
        """学习后策略的 avg_reward 不应劣于固定阈值（v2 交付标准：有基准证明）。"""
        res = run_backtest()
        self.assertTrue(
            res["learned_no_worse"],
            f"学习后 avg_reward={res['learned']['avg_reward']:.4f} < 固定={res['fixed']['avg_reward']:.4f}",
        )
        # 学习后在成本-质量权衡上应更优（效率不低于固定的 99%）
        self.assertGreaterEqual(
            res["learned"]["efficiency"], res["fixed"]["efficiency"] * 0.99
        )

    def test_backtest_deterministic(self):
        """带 seed 的回测应可复现（CI 稳定性）。"""
        r1 = run_backtest()
        r2 = run_backtest()
        self.assertEqual(r1["learned"]["avg_reward"], r2["learned"]["avg_reward"])
        self.assertEqual(r1["fixed"]["avg_reward"], r2["fixed"]["avg_reward"])


if __name__ == "__main__":
    unittest.main()
