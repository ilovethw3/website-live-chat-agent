"""
硅基流动平台模型提供商

实现硅基流动平台的 LLM 和 Embedding 提供商。
"""

from typing import List

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .base import EmbeddingProvider, LLMProvider


class SiliconFlowLLMProvider(LLMProvider):
    """硅基流动 LLM提供商"""

    def get_required_config_fields(self) -> List[str]:
        return ["api_key", "base_url"]

    def create_llm(self) -> ChatOpenAI:
        """创建硅基流动 LLM实例"""
        return ChatOpenAI(
            model=self.config.get("model", "Qwen/Qwen2.5-7B-Instruct"),
            openai_api_key=self.config["api_key"],
            openai_api_base=self.config["base_url"],
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 1000),
        )

    def get_models(self) -> List[str]:
        """获取支持的硅基流动模型列表"""
        return [
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-14B-Instruct",
            "Qwen/Qwen2.5-32B-Instruct",
            "Qwen/Qwen2.5-72B-Instruct",
            "Qwen/Qwen2.5-Coder-7B-Instruct",
            "Qwen/Qwen2.5-Coder-14B-Instruct"
        ]

    def validate_connection(self) -> bool:
        """验证硅基流动连接是否有效"""
        try:
            self.create_llm()  # 验证连接
            return True
        except Exception:
            return False


class SiliconFlowEmbeddingProvider(EmbeddingProvider):
    """硅基流动 Embedding提供商"""

    def get_required_config_fields(self) -> List[str]:
        return ["api_key"]  # base_url现在是可选的

    def create_embeddings(self) -> OpenAIEmbeddings:
        """创建硅基流动 Embeddings实例（支持独立URL）"""
        config = {
            "model": self.config.get("model", "BAAI/bge-large-zh-v1.5"),
            "openai_api_key": self.config["api_key"],
        }

        # 添加base_url（如果提供）
        if "base_url" in self.config and self.config["base_url"]:
            config["openai_api_base"] = self.config["base_url"]

        return OpenAIEmbeddings(**config)

    def get_models(self) -> List[str]:
        """获取支持的硅基流动 Embedding模型列表"""
        return [
            "BAAI/bge-large-zh-v1.5",
            "BAAI/bge-base-zh-v1.5",
            "BAAI/bge-small-zh-v1.5",
            "BAAI/bge-large-en-v1.5",
            "BAAI/bge-base-en-v1.5"
        ]

    def validate_connection(self) -> bool:
        """验证硅基流动 Embedding连接是否有效"""
        try:
            self.create_embeddings()  # 验证连接
            return True
        except Exception:
            return False
