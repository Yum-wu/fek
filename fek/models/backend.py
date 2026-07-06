"""LLM 后端抽象层。

FEK 对具体模型保持中立。一个后端只需实现 `complete` 方法。这样内核可以
完全离线运行（MockBackend），用于黑客松演示；也可以切换到真实模型
（OpenAIBackend），而无需改动其他任何代码。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..core.types import Completion


class LLMBackend(ABC):
    @abstractmethod
    def complete(self, system: str, prompt: str, model: str = "default") -> Completion:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...
