# FEK 文档导航（总入口）

> **FEK = Adaptive AI Compute Optimizer（自适应 AI 计算优化器）**。本页是所有文档的索引——按"你想做什么"挑入口。
> 新接触项目？从 [README.md](../README.md) 和 [VISION.md](../VISION.md) 开始。

---

## 🚀 想上手 / 跑起来
- [README.md](../README.md) — 项目门面：定位、Why FEK、30 秒看懂、Quick Demo、核心概念、架构、生态、路线图、诚实声明。
- [examples/](../examples/) — 命令行 Demo：`basic_demo.py` / `battle_demo.py` / `learning_demo.py`（零 API key，离线可跑）。
- [web/app.py](../web/app.py) — Streamlit 可视化界面（`streamlit run web/app.py`）。

## 🎯 想理解「FEK 是什么 / 为什么」
- [VISION.md](../VISION.md) — 新定位、第一性原理、非目标、设计原则。
- [architecture.md](architecture.md) — 架构总览、核心创新（约束感知·策略无关·可学习的策略优化闭环）、模块边界。
- [terminology.md](terminology.md) — 命名权威源（模块 / 术语 / 禁止用语）。

## 🏗️ 想深入技术
- [architecture.md](architecture.md) — 架构主文档（同上，含代码路径映射）。
- [learn-design.md](learn-design.md) — 学习层设计：bandit / 真实 token 成本 / 离线回测。

## 🧭 战略与路线
- [roadmap.md](roadmap.md) — Product（v1 / v2 / v3）与 Research（R1–R5）分离路线图。
- [migration-plan.md](migration-plan.md) — 可执行迁移清单（阶段 0–6；**阶段 6 = Pivot 代码落地**，待 RFC 合并后执行）。

## 🌐 生态与竞争
- [ecosystem/ai-infra-landscape.md](ecosystem/ai-infra-landscape.md) — 6 层 AI 基础设施生态图，FEK 属 **AI Compute Optimization Layer**。
- [competitive-analysis.md](competitive-analysis.md) — 10 个项目逐一对标（含 Claude Code / Hermes 重叠分析）。

## 📜 治理：RFC（先 RFC，后代码）
- [rfcs/README.md](rfcs/README.md) — RFC 流程、索引、状态。
- 关键 RFC：
  - **[0010](rfcs/0010-positioning-pivot.md)** positioning-pivot（Accepted，Supersedes 0001/0002）—— 战略定位重构。
  - **[0011](rfcs/0011-constraint-policy-optimizer.md)** constraint-policy-optimizer（Accepted，Supersedes 0003）—— 约束感知策略优化器。
  - **[0012](rfcs/0012-strategy-library.md)** strategy-library（Accepted）—— 可插拔策略库（MoA 降为普通策略）。
  - 0001–0009：早期 RFC（详见索引；0001/0002 已 Superseded）。

## 📦 历史文档（仅供参考，以新文档为准）
- [analysis.md](analysis.md) — 黑客松原始评估（已加历史横幅）。
- [reviews/architecture-review-2026.md](reviews/architecture-review-2026.md) — 早期架构评审（历史）。

---

*FEK 采用 **RFC 驱动开发**：所有重大设计先写 RFC、评审合并后再改代码。*
