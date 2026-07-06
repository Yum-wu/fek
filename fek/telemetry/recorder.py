"""遥测与学习层。

记录每一次执行的轨迹（成本 / 延迟 / 质量 / 策略），使 Demo 能展示
"成本感知"的推理叙事，也便于未来的策略引擎从中学习。轨迹保存在内存中，
并可选追加写入 JSONL 文件。
"""

from __future__ import annotations

import json
import time
from typing import List, Optional

from ..core.types import ExecutionResult


class TelemetryRecorder:
    def __init__(self, log_path: Optional[str] = None):
        self.traces: List[dict] = []
        self.log_path = log_path

    def record(self, result: ExecutionResult) -> dict:
        trace = {
            "ts": time.time(),
            "task_id": result.task_id,
            "strategy": result.strategy.value,
            "complexity": result.complexity.value,
            "complexity_score": round(result.complexity_score, 3),
            "latency_ms": round(result.total_latency_ms, 1),
            "cost_usd": round(result.total_cost_usd, 5),
            "quality": round(result.avg_quality, 3),
            "nodes": len(result.node_results),
        }
        self.traces.append(trace)
        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(trace) + "\n")
        return trace

    def summary(self) -> str:
        if not self.traces:
            return "暂无轨迹记录。"
        by_strategy: dict[str, List[dict]] = {}
        for t in self.traces:
            by_strategy.setdefault(t["strategy"], []).append(t)

        # ---- CJK 宽度感知对齐工具 ----
        # 中文字符在终端占 2 列显示宽度，ASCII 占 1 列。
        # 普通 str.format() 只按字符数填充，导致中英文混排错位。

        @staticmethod
        def _dw(s: str) -> int:
            """计算字符串的终端显示宽度（CJK=2, ASCII=1）。"""
            w = 0
            for ch in s:
                w += 2 if ord(ch) > 0x3000 else 1
            return w

        @staticmethod
        def _pad(s: str, target_dw: int) -> str:
            """用空格将 s 填充到目标显示宽度。"""
            return s + " " * max(0, target_dw - _dw(s))

        # 定义每列的目标显示宽度（与截图终端一致）
        col_strat = 12   # 策略名列
        col_count = 6    # 次数列
        col_cost = 12    # 平均成本列
        col_lat = 10     # 平均延迟列
        col_qual = 8     # 平均质量列

        header = (
            _pad("策略", col_strat)
            + _pad("次数", col_count)
            + _pad("平均成本", col_cost)
            + _pad("平均延迟", col_lat)
            + _pad("平均质量", col_qual)
        )
        lines = [header]
        for strat, ts in by_strategy.items():
            n = len(ts)
            avg_cost = sum(x["cost_usd"] for x in ts) / n
            avg_lat = sum(x["latency_ms"] for x in ts) / n
            avg_q = sum(x["quality"] for x in ts) / n
            line = (
                _pad(strat, col_strat)
                + _pad(str(n), col_count)
                + _pad(f"{avg_cost:.5f}", col_cost)
                + _pad(f"{avg_lat:.0f}", col_lat)
                + _pad(f"{avg_q:.3f}", col_qual)
            )
            lines.append(line)
        return "\n".join(lines)
