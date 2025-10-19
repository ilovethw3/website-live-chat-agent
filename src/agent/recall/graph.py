"""
召回Agent LangGraph子图

组装召回Agent的完整工作流，包括：
- prepare: 处理请求，加载配置
- fanout: 并行调用召回源
- merge: 汇总、排序、去重
- fallback: 降级处理
- output: 组装RecallResult
"""

import logging

from langgraph.graph import StateGraph

from src.agent.recall.nodes import (
    fallback_node,
    fanout_node,
    merge_node,
    output_node,
    prepare_node,
)
from src.agent.recall.schema import RecallRequest, RecallResult
from src.agent.recall.state import RecallState

logger = logging.getLogger(__name__)


def create_recall_graph() -> StateGraph:
    """
    创建召回Agent LangGraph子图

    Returns:
        编译后的召回Agent图
    """
    # 创建状态图
    workflow = StateGraph(RecallState)

    # 添加节点
    workflow.add_node("prepare", prepare_node)
    workflow.add_node("fanout", fanout_node)
    workflow.add_node("merge", merge_node)
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("output", output_node)

    # 设置入口点
    workflow.set_entry_point("prepare")

    # 添加边
    workflow.add_edge("prepare", "fanout")
    workflow.add_edge("fanout", "merge")
    workflow.add_edge("merge", "fallback")
    workflow.add_edge("fallback", "output")

    # 编译图
    recall_agent = workflow.compile()

    logger.info("Recall agent graph created successfully")

    return recall_agent


# 创建全局召回Agent实例
recall_agent = create_recall_graph()


async def invoke_recall_agent(request: RecallRequest) -> RecallResult:
    """
    调用召回Agent的便捷接口

    Args:
        request: 召回请求

    Returns:
        召回结果
    """
    try:
        # 构建初始状态
        initial_state = {
            "request": request,
        }

        # 调用召回Agent
        result = await recall_agent.ainvoke(initial_state)

        # 返回召回结果
        return result["result"]

    except Exception as e:
        logger.error(f"Recall agent invocation failed: {e}")

        # 返回错误结果
        return RecallResult(
            hits=[],
            latency_ms=0.0,
            degraded=True,
            trace_id=request.trace_id,
            experiment_id=request.experiment_id,
        )
