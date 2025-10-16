"""
URL配置解析器

支持智能优先级机制：独立URL > 提供商特定URL > 共享URL
"""

from enum import Enum
from typing import Any, Dict, Optional


class URLPriority(Enum):
    """URL优先级枚举"""
    INDEPENDENT = 1  # 独立URL（最高优先级）
    PROVIDER_SPECIFIC = 2  # 提供商特定URL
    SHARED = 3  # 共享URL（最低优先级）


class URLConfigParser:
    """URL配置解析器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化配置解析器

        Args:
            config: 配置字典，包含所有URL配置字段
        """
        self.config = config

    def resolve_embedding_url(self, provider: str) -> Optional[str]:
        """
        解析embedding URL，使用智能优先级机制

        Args:
            provider: 提供商名称 (openai, deepseek, siliconflow, anthropic)

        Returns:
            解析后的URL，如果未配置则返回None

        Raises:
            ValueError: 当提供商不支持时
        """
        # 1. 优先使用通用独立URL
        if self.config.get("embedding_base_url"):
            return self.config["embedding_base_url"]

        # 2. 使用提供商特定URL
        provider_specific_key = f"{provider}_embedding_base_url"
        if self.config.get(provider_specific_key):
            return self.config[provider_specific_key]

        # 3. 回退到共享URL（保持向后兼容）
        return self._get_legacy_embedding_url(provider)

    def _get_legacy_embedding_url(self, provider: str) -> Optional[str]:
        """
        获取传统共享URL配置

        Args:
            provider: 提供商名称

        Returns:
            传统URL配置，如果未配置则返回None

        Raises:
            ValueError: 当提供商不支持时
        """
        if provider == "deepseek":
            return self.config.get("deepseek_base_url")
        elif provider == "siliconflow":
            return self.config.get("siliconflow_base_url")
        elif provider == "openai":
            return None  # OpenAI使用默认URL
        elif provider == "anthropic":
            return None  # Anthropic使用默认URL
        elif provider == "local":
            return None  # 本地模型不需要URL
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

    def validate_url(self, url: Optional[str]) -> Dict[str, Any]:
        """
        验证URL格式和有效性

        Args:
            url: 要验证的URL

        Returns:
            验证结果字典，包含valid和error字段
        """
        if not url:
            return {"valid": True, "error": None}

        if not url.startswith(('http://', 'https://')):
            return {
                "valid": False,
                "error": f"Invalid URL format: {url}. Must start with http:// or https://"
            }

        return {"valid": True, "error": None}

    def get_url_priority(self, provider: str) -> URLPriority:
        """
        获取当前配置的URL优先级

        Args:
            provider: 提供商名称

        Returns:
            当前使用的URL优先级
        """
        if self.config.get("embedding_base_url"):
            return URLPriority.INDEPENDENT

        provider_specific_key = f"{provider}_embedding_base_url"
        if self.config.get(provider_specific_key):
            return URLPriority.PROVIDER_SPECIFIC

        return URLPriority.SHARED

    def get_all_embedding_urls(self) -> Dict[str, Optional[str]]:
        """
        获取所有embedding URL配置

        Returns:
            包含所有URL配置的字典
        """
        return {
            "embedding_base_url": self.config.get("embedding_base_url"),
            "openai_embedding_base_url": self.config.get("openai_embedding_base_url"),
            "deepseek_embedding_base_url": self.config.get("deepseek_embedding_base_url"),
            "siliconflow_embedding_base_url": self.config.get("siliconflow_embedding_base_url"),
            "anthropic_embedding_base_url": self.config.get("anthropic_embedding_base_url"),
        }
