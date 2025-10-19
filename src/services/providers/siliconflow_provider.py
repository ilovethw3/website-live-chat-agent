"""
硅基流动平台模型提供商

实现硅基流动平台的 LLM 和 Embedding 提供商。
"""

import asyncio
import logging
from typing import List

import httpx
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI

from .base import EmbeddingProvider, LLMProvider

logger = logging.getLogger(__name__)


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
        self.max_retries = 2  # 最大重试次数
        self.retry_delay = 1.0  # 重试延迟（秒）

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档列表"""
        try:
            # 检查是否已经在事件循环中
            asyncio.get_running_loop()
            # 如果已经在事件循环中，使用 run_in_executor 在单独线程中运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_async_in_thread, self.aembed_documents, texts)
                return future.result()
        except RuntimeError:
            # 没有运行的事件循环，使用 asyncio.run
            return asyncio.run(self.aembed_documents(texts))

    def embed_query(self, text: str) -> List[float]:
        """嵌入查询文本"""
        try:
            # 检查是否已经在事件循环中
            asyncio.get_running_loop()
            # 如果已经在事件循环中，使用 run_in_executor 在单独线程中运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_async_in_thread, self.aembed_query, text)
                return future.result()
        except RuntimeError:
            # 没有运行的事件循环，使用 asyncio.run
            return asyncio.run(self.aembed_query(text))

    def _run_async_in_thread(self, async_func, *args):
        """在单独线程中运行异步函数"""
        return asyncio.run(async_func(*args))

    async def _make_embedding_request(self, input_data, is_query: bool = False):
        """发送嵌入请求，包含重试机制和错误处理"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.base_url}/embeddings",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "input": input_data,
                            "model": self.model
                        }
                    )
                    response.raise_for_status()
                    data = response.json()

                    if is_query:
                        return data["data"][0]["embedding"]
                    else:
                        return [item["embedding"] for item in data["data"]]

            except httpx.HTTPStatusError as e:
                last_exception = e
                # 获取状态码，处理Mock对象的情况
                status_code = getattr(e.response, 'status_code', 500) if hasattr(e.response, 'status_code') else 500
                if status_code >= 500:
                    # 5xx 错误，可以重试
                    logger.warning(f"SiliconFlow API 5xx 错误 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                        continue
                else:
                    # 4xx 错误，不重试
                    logger.error(f"SiliconFlow API 4xx 错误: {e}")
                    raise

            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
                last_exception = e
                logger.warning(f"SiliconFlow API 网络错误 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                    continue
                else:
                    raise

            except Exception as e:
                last_exception = e
                logger.error(f"SiliconFlow API 未知错误: {e}")
                raise

        # 如果所有重试都失败了
        if last_exception:
            logger.error(f"SiliconFlow API 重试失败，已尝试 {self.max_retries + 1} 次")
            raise last_exception

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步嵌入文档列表"""
        return await self._make_embedding_request(texts, is_query=False)

    async def aembed_query(self, text: str) -> List[float]:
        """异步嵌入查询文本"""
        return await self._make_embedding_request(text, is_query=True)


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
