"""
召回源单元测试
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.agent.recall.schema import RecallHit, RecallRequest
from src.agent.recall.sources.faq_source import FAQRecallSource
from src.agent.recall.sources.keyword_source import KeywordRecallSource


class TestFAQRecallSource:
    """测试FAQ召回源"""

    @pytest.fixture
    def faq_source(self):
        """创建FAQ召回源实例"""
        return FAQRecallSource()

    @pytest.fixture
    def recall_request(self):
        """创建召回请求"""
        return RecallRequest(
            query="退货政策",
            session_id="session-123",
            trace_id="trace-456"
        )

    def test_source_name(self, faq_source):
        """测试召回源名称"""
        assert faq_source.source_name == "faq"

    @pytest.mark.asyncio
    async def test_acquire_with_matching_query(self, faq_source, recall_request):
        """测试匹配查询的召回"""
        recall_request.query = "退货政策"

        hits = await faq_source.acquire(recall_request)

        assert len(hits) > 0
        assert all(isinstance(hit, RecallHit) for hit in hits)
        assert all(hit.source == "faq" for hit in hits)
        assert all(hit.score > 0 for hit in hits)

    @pytest.mark.asyncio
    async def test_acquire_with_non_matching_query(self, faq_source, recall_request):
        """测试不匹配查询的召回"""
        recall_request.query = "完全不相关的查询内容"

        hits = await faq_source.acquire(recall_request)

        # 应该返回空结果或低分结果
        assert isinstance(hits, list)

    @pytest.mark.asyncio
    async def test_acquire_with_empty_query(self, faq_source, recall_request):
        """测试空查询"""
        recall_request.query = ""

        hits = await faq_source.acquire(recall_request)

        assert isinstance(hits, list)

    @pytest.mark.asyncio
    async def test_acquire_with_top_k_limit(self, faq_source, recall_request):
        """测试top_k限制"""
        recall_request.query = "退货政策"
        recall_request.top_k = 2

        hits = await faq_source.acquire(recall_request)

        assert len(hits) <= 2


class TestKeywordRecallSource:
    """测试关键词召回源"""

    @pytest.fixture
    def keyword_source(self):
        """创建关键词召回源实例"""
        return KeywordRecallSource()

    @pytest.fixture
    def recall_request(self):
        """创建召回请求"""
        return RecallRequest(
            query="价格是多少",
            session_id="session-123",
            trace_id="trace-456"
        )

    def test_source_name(self, keyword_source):
        """测试召回源名称"""
        assert keyword_source.source_name == "keyword"

    @pytest.mark.asyncio
    async def test_acquire_with_matching_query(self, keyword_source, recall_request):
        """测试匹配查询的召回"""
        recall_request.query = "价格是多少"

        hits = await keyword_source.acquire(recall_request)

        assert len(hits) > 0
        assert all(isinstance(hit, RecallHit) for hit in hits)
        assert all(hit.source == "keyword" for hit in hits)
        assert all(hit.score > 0 for hit in hits)

    @pytest.mark.asyncio
    async def test_acquire_with_non_matching_query(self, keyword_source, recall_request):
        """测试不匹配查询的召回"""
        recall_request.query = "完全不相关的查询内容"

        hits = await keyword_source.acquire(recall_request)

        # 应该返回空结果或低分结果
        assert isinstance(hits, list)

    def test_calculate_keyword_score(self, keyword_source):
        """测试关键词分数计算"""
        # 测试直接匹配
        rule = {
            "keywords": ["价格", "费用"],
            "patterns": [r"价格|费用"],
            "priority": 0.9
        }

        score = keyword_source._calculate_keyword_score("价格是多少", rule)
        assert score > 0

        # 测试不匹配
        score = keyword_source._calculate_keyword_score("完全不相关", rule)
        assert score == 0

    def test_synonym_matching(self, keyword_source):
        """测试同义词匹配"""
        # 测试同义词匹配
        rule = {
            "keywords": ["价格"],
            "patterns": [r"价格"],
            "priority": 0.9
        }

        # 直接匹配
        score1 = keyword_source._calculate_keyword_score("价格", rule)
        # 同义词匹配
        score2 = keyword_source._calculate_keyword_score("费用", rule)

        assert score1 > 0
        assert score2 > 0


class TestVectorRecallSource:
    """测试向量召回源（需要mock Milvus）"""

    @pytest.fixture
    def vector_source(self):
        """创建向量召回源实例"""
        from src.agent.recall.sources.vector_source import VectorRecallSource
        return VectorRecallSource()

    @pytest.fixture
    def recall_request(self):
        """创建召回请求"""
        return RecallRequest(
            query="测试查询",
            session_id="session-123",
            trace_id="trace-456"
        )

    def test_source_name(self, vector_source):
        """测试召回源名称"""
        assert vector_source.source_name == "vector"

    @pytest.mark.asyncio
    @patch('src.agent.recall.sources.vector_source.create_embeddings')
    @patch('src.agent.recall.sources.vector_source.milvus_service')
    async def test_acquire_success(self, mock_milvus, mock_embeddings, vector_source, recall_request):
        """测试成功召回"""
        # Mock embeddings
        mock_embeddings.return_value.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])

        # Mock milvus service
        mock_milvus.search_knowledge = AsyncMock(return_value=[
            {
                "text": "测试内容",
                "score": 0.85,
                "metadata": {"title": "测试文档"}
            }
        ])

        hits = await vector_source.acquire(recall_request)

        assert len(hits) > 0
        assert all(isinstance(hit, RecallHit) for hit in hits)
        assert all(hit.source == "vector" for hit in hits)

    @pytest.mark.asyncio
    @patch('src.agent.recall.sources.vector_source.create_embeddings')
    @patch('src.agent.recall.sources.vector_source.milvus_service')
    async def test_acquire_empty_results(self, mock_milvus, mock_embeddings, vector_source, recall_request):
        """测试空结果"""
        # Mock embeddings
        mock_embeddings.return_value.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])

        # Mock milvus service返回空结果
        mock_milvus.search_knowledge = AsyncMock(return_value=[])

        hits = await vector_source.acquire(recall_request)

        assert len(hits) == 0

    @pytest.mark.asyncio
    @patch('src.agent.recall.sources.vector_source.create_embeddings')
    @patch('src.agent.recall.sources.vector_source.milvus_service')
    async def test_acquire_exception_handling(self, mock_milvus, mock_embeddings, vector_source, recall_request):
        """测试异常处理"""
        # Mock embeddings抛出异常
        mock_embeddings.return_value.aembed_query = AsyncMock(side_effect=Exception("Embedding error"))
        
        hits = await vector_source.acquire(recall_request)
        
        # 应该返回空结果而不是抛出异常
        assert len(hits) == 0
    
    @pytest.mark.asyncio
    @patch('src.agent.recall.sources.vector_source.create_embeddings')
    @patch('src.agent.recall.sources.vector_source.milvus_service')
    @patch('src.agent.recall.sources.vector_source.truncate_text_to_tokens')
    async def test_acquire_query_truncation(self, mock_truncate, mock_milvus, mock_embeddings, vector_source, recall_request):
        """测试查询截断功能"""
        # Mock embeddings
        mock_embeddings.return_value.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        # Mock milvus service
        mock_milvus.search_knowledge = AsyncMock(return_value=[
            {
                "text": "测试内容",
                "score": 0.85,
                "metadata": {"title": "测试文档"}
            }
        ])
        
        # Mock截断函数
        mock_truncate.return_value = "截断后的查询"
        
        # 使用长查询
        recall_request.query = "这是一个非常长的查询" * 100
        
        hits = await vector_source.acquire(recall_request)
        
        # 验证截断函数被调用
        mock_truncate.assert_called_once_with(
            recall_request.query,
            max_tokens=500  # 默认vector_chunk_size
        )
        
        # 验证embeddings使用截断后的查询
        mock_embeddings.return_value.aembed_query.assert_called_once_with("截断后的查询")
        
        # 验证结果
        assert len(hits) == 1
        assert hits[0].source == "vector"
