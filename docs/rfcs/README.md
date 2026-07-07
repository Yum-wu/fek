# FEK RFC 流程（RFC-Driven Development）

> **规则：所有重大设计先写 RFC，再写代码。**  
> 代码量小但概念多，早立流程可避免术语/抽象再次漂移。



---

## 什么是 RFC

RFC（Request for Comments）= 一份**设计提案文档**，在写代码前描述：背景、问题、提案、备选、权衡、未来工作。评审合并后，代码才允许落地。

---

## 何时必须写 RFC

以下任一类改动，**必须**先开 RFC：

- 新增或修改**策略类型**（如加 DEBATE / REFLECTION）
- 新增、删除、合并**模块**（Task Profiler / Policy Engine / Graph Compiler / Compute Graph / Runtime / Fusion Engine / Evaluation / Telemetry）
- 修改 **Policy Engine / Compute Graph / Runtime** 的**公共接口**
- 改变**学习/奖励模型**
- 改变**项目定位或命名**
- 引入**新的外部依赖**（打破零依赖）

小 bug 修复、文档错别字、纯内部重构（不改公开接口）**不需要** RFC。

---

## 编号与文件

- 目录：`docs/rfcs/`
- 命名：`NNNN-slug.md`（4 位零填充序号，短横线 slug）
- 序号递增，不回收。
- 示例：`0009-task-profiling.md`、`0010-llm-judge.md`

---

## 状态机

| 状态           | 含义                 |
| ------------ | ------------------ |
| `Proposed`   | 已开 PR，等待评审         |
| `Accepted`   | 评审通过，可落地代码         |
| `Rejected`   | 评审否决，记录原因          |
| `Superseded` | 被更新的 RFC 取代（注明新编号） |

状态写在 RFC 顶部元数据。

---

## RFC 模板（每篇必须包含）

```markdown
# RFC NNNN · <标题>

- 状态：Proposed / Accepted / Rejected / Superseded
- 作者：<github 名>
- 日期：YYYY-MM-DD
- 关联：<相关 RFC / Issue>

## Background（背景）
## Problem（问题）
## Proposal（提案）
## Alternatives（备选方案）
## Tradeoffs（权衡）
## Future Work（未来工作）
```

---

## 流程

1. **开 RFC PR**：在 `docs/rfcs/` 新增 `NNNN-slug.md`，状态 `Proposed`。
2. **评审**：至少 1 名核心维护者 review；讨论在 PR 评论区。
3. **合并或否决**：合并 = `Accepted`；关闭 PR = `Rejected`（留记录）。
4. **实现**：`Accepted` 后才允许写对应代码；实现 PR 必须链接 RFC。
5. \*\* supersede\*\*：若提案被新 RFC 取代，旧 RFC 状态改 `Superseded` 并注明新编号。

---

## 当前 RFC 索引

| 编号   | 标题              | 状态       |
| ---- | --------------- | -------- |
| 0001 | Project Vision  | Accepted |
| 0002 | Execution Model | Accepted |
| 0003 | Policy Engine   | Accepted |
| 0004 | Compute Graph   | Accepted |
| 0005 | Runtime         | Accepted |
| 0006 | Fusion Engine   | Accepted |
| 0007 | Evaluation      | Accepted |
| 0008 | Roadmap         | Accepted |
| 0009 | Learning Optimizer | Accepted |
