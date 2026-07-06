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


def _check_graphviz_binary() -> bool:
    """快速检查 graphviz 系统 dot 二进制是否真正可用。"""
    try:
        import graphviz
        dot = graphviz.Digraph()
        dot.node("a", "test")
        dot.pipe(format="svg")
        return True
    except Exception:
        return False


def show_graph(result, kernel: FEKKernel):
    st.subheader("执行图（DAG）")
    # 为可视化重建产生该结果的执行图
    from fek import Task
    from fek.compiler import GraphBuilder

    task = Task(id=result.task_id, prompt=result.prompt)
    graph = GraphBuilder().build(result.strategy, task)

    node_count = len(graph.nodes)

    # ── 策略 1：graphviz（需 Python 包 + 系统(dot) 二进制都在）──
    if _check_graphviz_binary():
        try:
            import graphviz  # type: ignore

            src = graph.to_dot()
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
            st.graphviz_chart(styled, width="stretch")
            return
        except Exception:
            pass

    # ── 策略 2：Streamlit 原生 Mermaid（零依赖，官方支持）──
    mermaid_src = graph.to_mermaid()
    try:
        st.markdown(f"```mermaid\n{mermaid_src}\n```")
        return
    except Exception:
        pass

    # ── 策略 3：Flexbox 可视化（100% 可靠兜底）──
    st.markdown(_flex_dag(graph, result.strategy), unsafe_allow_html=True)


def _flex_dag(graph, strategy) -> str:
    """Flexbox DAG 兜底 —— 对单节点和多节点都给出有信息量的可视化。"""
    from fek.core.types import Strategy

    parts = []
    # 节点卡片
    for nid, n in graph.nodes.items():
        label = node_zh_label(n.role, n.kind)
        parts.append(f'<div class="fd-node">{label}</div>')

    # 连线箭头
    if len(graph.nodes) > 1:
        for nid, n in graph.nodes.items():
            for dep in n.depends_on:
                dep_label = node_zh_label(graph.nodes[dep].role, graph.nodes[dep].kind)
                parts.append(
                    f'<div class="fd-arrow">&#8594;</div>'
                    f'<div class="fd-edge">{dep_label} &#8594; {node_zh_label(n.role, n.kind)}</div>'
                )
    else:
        # 单节点时展示策略说明
        strat_desc = {
            Strategy.SINGLE: "单模型直接执行，无依赖节点",
            Strategy.MULTI_AGENT: "多角色协作流水线",
            Strategy.MOA: "并行多模型 + 融合",
        }
        desc = strat_desc.get(strategy, "执行图节点")
        parts.append(
            f'<div class="fd-info">'
            f'<span class="fd-info-icon">&#9432;</span>'
            f'{desc}'
            f'</div>'
        )

    return (
        '<div class="fd-wrap">'
        '<div class="fd-inner">'
        + "\n".join(parts)
        + "</div></div>"
        "<style>"
        ".fd-wrap{background:#0f1117;border:1px solid rgba(99,102,241,.25);"
        " border-radius:12px;padding:20px;margin:8px 0;}"
        ".fd-inner{display:flex;flex-direction:column;gap:10px;align-items:center;}"
        ".fd-node{background:#1e1b4b;border:2px solid #6366f1;border-radius:10px;"
        " color:#c7d2fe;padding:12px 24px;font-size:.92rem;font-weight:600;"
        " white-space:nowrap;text-align:center;}"
        ".fd-arrow{color:#6366f1;font-size:1.3rem;font-weight:bold;}"
        ".fd-edge{color:#9ca3af;font-size:.8rem;text-align:center;}"
        ".fd-info{display:flex;align-items:center;gap:6px;color:#9ca3af;"
        " font-size:.82rem;margin-top:4px;padding:8px 16px;background:rgba(99,102,241,.08);"
        " border-radius:8px;border:1px dashed rgba(99,102,241,.3);}"
        ".fd-info-icon{color:#6366f1;font-size:1rem;}"
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
                    "latency_ms": "延迟",
                    "cost_usd": "成本",
                    "quality": "质量",
                }
            )[["策略", "延迟", "成本", "质量"]]
            # 策略列用中文标签
            display_df["策略"] = display_df["策略"].map(
                lambda s: getattr(Strategy(s), "zh", s) if s else ""
            )
            # 数值格式化
            display_df["延迟"] = display_df["延迟"].map(lambda x: f"{x:.0f}ms")
            display_df["成本"] = display_df["成本"].map(lambda x: f"${x:.5f}")
            display_df["质量"] = display_df["质量"].map(lambda x: f"{x:.3f}")
            st.sidebar.dataframe(display_df, width=280, height=200)
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
