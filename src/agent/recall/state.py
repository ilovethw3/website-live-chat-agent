"""
召回Agent状态定义

RecallState定义了召回Agent在执行过程中的所有状态信息。
"""

from typing import TypedDict

from src.agent.recall.schema import RecallHit, RecallRequest, RecallResult


class RecallState(TypedDict):
    """
    召回Agent状态

    使用TypedDict定义状态结构，LangGraph会自动处理状态更新。

    Attributes:
        request: 召回请求（入口参数，整个流程不变）
        config: 召回配置（prepare节点设置，后续不变）
        start_time: 开始时间戳（prepare节点设置）
        hits: 召回命中结果列表（fanout产生，merge更新）
        result: 最终召回结果（output节点设置）
    """

    # 输入（不变）
    request: RecallRequest

    # 配置（prepare设置后不变）
    config: dict
    start_time: float

    # 中间结果（fanout/merge更新）
    hits: list[RecallHit]

    # 输出（output设置）
    result: RecallResult | None
