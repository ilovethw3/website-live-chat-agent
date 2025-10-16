"""
全局 pytest fixtures 和配置

提供测试所需的共享 fixtures，包括：
- Mock 服务（Milvus, Redis, LLM）
- 测试客户端
- 测试数据
"""

import os
from typing import Generator
from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

# 设置测试环境变量
os.environ.update({
    "LLM_PROVIDER": "deepseek",
    "DEEPSEEK_API_KEY": "test-deepseek-key",
    "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
    "DEEPSEEK_MODEL": "deepseek-chat",
    "MILVUS_HOST": "localhost",
    "MILVUS_PORT": "19530",
    "MILVUS_USER": "root",
    "MILVUS_PASSWORD": "",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_PASSWORD": "",
    "REDIS_DB": "0",
    "API_KEY": "test-api-key-12345",
    "LOG_LEVEL": "ERROR",  # 减少测试时的日志输出
    "EMBEDDING_PROVIDER": "siliconflow",  # 默认使用siliconflow
    "SILICONFLOW_API_KEY": "test-siliconflow-key",  # 添加siliconflow API key
    "SILICONFLOW_EMBEDDING_BASE_URL": "https://api.siliconflow.cn/v1/embeddings",  # 添加默认URL
    "EMBEDDING_MODEL": "text-embedding-ada-002",
    "EMBEDDING_DIM": "1536",
    "LANGGRAPH_CHECKPOINTER": "memory",
})


@pytest.fixture(scope="session")
def test_api_key() -> str:
    """测试 API Key"""
    return "test-api-key-12345"


@pytest.fixture
def api_headers(test_api_key: str) -> dict[str, str]:
    """API 认证头"""
    return {
        "Authorization": f"Bearer {test_api_key}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """FastAPI 测试客户端"""
    from src.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_milvus_collection():
    """Mock Milvus Collection"""
    mock = MagicMock()
    mock.search.return_value = [[]]  # 空搜索结果
    mock.insert.return_value = MagicMock(insert_count=1)
    mock.query.return_value = []
    mock.num_entities = 0
    return mock


@pytest.fixture
async def mock_milvus_service(mock_milvus_collection):
    """Mock Milvus 服务"""
    mock = AsyncMock()
    mock.knowledge_collection = mock_milvus_collection
    mock.history_collection = mock_milvus_collection
    mock.search.return_value = []
    mock.insert_documents.return_value = {"success": True, "inserted_count": 1}
    mock.health_check.return_value = True
    mock.initialize = AsyncMock()
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis 客户端（使用 fakeredis）"""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def mock_llm():
    """Mock LLM"""
    mock = MagicMock()
    mock.invoke.return_value = AIMessage(content="这是一个测试响应")
    mock.ainvoke = AsyncMock(return_value=AIMessage(content="这是一个异步测试响应"))
    mock.model_name = "deepseek-chat"
    return mock


@pytest.fixture
def mock_embeddings():
    """Mock Embeddings 模型"""
    mock = MagicMock()
    mock.embed_query.return_value = [0.1] * 1536
    mock.embed_documents.return_value = [[0.1] * 1536]
    mock.aembed_query = AsyncMock(return_value=[0.1] * 1536)
    return mock


@pytest.fixture
def sample_messages() -> list[dict]:
    """示例消息列表"""
    return [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
        {"role": "user", "content": "介绍一下你们的产品"},
    ]


@pytest.fixture
def sample_documents() -> list[dict]:
    """示例知识库文档"""
    return [
        {
            "text": "我们的退货政策是30天内无条件退货，只需提供购买凭证。",
            "metadata": {
                "source": "policy.md",
                "category": "退货政策",
                "updated_at": "2024-01-01",
            },
        },
        {
            "text": "我们的产品保修期为1年，保修期内免费维修。",
            "metadata": {
                "source": "warranty.md",
                "category": "保修政策",
                "updated_at": "2024-01-01",
            },
        },
        {
            "text": "我们支持微信支付、支付宝、银行卡等多种支付方式。",
            "metadata": {
                "source": "payment.md",
                "category": "支付方式",
                "updated_at": "2024-01-01",
            },
        },
    ]


@pytest.fixture
def sample_search_results() -> list[dict]:
    """示例检索结果"""
    return [
        {
            "id": "1",
            "text": "我们的退货政策是30天内无条件退货。",
            "score": 0.95,
            "metadata": {"source": "policy.md", "category": "退货政策"},
        },
        {
            "id": "2",
            "text": "退货时需要提供购买凭证。",
            "score": 0.88,
            "metadata": {"source": "policy.md", "category": "退货政策"},
        },
    ]


@pytest.fixture
def mock_agent_state() -> dict:
    """Mock Agent 状态"""
    return {
        "messages": [
            HumanMessage(content="你好"),
        ],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-session-123",
        "next_step": "call_llm",
    }


# 自动清理环境变量
@pytest.fixture(autouse=True)
def cleanup_env():
    """每次测试后清理环境变量"""
    yield
    # 测试后的清理工作可以在这里执行

