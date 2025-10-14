"""
测试 Milvus 服务模块

测试 Milvus 向量数据库的连接、检索和插入逻辑。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.milvus_service import MilvusService


@pytest.mark.asyncio
async def test_milvus_initialize():
    """测试 Milvus 初始化"""
    service = MilvusService()

    with patch("pymilvus.connections.connect") as mock_connect:
        with patch.object(
            service, "_create_knowledge_collection", new_callable=AsyncMock
        ) as mock_create_knowledge:
            with patch.object(
                service, "_create_history_collection", new_callable=AsyncMock
            ) as mock_create_history:
                await service.initialize()

                mock_connect.assert_called_once()
                # 应该初始化两个 collection（knowledge_base 和 conversation_history）
                mock_create_knowledge.assert_called_once()
                mock_create_history.assert_called_once()


@pytest.mark.asyncio
async def test_milvus_close():
    """测试 Milvus 关闭连接"""
    service = MilvusService()

    with patch("pymilvus.connections.disconnect") as mock_disconnect:
        await service.close()
        mock_disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_milvus_search_success(mock_embeddings):
    """测试向量检索成功"""
    service = MilvusService()
    service.knowledge_collection = MagicMock()

    # Mock 搜索结果
    mock_hit_1 = MagicMock()
    mock_hit_1.score = 0.9
    mock_hit_1.entity.get = lambda key: {
        "text": "文档1",
        "metadata": {"source": "doc1.md"},
    }.get(key)

    mock_hit_2 = MagicMock()
    mock_hit_2.score = 0.8
    mock_hit_2.entity.get = lambda key: {
        "text": "文档2",
        "metadata": {"source": "doc2.md"},
    }.get(key)

    mock_result = [[mock_hit_1, mock_hit_2]]
    service.knowledge_collection.search.return_value = mock_result

    # 使用 query_embedding 参数
    query_embedding = [0.1] * 768
    results = await service.search_knowledge(query_embedding=query_embedding, top_k=2)

    assert len(results) <= 2
    service.knowledge_collection.search.assert_called_once()


@pytest.mark.asyncio
async def test_milvus_search_empty_query():
    """测试空向量"""
    service = MilvusService()
    service.knowledge_collection = MagicMock()

    # 空的 embedding 向量会在 Milvus 搜索时触发错误
    # 这里测试传入空列表
    empty_embedding = []

    # Mock search to raise an error for empty embedding
    service.knowledge_collection.search.side_effect = ValueError("Invalid embedding")

    with pytest.raises(ValueError):
        await service.search_knowledge(query_embedding=empty_embedding, top_k=3)


@pytest.mark.asyncio
async def test_milvus_insert_documents_success(mock_embeddings):
    """测试插入文档成功"""
    service = MilvusService()
    service.knowledge_collection = MagicMock()

    documents = [
        {
            "id": "doc1",
            "text": "文档1",
            "embedding": [0.1] * 768,
            "metadata": {"source": "doc1.md"},
        },
        {
            "id": "doc2",
            "text": "文档2",
            "embedding": [0.2] * 768,
            "metadata": {"source": "doc2.md"},
        },
    ]

    # insert_knowledge 返回插入的数量
    result = await service.insert_knowledge(documents=documents)

    assert result == 2
    service.knowledge_collection.insert.assert_called_once()
    service.knowledge_collection.flush.assert_called_once()


@pytest.mark.asyncio
async def test_milvus_insert_empty_documents():
    """测试插入空文档列表"""
    service = MilvusService()
    service.knowledge_collection = MagicMock()

    result = await service.insert_knowledge(documents=[])

    assert result == 0


@pytest.mark.asyncio
async def test_milvus_health_check_healthy():
    """测试健康检查 - 健康状态"""
    service = MilvusService()

    with patch("pymilvus.utility.get_server_version", return_value="2.3.0"):
        is_healthy = service.health_check()
        assert is_healthy is True


@pytest.mark.asyncio
async def test_milvus_health_check_unhealthy():
    """测试健康检查 - 不健康状态"""
    service = MilvusService()

    with patch("pymilvus.connections.has_connection", return_value=False):
        is_healthy = service.health_check()
        assert is_healthy is False


@pytest.mark.asyncio
async def test_milvus_search_with_score_threshold(mock_embeddings):
    """测试带相似度阈值的检索"""
    service = MilvusService()
    service.knowledge_collection = MagicMock()

    # Mock 搜索结果，包含不同分数
    mock_hit_high = MagicMock()
    mock_hit_high.score = 0.95  # 高分数
    mock_hit_high.entity.get = lambda key: {
        "text": "高相关文档",
        "metadata": {},
    }.get(key)

    mock_hit_low = MagicMock()
    mock_hit_low.score = 0.5  # 低分数
    mock_hit_low.entity.get = lambda key: {
        "text": "低相关文档",
        "metadata": {},
    }.get(key)

    mock_result = [[mock_hit_high, mock_hit_low]]
    service.knowledge_collection.search.return_value = mock_result

    query_embedding = [0.1] * 768
    # 设置较高的阈值，应该过滤掉低分文档
    results = await service.search_knowledge(
        query_embedding=query_embedding, top_k=10, score_threshold=0.8
    )

    # 结果应该被过滤，只保留高分文档
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["score"] == 0.95


def test_milvus_singleton():
    """测试 Milvus Service 是单例"""
    from src.services.milvus_service import milvus_service as service1
    from src.services.milvus_service import milvus_service as service2

    assert service1 is service2

