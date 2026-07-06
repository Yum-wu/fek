# RFC 0004 · Compute Graph

- 状态：Accepted
- 作者：Yum-wu
- 日期：2026-07-07
- 关联：0002-execution-model, 0005-runtime, docs/terminology.md

## Background

当前 `core/graph.py` 定义 `ExecutionGraph`（DAG：节点 + 依赖）。Graph Compiler（`compiler/builder.py`）把 (Strategy, Task) 编译成图。运行时拓扑执行。

## Problem

1. **命名冲突**：`ExecutionGraph` 与"运行时执行"混淆。静态计划 vs 执行记录应是不同概念。
2. 缺少对"Compute Graph 是纯数据结构"的明确约束（不应含执行逻辑）。

## Proposal

- 重命名 `ExecutionGraph` → **`ComputeGraph`**（纯数据结构：nodes + edges + `topological_order()`）。
- 引入 **`Execution Trace`** 术语：Runtime 执行后产生的记录（节点结果 + 时序），与 Compute Graph 区分。
- Compute Graph **不含执行逻辑**；执行在 Runtime。
- 节点含：`role`、`kind`、`depends_on`。`node_zh_label()` 提供中文标签（见 web 可视化）。

## Alternatives

- **保留 ExecutionGraph**：否决——与 Execution Trace 混淆。
- **叫 Plan / DAG**：DAG 是实现细节不是领域词；Plan 偏 Agent Framework 语境；Compute Graph 最准。

## Tradeoffs

- 重命名影响 import 面广（core/graph、compiler、runtime、__init__），需随迁移计划单 PR 执行，全量测试通过。
- 不改运行时行为，纯重命名 + 注释。

## Future Work

- 图变异 / 角色自演化（R1 研究）：Compute Graph 形状从轨迹中演化，而非固定三模板。
- 分支/汇聚原语（branching）支持条件执行。
