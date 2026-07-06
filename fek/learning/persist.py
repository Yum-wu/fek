"""学习层持久化 —— 把 bandit 参数存到本地 JSON，使学习可跨运行累积。

这是 FEK "self-improving" 叙事的关键：训练一次，到处可用；重启后偏好不丢失。
文件格式简单、人类可读，便于调试与演示时展示"学到了什么"。
"""

from __future__ import annotations

import json
import os
from typing import Optional


def save(state: dict, path: str) -> None:
    """把学习状态字典写入 JSON 文件（父目录不存在则自动创建）。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def load(path: str) -> Optional[dict]:
    """读取学习状态；文件不存在或损坏时返回 None（调用方应回退到冷启动）。"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def reset(path: str) -> None:
    """删除学习状态文件，回到冷启动。"""
    if os.path.exists(path):
        os.remove(path)
