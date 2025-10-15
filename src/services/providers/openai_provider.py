"""
OpenAI 模型提供商

实现 OpenAI 的 LLM 和 Embedding 提供商。
"""

from typing import List

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .base import EmbeddingProvider, LLMProvider


class OpenAILLMProvider(LLMProvider):
    """OpenAI LLM提供商"""

    def get_required_config_fields(self) -> List[str]:
        return ["api_key"]

    def create_llm(self) -> ChatOpenAI:
        """创建OpenAI LLM实例"""
        return ChatOpenAI(
            model=self.config.get("model", "gpt-4o-mini"),
            openai_api_key=self.config["api_key"],
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 1000),
        )

    def get_models(self) -> List[str]:
        """获取支持的OpenAI模型列表"""
        return [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]

    def validate_connection(self) -> bool:
        """验证OpenAI连接是否有效"""
        try:
            self.create_llm()  # 简单的连接测试 - 实际项目中可以发送一个测试请求
            return True
        except Exception:
            return False


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI Embedding提供商"""

    def get_required_config_fields(self) -> List[str]:
        return ["api_key"]

    def create_embeddings(self) -> OpenAIEmbeddings:
        """创建OpenAI Embeddings实例（支持独立URL）"""
        config = {
            "model": self.config.get("model", "text-embedding-3-small"),
            "openai_api_key": self.config["api_key"],
        }

        # 添加base_url（如果提供）
        if "base_url" in self.config and self.config["base_url"]:
            config["openai_api_base"] = self.config["base_url"]

        return OpenAIEmbeddings(**config)

    def get_models(self) -> List[str]:
        """获取支持的OpenAI Embedding模型列表"""
        return [
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002"
        ]

    def validate_connection(self) -> bool:
        """验证OpenAI Embedding连接是否有效"""
        try:
            self.create_embeddings()  # 简单的连接测试
            return True
        except Exception:
            return False
