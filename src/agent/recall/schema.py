"""
召回编排层数据模型

定义召回Agent的输入输出数据结构：
- RecallRequest: 召回请求
- RecallHit: 召回命中结果
- RecallResult: 召回结果汇总
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class RecallRequest:
    """召回请求"""
    query: str
    session_id: str
    trace_id: str
    user_profile: dict[str, Any] | None = None
    context: list[str] | None = None
    experiment_id: str | None = None
    top_k: int = 5


@dataclass
class RecallHit:
    """召回命中结果"""
    source: str
    score: float
    confidence: float
    reason: str
    content: str
    metadata: dict[str, Any]


@dataclass
class RecallResult:
    """召回结果汇总"""
    hits: list[RecallHit]
    latency_ms: float
    degraded: bool
    trace_id: str
    experiment_id: str | None = None
