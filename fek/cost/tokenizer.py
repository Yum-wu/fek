"""真实 token 成本估算 —— 懒加载 tiktoken，缺失则优雅降级。

FEK 核心保持零依赖：本模块**不在模块顶层**导入 tiktoken，只在函数体内按需导入，
因此即使环境没有 tiktoken，import ``fek.cost`` 也不会失败。
"""

from __future__ import annotations


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int | None:
    """返回文本的 token 数。

    tiktoken 未安装，或模型名无法映射到已知编码器时，返回 ``None``（调用方回退）。
    """
    try:
        import tiktoken
    except ImportError:
        return None
    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def estimate_cost_usd(
    prompt: str,
    completion: str,
    model: str = "gpt-3.5-turbo",
    price_per_1k: float | None = None,
) -> float | None:
    """按 token 估算一次调用的美元成本。

    - ``price_per_1k`` 为每 1k token 的美元单价；为 ``None`` 时返回 ``None``
      （调用方应回退到固定估算）。
    - tiktoken 缺失时返回 ``None``。
    """
    if price_per_1k is None:
        return None
    pt = count_tokens(prompt, model) or 0
    ct = count_tokens(completion, model) or 0
    return (pt + ct) / 1000.0 * price_per_1k
