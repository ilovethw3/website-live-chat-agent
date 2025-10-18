"""
向量召回源适配器

封装现有Milvus检索为RecallSource实现，复用milvus_service。
"""

import logging

from src.agent.recall.schema import RecallHit, RecallRequest
from src.agent.recall.sources.base import RecallSource
from src.core.config import settings
from src.core.utils import truncate_text_to_tokens
from src.services.llm_factory import create_embeddings
from src.services.milvus_service import milvus_service

logger = logging.getLogger(__name__)


class VectorRecallSource(RecallSource):
    """向量召回源适配器"""

    def __init__(self):
        self._embeddings = None

    @property
    def source_name(self) -> str:
        """召回源名称"""
        return "vector"

    async def acquire(self, request: RecallRequest) -> list[RecallHit]:
        """
        执行向量召回
        
        Args:
            request: 召回请求
            
        Returns:
            召回命中结果列表
        """
        try:
            # 获取embeddings实例
            if self._embeddings is None:
                self._embeddings = create_embeddings()

            # 截断查询文本以避免token限制错误
            # 使用vector_chunk_size作为最大token数，确保不超过嵌入模型的限制
            truncated_query = truncate_text_to_tokens(
                request.query, 
                max_tokens=settings.vector_chunk_size
            )
            
            # 记录截断情况
            if len(truncated_query) < len(request.query):
                logger.warning(
                    f"Vector recall: query truncated from {len(request.query)} to {len(truncated_query)} chars "
                    f"to avoid token limit (max_tokens: {settings.vector_chunk_size})"
                )

            # 生成查询向量
            query_embedding = await self._embeddings.aembed_query(truncated_query)

            # 调用Milvus检索
            results = await milvus_service.search_knowledge(
                query_embedding=query_embedding,
                top_k=request.top_k,
            )

            if not results:
                logger.info(f"Vector recall: no results found for '{request.query}'")
                return []

            # 转换为RecallHit格式
            hits = []
            for i, result in enumerate(results):
                metadata = result.get("metadata", {})

                hit = RecallHit(
                    source=self.source_name,
                    score=result["score"],
                    confidence=result["score"],  # 向量召回中score即confidence
                    reason=f"向量相似度匹配 (相似度: {result['score']:.3f})",
                    content=result["text"],
                    metadata={
                        "title": metadata.get("title", "未命名文档"),
                        "url": metadata.get("url", ""),
                        "category": metadata.get("category", "未知"),
                        "rank": i + 1,
                        "vector_id": result.get("id", ""),
                    }
                )
                hits.append(hit)

            logger.info(
                f"Vector recall: found {len(hits)} results for '{request.query}' "
                f"(top score: {hits[0].score:.3f})"
            )

            return hits

        except Exception as e:
            logger.error(f"Vector recall failed for '{request.query}': {e}")
            # 返回空结果而不是抛出异常，让上层处理
            return []
