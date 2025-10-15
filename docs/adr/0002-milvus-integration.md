# ADR-0002: Milvus 向量数据库集成设计

**状态**: 已接受  
**日期**: 2025-10-13  
**负责人**: AR (Architect AI)  
**相关文档**: [Epic-001](../epics/epic-001-langgraph-rag-agent.md), [ADR-0001](./0001-langgraph-architecture.md)

---

## 背景

客服 Agent 需要从网站知识库中检索相关信息来回答用户问题。需求包括：

1. **知识库存储**：存储网站的 FAQ、产品信息、政策文档等（文本 + 向量）
2. **语义检索**：基于用户问题的语义相似度检索（而非关键词匹配）
3. **对话历史存储**：长期保存历史对话，支持跨会话检索
4. **高性能要求**：检索延迟 < 500ms，支持 100 QPS
5. **已有基础设施**：Milvus 已独立部署，需集成

---

## 决策

**使用已部署的 Milvus 作为唯一向量数据库**，设计两个 Collection：

1. **`knowledge_base`**：网站知识库（FAQ、产品、政策）
2. **`conversation_history`**：历史对话记忆（用于长期记忆和上下文检索）

**不引入关系型数据库**（MVP 阶段），所有结构化元数据存储在 Milvus 的 JSON 字段中。

---

## Collection 设计

### Collection 1: `knowledge_base`

**用途**: 存储网站知识库内容

**Schema 定义**:

```python
from pymilvus import CollectionSchema, FieldSchema, DataType

fields = [
    # 主键（UUID）
    FieldSchema(
        name="id",
        dtype=DataType.VARCHAR,
        max_length=64,
        is_primary=True,
        description="文档唯一标识"
    ),
    
    # 原始文本（支持最长 10000 字符）
    FieldSchema(
        name="text",
        dtype=DataType.VARCHAR,
        max_length=10000,
        description="文档文本内容"
    ),
    
    # 向量（使用 DeepSeek Embedding 或 OpenAI ada-002）
    FieldSchema(
        name="embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=1536,  # OpenAI text-embedding-ada-002 维度
        description="文本向量表示"
    ),
    
    # 元数据（JSON 格式，灵活存储）
    FieldSchema(
        name="metadata",
        dtype=DataType.JSON,
        description="""元数据结构：{
            "title": str,           # 文档标题
            "url": str,             # 来源 URL
            "category": str,        # 分类（FAQ/产品/政策）
            "language": str,        # 语言（zh/en）
            "author": str,          # 作者（可选）
            "tags": list[str]       # 标签（可选）
        }"""
    ),
    
    # 创建时间（Unix 时间戳）
    FieldSchema(
        name="created_at",
        dtype=DataType.INT64,
        description="创建时间戳（秒）"
    ),
]

schema = CollectionSchema(
    fields=fields,
    description="网站知识库",
    enable_dynamic_field=False  # 禁用动态字段，强制 schema
)
```

**索引配置**:

```python
from pymilvus import Collection

collection = Collection(name="knowledge_base", schema=schema)

# 向量索引（IVF_FLAT：平衡性能与准确率）
index_params = {
    "metric_type": "COSINE",    # 余弦相似度
    "index_type": "IVF_FLAT",   # Inverted File with Flat compression
    "params": {"nlist": 128}    # 聚类中心数量
}
collection.create_index(
    field_name="embedding",
    index_params=index_params
)

# 加载到内存
collection.load()
```

**为什么选择 IVF_FLAT**:
- ✅ **平衡性能与准确率**：比暴力搜索快 10-100 倍，准确率 > 95%
- ✅ **适合中等规模**：100 万文档以下性能优秀
- ⚠️ **备选方案**：超过 100 万文档时，考虑 `HNSW` 索引

---

### Collection 2: `conversation_history`

**用途**: 存储历史对话，支持长期记忆和跨会话检索

**Schema 定义**:

