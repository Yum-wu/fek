"""LLM 后端实现。"""
from .backend import LLMBackend
from .mock import MockBackend
from .openai_backend import OpenAIBackend

__all__ = ["LLMBackend", "MockBackend", "OpenAIBackend"]


def from_env() -> LLMBackend:
    """工厂方法：根据 FEK_MODE 环境变量选择后端（默认 mock）。"""
    import os

    mode = os.getenv("FEK_MODE", "mock").lower()
    if mode == "openai":
        return OpenAIBackend(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )
    return MockBackend()
