"""
模型提供商基础接口

定义统一的模型提供商接口和抽象基类。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel


class ModelProvider(ABC):
    """模型提供商抽象基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._validate_config()

    @abstractmethod
    def create_llm(self) -> BaseChatModel:
        """创建LLM实例"""
        pass

    @abstractmethod
    def create_embeddings(self) -> Embeddings:
        """创建Embeddings实例"""
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """获取支持的模型列表"""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """验证连接是否有效"""
        pass

    def _validate_config(self) -> None:
        """验证配置的完整性"""
        required_fields = self.get_required_config_fields()
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                raise ValueError(f"Missing required config field: {field}")

    @abstractmethod
    def get_required_config_fields(self) -> List[str]:
        """获取必需的配置字段"""
        pass


class LLMProvider(ModelProvider):
    """LLM提供商基类"""

    @abstractmethod
    def create_llm(self) -> BaseChatModel:
        """创建LLM实例"""
        pass

    def create_embeddings(self) -> Embeddings:
        """LLM提供商不支持embeddings"""
        raise NotImplementedError("LLM provider does not support embeddings")

    @abstractmethod
    def get_models(self) -> List[str]:
        """获取支持的LLM模型列表"""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """验证LLM连接是否有效"""
        pass


class EmbeddingProvider(ModelProvider):
    """Embedding提供商基类"""

    @abstractmethod
    def create_embeddings(self) -> Embeddings:
        """创建Embeddings实例"""
        pass

    def create_llm(self) -> BaseChatModel:
        """Embedding提供商不支持LLM"""
        raise NotImplementedError("Embedding provider does not support LLM")

    @abstractmethod
    def get_models(self) -> List[str]:
        """获取支持的Embedding模型列表"""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """验证Embedding连接是否有效"""
        pass


class HybridProvider(ModelProvider):
    """混合提供商基类（同时支持LLM和Embedding）"""

    @abstractmethod
    def create_llm(self) -> BaseChatModel:
        """创建LLM实例"""
        pass

    @abstractmethod
    def create_embeddings(self) -> Embeddings:
        """创建Embeddings实例"""
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """获取支持的所有模型列表"""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """验证连接是否有效"""
        pass
