"""
LangGraph Agent 条件边

定义 Agent 工作流中的条件判断逻辑。
"""

import logging

from src.agent.main.state import AgentState

logger = logging.getLogger(__name__)


def should_retrieve(state: AgentState) -> str:
    """
    条件边：判断是否需要检索知识库

    Args:
        state: 当前 Agent 状态

    Returns:
        下一个节点名称: "retrieve" 或 "llm"
    """
    next_step = state.get("next_step", "direct")

    if next_step == "retrieve":
        logger.debug("🔀 Conditional edge: routing to retrieve node")
        return "retrieve"
    else:
        logger.debug("🔀 Conditional edge: routing to llm node (direct)")
        return "llm"


def should_continue(state: AgentState) -> str:
    """
    条件边：判断是否继续执行或结束

    可用于：
    - 检查是否有错误
    - 检查置信度是否需要人工介入
    - 检查是否需要工具调用

    Args:
        state: 当前 Agent 状态

    Returns:
        "END" 表示结束，否则返回下一个节点名称
    """
    # 检查是否有错误
    if state.get("error"):
        logger.warning("⚠️ Error detected, ending workflow")
        return "END"

    # 检查置信度（可选：低置信度时人工介入）
    confidence = state.get("confidence_score")
    if confidence is not None and confidence < 0.5:
        logger.warning(f"⚠️ Low confidence ({confidence:.2f}), but continuing (no human review)")
        # 未来可以在这里添加人工介入节点
        # return "human_review"

    # 正常结束
    logger.debug("✅ Workflow completed successfully")
    return "END"

