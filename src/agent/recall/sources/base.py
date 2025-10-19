"""
召回源基类接口

定义统一的召回源接口，所有召回源都必须实现此接口。
"""

from abc import ABC, abstractmethod

from src.agent.recall.schema import RecallHit, RecallRequest


class RecallSource(ABC):
    """召回源基类接口"""

    @abstractmethod
    async def acquire(self, request: RecallRequest) -> list[RecallHit]:
        """
        执行召回

        Args:
            request: 召回请求

        Returns:
            召回命中结果列表
        """
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        召回源名称

        Returns:
            召回源名称
        """
        pass
