"""
知识库数据模型
"""

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """文档切片"""

    text: str = Field(..., max_length=10000, description="文档文本内容")
    metadata: dict = Field(default_factory=dict, description="文档元数据")


class KnowledgeUpsertRequest(BaseModel):
    """知识库上传请求"""

    documents: list[DocumentChunk] = Field(..., min_length=0, max_length=100)
    collection_name: str = Field(default="knowledge_base")
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)


class KnowledgeUpsertResponse(BaseModel):
    """知识库上传响应"""

    success: bool
    inserted_count: int
    collection_name: str
    message: str


class SearchResult(BaseModel):
    """搜索结果"""

    text: str
    score: float = Field(..., ge=0.0, le=1.0, description="相似度分数")
    metadata: dict


class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求"""

    query: str
    top_k: int = Field(default=3, ge=1, le=10)
    collection_name: str = Field(default="knowledge_base")


class KnowledgeSearchResponse(BaseModel):
    """知识库搜索响应"""

    results: list[SearchResult]
    query: str
    total_results: int

