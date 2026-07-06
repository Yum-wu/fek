import unittest

from fek import FEKKernel
from fek.core.types import Strategy


class TestKernel(unittest.TestCase):
    def setUp(self):
        self.kernel = FEKKernel()  # mock backend, offline

    def test_run_returns_result(self):
        r = self.kernel.run("What is 2+2?")
        self.assertEqual(r.strategy, Strategy.SINGLE)
        self.assertTrue(r.final_output)
        self.assertGreaterEqual(r.avg_quality, 0.0)

    def test_hard_task_routes_to_moa(self):
        hard = "Compare and debate the trade-offs of microservices versus monoliths, considering latency, cost, and team structure."
        r = self.kernel.run(hard)
        self.assertEqual(r.strategy, Strategy.MOA)
        self.assertTrue(r.fused)

    def test_battle_runs_all_strategies(self):
        results = self.kernel.run_all_strategies("Design a caching layer for a social app.")
        self.assertEqual(set(results.keys()), set(Strategy))
        for r in results.values():
            self.assertTrue(r.final_output)

    def test_telemetry_records(self):
        self.kernel.run("hello")
        self.assertEqual(len(self.kernel.telemetry.traces), 1)


if __name__ == "__main__":
    unittest.main()
