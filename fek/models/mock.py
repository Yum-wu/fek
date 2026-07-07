"""离线 Mock 后端。

在**完全不发网络请求**的前提下，生成可信、且与角色相关的回答，让评委
无需任何 API key 就能跑通整个 Demo。延迟与成本均为模拟值，目的是让
"成本感知"的遥测叙事（MoA = 质量更高但成本/延迟也更高）在演示中真实可见。
"""

from __future__ import annotations

import hashlib
import time

from ..core.types import Completion
from .backend import LLMBackend

# 每个模拟模型的定价（每次调用美元）与延迟（毫秒）
_MODEL_PROFILE = {
    "gpt-fast": {"cost": 0.00010, "latency": 70},
    "gpt-smart": {"cost": 0.00090, "latency": 180},
    "claude-x": {"cost": 0.00140, "latency": 220},
    # 本地模型：零成本、低延迟，用于满足隐私=local_only 约束的离线演示
    "local-model": {"cost": 0.0, "latency": 60},
}

# 不同角色对应的回答模板
_ROLE_TEMPLATES = {
    "planner": "计划：将需求拆解为步骤。(1) 澄清目标；(2) 列出方法；(3) 标注风险。",
    "executor": "方案：围绕核心诉求，给出具体步骤与推理。",
    "critic": "批判：指出遗漏、边界情况，以及一条改进建议。",
    "synthesizer": "综合：将计划与解答合成为一份连贯的答案。",
    "solver": "回答：直接、结构化地回答请求。",
}


class MockBackend(LLMBackend):
    def __init__(self, seed_models: tuple[str, ...] = ("gpt-fast", "gpt-smart", "claude-x", "local-model")):
        self.models = list(seed_models)

    @property
    def name(self) -> str:
        return "mock"

    def _deterministic_jitter(self, text: str, span: float) -> float:
        # 基于文本哈希生成确定性抖动，保证 mock 结果稳定可复现
        h = hashlib.sha256(text.encode()).hexdigest()
        return (int(h[:8], 16) % 1000) / 1000.0 * span

    def complete(self, system: str, prompt: str, model: str = "gpt-fast") -> Completion:
        profile = _MODEL_PROFILE.get(model, _MODEL_PROFILE["gpt-fast"])
        # 模拟模型调用延迟
        time.sleep(profile["latency"] / 1000.0)

        # 根据 system 提示中的角色关键词，选定回答模板
        role = "solver"
        low = system.lower()
        if "planner" in low:
            role = "planner"
        elif "critic" in low:
            role = "critic"
        elif "synthesizer" in low or "synthesis" in low:
            role = "synthesizer"
        elif "executor" in low:
            role = "executor"

        base = _ROLE_TEMPLATES.get(role, _ROLE_TEMPLATES["solver"])
        # 让回答回显用户任务，使其看起来"理解了任务"
        snippet = prompt.strip().replace("\n", " ")[:120]
        content = f"[{model}] {base}\n\n任务上下文：\"{snippet}...\""
        # 加入微小确定性差异，使不同模型的输出有所区分
        jitter = self._deterministic_jitter(content, 1.0)
        content += f"\n(置信度标记：{jitter:.2f})"
        return Completion(content=content, model=model, latency_ms=profile["latency"], cost_usd=profile["cost"])
