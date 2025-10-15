"""
Milvus 向量数据库服务

提供知识库和对话历史的向量存储与检索功能。
"""

import logging
import time
from typing import Any

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from src.core.config import settings
from src.core.exceptions import MilvusConnectionError

logger = logging.getLogger(__name__)


class MilvusService:
    """Milvus 向量数据库服务"""

    def __init__(self) -> None:
        self.conn_alias = "default"
        self.knowledge_collection: Collection | None = None
        self.history_collection: Collection | None = None

    async def initialize(self) -> None:
        """
        初始化 Milvus 连接和 Collections

        Raises:
            MilvusConnectionError: 连接失败
        """
        try:
            # 连接 Milvus
            connections.connect(
                alias=self.conn_alias,
                host=settings.milvus_host,
                port=settings.milvus_port,
                user=settings.milvus_user,
                password=settings.milvus_password,
                db_name=settings.milvus_database,
                timeout=10,
            )
            logger.info(
                f"✅ Connected to Milvus: {settings.milvus_host}:{settings.milvus_port}"
            )

            # 创建或加载 Collections
            await self._create_knowledge_collection()
            await self._create_history_collection()

        except Exception as e:
            logger.error(f"❌ Failed to connect to Milvus: {e}")
            raise MilvusConnectionError(f"Failed to connect to Milvus: {e}") from e

    async def _create_knowledge_collection(self) -> None:
        """创建知识库 Collection（如果不存在）"""
        collection_name = settings.milvus_knowledge_collection

        # 检查 Collection 是否存在
        if utility.has_collection(collection_name, using=self.conn_alias):
            logger.info(f"📂 Collection '{collection_name}' already exists, loading...")
            self.knowledge_collection = Collection(collection_name, using=self.conn_alias)
            self.knowledge_collection.load()
            return

        # 定义 Schema
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                max_length=64,
                is_primary=True,
                description="文档唯一标识",
            ),
            FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=10000,
                description="文档文本内容",
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=settings.embedding_dim,
                description="文本向量",
            ),
            FieldSchema(name="metadata", dtype=DataType.JSON, description="文档元数据"),
            FieldSchema(
                name="created_at", dtype=DataType.INT64, description="创建时间戳（秒）"
            ),
        ]

        schema = CollectionSchema(
            fields=fields,
            description="网站知识库",
            enable_dynamic_field=False,
        )

        # 创建 Collection
        self.knowledge_collection = Collection(
            name=collection_name,
            schema=schema,
            using=self.conn_alias,
        )

        # 创建向量索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }
        self.knowledge_collection.create_index(
            field_name="embedding",
            index_params=index_params,
        )

        # 加载到内存
        self.knowledge_collection.load()
        logger.info(f"✅ Created and loaded collection: {collection_name}")

    async def _create_history_collection(self) -> None:
        """创建对话历史 Collection（如果不存在）"""
        collection_name = settings.milvus_history_collection

        if utility.has_collection(collection_name, using=self.conn_alias):
            logger.info(f"📂 Collection '{collection_name}' already exists, loading...")
            self.history_collection = Collection(collection_name, using=self.conn_alias)
            self.history_collection.load()
            return

        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                max_length=64,
                is_primary=True,
            ),
            FieldSchema(
                name="session_id",
                dtype=DataType.VARCHAR,
                max_length=64,
                description="会话ID",
            ),
            FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=5000,
                description="对话文本",
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=settings.embedding_dim,
            ),
            FieldSchema(
                name="role",
                dtype=DataType.VARCHAR,
                max_length=20,
                description="user 或 assistant",
            ),
            FieldSchema(name="timestamp", dtype=DataType.INT64, description="消息时间戳"),
        ]

        schema = CollectionSchema(
            fields=fields,
            description="历史对话记忆",
        )

        self.history_collection = Collection(
            name=collection_name,
            schema=schema,
            using=self.conn_alias,
        )

        # 向量索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 64},
        }
        self.history_collection.create_index(
            field_name="embedding",
            index_params=index_params,
        )

        # session_id 标量索引（加速按会话查询）
        self.history_collection.create_index(
            field_name="session_id",
            index_params={"index_type": "STL_SORT"},
        )

        self.history_collection.load()
        logger.info(f"✅ Created and loaded collection: {collection_name}")

    async def search_knowledge(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        从知识库检索相关文档

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            score_threshold: 分数阈值（可选，低于阈值的结果会被过滤）

        Returns:
            检索结果列表，每个结果包含: {text, score, metadata}
        """
        if not self.knowledge_collection:
            raise MilvusConnectionError("Knowledge collection not initialized")

        # 执行向量检索
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 16}}

        results = self.knowledge_collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "metadata", "created_at"],
        )

        # 格式化结果
        filtered_results = []
        threshold = score_threshold or settings.rag_score_threshold

        for hit in results[0]:
            if hit.score >= threshold:
                filtered_results.append(
                    {
                        "text": hit.entity.get("text"),
                        "score": hit.score,
                        "metadata": hit.entity.get("metadata"),
                    }
                )

        logger.debug(
            f"🔍 Knowledge search: {len(filtered_results)}/{top_k} results above threshold {threshold}"
        )
        return filtered_results

    async def insert_knowledge(
        self,
        documents: list[dict[str, Any]],
    ) -> int:
        """
        批量插入知识库文档

        Args:
            documents: 文档列表，每个文档包含: {id, text, embedding, metadata}

        Returns:
            插入的文档数量
        """
        if not self.knowledge_collection:
            raise MilvusConnectionError("Knowledge collection not initialized")

        if not documents:
            return 0

        # 准备数据
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        embeddings = [doc["embedding"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        timestamps = [int(time.time())] * len(documents)

        # 插入
        self.knowledge_collection.insert(
            [ids, texts, embeddings, metadatas, timestamps]
        )

        # 刷新索引
        self.knowledge_collection.flush()

        logger.info(f"📥 Inserted {len(documents)} documents into knowledge base")
        return len(documents)

    async def search_history_by_session(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        按会话ID查询历史对话

        Args:
            session_id: 会话ID
            limit: 返回结果数量

        Returns:
            对话历史列表，按时间排序
        """
        if not self.history_collection:
            raise MilvusConnectionError("History collection not initialized")

        results = self.history_collection.query(
            expr=f'session_id == "{session_id}"',
            output_fields=["text", "role", "timestamp"],
            limit=limit,
        )

        # 按时间排序
        sorted_results = sorted(results, key=lambda x: x["timestamp"])
        return sorted_results

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            True if connected, False otherwise
        """
        try:
            version = utility.get_server_version(using=self.conn_alias)
            logger.debug(f"Milvus server version: {version}")
            return version is not None
        except Exception as e:
            logger.error(f"Milvus health check failed: {e}")
            return False

    async def close(self) -> None:
        """关闭 Milvus 连接"""
        try:
            connections.disconnect(alias=self.conn_alias)
            logger.info("✅ Milvus connection closed")
        except Exception as e:
            logger.error(f"Error closing Milvus connection: {e}")


# 全局服务实例
milvus_service = MilvusService()

