"""图编译器 —— 将（策略, 任务）编译为可运行的计算图（Compute Graph）。

这就是 FEK 的"AI 执行编译器"（v1 内核）。每种策略都会编译出一张不同的 DAG，
因此同一个任务可以用三种方式执行，并在 Demo 的"对战模式"中并排比较。
"""

from __future__ import annotations

from ..core.graph import ComputeGraph, GraphNode
from ..core.types import Strategy, Task


class GraphBuilder:
    def __init__(self, moa_models: tuple[str, ...] = ("gpt-fast", "gpt-smart", "claude-x")):
        self.moa_models = list(moa_models)

    def build(self, strategy: Strategy, task: Task) -> ComputeGraph:
        if strategy == Strategy.SINGLE:
            return self._single(task)
        if strategy == Strategy.MULTI_AGENT:
            return self._multi_agent(task)
        return self._moa(task)

    def _single(self, task: Task) -> ComputeGraph:
        # 单模型：仅一个求解节点
        g = ComputeGraph()
        g.add(GraphNode("solver", "solver", "llm", model="gpt-fast",
                        prompt_template=task.prompt))
        return g

    def _multi_agent(self, task: Task) -> ComputeGraph:
        # 多智能体：规划 -> 执行 -> 批判 -> 综合，形成串行 DAG
        g = ComputeGraph()
        planner = g.add(GraphNode("planner", "planner", "llm", model="gpt-smart",
                                  prompt_template=f"为以下任务制定方案：{task.prompt}"))
        executor = g.add(GraphNode("executor", "executor", "llm", model="gpt-fast",
                                   prompt_template=f"执行该方案：{task.prompt}").with_dep("planner"))
        critic = g.add(GraphNode("critic", "critic", "llm", model="claude-x",
                                 prompt_template=f"批判该执行结果：{task.prompt}").with_dep("executor"))
        g.add(GraphNode("synthesizer", "synthesizer", "llm", model="gpt-smart",
                        prompt_template=f"综合出最终答案：{task.prompt}").with_dep("critic"))
        return g

    def _moa(self, task: Task) -> ComputeGraph:
        # 混合智能体：多个并行模型 -> 融合节点 -> 反思节点
        g = ComputeGraph()
        leaf_ids = []
        for i, m in enumerate(self.moa_models):
            nid = f"agent_{i}"
            g.add(GraphNode(nid, f"agent_{i}", "llm", model=m,
                            prompt_template=f"从你的视角求解：{task.prompt}"))
            leaf_ids.append(nid)
        fusion = g.add(GraphNode("fusion", "fusion", "fusion",
                                 prompt_template="融合各智能体的输出").with_dep(*leaf_ids))
        g.add(GraphNode("reflect", "reflect", "reflect",
                        prompt_template="反思并评估融合后的答案").with_dep("fusion"))
        return g
