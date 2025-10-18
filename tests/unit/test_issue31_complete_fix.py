"""
测试Issue #31完整修复 - 验证所有embedding调用都进行了token截断
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.tools import search_knowledge_for_agent
from src.api.v1.knowledge import search_knowledge


class TestIssue31CompleteFix:
    """测试Issue #31的完整修复"""

    @pytest.mark.asyncio
    async def test_search_knowledge_for_agent_token_truncation(self):
        """测试search_knowledge_for_agent函数的token截断"""
        # 模拟长查询文本（超过512 tokens）
        long_query = "这是一个非常长的查询文本，" * 100  # 确保超过512 tokens

        # 模拟embeddings和milvus_service
        mock_embeddings = AsyncMock()
        mock_embeddings.aembed_query.return_value = [0.1] * 1536  # 模拟embedding向量

        mock_milvus_service = AsyncMock()
        mock_milvus_service.search_knowledge.return_value = [
            {"text": "测试文档", "score": 0.9, "metadata": {}}
        ]

        with patch('src.agent.tools.create_embeddings', return_value=mock_embeddings), \
             patch('src.agent.tools.milvus_service', mock_milvus_service), \
             patch('src.agent.tools.logger') as mock_logger:

            # 调用函数
            result = await search_knowledge_for_agent(long_query, top_k=3)

            # 验证结果
            assert len(result) == 1
            assert result[0]["text"] == "测试文档"

            # 验证embedding调用时使用了截断后的查询
            mock_embeddings.aembed_query.assert_called_once()
            called_query = mock_embeddings.aembed_query.call_args[0][0]

            # 验证查询被截断了
            assert len(called_query) < len(long_query)
            assert len(called_query) <= 512 * 3  # 字符数应该远小于原始长度

            # 验证日志记录
            mock_logger.warning.assert_called()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "Query truncated" in warning_msg

    @pytest.mark.asyncio
    async def test_search_knowledge_api_token_truncation(self):
        """测试search_knowledge API函数的token截断"""
        # 模拟长查询文本
        long_query = "这是一个非常长的查询文本，" * 100

        # 模拟llm_factory和milvus_service
        mock_embeddings = AsyncMock()
        mock_embeddings.aembed_query.return_value = [0.1] * 1536

        mock_llm_factory = MagicMock()
        mock_llm_factory.create_embeddings.return_value = mock_embeddings

        mock_milvus_service = AsyncMock()
        mock_milvus_service.search_knowledge.return_value = [
            {"text": "测试文档", "score": 0.9, "metadata": {}}
        ]

        with patch('src.api.v1.knowledge.llm_factory', mock_llm_factory), \
             patch('src.api.v1.knowledge.milvus_service', mock_milvus_service):

            # 调用函数
            result = await search_knowledge(long_query, top_k=3)

            # 验证结果
            assert len(result.results) == 1
            assert result.results[0].text == "测试文档"

            # 验证embedding调用时使用了截断后的查询
            mock_embeddings.aembed_query.assert_called_once()
            called_query = mock_embeddings.aembed_query.call_args[0][0]

            # 验证查询被截断了
            assert len(called_query) < len(long_query)
            assert len(called_query) <= 512 * 3  # 字符数应该远小于原始长度

    @pytest.mark.asyncio
    async def test_short_query_no_truncation(self):
        """测试短查询不会被截断"""
        short_query = "短查询"

        mock_embeddings = AsyncMock()
        mock_embeddings.aembed_query.return_value = [0.1] * 1536

        mock_milvus_service = AsyncMock()
        mock_milvus_service.search_knowledge.return_value = [
            {"text": "测试文档", "score": 0.9, "metadata": {}}
        ]

        with patch('src.agent.tools.create_embeddings', return_value=mock_embeddings), \
             patch('src.agent.tools.milvus_service', mock_milvus_service), \
             patch('src.agent.tools.logger') as mock_logger:

            # 调用函数
            result = await search_knowledge_for_agent(short_query, top_k=3)

            # 验证结果
            assert len(result) == 1

            # 验证embedding调用时使用了原始查询
            mock_embeddings.aembed_query.assert_called_once()
            called_query = mock_embeddings.aembed_query.call_args[0][0]
            assert called_query == short_query

            # 验证没有截断日志
            mock_logger.warning.assert_not_called()

    def test_truncate_text_to_tokens_integration(self):
        """测试truncate_text_to_tokens函数的集成"""
        from src.core.utils import truncate_text_to_tokens

        # 测试长文本截断
        long_text = "这是一个测试文本，" * 200  # 确保超过512 tokens
        truncated = truncate_text_to_tokens(long_text, max_tokens=512)

        # 验证截断结果
        assert len(truncated) < len(long_text)
        assert len(truncated) > 0

        # 测试短文本不截断
        short_text = "短文本"
        not_truncated = truncate_text_to_tokens(short_text, max_tokens=512)
        assert not_truncated == short_text

    def test_chunk_text_for_embedding_integration(self):
        """测试chunk_text_for_embedding函数的集成"""
        from src.core.utils import chunk_text_for_embedding

        # 测试长文本分块
        long_text = "这是一个测试文档，" * 200  # 确保需要分块
        chunks = chunk_text_for_embedding(long_text, max_tokens=512)

        # 验证分块结果
        assert len(chunks) > 1
        assert all(len(chunk) > 0 for chunk in chunks)

        # 测试短文本不分块
        short_text = "短文档"
        single_chunk = chunk_text_for_embedding(short_text, max_tokens=512)
        assert len(single_chunk) == 1
        assert single_chunk[0] == short_text
