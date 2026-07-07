import unittest

from fek.core.graph import ComputeGraph, GraphNode
from fek.core.types import Strategy, Task
from fek.compiler import GraphBuilder


class TestGraph(unittest.TestCase):
    def test_topological_order(self):
        g = ComputeGraph()
        g.add(GraphNode("a", "solver", "llm"))
        g.add(GraphNode("b", "critic", "llm").with_dep("a"))
        order = g.topological_order()
        self.assertEqual(order, ["a", "b"])

    def test_cycle_detection(self):
        g = ComputeGraph()
        g.add(GraphNode("a", "x", "llm").with_dep("b"))
        g.add(GraphNode("b", "y", "llm").with_dep("a"))
        with self.assertRaises(ValueError):
            g.topological_order()

    def test_builder_strategies(self):
        b = GraphBuilder()
        task = Task(id="t1", prompt="do something")
        for strat in Strategy:
            g = b.build(strat, task)
            self.assertTrue(len(g.nodes) >= 1)
        # MOA must contain a fusion node
        moa = b.build(Strategy.MOA, task)
        self.assertTrue(any(n.kind == "fusion" for n in moa.nodes.values()))

    def test_dot_and_mermaid(self):
        g = GraphBuilder().build(Strategy.MULTI_AGENT, Task(id="t", prompt="x"))
        self.assertIn("digraph", g.to_dot())
        self.assertIn("graph TD", g.to_mermaid())


if __name__ == "__main__":
    unittest.main()
