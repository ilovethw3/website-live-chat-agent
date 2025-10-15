"""
模型提供商插件系统

支持动态加载和注册不同的模型提供商。
"""

from typing import Any, Dict, Type

from .base import EmbeddingProvider, LLMProvider, ModelProvider
from .deepseek_provider import DeepSeekEmbeddingProvider, DeepSeekLLMProvider
from .openai_provider import OpenAIEmbeddingProvider, OpenAILLMProvider
from .siliconflow_provider import SiliconFlowEmbeddingProvider, SiliconFlowLLMProvider

# 提供商注册表
_PROVIDER_REGISTRY: Dict[str, Type[ModelProvider]] = {
    # OpenAI 提供商
    "openai_llm": OpenAILLMProvider,
    "openai_embedding": OpenAIEmbeddingProvider,

    # DeepSeek 提供商
    "deepseek_llm": DeepSeekLLMProvider,
    "deepseek_embedding": DeepSeekEmbeddingProvider,

    # 硅基流动提供商
    "siliconflow_llm": SiliconFlowLLMProvider,
    "siliconflow_embedding": SiliconFlowEmbeddingProvider,
}


def get_provider(provider_name: str) -> Type[ModelProvider]:
    """
    获取提供商类

    Args:
        provider_name: 提供商名称

    Returns:
        提供商类

    Raises:
        ValueError: 不支持的提供商
    """
    if provider_name not in _PROVIDER_REGISTRY:
        available = ", ".join(_PROVIDER_REGISTRY.keys())
        raise ValueError(f"Unsupported provider: {provider_name}. Available: {available}")

    return _PROVIDER_REGISTRY[provider_name]


def create_provider(provider_name: str, config: Dict[str, Any]) -> ModelProvider:
    """
    创建提供商实例

    Args:
        provider_name: 提供商名称
        config: 配置字典

    Returns:
        提供商实例
    """
    provider_class = get_provider(provider_name)
    return provider_class(config)


def list_providers() -> Dict[str, str]:
    """
    列出所有可用的提供商

    Returns:
        提供商名称到描述的映射
    """
    return {
        "openai_llm": "OpenAI LLM Provider",
        "openai_embedding": "OpenAI Embedding Provider",
        "deepseek_llm": "DeepSeek LLM Provider",
        "deepseek_embedding": "DeepSeek Embedding Provider",
        "siliconflow_llm": "SiliconFlow LLM Provider",
        "siliconflow_embedding": "SiliconFlow Embedding Provider",
    }


def register_provider(name: str, provider_class: Type[ModelProvider]) -> None:
    """
    注册新的提供商

    Args:
        name: 提供商名称
        provider_class: 提供商类
    """
    _PROVIDER_REGISTRY[name] = provider_class


__all__ = [
    "ModelProvider",
    "LLMProvider",
    "EmbeddingProvider",
    "get_provider",
    "create_provider",
    "list_providers",
    "register_provider",
]
