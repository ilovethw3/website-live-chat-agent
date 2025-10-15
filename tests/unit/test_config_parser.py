"""
配置解析器测试

测试URLConfigParser的各种配置场景和优先级机制
"""

import pytest

from src.core.config_parser import URLConfigParser, URLPriority


class TestURLConfigParser:
    """URL配置解析器测试类"""

    def test_independent_url_priority(self):
        """测试独立URL优先级（最高）"""
        config = {
            "embedding_base_url": "https://independent.com/v1",
            "deepseek_embedding_base_url": "https://embedding.deepseek.com/v1",
            "deepseek_base_url": "https://api.deepseek.com/v1"
        }
        parser = URLConfigParser(config)

        url = parser.resolve_embedding_url("deepseek")
        assert url == "https://independent.com/v1"

        priority = parser.get_url_priority("deepseek")
        assert priority == URLPriority.INDEPENDENT

    def test_provider_specific_url_priority(self):
        """测试提供商特定URL优先级（中等）"""
        config = {
            "embedding_base_url": None,
            "deepseek_embedding_base_url": "https://embedding.deepseek.com/v1",
            "deepseek_base_url": "https://api.deepseek.com/v1"
        }
        parser = URLConfigParser(config)

        url = parser.resolve_embedding_url("deepseek")
        assert url == "https://embedding.deepseek.com/v1"

        priority = parser.get_url_priority("deepseek")
        assert priority == URLPriority.PROVIDER_SPECIFIC

    def test_shared_url_priority(self):
        """测试共享URL优先级（最低）"""
        config = {
            "embedding_base_url": None,
            "deepseek_embedding_base_url": None,
            "deepseek_base_url": "https://api.deepseek.com/v1"
        }
        parser = URLConfigParser(config)

        url = parser.resolve_embedding_url("deepseek")
        assert url == "https://api.deepseek.com/v1"

        priority = parser.get_url_priority("deepseek")
        assert priority == URLPriority.SHARED

    def test_no_url_configuration(self):
        """测试无URL配置"""
        config = {
            "embedding_base_url": None,
            "deepseek_embedding_base_url": None,
            "deepseek_base_url": None
        }
        parser = URLConfigParser(config)

        url = parser.resolve_embedding_url("deepseek")
        assert url is None

        priority = parser.get_url_priority("deepseek")
        assert priority == URLPriority.SHARED

    def test_openai_provider(self):
        """测试OpenAI提供商"""
        config = {
            "embedding_base_url": None,
            "openai_embedding_base_url": "https://api.openai.com/v1",
            "openai_base_url": None
        }
        parser = URLConfigParser(config)

        url = parser.resolve_embedding_url("openai")
        assert url == "https://api.openai.com/v1"

        priority = parser.get_url_priority("openai")
        assert priority == URLPriority.PROVIDER_SPECIFIC

    def test_siliconflow_provider(self):
        """测试SiliconFlow提供商"""
        config = {
            "embedding_base_url": None,
            "siliconflow_embedding_base_url": "https://embedding.siliconflow.cn/v1",
            "siliconflow_base_url": "https://api.siliconflow.cn/v1"
        }
        parser = URLConfigParser(config)

        url = parser.resolve_embedding_url("siliconflow")
        assert url == "https://embedding.siliconflow.cn/v1"

        priority = parser.get_url_priority("siliconflow")
        assert priority == URLPriority.PROVIDER_SPECIFIC

    def test_anthropic_provider(self):
        """测试Anthropic提供商"""
        config = {
            "embedding_base_url": None,
            "anthropic_embedding_base_url": "https://api.anthropic.com/v1",
            "anthropic_base_url": None
        }
        parser = URLConfigParser(config)

        url = parser.resolve_embedding_url("anthropic")
        assert url == "https://api.anthropic.com/v1"

        priority = parser.get_url_priority("anthropic")
        assert priority == URLPriority.PROVIDER_SPECIFIC

    def test_local_provider(self):
        """测试本地提供商"""
        config = {
            "embedding_base_url": None,
            "local_embedding_base_url": None,
            "local_base_url": None
        }
        parser = URLConfigParser(config)

        url = parser.resolve_embedding_url("local")
        assert url is None

        priority = parser.get_url_priority("local")
        assert priority == URLPriority.SHARED

    def test_unsupported_provider(self):
        """测试不支持的提供商"""
        config = {}
        parser = URLConfigParser(config)

        with pytest.raises(ValueError, match="Unsupported embedding provider: invalid"):
            parser.resolve_embedding_url("invalid")

    def test_url_validation_valid(self):
        """测试URL验证 - 有效URL"""
        config = {}
        parser = URLConfigParser(config)

        # 测试HTTPS URL
        result = parser.validate_url("https://api.example.com/v1")
        assert result["valid"] is True
        assert result["error"] is None

        # 测试HTTP URL
        result = parser.validate_url("http://api.example.com/v1")
        assert result["valid"] is True
        assert result["error"] is None

    def test_url_validation_invalid(self):
        """测试URL验证 - 无效URL"""
        config = {}
        parser = URLConfigParser(config)

        # 测试无效格式
        result = parser.validate_url("invalid-url")
        assert result["valid"] is False
        assert "Invalid URL format" in result["error"]

        # 测试空URL
        result = parser.validate_url("")
        assert result["valid"] is True  # 空URL被认为是有效的（未配置）

        # 测试None
        result = parser.validate_url(None)
        assert result["valid"] is True  # None被认为是有效的（未配置）

    def test_get_all_embedding_urls(self):
        """测试获取所有embedding URL配置"""
        config = {
            "embedding_base_url": "https://independent.com/v1",
            "openai_embedding_base_url": "https://api.openai.com/v1",
            "deepseek_embedding_base_url": "https://embedding.deepseek.com/v1",
            "siliconflow_embedding_base_url": "https://embedding.siliconflow.cn/v1",
            "anthropic_embedding_base_url": "https://api.anthropic.com/v1"
        }
        parser = URLConfigParser(config)

        all_urls = parser.get_all_embedding_urls()

        assert all_urls["embedding_base_url"] == "https://independent.com/v1"
        assert all_urls["openai_embedding_base_url"] == "https://api.openai.com/v1"
        assert all_urls["deepseek_embedding_base_url"] == "https://embedding.deepseek.com/v1"
        assert all_urls["siliconflow_embedding_base_url"] == "https://embedding.siliconflow.cn/v1"
        assert all_urls["anthropic_embedding_base_url"] == "https://api.anthropic.com/v1"

    def test_priority_override(self):
        """测试优先级覆盖"""
        config = {
            "embedding_base_url": "https://independent.com/v1",
            "deepseek_embedding_base_url": "https://embedding.deepseek.com/v1",
            "deepseek_base_url": "https://api.deepseek.com/v1"
        }
        parser = URLConfigParser(config)

        # 独立URL应该覆盖所有其他配置
        url = parser.resolve_embedding_url("deepseek")
        assert url == "https://independent.com/v1"

        # 提供商特定URL应该覆盖共享URL
        config["embedding_base_url"] = None
        parser = URLConfigParser(config)
        url = parser.resolve_embedding_url("deepseek")
        assert url == "https://embedding.deepseek.com/v1"

    def test_legacy_url_fallback(self):
        """测试传统URL回退机制"""
        config = {
            "embedding_base_url": None,
            "deepseek_embedding_base_url": None,
            "deepseek_base_url": "https://api.deepseek.com/v1",
            "siliconflow_base_url": "https://api.siliconflow.cn/v1"
        }
        parser = URLConfigParser(config)

        # DeepSeek应该使用传统URL
        url = parser.resolve_embedding_url("deepseek")
        assert url == "https://api.deepseek.com/v1"

        # SiliconFlow应该使用传统URL
        url = parser.resolve_embedding_url("siliconflow")
        assert url == "https://api.siliconflow.cn/v1"

        # OpenAI应该返回None（使用默认URL）
        url = parser.resolve_embedding_url("openai")
        assert url is None

        # Anthropic应该返回None（使用默认URL）
        url = parser.resolve_embedding_url("anthropic")
        assert url is None

    def test_complex_configuration(self):
        """测试复杂配置场景"""
        config = {
            "embedding_base_url": "https://global-embedding.com/v1",
            "openai_embedding_base_url": "https://api.openai.com/v1",
            "deepseek_embedding_base_url": "https://embedding.deepseek.com/v1",
            "siliconflow_embedding_base_url": "https://embedding.siliconflow.cn/v1",
            "anthropic_embedding_base_url": "https://api.anthropic.com/v1",
            "deepseek_base_url": "https://api.deepseek.com/v1",
            "siliconflow_base_url": "https://api.siliconflow.cn/v1"
        }
        parser = URLConfigParser(config)

        # 所有提供商都应该使用独立URL
        for provider in ["openai", "deepseek", "siliconflow", "anthropic"]:
            url = parser.resolve_embedding_url(provider)
            assert url == "https://global-embedding.com/v1"
            priority = parser.get_url_priority(provider)
            assert priority == URLPriority.INDEPENDENT

    def test_empty_config(self):
        """测试空配置"""
        config = {}
        parser = URLConfigParser(config)

        # 所有提供商都应该返回None
        for provider in ["openai", "deepseek", "siliconflow", "anthropic", "local"]:
            url = parser.resolve_embedding_url(provider)
            assert url is None
            priority = parser.get_url_priority(provider)
            assert priority == URLPriority.SHARED

    def test_partial_config(self):
        """测试部分配置"""
        config = {
            "deepseek_embedding_base_url": "https://embedding.deepseek.com/v1",
            "siliconflow_base_url": "https://api.siliconflow.cn/v1"
        }
        parser = URLConfigParser(config)

        # DeepSeek应该使用提供商特定URL
        url = parser.resolve_embedding_url("deepseek")
        assert url == "https://embedding.deepseek.com/v1"

        # SiliconFlow应该使用共享URL
        url = parser.resolve_embedding_url("siliconflow")
        assert url == "https://api.siliconflow.cn/v1"

        # 其他提供商应该返回None
        for provider in ["openai", "anthropic", "local"]:
            url = parser.resolve_embedding_url(provider)
            assert url is None


