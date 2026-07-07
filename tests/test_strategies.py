"""Strategy Library 单测（RFC 0012 / 迁移计划阶段 6.4）。"""
import unittest

from fek.core.types import ConstraintProfile, Task
from fek.strategies import (
    DEFAULT_LIBRARY,
    Debate,
    Hierarchical,
    MoA,
    Parallel,
    PlannerPlusReviewer,
    Reflection,
    Single,
    TreeOfThoughts,
    StrategyLibrary,
)
from fek.strategies.protocol import BaseStrategy


def _task() -> Task:
    return Task(id="t", prompt="示例任务")


# 普通（无隐私）画像：三个可用模型
_NORMAL = ConstraintProfile(
    normalized_quality=0.0, budget=None, latency=None, privacy_level=0,
    allowed_models=["gpt-fast", "gpt-smart", "claude-x"], feasible=True,
)
# 隐私 local_only 画像：仅一个本地模型
_LOCAL = ConstraintProfile(
    normalized_quality=0.0, budget=None, latency=None, privacy_level=2,
    allowed_models=["local-model"], feasible=True,
)
# 不可行画像
_INFEASIBLE = ConstraintProfile(
    normalized_quality=0.0, budget=None, latency=None, privacy_level=0,
    allowed_models=[], feasible=False,
)


class TestStrategyLibraryRegistry(unittest.TestCase):
    def test_default_library_has_eight(self):
        self.assertEqual(len(DEFAULT_LIBRARY.all()), 8)
        self.assertEqual(
            DEFAULT_LIBRARY.names(),
            [
                "single", "planner_plus_reviewer", "reflection", "debate",
                "tree_of_thoughts", "moa", "parallel", "hierarchical",
            ],
        )

    def test_filter_by_profile(self):
        # 普通画像：8 个都支持
        self.assertEqual(len(DEFAULT_LIBRARY.filter(_NORMAL)), 8)
        # 隐私 local_only：多模型策略被剪枝，仅剩单模型类
        supported = {s.name for s in DEFAULT_LIBRARY.filter(_LOCAL)}
        self.assertIn("single", supported)
        self.assertNotIn("moa", supported)
        self.assertNotIn("debate", supported)
        self.assertNotIn("parallel", supported)
        self.assertNotIn("tree_of_thoughts", supported)

    def test_infeasible_profile_supports_none(self):
        self.assertEqual(DEFAULT_LIBRARY.filter(_INFEASIBLE), [])


class TestStrategyBuild(unittest.TestCase):
    def _check_graph(self, strategy: BaseStrategy):
        g = strategy.build(_task(), None, _NORMAL.allowed_models)
        # 合法 DAG：拓扑排序不抛异常、非空、每个依赖都存在
        self.assertTrue(g.nodes)
        order = g.topological_order()
        self.assertEqual(len(order), len(g.nodes))
        for nid in order:
            for dep in g.get(nid).depends_on:
                self.assertIn(dep, g.nodes)

    def test_all_build_valid_graph(self):
        for s in DEFAULT_LIBRARY.all():
            with self.subTest(strategy=s.name):
                self._check_graph(s)

    def test_single_is_one_node(self):
        g = Single().build(_task(), None, ["gpt-fast"])
        self.assertEqual(len(g.nodes), 1)
        self.assertEqual(g.get("solver").role, "solver")

    def test_moa_has_fusion_node(self):
        g = MoA().build(_task(), None, ["gpt-fast", "gpt-smart", "claude-x"])
        self.assertTrue(any(n.kind == "fusion" for n in g.nodes.values()))

    def test_debate_has_two_agents_and_judge(self):
        g = Debate().build(_task(), None, ["gpt-smart", "claude-x"])
        self.assertIn("agent_0", g.nodes)
        self.assertIn("agent_1", g.nodes)
        self.assertIn("judge", g.nodes)

    def test_local_only_still_builds_single(self):
        # 单模型策略在本地模型下也能 build（隐私感知由 supports 把关，build 始终合法）
        g = Single().build(_task(), None, ["local-model"])
        self.assertEqual(g.get("solver").model, "local-model")


if __name__ == "__main__":
    unittest.main()
