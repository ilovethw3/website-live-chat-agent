"""
DeepSeek 模型提供商

实现 DeepSeek 的 LLM 和 Embedding 提供商。
"""

from typing import List

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .base import EmbeddingProvider, LLMProvider


class DeepSeekLLMProvider(LLMProvider):
    """DeepSeek LLM提供商（使用OpenAI兼容接口）"""

    def get_required_config_fields(self) -> List[str]:
        return ["api_key", "base_url"]

    def create_llm(self) -> ChatOpenAI:
        """创建DeepSeek LLM实例"""
        return ChatOpenAI(
            model=self.config.get("model", "deepseek-chat"),
            openai_api_key=self.config["api_key"],
            openai_api_base=self.config["base_url"],
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 1000),
        )

    def get_models(self) -> List[str]:
        """获取支持的DeepSeek模型列表"""
        return [
            "deepseek-chat",
            "deepseek-coder",
            "deepseek-math"
        ]

    def validate_connection(self) -> bool:
        """验证DeepSeek连接是否有效"""
        try:
            self.create_llm()  # 验证连接
            return True
        except Exception:
            return False


class DeepSeekEmbeddingProvider(EmbeddingProvider):
    """DeepSeek Embedding提供商"""

    def get_required_config_fields(self) -> List[str]:
        return ["api_key", "base_url"]

    def create_embeddings(self) -> OpenAIEmbeddings:
        """创建DeepSeek Embeddings实例"""
        return OpenAIEmbeddings(
            model=self.config.get("model", "deepseek-embedding"),
            openai_api_key=self.config["api_key"],
            openai_api_base=self.config["base_url"],
        )

    def get_models(self) -> List[str]:
        """获取支持的DeepSeek Embedding模型列表"""
        return [
            "deepseek-embedding"
        ]

    def validate_connection(self) -> bool:
        """验证DeepSeek Embedding连接是否有效"""
        try:
            self.create_embeddings()  # 验证连接
            return True
        except Exception:
            return False
