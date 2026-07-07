"""执行运行时（Execution Runtime）。

按拓扑顺序遍历编译好的 DAG，对每个节点调用后端；遇到融合节点则执行 MoA 融合，
并通过评估层对质量打分。这正是 FEK 愿景中的"执行运行时（Go）"——此处为了
黑客松的开发速度用 Python 实现，但职责划分保持一致。
"""

from __future__ import annotations

from ..core.graph import ComputeGraph
from ..core.types import NodeResult, Task
from ..fusion import fuse
from ..models.backend import LLMBackend
from ..evaluation import score_quality


class Executor:
    def __init__(self, backend: LLMBackend):
        self.backend = backend

    def run(self, task: Task, graph: ComputeGraph) -> tuple[list[NodeResult], str, bool]:
        results: list[NodeResult] = []
        outputs: dict[str, str] = {}

        for nid in graph.topological_order():
            node = graph.get(nid)
            if node.kind == "fusion":
                # 融合节点：收集所有依赖节点的输出，进行 MoA 融合
                labels = [f"agent_{i}" for i in range(len(node.depends_on))]
                merged = fuse([outputs[d] for d in node.depends_on], labels)
                nr = NodeResult(nid, node.role, node.kind, "moa-fusion",
                                merged, 0.0, 0.0, score_quality(merged))
                outputs[nid] = merged
            else:
                # 普通 LLM 节点：以角色身份调用后端
                sys_prompt = f"你是 FEK 执行图中的 {node.role} 节点。"
                comp = self.backend.complete(sys_prompt, node.prompt_template, node.model)
                q = score_quality(comp.content)
                nr = NodeResult(nid, node.role, node.kind, comp.model,
                                comp.content, comp.latency_ms, comp.cost_usd, q)
                outputs[nid] = comp.content
            results.append(nr)

        fused = any(n.kind == "fusion" for n in results)
        # 最终输出：若存在融合节点，取融合/综合后的答案；否则取最后一个节点
        if fused:
            fusion_node = next(n for n in graph.nodes.values() if n.kind == "fusion")
            final_output = outputs.get(fusion_node.id, "")
        else:
            final_output = outputs[graph.topological_order()[-1]] if outputs else ""
        return results, final_output, fused
