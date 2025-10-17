"""
硅基流动平台模型提供商

实现硅基流动平台的 LLM 和 Embedding 提供商。
"""

import asyncio
from typing import List

import httpx
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI

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


class SiliconFlowEmbeddings(Embeddings):
    """硅基流动自定义Embedding类，确保发送文本而不是token ID数组"""

    def __init__(self, api_key: str, model: str = "BAAI/bge-large-zh-v1.5", base_url: str = "https://api.siliconflow.cn/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档列表"""
        return asyncio.run(self.aembed_documents(texts))

    def embed_query(self, text: str) -> List[float]:
        """嵌入查询文本"""
        return asyncio.run(self.aembed_query(text))

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步嵌入文档列表"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": texts,  # 直接发送文本列表
                    "model": self.model
                }
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]

    async def aembed_query(self, text: str) -> List[float]:
        """异步嵌入查询文本"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,  # 直接发送文本，不是token ID数组
                    "model": self.model
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]


class SiliconFlowEmbeddingProvider(EmbeddingProvider):
    """硅基流动 Embedding提供商"""

    def get_required_config_fields(self) -> List[str]:
        return ["api_key"]  # base_url现在是可选的

    def create_embeddings(self) -> SiliconFlowEmbeddings:
        """创建硅基流动 Embeddings实例（使用自定义实现）"""
        return SiliconFlowEmbeddings(
            api_key=self.config["api_key"],
            model=self.config.get("model", "BAAI/bge-large-zh-v1.5"),
            base_url=self.config.get("base_url", "https://api.siliconflow.cn/v1")
        )

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
