# RFC 0005 · Runtime

- 状态：Accepted
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：0004-compute-graph, 0006-fusion-engine, 0007-evaluation

## Background

`runtime/executor.py` 拓扑序执行 Compute Graph，调用 `LLMBackend`，在 MoA/MULTI_AGENT 下调用 Fusion Engine，并产出 `ExecutionResult`（节点结果 + 最终输出 + 融合标记）。

## Problem

1. Runtime 当前耦合了 Fusion 调用与 Evaluation 调用，边界尚可更清晰。
2. 缺"Execution Trace"作为一等概念（目前混在 ExecutionResult 里）。
3. 并行执行已支持（拓扑），但重试/超时未定义。

## Proposal

- **接口**：`execute(graph: ComputeGraph, backend: LLMBackend) -> ExecutionResult`。
- Runtime 内部在合适策略下调 Fusion Engine（多输出聚合）与 Evaluation（质量分）。
- 明确 `ExecutionResult` 包含 `Execution Trace`（节点级时序/成本/延迟），供 Telemetry 消费。
- 边界：Runtime 负责"跑图"；Fusion/Evaluation 是它调用的子组件。

## Alternatives

- **把 Fusion/Evaluation 提出 Runtime 作为独立调用**：增加编排复杂度，当前不值，保留 Runtime 内调用。
- **引入 Worker 池**：当前任务规模不需要；列入未来（分布式执行研究）。

## Tradeoffs

- 耦合 Fusion/Evaluation 简化调用，但模块边界靠约定维持；靠文档（docs/architecture.md）保证。

## Future Work

- 重试/超时/降级策略。
- R2 自主内核：Runtime 支持动态子任务注入。
- 分布式执行（仅研究，与零依赖冲突）。
