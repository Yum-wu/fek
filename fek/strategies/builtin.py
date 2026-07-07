"""内置策略实现（均源自已有论文 / 项目，FEK 适配而非发明，RFC 0012）。

- ``Single`` 单模型一次调用
- ``PlannerPlusReviewer`` 规划 + 批判
- ``Reflection`` 自反思循环（Reflexion）
- ``Debate`` 多角色辩论
- ``TreeOfThoughts`` 树搜索（ToT）
- ``MoA`` 混合专家（Hermes/Together 风格；FEK 适配，不重造）
- ``Parallel`` 并行多模型投票/融合
- ``Hierarchical`` 层级分解

所有策略的 ``build()`` 都产出合法的 ``ComputeGraph``（DAG），由 Runtime 执行。
MoA 只是其中一个普通策略，与其他策略平权 —— 这正是 Pivot 的核心立场。
"""

from __future__ import annotations

from ..core.graph import ComputeGraph, GraphNode
from ..core.types import Constraints, Task
from .protocol import BaseStrategy


class Single(BaseStrategy):
    name = "single"
    zh = "单模型"
    cost_tier = 1.0
    quality_est = 0.85
    min_models = 1
    node_count = 1

    def build(self, task: Task, constraints: Constraints | None, models: list[str]) -> ComputeGraph:
        ms = self._models(models)
        g = ComputeGraph()
        g.add(GraphNode("solver", "solver", "llm", model=ms[0], prompt_template=task.prompt))
        return g


class PlannerPlusReviewer(BaseStrategy):
    name = "planner_plus_reviewer"
    zh = "规划 + 批判"
    cost_tier = 2.0
    quality_est = 0.88
    min_models = 1
    node_count = 3

    def build(self, task: Task, constraints: Constraints | None, models: list[str]) -> ComputeGraph:
        ms = self._models(models)
        g = ComputeGraph()
        g.add(GraphNode("planner", "planner", "llm", model=ms[0],
                        prompt_template=f"为以下任务制定方案：{task.prompt}"))
        g.add(GraphNode("critic", "critic", "llm", model=ms[-1],
                        prompt_template=f"批判该方案并给出改进：{task.prompt}").with_dep("planner"))
        g.add(GraphNode("synthesizer", "synthesizer", "llm", model=ms[0],
                        prompt_template=f"综合出最终答案：{task.prompt}").with_dep("critic"))
        return g


class Reflection(BaseStrategy):
    name = "reflection"
    zh = "自反思"
    cost_tier = 2.5
    quality_est = 0.89
    min_models = 1
    node_count = 3

    def build(self, task: Task, constraints: Constraints | None, models: list[str]) -> ComputeGraph:
        ms = self._models(models)
        g = ComputeGraph()
        g.add(GraphNode("solver", "solver", "llm", model=ms[0], prompt_template=task.prompt))
        g.add(GraphNode("reflect", "reflect", "reflect", model=ms[0],
                        prompt_template=f"反思并改进上述回答：{task.prompt}").with_dep("solver"))
        g.add(GraphNode("synthesizer", "synthesizer", "llm", model=ms[0],
                        prompt_template=f"产出最终精炼答案：{task.prompt}").with_dep("reflect"))
        return g


class Debate(BaseStrategy):
    name = "debate"
    zh = "多角色辩论"
    cost_tier = 3.0
    quality_est = 0.90
    min_models = 2
    node_count = 3

    def build(self, task: Task, constraints: Constraints | None, models: list[str]) -> ComputeGraph:
        ms = self._models(models, ["gpt-smart", "claude-x"])
        g = ComputeGraph()
        g.add(GraphNode("agent_0", "agent_0", "llm", model=ms[0],
                        prompt_template=f"作为正方，论证：{task.prompt}"))
        g.add(GraphNode("agent_1", "agent_1", "llm", model=ms[1],
                        prompt_template=f"作为反方，论证：{task.prompt}"))
        g.add(GraphNode("judge", "judge", "fusion",
                        prompt_template="综合双方辩论，给出结论").with_dep("agent_0", "agent_1"))
        return g


