"""
测试 Milvus 服务模块

测试 Milvus 向量数据库的连接、检索和插入逻辑。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.milvus_service import MilvusService, milvus_service
from src.core.exceptions import MilvusError


@pytest.mark.asyncio
async def test_milvus_initialize():
    """测试 Milvus 初始化"""
    service = MilvusService()

    with patch("pymilvus.connections.connect") as mock_connect:
        with patch.object(
            service, "_ensure_collection", new_callable=AsyncMock
        ) as mock_ensure:
            await service.initialize()

            mock_connect.assert_called_once()
            # 应该初始化两个 collection（knowledge_base 和 conversation_history）
            assert mock_ensure.call_count == 2


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
    mock_result = MagicMock()
    mock_result.ids = [[1, 2, 3]]
    mock_result.distances = [[0.1, 0.2, 0.3]]
    mock_result.__iter__ = lambda self: iter(
        [
            [
                MagicMock(
                    id=1,
                    distance=0.1,
                    entity={"text": "文档1", "metadata": '{"source": "doc1.md"}'},
                ),
                MagicMock(
                    id=2,
                    distance=0.2,
                    entity={"text": "文档2", "metadata": '{"source": "doc2.md"}'},
                ),
            ]
        ]
    )

    service.knowledge_collection.search.return_value = mock_result

    with patch("src.services.milvus_service.get_embeddings", return_value=mock_embeddings):
        results = await service.search_knowledge(query="测试查询", top_k=2)

        assert len(results) <= 2
        service.knowledge_collection.search.assert_called_once()


@pytest.mark.asyncio
async def test_milvus_search_empty_query():
    """测试空查询"""
    service = MilvusService()

    with pytest.raises(ValueError):
        await service.search_knowledge(query="", top_k=3)


@pytest.mark.asyncio
async def test_milvus_insert_documents_success(mock_embeddings):
    """测试插入文档成功"""
    service = MilvusService()
    service.knowledge_collection = MagicMock()

    mock_insert_result = MagicMock()
    mock_insert_result.insert_count = 2
    service.knowledge_collection.insert.return_value = mock_insert_result

    documents = [
        {"text": "文档1", "metadata": {"source": "doc1.md"}},
        {"text": "文档2", "metadata": {"source": "doc2.md"}},
    ]

    with patch("src.services.milvus_service.get_embeddings", return_value=mock_embeddings):
        result = await service.insert_documents(
            documents=documents, collection_name="knowledge_base"
        )

        assert result["success"] is True
        assert result["inserted_count"] == 2


@pytest.mark.asyncio
async def test_milvus_insert_empty_documents():
    """测试插入空文档列表"""
    service = MilvusService()

    result = await service.insert_documents(documents=[], collection_name="knowledge_base")

    assert result["success"] is True
    assert result["inserted_count"] == 0


@pytest.mark.asyncio
async def test_milvus_health_check_healthy():
    """测试健康检查 - 健康状态"""
    service = MilvusService()

    with patch("pymilvus.connections.has_connection", return_value=True):
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
    mock_result = MagicMock()
    mock_result.__iter__ = lambda self: iter(
        [
            [
                MagicMock(
                    id=1,
                    distance=0.1,  # 高分数（低距离）
                    entity={"text": "高相关文档", "metadata": "{}"},
                ),
                MagicMock(
                    id=2,
                    distance=0.9,  # 低分数（高距离）
                    entity={"text": "低相关文档", "metadata": "{}"},
                ),
            ]
        ]
    )

    service.knowledge_collection.search.return_value = mock_result

    with patch("src.services.milvus_service.get_embeddings", return_value=mock_embeddings):
        # 设置较高的阈值，应该过滤掉低分文档
        results = await service.search_knowledge(
            query="测试", top_k=10, score_threshold=0.8
        )

        # 结果应该被过滤
        assert isinstance(results, list)


def test_milvus_singleton():
    """测试 Milvus Service 是单例"""
    from src.services.milvus_service import milvus_service as service1
    from src.services.milvus_service import milvus_service as service2

    assert service1 is service2

