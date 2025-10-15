"""
知识库管理 API

提供知识库文档上传、检索测试等功能。
"""

import logging
import uuid

from fastapi import APIRouter, Depends, Query

from src.core.security import verify_api_key
from src.models.knowledge import (
    KnowledgeSearchResponse,
    KnowledgeUpsertRequest,
    KnowledgeUpsertResponse,
    SearchResult,
)
from src.services import llm_factory
from src.services.milvus_service import milvus_service

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/knowledge/upsert", response_model=KnowledgeUpsertResponse)
async def upsert_knowledge(request: KnowledgeUpsertRequest) -> KnowledgeUpsertResponse:
    """
    批量上传知识库文档

    自动处理：
    1. 文档切片（TODO: 实现文本切片逻辑）
    2. 生成 Embedding
    3. 存入 Milvus
    """
    logger.info(f"📥 Upserting {len(request.documents)} documents to knowledge base")

    try:
        # 创建 Embeddings 实例（按模块引用，便于测试补丁生效）
        embeddings = llm_factory.create_embeddings()

        # 准备插入数据
        documents_to_insert = []

        for doc in request.documents:
            # 生成文档 ID
            doc_id = str(uuid.uuid4())

            # 生成 Embedding
            embedding = await embeddings.aembed_query(doc.text)

            documents_to_insert.append(
                {
                    "id": doc_id,
                    "text": doc.text,
                    "embedding": embedding,
                    "metadata": doc.metadata,
                }
            )

        # 批量插入到 Milvus（兼容不同服务实现/测试桩）
        inserted_count: int = 0
        if hasattr(milvus_service, "insert_documents"):
            result = await milvus_service.insert_documents(documents_to_insert)  # type: ignore[attr-defined]
            if isinstance(result, dict) and "inserted_count" in result:
                inserted_count = int(result["inserted_count"])
            elif isinstance(result, int):
                inserted_count = result
            else:
                inserted_count = len(documents_to_insert)
        else:
            inserted_count = await milvus_service.insert_knowledge(documents_to_insert)

        logger.info(f"✅ Successfully inserted {inserted_count} documents")

        return KnowledgeUpsertResponse(
            success=True,
            inserted_count=inserted_count,
            collection_name=request.collection_name,
            message=f"成功上传 {len(request.documents)} 个文档，共生成 {inserted_count} 个向量切片",
        )

    except Exception as e:
        logger.error(f"❌ Failed to upsert knowledge: {e}")
        return KnowledgeUpsertResponse(
            success=False,
            inserted_count=0,
            collection_name=request.collection_name,
            message=f"上传失败: {str(e)}",
        )


@router.get("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    query: str = Query(..., description="搜索查询"),
    top_k: int = Query(default=3, ge=1, le=10, description="返回结果数量"),
) -> KnowledgeSearchResponse:
    """
    测试知识库检索

    用于调试和验证知识库内容。
    """
    logger.info(f"🔍 Searching knowledge base: query='{query}', top_k={top_k}")

    try:
        # 生成查询向量
        embeddings = llm_factory.create_embeddings()
        query_embedding = await embeddings.aembed_query(query)

        # 检索
        results = await milvus_service.search_knowledge(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        # 格式化结果
        formatted_results = [
            SearchResult(
                text=result["text"],
                score=result["score"],
                metadata=result.get("metadata", {}),
            )
            for result in results
        ]

        logger.info(f"✅ Found {len(formatted_results)} results")

        return KnowledgeSearchResponse(
            results=formatted_results,
            query=query,
            total_results=len(formatted_results),
        )

    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        return KnowledgeSearchResponse(
            results=[],
            query=query,
            total_results=0,
        )

