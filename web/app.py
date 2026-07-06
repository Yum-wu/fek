"""FEK 的 Streamlit 演示界面。

可视化展示一个任务的完整 FEK 流水线：复杂度 -> 策略决策 -> 执行图 ->
各节点输出 -> 融合后的最终答案；并提供"对战模式"，用成本 / 延迟 / 质量
遥测并排比较三种策略。

运行（mock 模式，离线）：
    streamlit run web/app.py

运行（真实 LLM）：
    export FEK_MODE=openai && export OPENAI_API_KEY=sk-...
    streamlit run web/app.py
"""

from __future__ import annotations

import os
import pathlib
import sys

# 使 `streamlit run web/app.py` 也能正确导入项目根目录
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import streamlit as st

from fek import FEKKernel, Strategy
from fek.core.graph import node_zh_label


@st.cache_resource
def get_kernel() -> FEKKernel:
    # 通过 cache_resource，遥测在多次重跑之间持续累积
    return FEKKernel(telemetry_log="fek_traces.jsonl")


def _pipeline_html(result) -> str:
    """生成带箭头连接的流水线 HTML。"""
    stages = [
        ("任务", result.prompt[:40] + ("\u2026" if len(result.prompt) > 40 else "")),
        ("复杂度", f"{result.complexity.zh} ({result.complexity_score:.2f})"),
        ("策略", result.strategy.zh),
        ("执行图", f"{len(result.node_results)} 个节点"),
        ("输出", "已融合" if result.fused else "单模型"),
    ]
    cards = []
    for label, val in stages:
        cards.append(
            f'<div class="pipe-card">'
            f'<div class="pipe-label">{label}</div>'
            f'<div class="pipe-val">{val}</div>'
            f"</div>"
        )
    arrows = '<div class="pipe-arrow">&#10132;</div>'  # ➠
    body = arrows.join(cards)
    return (
        f'<div class="pipe-row">{body}</div>'
        f"<style>"
        f".pipe-row {{display:flex;align-items:center;gap:0px;margin:16px 0;}}"
        f".pipe-card {{"
        f" flex:1;text-align:center;"
        f" background:rgba(49,51,56,0.7);border:1px solid rgba(255,255,255,.12);"
        f" border-radius:10px;padding:12px 8px;min-width:0;}}"
        f".pipe-label {{font-size:.78rem;color:#9ca3af;font-weight:600;letter-spacing:.5px;}}"
        f".pipe-val {{font-size:.85rem;color:#e5e7eb;margin-top:4px;word-break:break-all;}}"
        f".pipe-arrow {{color:#6366f1;font-size:1.4rem;margin:0 2px;flex-shrink:0;}}"
        f"</style>"
    )


def show_pipeline(result):
    st.subheader("执行流水线")
    st.markdown(_pipeline_html(result), unsafe_allow_html=True)


def show_graph(result, kernel: FEKKernel):
    st.subheader("执行图（DAG）")
    # 为可视化重建产生该结果的执行图
    from fek import Task
    from fek.classifier import ComplexityClassifier
    from fek.compiler import GraphBuilder

    task = Task(id=result.task_id, prompt=result.prompt)
    graph = GraphBuilder().build(result.strategy, task)

    # 策略 1：graphviz Python 包 + 系统二进制
    try:
        import graphviz  # type: ignore

        src = graph.to_dot()
        # 注入暗黑主题样式
        styled = src.replace(
            'node [shape=box, style=rounded];',
            (
                "node [shape=box, style=rounded, fontname='sans-serif', "
                "color='#6366f1', fillcolor='#1e1e2e', fontcolor='#e5e7eb', "
                "penwidth=2];"
                "edge [color='#6366f1', penwidth=1.5, arrowsize=.8];"
                "bgcolor='#0f1117';"
                "rankdir=TB;"
            ),
        )
        st.graphviz_chart(styled, use_container_width=True)
        return
    except Exception:
        pass

    # 策略 2：Mermaid 渲染（Streamlit 原生支持）
    mermaid_src = graph.to_mermaid()
    try:
        # 尝试直接用 Streamlit 的 Mermaid 支持（部分版本可用）
        with st.container():
            st.components.v1.html(
                _mermaid_html(mermaid_src), height=max(160, len(graph.nodes) * 60)
            )
        return
    except Exception:
        pass

    # 策略 3：纯 HTML 节点-连线图（零依赖兜底）
    st.markdown(_html_dag(graph), unsafe_allow_html=True)


def _mermaid_html(mermaid_src: str) -> str:
    return f"""
<!DOCTYPE html><html><head>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head><body style="background:#0d1117;color:#e5e7eb;padding:12px;">
<div class="mermaid">{mermaid_src}</div>
<script>mermaid.initialize({{startOnLoad:true,theme:'dark',securityLevel:'loose'}});</script>
</body></html>"""