```python
fields = [
    # 主键
    FieldSchema(
        name="id",
        dtype=DataType.VARCHAR,
        max_length=64,
        is_primary=True
    ),
    
    # 会话ID（用于按会话查询）
    FieldSchema(
        name="session_id",
        dtype=DataType.VARCHAR,
        max_length=64,
        description="会话唯一标识"
    ),
    
    # 对话文本
    FieldSchema(
        name="text",
        dtype=DataType.VARCHAR,
        max_length=5000,
        description="用户问题或 Agent 回答"
    ),
    
    # 向量
    FieldSchema(
        name="embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=1536
    ),
    
    # 角色（user/assistant）
    FieldSchema(
        name="role",
        dtype=DataType.VARCHAR,
        max_length=20,
        description="user 或 assistant"
    ),
    
    # 时间戳
    FieldSchema(
        name="timestamp",
        dtype=DataType.INT64,
        description="消息时间戳（秒）"
    ),
]

schema = CollectionSchema(
    fields=fields,
    description="历史对话记忆"
)
```

**索引配置**:

```python
collection = Collection(name="conversation_history", schema=schema)

# 向量索引
index_params = {
    "metric_type": "COSINE",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 64}  # 对话数量较少，减少 nlist
}
collection.create_index(field_name="embedding", index_params=index_params)

# session_id 字段使用默认索引
# 注意：STL_SORT只支持数值类型，VARCHAR字段使用默认索引即可
# 默认索引对字符串字段查询性能已经足够

collection.load()
```

---

## 检索策略

### 1. 知识库检索

**基础检索**:

```python
async def search_knowledge(query: str, top_k: int = 3) -> list[dict]:
    """从知识库检索相关文档"""
    # 1. 生成查询向量
    query_embedding = await embedding_service.embed(query)
    
    # 2. 执行向量检索
    results = await collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"nprobe": 16}},
        limit=top_k,
        output_fields=["text", "metadata", "created_at"]
    )
    
    # 3. 过滤低分结果
    filtered_results = [
        {
            "text": hit.entity.get("text"),
            "score": hit.score,
            "metadata": hit.entity.get("metadata"),
        }
        for hit in results[0]
        if hit.score > 0.7  # 分数阈值
    ]
    
    return filtered_results
```

**混合检索（可选，未来优化）**:

```python
async def hybrid_search(query: str, category: str = None) -> list[dict]:
    """混合检索：向量相似度 + 元数据过滤"""
    query_embedding = await embedding_service.embed(query)
    
    # 构建过滤表达式
    filter_expr = f'metadata["category"] == "{category}"' if category else ""
    
    results = await collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"nprobe": 16}},
        limit=10,  # 多检索一些，后续 Rerank
        output_fields=["text", "metadata"],
        expr=filter_expr  # 元数据过滤
    )
    
    # Rerank（可选）
    reranked = await rerank_service.rerank(query, results)
    return reranked[:3]
```

---

### 2. 对话历史检索

**场景 1: 按会话ID查询**（获取最近 N 轮对话）

```python
async def get_session_history(session_id: str, limit: int = 10) -> list[dict]:
    """获取指定会话的历史对话"""
    results = await collection.query(
        expr=f'session_id == "{session_id}"',
        output_fields=["text", "role", "timestamp"],
        limit=limit
    )
    
    # 按时间排序
    sorted_results = sorted(results, key=lambda x: x["timestamp"])
    return sorted_results
```

**场景 2: 跨会话语义检索**（查找相似历史问题）

```python
async def search_similar_conversations(query: str, top_k: int = 2) -> list[dict]:
    """检索历史中相似的对话"""
    query_embedding = await embedding_service.embed(query)
    
    results = await collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"nprobe": 8}},
        limit=top_k,
        output_fields=["text", "role", "session_id"],
        expr='role == "user"'  # 仅检索用户提问
    )
    
    return results[0]
```

---

## Embedding 模型选择

### 方案 A: OpenAI `text-embedding-ada-002`（推荐用于生产）

**特点**:
- ✅ 维度: 1536
- ✅ 质量高，适合多语言
- ✅ 成本低（$0.0001/1K tokens）
- ⚠️ 需要网络请求

