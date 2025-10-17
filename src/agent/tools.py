"""
LangGraph Agent 工具

定义 Agent 可以调用的工具（知识库检索、历史对话检索等）。
"""

import logging
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.services.llm_factory import create_embeddings
from src.services.milvus_service import milvus_service

logger = logging.getLogger(__name__)


class KnowledgeSearchInput(BaseModel):
    """知识库检索工具输入"""

    query: str = Field(description="要搜索的问题或关键词")
    top_k: int = Field(default=3, ge=1, le=10, description="返回结果数量")


class HistorySearchInput(BaseModel):
    """历史对话检索工具输入"""

    query: str = Field(description="要搜索的历史对话关键词")
    session_id: str = Field(description="会话ID")
    top_k: int = Field(default=2, ge=1, le=5, description="返回结果数量")


@tool("knowledge_search", args_schema=KnowledgeSearchInput, return_direct=False)
async def knowledge_search_tool(query: str, top_k: int = 3) -> str:
    """
    搜索网站知识库

    从 Milvus 向量数据库检索与查询相关的知识库文档。
    适用于回答关于产品、FAQ、政策等网站特定问题。

    Args:
        query: 用户问题或关键词
        top_k: 返回结果数量

    Returns:
        格式化的检索结果字符串
    """
    try:
        # 生成查询向量
        embeddings = create_embeddings()

        # 截断查询文本到512 tokens以内（查询通常不需要分块）
        from src.core.utils import truncate_text_to_tokens
        truncated_query = truncate_text_to_tokens(query, max_tokens=512)
        query_embedding = await embeddings.aembed_query(truncated_query)

        # 添加日志提示
        if len(query) != len(truncated_query):
            logger.warning(
                f"Query truncated from {len(query)} to {len(truncated_query)} chars "
                f"to fit 512 token limit"
            )

        # 检索知识库
        results = await milvus_service.search_knowledge(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        if not results:
            return "知识库中未找到相关信息。"

        # 格式化结果
        formatted_results = []
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            title = metadata.get("title", "未命名文档")
            formatted_results.append(
                f"[文档{i}] {title} (相似度: {result['score']:.2f})\n{result['text']}"
            )

        logger.info(f"🔍 Knowledge search: found {len(results)} results for '{query}'")
        return "\n\n".join(formatted_results)

    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        return f"知识库检索失败: {str(e)}"


@tool("history_search", args_schema=HistorySearchInput, return_direct=False)
async def history_search_tool(query: str, session_id: str, top_k: int = 2) -> str:
    """
    搜索历史对话记录

    从 Milvus 检索当前会话的历史对话，用于理解上下文。

    Args:
        query: 搜索关键词
        session_id: 会话ID
        top_k: 返回结果数量

    Returns:
        格式化的历史对话字符串
    """
    try:
        # 获取会话历史
        results = await milvus_service.search_history_by_session(
            session_id=session_id,
            limit=top_k,
        )

        if not results:
            return "未找到相关历史对话。"

        # 格式化结果
        formatted_results = []
        for result in results:
            role = "用户" if result["role"] == "user" else "助手"
            formatted_results.append(f"{role}: {result['text']}")

        logger.info(f"📜 History search: found {len(results)} messages for session {session_id}")
        return "\n".join(formatted_results)

    except Exception as e:
        logger.error(f"History search failed: {e}")
        return f"历史对话检索失败: {str(e)}"


# 工具列表（供 LangGraph 使用）
AGENT_TOOLS = [
    knowledge_search_tool,
    # history_search_tool,  # 可选：如果需要跨会话检索
]


async def search_knowledge_for_agent(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """
    供 Agent 节点直接调用的知识库检索函数

    不使用 @tool 装饰器，直接返回结构化数据。

    Args:
        query: 查询问题
        top_k: 返回结果数量

    Returns:
        检索结果列表
    """
    try:
        embeddings = create_embeddings()
        # 截断查询文本到512 tokens以内
        from src.core.utils import truncate_text_to_tokens
        truncated_query = truncate_text_to_tokens(query, max_tokens=512)
        query_embedding = await embeddings.aembed_query(truncated_query)

        # 添加日志提示
        if len(query) != len(truncated_query):
            logger.warning(f"Query truncated from {len(query)} to {len(truncated_query)} chars to fit 512 token limit")

        results = await milvus_service.search_knowledge(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        logger.info(f"🔍 Retrieved {len(results)} documents for: {query}")
        return results

    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        return []

