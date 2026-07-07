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
    st.html(_pipeline_html(result))


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
    if node_count == 0:
        st.caption("⚠️ 执行图为空（无节点），跳过渲染")
        return

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

    # ── 策略 2：纯 HTML/CSS 可视化（零依赖，100% 可靠）──
    st.html(_visual_dag(graph, result.strategy))


def _visual_dag(graph, strategy) -> str:
    """零依赖的纯 HTML/CSS DAG 可视化 —— 对单/多节点都给出漂亮的图形。"""
    from fek.core.types import Strategy

    nodes_list = list(graph.nodes.items())
    n_count = len(nodes_list)

    # ── 节点卡片 HTML ──
    node_cards = []
    for nid, n in nodes_list:
        label = node_zh_label(n.role, n.kind)
        node_cards.append(
            f'<div class="vd-node" id="vd-{nid}">'
            f'<div class="vd-node-icon">&#9881;</div>'
            f'<div class="vd-node-label">{label}</div>'
            f'<div class="vd-node-kind">{n.kind}</div>'
            f"</div>"
        )

    # ── 连线（SVG 绝对定位在容器内）──
    svg_lines = []
    if n_count > 1:
        for nid, n in nodes_list:
            for dep in n.depends_on:
                svg_lines.append(
                    f'<line class="vd-edge" data-from="#vd-{dep}" data-to="#vd-{nid}"/>'
                )

    # ── 单节点时的说明文字 ──
    info_html = ""
    if n_count == 1:
        strat_info = {
            Strategy.SINGLE: ("单模型直接执行", "一个 LLM 调用完成全部任务"),
            Strategy.MULTI_AGENT: ("多角色协作流水线", "规划 → 执行 → 批判 → 综合"),
            Strategy.MOA: ("并行多模型融合", "多个模型并行推理 + 融合层综合"),
        }
        title, desc = strat_info.get(strategy, ("执行图", ""))
        info_html = (
            f'<div class="vd-info">'
            f'<div class="vd-info-title">{title}</div>'
            f'<div class="vd-info-desc">{desc}</div>'
            f"</div>"
        )
        node_html = f'<div class="vd-single-center">{"".join(node_cards)}{info_html}</div>'
    else:
        node_html = '<div class="vd-multi-col">' + "".join(node_cards) + "</div>"

    return (
        '<div class="vd-container">'
        # SVG 箭头定义
        + '<svg class="vd-svg-defs" width="0" height="0">'
        + '<defs>'
        + '<marker id="vd-arrow" viewBox="0 0 10 10" refX="8" refY="5"'
        + ' markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        + '<path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1"/>'
        + "</marker>"
        + "</defs></svg>"
        # 节点区域
        + node_html
        # 多节点的连接箭头
        + (f'<div class="vd-edges">{"".join(svg_lines)}</div>' if n_count > 1 else "")
        + "</div>"
        # 样式
        + "<style>"
        ".vd-container{position:relative;background:#0f1117;border-radius:12px;"
        " border:1px solid rgba(99,102,241,.25);padding:28px 20px;margin:10px 0;}"
        # 节点卡片
        ".vd-node{background:linear-gradient(135deg,#1e1b4b,#1a1744);"
        " border:2px solid #6366f1;border-radius:12px;padding:16px 24px;"
        " display:flex;flex-direction:column;align-items:center;gap:6px;"
        " min-width:140px;transition:transform .15s ease;}"
        ".vd-node:hover{transform:translateY(-2px);border-color:#818cf8;}"
        ".vd-node-icon{font-size:1.4rem;color:#818cf8;}"
        ".vd-node-label{font-size:.92rem;font-weight:700;color:#e5e7eb;white-space:nowrap;}"
        ".vd-node-kind{font-size:.72rem;color:#6366f1;text-transform:uppercase;"
        " letter-spacing:1.5px;font-weight:600;margin-top:2px;}"
        # 单节点居中布局
        ".vd-single-center{display:flex;flex-direction:column;align-items:center;gap:18px;}"
        # 信息框
        ".vd-info{display:flex;flex-direction:column;align-items:center;gap:4px;"
        " padding:12px 24px;background:rgba(99,102,241,.08);border-radius:10px;"
        " border:1px dashed rgba(99,102,241,.35);max-width:320px;text-align:center;}"
        ".vd-info-title{font-size:.9rem;font-weight:700;color:#a5b4fc;}"
        ".vd-info-desc{font-size:.78rem;color:#9ca3af;line-height:1.45;}"
        # 多节点横向排列
        ".vd-multi-col{display:flex;justify-content:center;align-items:flex-start;"
        " gap:20px;flex-wrap:wrap;}"
        # SVG 连线
        ".vd-edges{position:absolute;top:0;left:0;width:100%;height:100%;"
        " pointer-events:none;z-index:0;overflow:hidden;}"
        ".vd-edge{stroke:#6366f1;stroke-width:2;marker-end:url(#vd-arrow);"
        " opacity:.6;}"
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


def _show_result_summary(result):
    """将 result.summary() 的信息拆分为格式化的指标行，替代原始字符串。"""
    cols = st.columns(5, gap="small")
    with cols[0]:
        st.metric("策略", result.strategy.zh)
    with cols[1]:
        st.metric("复杂度", f"{result.complexity.zh} ({result.complexity_score:.2f})")
    with cols[2]:
        st.metric("节点数", str(len(result.node_results)))
    with cols[3]:
        st.metric(
            "延迟 / 成本",
            f"{result.total_latency_ms:.0f}ms / ${result.total_cost_usd:.5f}",
        )
    with cols[4]:
        fused = "✅" if result.fused else "—"
        st.metric(
            "质量",
            f"{result.avg_quality:.2f}",
            delta=f"融合 {fused}",
            delta_color="normal" if result.fused else "off",
        )


def main():
    st.set_page_config(page_title="FEK —— 自适应 AI 执行引擎", layout="wide")
    mode = os.getenv("FEK_MODE", "mock")
    st.title("⚡ FEK —— 自适应 AI 执行引擎")
    st.caption(
        f"自适应 AI 执行引擎 · 模式：**{mode}** · "
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
            # 用指标行替代原始 summary 字符串
            _show_result_summary(result)
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
