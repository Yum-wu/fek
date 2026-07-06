# 🤝 如何参与贡献

感谢你对 **FEK（Fusion Execution Kernel）** 感兴趣！这是一个黑客松级、面向开源社区的自适应执行内核。无论你是来修 bug、加功能，还是提建议，都欢迎。

## 🧰 本地开发环境

```bash
# 1. Fork 并克隆你的副本
git clone https://github.com/<你的用户名>/fek.git
cd fek

# 2. 创建虚拟环境（推荐）
python -m venv .venv && source .venv/bin/activate

# 3. 以可编辑模式安装（核心层零第三方依赖）
pip install -e .

# 4. 跑测试，确认环境正常
python -m unittest discover -s tests -v
```

> 核心内核（`fek/`）仅依赖 Python 标准库，`mock` 模式下**无需任何 API key** 即可运行。
> 仅在需要 Web 界面或真实 LLM 时才安装 `streamlit` / `openai`。

## ✅ 提交前检查清单

- [ ] 新代码在 `mock` 模式下可运行（不依赖外部 API）
- [ ] `python -m unittest discover -s tests -v` 全部通过
- [ ] 新增功能**同步补充测试**
- [ ] 中文注释 / 文档字符串（与现有代码风格一致）
- [ ] 改动在 `docs/analysis.md` 或 README 中有对应说明（如涉及架构）

## 🎯 好的起步任务（good first issue）

- 实现 `telemetry.learn()`：基于历史轨迹学习策略偏移
- 接入**真实反思裁判**：用 LLM 替代当前的启发式质量评分
- 新增策略类型（如 `TREE_OF_THOUGHT`、`SELF_CONSISTENCY`）
- 给 Web 界面加策略选择的实时解释面板

## 🔀 PR 流程

1. 从 `main` 切出特性分支：`git checkout -b feat/your-feature`
2. 提交小而聚焦的改动，信息用中文或英文均可，但要说明**为什么**
3. 推送并发起 Pull Request，描述：解决了什么问题 / 怎么验证 / 关联 Issue
4. CI 会自动在 Python 3.10–3.13 上跑测试，请确保所有任务变绿

## 💬 行为准则

参与本项目的所有人都需要遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

---

再次感谢你的参与 —— FEK 的价值在于社区一起把它从 Demo 推向真正的 v2/v3/v4。
