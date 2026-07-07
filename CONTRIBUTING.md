# 参与贡献 · Contributing to FEK

感谢你对 FEK（**Adaptive AI Execution Engine / 自适应 AI 执行引擎**）感兴趣！

## 开发流程：RFC 驱动（RFC-Driven Development）

FEK 采用 **RFC-Driven Development**。所有重大设计变更**必须先写 RFC，评审合并后再写代码**：

- 新增策略类型（如 `DEBATE` / `REFLECTION`）
- 新增或删除模块（如新增 Scheduler）
- 修改 Policy Engine / Compute Graph / Runtime 的公共接口
- 修改学习层 / 奖励模型
- 修改项目定位、命名（以 `docs/terminology.md` 为权威来源）
- 引入新的第三方依赖

**不需要 RFC 的情况**：bug 修复、文档错别字、不改公开接口的内部重构。

### 如何开 RFC

1. 在 `docs/rfcs/` 下新建 `NNNN-slug.md`（编号顺延，状态 `Proposed`）。
2. 按模板写：`Background / Problem / Proposal / Alternatives / Tradeoffs / Future Work`。
3. 开 PR，标签 `rfc`，等待评审合并（状态转 `Accepted`）。
4. RFC 合并后，再开实现 PR。

## Pull Request 规范

- PR 描述里填 RFC 勾选项；若改动属“重大设计”，**必须关联状态为 `Accepted` 的 RFC**。
- 保持 `fek/` 核心包**零第三方依赖**（mock 后端保证离线可跑）。
- 所有新代码带测试，`python -m unittest` 全绿才能合并。
- 代码注释 / 文档字符串 / 文档正文用**中文**；技术专有名词（DAG / MoA / SINGLE / Compute Graph 等）保留英文。

## 本地开发

```bash
# 跑全部测试（CI 同款）
python -m unittest discover -s tests -v
```

更多：RFC 流程见 `docs/rfcs/README.md`，项目原则见 `VISION.md`，命名规范见 `docs/terminology.md`。