**代码示例**:

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key=settings.openai_api_key
)

vector = await embeddings.aembed_query("用户问题")
```

---

### 方案 B: DeepSeek Embedding（推荐用于默认 LLM）

**特点**:
- ✅ 中文效果优秀
- ✅ 成本极低
- ⚠️ 需确认 API 兼容性

**代码示例**:

```python
# 假设 DeepSeek 提供 OpenAI 兼容接口
embeddings = OpenAIEmbeddings(
    model="deepseek-embedding",
    openai_api_base="https://api.deepseek.com/v1",
    openai_api_key=settings.deepseek_api_key
)
```

---

### 方案 C: 本地 Embedding 模型（离线部署）

**特点**:
- ✅ 无网络依赖
- ✅ 数据隐私
- ⚠️ 需要 GPU 资源

**推荐模型**: `bge-large-zh-v1.5`（中文）、`bge-large-en-v1.5`（英文）

```python
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-zh-v1.5",
    model_kwargs={"device": "cuda"},
    encode_kwargs={"normalize_embeddings": True}
)
```

**决策**: MVP 阶段使用 **DeepSeek Embedding** 或 **OpenAI ada-002**，根据实际成本和效果选择。

---

## 性能优化策略

### 1. 连接池管理

```python
from pymilvus import connections, utility

class MilvusService:
    def __init__(self):
        self.conn_alias = "default"
        self._connect()
    
    def _connect(self):
        connections.connect(
            alias=self.conn_alias,
            host=settings.milvus_host,
            port=settings.milvus_port,
            user=settings.milvus_user,
            password=settings.milvus_password,
            pool_size=10  # 连接池大小
        )
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            return utility.get_server_version(using=self.conn_alias) is not None
        except Exception:
            return False
```

---

### 2. 批量插入优化

```python
async def batch_insert_knowledge(documents: list[dict], batch_size: int = 100):
    """批量插入知识库"""
    collection = Collection("knowledge_base")
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        
        # 准备数据
        ids = [doc["id"] for doc in batch]
        texts = [doc["text"] for doc in batch]
        embeddings = await embedding_service.embed_batch(texts)  # 批量 Embedding
        metadatas = [doc["metadata"] for doc in batch]
        timestamps = [int(time.time())] * len(batch)
        
        # 插入
        collection.insert([ids, texts, embeddings, metadatas, timestamps])
    
    # 刷新索引
    collection.flush()
```

---

### 3. 缓存热点查询

```python
import hashlib
from functools import wraps

def cache_search_results(ttl: int = 300):
    """缓存检索结果（5分钟）"""
    def decorator(func):
        @wraps(func)
        async def wrapper(query: str, *args, **kwargs):
            # 生成缓存 key
            cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
            
            # 检查 Redis 缓存
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 执行检索
            results = await func(query, *args, **kwargs)
            
            # 存入缓存
            await redis_client.setex(cache_key, ttl, json.dumps(results))
            return results
        
        return wrapper
    return decorator

@cache_search_results(ttl=300)
async def search_knowledge(query: str, top_k: int = 3):
    # ... 检索逻辑
    pass
```

---

## 数据生命周期管理

### 1. 知识库更新策略

**场景**: 网站内容更新，需要更新知识库

```python
async def upsert_knowledge(doc_id: str, text: str, metadata: dict):
    """更新或插入文档（Upsert）"""
    collection = Collection("knowledge_base")
    
    # 1. 检查文档是否存在
    existing = collection.query(
        expr=f'id == "{doc_id}"',
        output_fields=["id"]
    )
    
    if existing:
        # 2. 删除旧文档
        collection.delete(expr=f'id == "{doc_id}"')
    
    # 3. 插入新文档
    embedding = await embedding_service.embed(text)
    collection.insert([[doc_id], [text], [embedding], [metadata], [int(time.time())]])
    collection.flush()
