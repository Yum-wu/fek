"""计算图（Compute Graph，DAG）数据结构 + 序列化辅助方法。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# 节点角色 / 类型 -> 中文显示名（仅用于可视化标签，不改变内部 kind 取值）
_ROLE_ZH = {
    "solver": "求解器",
    "planner": "规划器",
    "executor": "执行器",
    "critic": "批判者",
    "synthesizer": "综合器",
    "fusion": "融合器",
    "reflect": "反思器",
}
_KIND_ZH = {
    "llm": "大语言模型",
    "fusion": "融合",
    "reflect": "反思",
}


def node_zh_label(role: str, kind: str) -> str:
    """返回节点的中文标签，形如「求解器｜大语言模型」。"""
    if role.startswith("agent_"):
        idx = role.split("_", 1)[1]
        return f"并行智能体 {idx}"
    r = _ROLE_ZH.get(role, role)
    k = _KIND_ZH.get(kind, kind)
    return f"{r}｜{k}"


@dataclass
class GraphNode:
    id: str
    role: str
    kind: str  # 节点类型："llm" | "fusion" | "reflect"
    depends_on: List[str] = field(default_factory=list)
    model: str = "default"
    prompt_template: str = ""

    def with_dep(self, *dep_ids: str) -> "GraphNode":
        # 追加依赖节点；返回自身以支持链式调用
        self.depends_on.extend(dep_ids)
        return self


@dataclass
class ComputeGraph:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)

    def add(self, node: GraphNode) -> GraphNode:
        self.nodes[node.id] = node
        return node

    def get(self, node_id: str) -> GraphNode:
        return self.nodes[node_id]

    def roots(self) -> List[str]:
        # 返回没有依赖的入口节点
        return [nid for nid, n in self.nodes.items() if not n.depends_on]

    def topological_order(self) -> List[str]:
        """拓扑排序（Kahn 算法）。若检测到环则抛异常。"""
        indeg = {nid: 0 for nid in self.nodes}
        for n in self.nodes.values():
            for d in n.depends_on:
                indeg[n.id] += 1
        queue = [nid for nid, d in indeg.items() if d == 0]
        order: List[str] = []
        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for m in self.nodes.values():
                if nid in m.depends_on:
                    indeg[m.id] -= 1
                    if indeg[m.id] == 0:
                        queue.append(m.id)
        if len(order) != len(self.nodes):
            raise ValueError("计算图中检测到环")
        return order

    def to_dot(self) -> str:
        """导出 Graphviz DOT 格式，供可视化工具使用。"""
        lines = ["digraph G {", "  rankdir=TB; node [shape=box, style=rounded];"]
        for nid, n in self.nodes.items():
            label = node_zh_label(n.role, n.kind).replace("｜", "\\n")
            lines.append(f'  "{nid}" [label="{label}"];')
        for nid, n in self.nodes.items():
            for dep in n.depends_on:
                lines.append(f'  "{dep}" -> "{nid}";')
        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """导出 Mermaid 流程图，供 markdown / Streamlit 渲染。"""
        lines = ["graph TD"]
        for nid, n in self.nodes.items():
            lines.append(f'    {nid}["{node_zh_label(n.role, n.kind)}"]')
        for nid, n in self.nodes.items():
            for dep in n.depends_on:
                lines.append(f"    {dep} --> {nid}")
        return "\n".join(lines)
