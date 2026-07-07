"""真实 OpenAI 兼容后端（可选依赖）。

仅在 FEK_MODE=openai 时导入。使用 `openai` 包；若未安装，内核会抛出
清晰、可操作的错误提示，而不是崩溃。
"""

from __future__ import annotations

import os
import time

from ..core.types import Completion
from .backend import LLMBackend
from ..cost import estimate_cost_usd

# 每次调用固定估算（tiktoken 缺失时的回退，单位：美元/次）
_DEFAULT_PRICING = {
    "gpt-4o": 0.005,
    "gpt-4o-mini": 0.0002,
    "gpt-3.5-turbo": 0.0005,
}

# 每 1k token 真实单价（tiktoken 可用时启用真实计费，单位：美元/1k token）
_TOKEN_PRICING_PER_1K = {
    "gpt-4o": 0.005,
    "gpt-4o-mini": 0.00015,
    "gpt-3.5-turbo": 0.0005,
}


class OpenAIBackend(LLMBackend):
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str = "gpt-4o-mini"):
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "真实模式需要 `openai` 包，请执行：pip install openai"
            ) from e
        self.model = model
        self._client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"), base_url=base_url)
        self._pricing = _DEFAULT_PRICING.get(model, 0.0005)

    @property
    def name(self) -> str:
        return "openai"

    def complete(self, system: str, prompt: str, model: str | None = None) -> Completion:
        m = model or self.model
        t0 = time.time()
        resp = self._client.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        latency = (time.time() - t0) * 1000.0
        content = resp.choices[0].message.content or ""
        # 真实成本：tiktoken 可用时按 token 计费（cost 信号更可信）；
        # 否则回退每次调用固定估算（功能不退化）
        cost = estimate_cost_usd(prompt, content, m, _TOKEN_PRICING_PER_1K.get(m))
        if cost is None:
            cost = self._pricing
        return Completion(content=content, model=m, latency_ms=latency, cost_usd=cost)