```

---

### 2. 对话历史清理策略

**策略**: 保留 30 天对话，自动删除过期数据

```python
import asyncio

async def cleanup_old_conversations():
    """定时清理 30 天前的对话"""
    collection = Collection("conversation_history")
    
    # 计算 30 天前的时间戳
    thirty_days_ago = int(time.time()) - (30 * 24 * 3600)
    
    # 删除过期数据
    collection.delete(expr=f"timestamp < {thirty_days_ago}")
    
    # 记录日志
    logger.info(f"Cleaned conversations older than {thirty_days_ago}")

# 每天凌晨 3 点执行
# （在 FastAPI 启动时注册定时任务）
```

---

## 存储架构决策：不引入关系型数据库

### 理由

**MVP 阶段的数据需求**：

| 数据类型 | Milvus JSON 字段 | 是否够用？ |
|---------|-----------------|----------|
| 知识库元数据（标题、URL、分类） | ✅ 支持 | ✅ 够用 |
| 会话元数据（session_id、时间） | ✅ 支持 | ✅ 够用 |
| API Key 管理 | 环境变量 | ✅ 单 Key 够用 |
| 系统日志 | 文件 / ELK | ✅ 够用 |

**未来扩展路径**（何时引入 PostgreSQL）：

当满足以下任一条件时，考虑引入关系型数据库：
1. 需要支持 > 5 个 WordPress 网站（多租户 API Key 管理）
2. 需要长期保留会话历史（> 30 天，且需复杂查询统计）
3. 需要合规审计日志（GDPR、等保）
4. 需要知识库版本管理和回滚

**参考**: [ADR-0003: 存储架构决策](./0003-storage-architecture.md)（未来补充）

---

## 监控与告警

### 关键指标

```python
from prometheus_client import Histogram, Counter

# 检索延迟
search_latency = Histogram(
    "milvus_search_latency_seconds",
    "Milvus search latency",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

# 检索成功率
search_success = Counter("milvus_search_success_total", "Successful searches")
search_failure = Counter("milvus_search_failure_total", "Failed searches")

# 使用示例
@search_latency.time()
async def search_knowledge(query: str):
    try:
        results = await collection.search(...)
        search_success.inc()
        return results
    except Exception as e:
        search_failure.inc()
        raise
```

### 健康检查端点

```python
@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    milvus_healthy = milvus_service.health_check()
    
    return {
        "status": "healthy" if milvus_healthy else "unhealthy",
        "services": {
            "milvus": {
                "status": "healthy" if milvus_healthy else "unhealthy",
                "host": settings.milvus_host,
                "collections": ["knowledge_base", "conversation_history"]
            }
        },
        "timestamp": int(time.time())
    }
```

---

## 验证标准

### 功能验证
- [x] 能成功连接已部署的 Milvus
- [x] `knowledge_base` Collection 创建成功
- [x] `conversation_history` Collection 创建成功
- [x] 向量检索返回正确结果（Top-K）
- [x] 元数据过滤生效

### 性能验证
- [ ] 单次检索延迟 < 500ms（P95）
- [ ] 支持 100 QPS 并发检索
- [ ] 批量插入 1000 个文档 < 10秒

### 质量验证
- [ ] 知识库检索准确率 > 85%（人工标注 100 个样本）
- [ ] 分数阈值 0.7 能有效过滤无关结果

---

## 相关决策

- [ADR-0001: LangGraph 架构](./0001-langgraph-architecture.md)
- [ADR-0003: 存储架构决策](./0003-storage-architecture.md)（待编写）

---

## 参考资料

- [Milvus 官方文档](https://milvus.io/docs)
- [LangChain Milvus 集成](https://python.langchain.com/docs/integrations/vectorstores/milvus)
- [OpenAI Embeddings 指南](https://platform.openai.com/docs/guides/embeddings)

---

**变更历史**:

| 日期 | 版本 | 变更内容 | 负责人 |
|------|------|---------|--------|
| 2025-10-13 | 1.0 | 初始版本，定义 Milvus Collection 和检索策略 | AR AI |

