# RFC 0006 · Fusion Engine

- 状态：Accepted
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：0002-execution-model, 0005-runtime

## Background

`fusion/moa.py` 的 `fuse()` 把多个节点输出聚合成一个答案（当前用确定性结构化合并）。"Fusion" 也是 FEK 名字的来源——但只是众多策略之一的子组件。

## Problem

1. **叙事错位**：项目名曾叫 "Fusion Execution Kernel"，暗示 Fusion 是全局核心；实际它只是 MoA/MULTI_AGENT 策略下的聚合器。
2. 融合策略单一（结构化合并），未体现 MoA 的"aggregator 综合"。

## Proposal

- 明确定位 Fusion Engine 为 **Runtime 的子组件**，仅在多输出策略（MOA / MULTI_AGENT）下调用。
- **接口**：`fuse(outputs: list[NodeOutput]) -> FusedOutput`。
- 当前默认：确定性结构化合并（可解释、零依赖）。
- 未来：可插拔 aggregator（LLM 融合 / 投票 / 加权），作为可选策略。

## Alternatives

- **把 Fusion 提为全局核心**：否决——违背"按任务选策略"定位，FEK 不总是融合。
- **每策略各写融合**：重复，集中到 Fusion Engine 更清晰。

## Tradeoffs

- 默认结构化合并牺牲了一些 MoA 的"智能感"，但保证可解释、零依赖、可演示；LLM 融合留作可选。

## Future Work

- LLM aggregator 作为可选后端（需真实 LLM）。
- 多维度融合（按正确性/完整性分别加权）。
