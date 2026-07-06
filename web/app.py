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


@st.cache_resource
def get_kernel() -> FEKKernel:
    # 通过 cache_resource，遥测在多次重跑之间持续累积
    return FEKKernel(telemetry_log="fek_traces.jsonl")


def show_pipeline(result):
    st.subheader("执行流水线")
    stages = [
        ("任务", result.prompt[:40] + ("…" if len(result.prompt) > 40 else "")),
        ("复杂度", f"{result.complexity.value} ({result.complexity_score:.2f})"),
        ("策略", result.strategy.value),
        ("执行图", f"{len(result.node_results)} 个节点"),
        ("输出", "已融合" if result.fused else "单模型"),
    ]
    cols = st.columns(len(stages))
    for i, (label, val) in enumerate(stages):
        with cols[i]:
            st.markdown(f"**{label}**")
            st.info(val)
            if i < len(stages) - 1:
                st.caption("↓")


def show_graph(result, kernel: FEKKernel):
    st.subheader("执行图（DAG）")
    # 为可视化重建产生该结果的执行图
    from fek import Task
    from fek.classifier import ComplexityClassifier
    from fek.compiler import GraphBuilder

    task = Task(id=result.task_id, prompt=result.prompt)
    graph = GraphBuilder().build(result.strategy, task)
    try:
        import graphviz  # type: ignore

        st.graphviz_chart(graph.to_dot())
    except Exception:
        st.code(graph.to_mermaid(), language="mermaid")
        st.caption("安装 `graphviz` 可获得可交互图形：pip install graphviz")


def show_nodes(result):
    st.subheader("节点结果")
    for nr in result.node_results:
        with st.expander(f"{nr.role}  ·  {nr.kind}  ·  {nr.model}"):
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
            st.sidebar.dataframe(df[["strategy", "latency_ms", "cost_usd", "quality"]], height=200)
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
            with st.spinner("正在运行 SINGLE / MULTI_AGENT / MOA…"):
                results = kernel.run_all_strategies(bprompt)
            cols = st.columns(3)
            for i, strat in enumerate([Strategy.SINGLE, Strategy.MULTI_AGENT, Strategy.MOA]):
                r = results[strat]
                with cols[i]:
                    st.markdown(f"### {strat.value}")
                    st.metric("质量", f"{r.avg_quality:.2f}")
                    st.metric("延迟", f"{r.total_latency_ms:.0f} ms")
                    st.metric("成本", f"${r.total_cost_usd:.5f}")
                    st.metric("已融合", "是" if r.fused else "否")
            st.subheader("质量最高的答案")
            best = max(results.values(), key=lambda x: x.avg_quality)
            st.info(f"胜出：{best.strategy.value}")
            st.markdown(best.final_output)


if __name__ == "__main__":
    main()