class TreeOfThoughts(BaseStrategy):
    name = "tree_of_thoughts"
    zh = "思维树"
    cost_tier = 3.5
    quality_est = 0.92
    min_models = 2
    node_count = 5

    def build(self, task: Task, constraints: Constraints | None, models: list[str]) -> ComputeGraph:
        ms = self._models(models, ["gpt-fast", "gpt-smart", "claude-x"])
        g = ComputeGraph()
        g.add(GraphNode("root", "solver", "llm", model=ms[0],
                        prompt_template=f"提出问题的核心：{task.prompt}"))
        for i in range(3):
            g.add(GraphNode(f"agent_{i}", f"agent_{i}", "llm", model=ms[i % len(ms)],
                            prompt_template=f"从一条思路展开解法：{task.prompt}").with_dep("root"))
        g.add(GraphNode("select", "select", "fusion",
                        prompt_template="从多条思路中选出最优").with_dep("agent_0", "agent_1", "agent_2"))
        return g


class MoA(BaseStrategy):
    name = "moa"
    zh = "混合专家（MoA）"
    cost_tier = 4.0
    quality_est = 0.93
    min_models = 2
    node_count = 4

    def build(self, task: Task, constraints: Constraints | None, models: list[str]) -> ComputeGraph:
        ms = self._models(models, ["gpt-fast", "gpt-smart", "claude-x"])
        # 用前 2~3 个模型组成并行层
        layer = ms[:3] if len(ms) >= 3 else ms
        g = ComputeGraph()
        leaf_ids = []
        for i, m in enumerate(layer):
            nid = f"agent_{i}"
            g.add(GraphNode(nid, nid, "llm", model=m,
                            prompt_template=f"从你的视角求解：{task.prompt}"))
            leaf_ids.append(nid)
        g.add(GraphNode("fusion", "fusion", "fusion",
                        prompt_template="融合各智能体的输出").with_dep(*leaf_ids))
        g.add(GraphNode("reflect", "reflect", "reflect",
                        prompt_template="反思并评估融合后的答案").with_dep("fusion"))
        return g


class Parallel(BaseStrategy):
    name = "parallel"
    zh = "并行多模型"
    cost_tier = 3.0
    quality_est = 0.90
    min_models = 2
    node_count = 3

    def build(self, task: Task, constraints: Constraints | None, models: list[str]) -> ComputeGraph:
        ms = self._models(models, ["gpt-fast", "gpt-smart", "claude-x"])
        k = max(2, min(3, len(ms)))
        g = ComputeGraph()
        for i in range(k):
            m = ms[i % len(ms)]
            g.add(GraphNode(f"agent_{i}", f"agent_{i}", "llm", model=m,
                            prompt_template=f"独立求解：{task.prompt}"))
        g.add(GraphNode("fusion", "fusion", "fusion",
                        prompt_template="融合并行结果").with_dep(*[f"agent_{i}" for i in range(k)]))
        return g


class Hierarchical(BaseStrategy):
    name = "hierarchical"
    zh = "层级分解"
    cost_tier = 3.5
    quality_est = 0.91
    min_models = 1
    node_count = 5

    def build(self, task: Task, constraints: Constraints | None, models: list[str]) -> ComputeGraph:
        ms = self._models(models)
        g = ComputeGraph()
        g.add(GraphNode("decompose", "planner", "llm", model=ms[0],
                        prompt_template=f"把任务分解为若干子问题：{task.prompt}"))
        k = 3
        for i in range(k):
            g.add(GraphNode(f"sub_{i}", "executor", "llm", model=ms[i % len(ms)],
                            prompt_template=f"解决子问题 {i + 1}：{task.prompt}").with_dep("decompose"))
        g.add(GraphNode("aggregate", "synthesizer", "llm", model=ms[0],
                        prompt_template=f"汇总子问题答案：{task.prompt}").with_dep(
                            *[f"sub_{i}" for i in range(k)]))
        return g


# 内置策略清单（顺序即注册顺序）
BUILTIN_STRATEGIES: list[BaseStrategy] = [
    Single(),
    PlannerPlusReviewer(),
    Reflection(),
    Debate(),
    TreeOfThoughts(),
    MoA(),
    Parallel(),
    Hierarchical(),
]
