"""
快速提升测试覆盖率的补充测试
"""

from unittest.mock import patch

import pytest

from src.core.config import settings
from src.core.exceptions import (
    AgentExecutionError,
    AuthenticationError,
    ConfigurationError,
    LLMError,
    MilvusConnectionError,
    MilvusError,
    RedisConnectionError,
    ValidationError,
)


def test_exceptions():
    """测试异常类的实例化"""
    # 测试各种异常类
    assert str(ConfigurationError("配置错误")) == "配置错误"
    assert str(AuthenticationError("认证失败")) == "认证失败"
    assert str(ValidationError("验证失败")) == "验证失败"
    assert str(MilvusError("Milvus错误")) == "Milvus错误"
    assert str(MilvusConnectionError("Milvus连接错误")) == "Milvus连接错误"
    assert str(RedisConnectionError("Redis连接错误")) == "Redis连接错误"
    assert str(LLMError("LLM错误")) == "LLM错误"
    assert str(AgentExecutionError("Agent执行错误")) == "Agent执行错误"


def test_config_properties():
    """测试配置属性的边界情况"""
    # 测试embedding_model_name属性
    with patch.object(settings, 'embedding_provider', 'openai'):
        with patch.object(settings, 'embedding_model', 'text-embedding-ada-002'):
            assert settings.embedding_model_name == 'text-embedding-ada-002'

    with patch.object(settings, 'embedding_provider', 'local'):
        with patch.object(settings, 'embedding_model', 'local-embedding'):
            assert settings.embedding_model_name == 'local-embedding'

    # 测试不支持的provider
    with patch.object(settings, 'embedding_provider', 'unsupported'):
        with pytest.raises(ValueError, match="Unsupported embedding provider"):
            _ = settings.embedding_model_name


def test_config_validation():
    """测试配置验证"""
    # 测试validate_configuration方法
    results = settings.validate_configuration()
    assert isinstance(results, dict)


def test_security_verify_api_key():
    """测试API密钥验证的边界情况"""
    import asyncio

    from fastapi import HTTPException

    from src.core.security import verify_api_key

    # 测试无效的API密钥
    async def test_invalid_key():
        with pytest.raises(HTTPException):
            await verify_api_key("invalid-key")

    asyncio.run(test_invalid_key())


def test_utils_functions():
    """测试工具函数的边界情况"""
    from src.core.utils import chunk_text_for_embedding, truncate_text_to_tokens

    # 测试空文本
    assert truncate_text_to_tokens("", 100) == ""
    assert chunk_text_for_embedding("", 100) == [""]

    # 测试None输入 - 这些函数不处理None，会抛出异常
    with pytest.raises((TypeError, AttributeError)):
        truncate_text_to_tokens(None, 100)
    with pytest.raises((TypeError, AttributeError)):
        chunk_text_for_embedding(None, 100)

    # 测试负数max_tokens
    assert truncate_text_to_tokens("test", -1) == ""
    assert chunk_text_for_embedding("test", -1) == []


def test_openai_schema_models():
    """测试OpenAI schema模型"""
    from src.models.openai_schema import (
        ChatCompletionChoice,
        ChatCompletionResponse,
        ChatCompletionUsage,
        ChatMessage,
        OpenAIModelList,
        OpenAIModelRef,
    )

    # 测试模型引用
    model_ref = OpenAIModelRef(
        id="test-model",
        created=1234567890,
        owned_by="test-owner"
    )
    assert model_ref.id == "test-model"
    assert model_ref.created == 1234567890
    assert model_ref.owned_by == "test-owner"

    # 测试模型列表
    model_list = OpenAIModelList(data=[model_ref])
    assert len(model_list.data) == 1
    assert model_list.data[0].id == "test-model"

    # 测试聊天消息
    message = ChatMessage(role="user", content="Hello")
    assert message.role == "user"
    assert message.content == "Hello"

    # 测试使用统计
    usage = ChatCompletionUsage(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30
    )
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 30

    # 测试选择项
    choice = ChatCompletionChoice(
        index=0,
        message=message,
        finish_reason="stop"
    )
    assert choice.index == 0
    assert choice.finish_reason == "stop"

    # 测试完整响应
    response = ChatCompletionResponse(
        id="test-id",
        created=1234567890,
        model="test-model",
        choices=[choice],
        usage=usage
    )
    assert response.id == "test-id"
    assert response.model == "test-model"
    assert len(response.choices) == 1


def test_knowledge_models():
    """测试知识库模型"""
    from src.models.knowledge import (
        DocumentChunk,
        KnowledgeSearchRequest,
        KnowledgeSearchResponse,
        KnowledgeUpsertRequest,
        KnowledgeUpsertResponse,
        SearchResult,
    )

    # 测试文档切片
    chunk = DocumentChunk(
        text="测试内容",
        metadata={"source": "test"}
    )
    assert chunk.text == "测试内容"
    assert chunk.metadata["source"] == "test"

    # 测试上传请求
    request = KnowledgeUpsertRequest(
        documents=[chunk],
        collection_name="test_collection"
    )
    assert len(request.documents) == 1
    assert request.collection_name == "test_collection"

    # 测试上传响应
    response = KnowledgeUpsertResponse(
        success=True,
        inserted_count=1,
        collection_name="test_collection",
        message="成功"
    )
    assert response.success is True
    assert response.inserted_count == 1

    # 测试搜索结果
    result = SearchResult(
        text="测试内容",
        score=0.95,
        metadata={"source": "test"}
    )
    assert result.text == "测试内容"
    assert result.score == 0.95

    # 测试搜索请求
    search_req = KnowledgeSearchRequest(
        query="测试查询",
        top_k=3
    )
    assert search_req.query == "测试查询"
    assert search_req.top_k == 3

    # 测试搜索响应
    search_resp = KnowledgeSearchResponse(
        results=[result],
        query="测试查询",
        total_results=1
    )
    assert len(search_resp.results) == 1
    assert search_resp.total_results == 1
