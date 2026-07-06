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
        # 按策略汇总平均成本 / 延迟 / 质量
        lines = ["策略         次数  平均成本    平均延迟  平均质量"]
        for strat, ts in by_strategy.items():
            n = len(ts)
            avg_cost = sum(x["cost_usd"] for x in ts) / n
            avg_lat = sum(x["latency_ms"] for x in ts) / n
            avg_q = sum(x["quality"] for x in ts) / n
            lines.append(f"{strat:<12}{n:<4}{avg_cost:<11.5f}{avg_lat:<10.0f}{avg_q:.3f}")
        return "\n".join(lines)
