"""
LangGraph StateGraph 构建

组装所有节点和边，构建完整的 Agent 工作流。
"""

import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agent.edges import should_continue, should_retrieve
from src.agent.nodes import call_llm_node, retrieve_node, router_node
from src.agent.state import AgentState
from src.core.config import settings

logger = logging.getLogger(__name__)


def create_agent_graph() -> StateGraph:
    """
    创建 LangGraph Agent 工作流

    工作流程：
    1. START → router → 判断是否需要检索
    2. 需要检索 → retrieve → llm → END
    3. 不需要检索 → llm → END

    Returns:
        编译后的 LangGraph App
    """
    logger.info("🔧 Building LangGraph StateGraph...")

    # 创建 StateGraph
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("router", router_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("llm", call_llm_node)

    # 设置入口点
    workflow.set_entry_point("router")

    # 添加条件边: router → retrieve 或 llm
    workflow.add_conditional_edges(
        "router",
        should_retrieve,
        {
            "retrieve": "retrieve",  # 需要检索 → 检索节点
            "llm": "llm"            # 不需要检索 → 直接 LLM
        }
    )

    # 添加边: retrieve → llm
    workflow.add_edge("retrieve", "llm")

    # 添加条件边: llm → END（可扩展为人工介入）
    workflow.add_conditional_edges(
        "llm",
        should_continue,
        {
            "END": END
        }
    )

    logger.info("✅ StateGraph built successfully")
    return workflow


def compile_agent_graph() -> any:
    """
    编译 Agent Graph

    根据配置选择 Checkpointer：
    - memory: MemorySaver（开发/测试）
    - redis: RedisSaver（生产环境）

    Returns:
        编译后的 LangGraph App
    """
    workflow = create_agent_graph()

    # 选择 Checkpointer
    if settings.langgraph_checkpointer == "memory":
        logger.info("📝 Using MemorySaver for checkpointing")
        checkpointer = MemorySaver()
    elif settings.langgraph_checkpointer == "redis":
        logger.info("📝 Using RedisSaver for checkpointing")
        try:
            import redis
            from langgraph.checkpoint.redis import RedisSaver

            redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password if settings.redis_password else None,
                db=settings.redis_db,
                decode_responses=False,  # RedisSaver 需要 bytes
            )

            checkpointer = RedisSaver(redis_client)
        except ImportError:
            logger.warning("⚠️ langgraph-checkpoint-redis not installed, falling back to MemorySaver")
            checkpointer = MemorySaver()
        except Exception as e:
            logger.error(f"❌ Failed to create RedisSaver: {e}, falling back to MemorySaver")
            checkpointer = MemorySaver()
    else:
        logger.warning(f"⚠️ Unknown checkpointer: {settings.langgraph_checkpointer}, using MemorySaver")
        checkpointer = MemorySaver()

    # 编译
    app = workflow.compile(checkpointer=checkpointer)

    logger.info("✅ LangGraph App compiled successfully")
    return app


# 全局 Agent App 实例（延迟初始化）
_agent_app = None


def get_agent_app() -> any:
    """
    获取 Agent App 单例

    Returns:
        编译后的 LangGraph App
    """
    global _agent_app
    if _agent_app is None:
        _agent_app = compile_agent_graph()
    return _agent_app


async def run_agent(
    user_message: str,
    session_id: str,
    chat_history: list | None = None
) -> dict:
    """
    执行 Agent 推理

    Args:
        user_message: 用户消息
        session_id: 会话ID（用于 Checkpointer）
        chat_history: 历史对话（可选，如果使用 Checkpointer 则自动加载）

    Returns:
        Agent 响应和状态
    """
    from langchain_core.messages import HumanMessage

    app = get_agent_app()

    # 构建初始状态
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": session_id,
        "next_step": None,
        "error": None,
        "confidence_score": None,
    }

    # 配置（包含 session_id 用于 Checkpointer）
    config = {"configurable": {"thread_id": session_id}}

    # 执行 Agent
    try:
        result = await app.ainvoke(initial_state, config)
        logger.info(f"✅ Agent execution completed for session {session_id}")
        return result
    except Exception as e:
        logger.error(f"❌ Agent execution failed: {e}")
        raise


async def stream_agent(
    user_message: str,
    session_id: str,
) -> any:
    """
    流式执行 Agent（用于 SSE）

    Args:
        user_message: 用户消息
        session_id: 会话ID

    Yields:
        Agent 执行过程中的状态更新
    """
    from langchain_core.messages import HumanMessage

    app = get_agent_app()

    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": session_id,
        "next_step": None,
        "error": None,
        "confidence_score": None,
    }

    config = {"configurable": {"thread_id": session_id}}

    try:
        async for chunk in app.astream(initial_state, config):
            logger.debug(f"📦 Agent chunk: {list(chunk.keys())}")
            yield chunk
    except Exception as e:
        logger.error(f"❌ Agent streaming failed: {e}")
        raise