class TestURLPriority:
    """URL优先级枚举测试"""

    def test_priority_order(self):
        """测试优先级顺序"""
        assert URLPriority.INDEPENDENT.value < URLPriority.PROVIDER_SPECIFIC.value
        assert URLPriority.PROVIDER_SPECIFIC.value < URLPriority.SHARED.value

    def test_priority_comparison(self):
        """测试优先级比较"""
        assert URLPriority.INDEPENDENT.value < URLPriority.PROVIDER_SPECIFIC.value
        assert URLPriority.PROVIDER_SPECIFIC.value < URLPriority.SHARED.value
        assert URLPriority.INDEPENDENT.value < URLPriority.SHARED.value


class TestURLConfigParserIntegration:
    """URL配置解析器集成测试"""

    def test_real_world_scenario_1(self):
        """测试真实场景1：企业级配置"""
        config = {
            "embedding_base_url": "https://enterprise-embedding.company.com/v1",
            "openai_embedding_base_url": "https://api.openai.com/v1",
            "deepseek_embedding_base_url": "https://embedding.deepseek.com/v1",
            "siliconflow_embedding_base_url": "https://embedding.siliconflow.cn/v1",
            "anthropic_embedding_base_url": "https://api.anthropic.com/v1"
        }
        parser = URLConfigParser(config)

        # 所有提供商都应该使用企业级独立URL
        for provider in ["openai", "deepseek", "siliconflow", "anthropic"]:
            url = parser.resolve_embedding_url(provider)
            assert url == "https://enterprise-embedding.company.com/v1"

    def test_real_world_scenario_2(self):
        """测试真实场景2：混合配置"""
        config = {
            "embedding_base_url": None,
            "openai_embedding_base_url": "https://api.openai.com/v1",
            "deepseek_embedding_base_url": None,
            "siliconflow_embedding_base_url": "https://embedding.siliconflow.cn/v1",
            "deepseek_base_url": "https://api.deepseek.com/v1",
            "siliconflow_base_url": "https://api.siliconflow.cn/v1"
        }
        parser = URLConfigParser(config)

        # OpenAI应该使用提供商特定URL
        url = parser.resolve_embedding_url("openai")
        assert url == "https://api.openai.com/v1"

        # DeepSeek应该使用共享URL
        url = parser.resolve_embedding_url("deepseek")
        assert url == "https://api.deepseek.com/v1"

        # SiliconFlow应该使用提供商特定URL
        url = parser.resolve_embedding_url("siliconflow")
        assert url == "https://embedding.siliconflow.cn/v1"

    def test_real_world_scenario_3(self):
        """测试真实场景3：开发环境配置"""
        config = {
            "embedding_base_url": "https://dev-embedding.company.com/v1",
            "openai_embedding_base_url": None,
            "deepseek_embedding_base_url": None,
            "siliconflow_embedding_base_url": None,
            "anthropic_embedding_base_url": None
        }
        parser = URLConfigParser(config)

        # 所有提供商都应该使用开发环境独立URL
        for provider in ["openai", "deepseek", "siliconflow", "anthropic"]:
            url = parser.resolve_embedding_url(provider)
            assert url == "https://dev-embedding.company.com/v1"
