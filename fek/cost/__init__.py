"""可选 tokenizer 成本估算（核心零依赖之外的可选增强）。

仅当真实模式（FEK_MODE=openai）且用户装了 tiktoken 时提供真实 token 计费，
使奖励函数的 cost 信号可信。未安装 tiktoken 时所有函数返回 None，调用方回退到固定估算。
"""

from __future__ import annotations

from .tokenizer import count_tokens, estimate_cost_usd

__all__ = ["count_tokens", "estimate_cost_usd"]
