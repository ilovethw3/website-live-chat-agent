"""
临时测试脚本：验证 LangGraph Agent 是否正常工作

使用前需要设置环境变量：
export DEEPSEEK_API_KEY=your-key
export MILVUS_HOST=your-milvus-host
export API_KEY=test-key
"""

import asyncio
import logging

from langchain_core.messages import HumanMessage

from src.agent.main.graph import get_agent_app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_agent():
    """测试 Agent 基本功能"""
    logger.info("=" * 50)
    logger.info("🧪 Testing LangGraph Agent...")
    logger.info("=" * 50)

    # 获取 Agent App
    app = get_agent_app()

    # 测试用例 1: 简单打招呼
    logger.info("\n📝 Test Case 1: Simple Greeting")
    logger.info("-" * 50)

    state1 = {
        "messages": [HumanMessage(content="你好")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-session-1",
        "next_step": None,
        "error": None,
        "confidence_score": None,
    }

    config1 = {"configurable": {"thread_id": "test-session-1"}}

    result1 = await app.ainvoke(state1, config1)

    logger.info(f"Router Decision: {result1.get('next_step')}")
    logger.info(f"Retrieved Docs: {len(result1.get('retrieved_docs', []))}")
    logger.info(f"Response: {result1['messages'][-1].content}")

    # 测试用例 2: 需要检索的问题（模拟）
    logger.info("\n📝 Test Case 2: Question Requiring Retrieval")
    logger.info("-" * 50)

    state2 = {
        "messages": [HumanMessage(content="你们的退货政策是什么？")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-session-2",
        "next_step": None,
        "error": None,
        "confidence_score": None,
    }

    config2 = {"configurable": {"thread_id": "test-session-2"}}

    result2 = await app.ainvoke(state2, config2)

    logger.info(f"Router Decision: {result2.get('next_step')}")
    logger.info(f"Retrieved Docs: {len(result2.get('retrieved_docs', []))}")
    logger.info(f"Confidence Score: {result2.get('confidence_score')}")
    logger.info(f"Response: {result2['messages'][-1].content}")

    # 测试用例 3: 流式响应
    logger.info("\n📝 Test Case 3: Streaming Response")
    logger.info("-" * 50)

    state3 = {
        "messages": [HumanMessage(content="介绍一下你们的产品")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-session-3",
        "next_step": None,
        "error": None,
        "confidence_score": None,
    }

    config3 = {"configurable": {"thread_id": "test-session-3"}}

    logger.info("Streaming chunks:")
    async for chunk in app.astream(state3, config3):
        logger.info(f"  - Node: {list(chunk.keys())}")

    logger.info("\n" + "=" * 50)
    logger.info("✅ All tests completed!")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_agent())

