"""
LLM 模型工厂

根据配置返回对应的 LLM 实例（DeepSeek/OpenAI/Claude）。
"""

import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from src.core.config import settings
from src.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def create_llm() -> BaseChatModel:
    """
    创建 LLM 实例

    根据 settings.llm_provider 返回对应的 Chat Model。

    Returns:
        BaseChatModel 实例

    Raises:
        ConfigurationError: 不支持的 LLM 提供商或缺少 API Key
    """
    provider = settings.llm_provider

    try:
        if provider == "deepseek":
            return _create_deepseek_llm()
        elif provider == "openai":
            return _create_openai_llm()
        elif provider == "anthropic":
            return _create_anthropic_llm()
        else:
            raise ConfigurationError(f"Unsupported LLM provider: {provider}")
    except Exception as e:
        logger.error(f"Failed to create LLM: {e}")
        raise


def _create_deepseek_llm() -> ChatOpenAI:
    """
    创建 DeepSeek LLM（使用 OpenAI 兼容接口）

    DeepSeek 提供 OpenAI 兼容的 API，可使用 ChatOpenAI 类。
    """
    if not settings.deepseek_api_key:
        raise ConfigurationError(
            "DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek"
        )

    logger.info(f"Creating DeepSeek LLM: {settings.deepseek_model}")

    return ChatOpenAI(
        model=settings.deepseek_model,
        openai_api_key=settings.deepseek_api_key,
        openai_api_base=settings.deepseek_base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        model_kwargs={
            "top_p": 1.0,
        },
    )


def _create_openai_llm() -> ChatOpenAI:
    """创建 OpenAI LLM"""
    if not settings.openai_api_key:
        raise ConfigurationError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

    logger.info(f"Creating OpenAI LLM: {settings.openai_model}")

    return ChatOpenAI(
        model=settings.openai_model,
        openai_api_key=settings.openai_api_key,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )


def _create_anthropic_llm() -> Any:
    """创建 Anthropic Claude LLM"""
    if not settings.anthropic_api_key:
        raise ConfigurationError(
            "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
        )

    logger.info(f"Creating Anthropic LLM: {settings.anthropic_model}")

    try:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.anthropic_model,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
    except ImportError as e:
        raise ConfigurationError(
            "langchain-anthropic not installed. Run: pip install langchain-anthropic"
        ) from e


def create_embeddings() -> Any:
    """
    创建 Embedding 模型

    根据 settings.embedding_provider 返回对应的 Embeddings 实例。

    Returns:
        Embeddings 实例
    """
    provider = settings.embedding_provider

    try:
        if provider == "deepseek":
            return _create_deepseek_embeddings()
        elif provider == "openai":
            return _create_openai_embeddings()
        elif provider == "local":
            return _create_local_embeddings()
        else:
            raise ConfigurationError(f"Unsupported embedding provider: {provider}")
    except Exception as e:
        logger.error(f"Failed to create embeddings: {e}")
        raise


def _create_deepseek_embeddings() -> Any:
    """创建 DeepSeek Embeddings（使用 OpenAI 兼容接口）"""
    if not settings.deepseek_api_key:
        raise ConfigurationError(
            "DEEPSEEK_API_KEY is required when EMBEDDING_PROVIDER=deepseek"
        )

    logger.info(f"Creating DeepSeek Embeddings: {settings.embedding_model}")

    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.deepseek_api_key,
        openai_api_base=settings.deepseek_base_url,
    )


def _create_openai_embeddings() -> Any:
    """创建 OpenAI Embeddings"""
    if not settings.openai_api_key:
        raise ConfigurationError(
            "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai"
        )

    logger.info(f"Creating OpenAI Embeddings: {settings.embedding_model}")

    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )


def _create_local_embeddings() -> Any:
    """创建本地 Embedding 模型（如 bge-large-zh-v1.5）"""
    logger.info(f"Creating Local Embeddings: {settings.embedding_model}")

    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},  # 或 "cuda" 如果有 GPU
            encode_kwargs={"normalize_embeddings": True},
        )
    except ImportError as e:
        raise ConfigurationError(
            "sentence-transformers not installed. "
            "Run: pip install sentence-transformers"
        ) from e

