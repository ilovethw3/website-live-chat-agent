"""
召回Agent配置加载

从settings加载召回配置，包括：
- 召回源配置
- 权重配置
- 超时和重试配置
- 合并策略配置
- 降级配置
- 实验配置
"""

from typing import Any

from src.core.config import settings


def load_recall_config() -> dict[str, Any]:
    """
    从settings加载召回配置

    Returns:
        召回配置字典
    """
    # 解析权重配置
    weights = parse_source_weights(settings.recall_source_weights)

    config = {
        "sources": settings.recall_sources,
        "weights": weights,
        "timeout_ms": settings.recall_timeout_ms,
        "retry": settings.recall_retry,
        "merge_strategy": settings.recall_merge_strategy,
        "degrade_threshold": settings.recall_degrade_threshold,
        "fallback_enabled": settings.recall_fallback_enabled,
        "experiment_enabled": settings.recall_experiment_enabled,
        "experiment_platform": settings.recall_experiment_platform,
    }

    return config


def parse_source_weights(weights_str: str) -> dict[str, float]:
    """
    解析权重配置字符串

    Args:
        weights_str: 权重配置字符串，格式如 "vector:1.0,faq:0.8"

    Returns:
        权重字典
    """
    weights = {}

    if not weights_str:
        return weights

    for item in weights_str.split(","):
        item = item.strip()
        if ":" in item:
            try:
                source, weight = item.split(":", 1)
                weights[source.strip()] = float(weight.strip())
            except ValueError:
                # 忽略格式错误的配置项
                continue

    return weights


def validate_recall_config(config: dict[str, Any]) -> dict[str, bool]:
    """
    验证召回配置的有效性

    Args:
        config: 召回配置

    Returns:
        验证结果字典
    """
    results = {}

    # 验证召回源
    valid_sources = ["vector", "faq", "keyword"]
    invalid_sources = [s for s in config["sources"] if s not in valid_sources]
    results["sources_valid"] = len(invalid_sources) == 0
    if invalid_sources:
        results["invalid_sources"] = invalid_sources

    # 验证权重配置
    weights = config["weights"]
    for source in config["sources"]:
        if source not in weights:
            weights[source] = 1.0  # 设置默认权重

    # 验证超时配置
    timeout_ms = config["timeout_ms"]
    results["timeout_valid"] = 100 <= timeout_ms <= 10000

    # 验证重试配置
    retry = config["retry"]
    results["retry_valid"] = 0 <= retry <= 3

    # 验证降级阈值
    threshold = config["degrade_threshold"]
    results["threshold_valid"] = 0.0 <= threshold <= 1.0

    return results
