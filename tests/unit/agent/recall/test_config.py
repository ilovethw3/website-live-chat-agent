"""
召回配置单元测试
"""

from unittest.mock import patch

from src.agent.recall.config import load_recall_config, parse_source_weights, validate_recall_config


class TestLoadRecallConfig:
    """测试配置加载"""

    @patch('src.agent.recall.config.settings')
    def test_load_recall_config_basic(self, mock_settings):
        """测试基础配置加载"""
        mock_settings.recall_sources = ["vector", "faq"]
        mock_settings.recall_source_weights = "vector:1.0,faq:0.8"
        mock_settings.recall_timeout_ms = 3000
        mock_settings.recall_retry = 1
        mock_settings.recall_merge_strategy = "weighted"
        mock_settings.recall_degrade_threshold = 0.5
        mock_settings.recall_fallback_enabled = True
        mock_settings.recall_experiment_enabled = False
        mock_settings.recall_experiment_platform = None

        config = load_recall_config()

        assert config["sources"] == ["vector", "faq"]
        assert config["weights"]["vector"] == 1.0
        assert config["weights"]["faq"] == 0.8
        assert config["timeout_ms"] == 3000
        assert config["retry"] == 1
        assert config["merge_strategy"] == "weighted"
        assert config["degrade_threshold"] == 0.5
        assert config["fallback_enabled"] is True
        assert config["experiment_enabled"] is False
        assert config["experiment_platform"] is None

    @patch('src.agent.recall.config.settings')
    def test_load_recall_config_with_experiment(self, mock_settings):
        """测试实验配置"""
        mock_settings.recall_sources = ["vector"]
        mock_settings.recall_source_weights = "vector:1.0"
        mock_settings.recall_timeout_ms = 3000
        mock_settings.recall_retry = 1
        mock_settings.recall_merge_strategy = "weighted"
        mock_settings.recall_degrade_threshold = 0.5
        mock_settings.recall_fallback_enabled = True
        mock_settings.recall_experiment_enabled = True
        mock_settings.recall_experiment_platform = "internal"

        config = load_recall_config()

        assert config["experiment_enabled"] is True
        assert config["experiment_platform"] == "internal"


class TestParseSourceWeights:
    """测试权重解析"""

    def test_parse_source_weights_basic(self):
        """测试基础权重解析"""
        weights_str = "vector:1.0,faq:0.8,keyword:0.6"

        weights = parse_source_weights(weights_str)

        assert weights["vector"] == 1.0
        assert weights["faq"] == 0.8
        assert weights["keyword"] == 0.6

    def test_parse_source_weights_empty(self):
        """测试空权重字符串"""
        weights = parse_source_weights("")

        assert weights == {}

    def test_parse_source_weights_none(self):
        """测试None权重字符串"""
        weights = parse_source_weights(None)

        assert weights == {}

    def test_parse_source_weights_invalid_format(self):
        """测试无效格式"""
        weights_str = "vector:1.0,invalid_format,faq:0.8"

        weights = parse_source_weights(weights_str)

        # 应该忽略无效格式，保留有效部分
        assert weights["vector"] == 1.0
        assert weights["faq"] == 0.8
        assert "invalid_format" not in weights

    def test_parse_source_weights_with_spaces(self):
        """测试带空格的权重字符串"""
        weights_str = " vector : 1.0 , faq : 0.8 "

        weights = parse_source_weights(weights_str)

        assert weights["vector"] == 1.0
        assert weights["faq"] == 0.8


class TestValidateRecallConfig:
    """测试配置验证"""

    def test_validate_recall_config_valid(self):
        """测试有效配置"""
        config = {
            "sources": ["vector", "faq"],
            "weights": {"vector": 1.0, "faq": 0.8},
            "timeout_ms": 3000,
            "retry": 1,
            "degrade_threshold": 0.5
        }

        results = validate_recall_config(config)

        assert results["sources_valid"] is True
        assert results["timeout_valid"] is True
        assert results["retry_valid"] is True
        assert results["threshold_valid"] is True

    def test_validate_recall_config_invalid_sources(self):
        """测试无效召回源"""
        config = {
            "sources": ["vector", "invalid_source"],
            "weights": {"vector": 1.0},
            "timeout_ms": 3000,
            "retry": 1,
            "degrade_threshold": 0.5
        }

        results = validate_recall_config(config)

        assert results["sources_valid"] is False
        assert "invalid_source" in results["invalid_sources"]

    def test_validate_recall_config_invalid_timeout(self):
        """测试无效超时"""
        config = {
            "sources": ["vector"],
            "weights": {"vector": 1.0},
            "timeout_ms": 50,  # 低于最小值
            "retry": 1,
            "degrade_threshold": 0.5
        }

        results = validate_recall_config(config)

        assert results["timeout_valid"] is False

    def test_validate_recall_config_invalid_retry(self):
        """测试无效重试次数"""
        config = {
            "sources": ["vector"],
            "weights": {"vector": 1.0},
            "timeout_ms": 3000,
            "retry": 5,  # 超过最大值
            "degrade_threshold": 0.5
        }

        results = validate_recall_config(config)

        assert results["retry_valid"] is False

    def test_validate_recall_config_invalid_threshold(self):
        """测试无效降级阈值"""
        config = {
            "sources": ["vector"],
            "weights": {"vector": 1.0},
            "timeout_ms": 3000,
            "retry": 1,
            "degrade_threshold": 1.5  # 超过最大值
        }

        results = validate_recall_config(config)

        assert results["threshold_valid"] is False

    def test_validate_recall_config_missing_weights(self):
        """测试缺失权重配置"""
        config = {
            "sources": ["vector", "faq"],
            "weights": {"vector": 1.0},  # 缺少faq权重
            "timeout_ms": 3000,
            "retry": 1,
            "degrade_threshold": 0.5
        }

        validate_recall_config(config)

        # 应该为缺失的源设置默认权重
        assert "faq" in config["weights"]
        assert config["weights"]["faq"] == 1.0