def _html_dag(graph) -> str:
    """零依赖的 HTML DAG 兜底渲染。"""
    nodes_html = []
    for nid, n in graph.nodes.items():
        label = node_zh_label(n.role, n.kind)
        nodes_html.append(f'<div id="n-{nid}" class="dag-node">{label}</div>')

    edges_html = []
    for nid, n in graph.nodes.items():
        for dep in n.depends_on:
            edges_html.append(
                f'<svg class="dag-edge" style="position:absolute;'
                f'pointer-events:none;z-index:0;">'
                f'<line id="e-{dep}-{nid}" data-from="#n-{dep}" data-to="#n-{nid}" '
                f'stroke="#6366f1" stroke-width="2" marker-end="url(#arrow)"/>'
                f"</svg>"
            )

    return (
        f'<div style="position:relative;padding:24px 16px;">'
        f'<svg width="0" height="0"><defs>'
        f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"'
        f' markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1"/>'
        f'</marker></defs></svg>'
        f'<div style="display:flex;flex-direction:column;gap:20px;align-items:center;'
        f' position:relative;z-index:1;">'
        + "\n".join(nodes_html)
        + "</div></div>"
        + "\n".join(edges_html)
        + "<style>"
        ".dag-node{display:inline-block;background:#1e1e2e;border:2px solid #6366f1;"
        " border-radius:10px;color:#e5e7eb;padding:10px 18px;font-size:.88rem;"
        " text-align:center;white-space:nowrap;}"
        "</style>"
    )


def show_nodes(result):
    st.subheader("节点结果")
    for nr in result.node_results:
        with st.expander(f"{node_zh_label(nr.role, nr.kind)}  ·  {nr.model}"):
            st.write(nr.content)
            st.caption(
                f"延迟={nr.latency_ms:.0f}ms · 成本=${nr.cost_usd:.5f} · 质量={nr.quality:.2f}"
            )


def show_telemetry(kernel: FEKKernel):
    st.sidebar.subheader("遥测（成本感知叙事）")
    st.sidebar.code(kernel.telemetry.summary() or "暂无运行记录")
    if kernel.telemetry.traces:
        try:
            import pandas as pd

            df = pd.DataFrame(kernel.telemetry.traces)
            # 中文列名映射
            display_df = df.rename(
                columns={
                    "strategy": "策略",
                    "latency_ms": "延迟(ms)",
                    "cost_usd": "成本($)",
                    "quality": "质量",
                }
            )[["策略", "延迟(ms)", "成本($)", "质量"]]
            # 策略列用中文标签
            display_df["策略"] = display_df["策略"].map(
                lambda s: getattr(Strategy(s), "zh", s) if s else ""
            )
            st.sidebar.dataframe(display_df, use_container_width=True, height=200)
        except ImportError:
            st.sidebar.caption("安装 pandas 可查看详细轨迹表：pip install pandas")


def main():
    st.set_page_config(page_title="FEK —— 融合执行内核", layout="wide")
    mode = os.getenv("FEK_MODE", "mock")
    st.title("⚡ FEK —— 融合执行内核")
    st.caption(
        f"自适应多模型执行内核 · 模式：**{mode}** · "
        "FEK 架构的 v0/v1 黑客松 Demo"
    )

    kernel = get_kernel()
    show_telemetry(kernel)

    tab_auto, tab_battle = st.tabs(["自动（系统决策）", "对战（三种策略全跑）"])

    with tab_auto:
        prompt = st.text_area(
            "输入一个任务",
            value="对比并辩论微服务与单体架构在高速成长型初创公司中的取舍，"
            "需考虑延迟、成本与团队结构。",
            height=120,
        )
        if st.button("运行 FEK", type="primary"):
            with st.spinner("FEK 正在思考…"):
                result = kernel.run(prompt)
            st.success(result.summary())
            st.markdown(f"**策略决策：** {kernel.policy.explain(result.complexity_score)}")
            show_pipeline(result)
            show_graph(result, kernel)
            show_nodes(result)
            st.subheader("最终输出")
            st.markdown(result.final_output)

    with tab_battle:
        bprompt = st.text_area(
            "输入一个困难任务以比较策略",
            value="为一款服务 100 万并发用户的实时协作白板设计架构。",
            height=120,
            key="battle_prompt",
        )
        if st.button("运行对战", type="primary"):
            with st.spinner("正在运行 单模型 / 多智能体 / 混合专家（MoA）…"):
                results = kernel.run_all_strategies(bprompt)
            cols = st.columns(3)
            for i, strat in enumerate([Strategy.SINGLE, Strategy.MULTI_AGENT, Strategy.MOA]):
                r = results[strat]
                with cols[i]:
                    st.markdown(f"### {strat.zh}")
                    st.metric("质量", f"{r.avg_quality:.2f}")
                    st.metric("延迟", f"{r.total_latency_ms:.0f} ms")
                    st.metric("成本", f"${r.total_cost_usd:.5f}")
                    st.metric("已融合", "是" if r.fused else "否")
            st.subheader("质量最高的答案")
            best = max(results.values(), key=lambda x: x.avg_quality)
            st.info(f"胜出：{best.strategy.zh}")
            st.markdown(best.final_output)


if __name__ == "__main__":
    main()
