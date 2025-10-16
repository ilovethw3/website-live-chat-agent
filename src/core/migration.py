"""
配置迁移工具

提供从旧配置到插件化架构的迁移功能。
"""

import logging
from typing import Any, Dict

from src.core.config import settings

logger = logging.getLogger(__name__)


def migrate_legacy_config() -> Dict[str, Any]:
    """
    迁移旧配置到插件化架构

    Returns:
        迁移后的配置字典
    """
    migration_result = {
        "success": True,
        "changes": [],
        "warnings": [],
        "new_config": {}
    }

    try:
        # 检查是否需要迁移
        if _is_legacy_config():
            logger.info("检测到旧配置，开始迁移到插件化架构")

            # 迁移LLM配置
            llm_config = _migrate_llm_config()
            if llm_config:
                migration_result["new_config"].update(llm_config)
                migration_result["changes"].append("LLM配置已迁移到插件化架构")

            # 迁移Embedding配置
            embedding_config = _migrate_embedding_config()
            if embedding_config:
                migration_result["new_config"].update(embedding_config)
                migration_result["changes"].append("Embedding配置已迁移到插件化架构")

            # 添加硅基流动平台支持
            siliconflow_config = _add_siliconflow_support()
            if siliconflow_config:
                migration_result["new_config"].update(siliconflow_config)
                migration_result["changes"].append("已添加硅基流动平台支持")

            logger.info("配置迁移完成")
        else:
            logger.info("配置已经是插件化架构，无需迁移")
            migration_result["changes"].append("配置已经是插件化架构")

    except Exception as e:
        logger.error(f"配置迁移失败: {e}")
        migration_result["success"] = False
        migration_result["warnings"].append(f"迁移失败: {str(e)}")

    return migration_result


def _is_legacy_config() -> bool:
    """检查是否为旧配置"""
    # 检查是否存在新的插件化配置
    return not hasattr(settings, 'siliconflow_api_key')


def _migrate_llm_config() -> Dict[str, Any]:
    """迁移LLM配置"""
    config = {}

    # 保持现有LLM配置不变（向后兼容）
    if settings.llm_provider:
        config["LLM_PROVIDER"] = settings.llm_provider

    if hasattr(settings, 'deepseek_api_key') and settings.deepseek_api_key:
        config["DEEPSEEK_API_KEY"] = settings.deepseek_api_key
        config["DEEPSEEK_BASE_URL"] = settings.deepseek_base_url
        config["DEEPSEEK_MODEL"] = settings.deepseek_model

    if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
        config["OPENAI_API_KEY"] = settings.openai_api_key
        config["OPENAI_MODEL"] = settings.openai_model

    if hasattr(settings, 'anthropic_api_key') and settings.anthropic_api_key:
        config["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        config["ANTHROPIC_MODEL"] = settings.anthropic_model

    return config


def _migrate_embedding_config() -> Dict[str, Any]:
    """迁移Embedding配置"""
    config = {}

    # 保持现有Embedding配置不变（向后兼容）
    if settings.embedding_provider:
        config["EMBEDDING_PROVIDER"] = settings.embedding_provider

    if hasattr(settings, 'embedding_model'):
        config["EMBEDDING_MODEL"] = settings.embedding_model

    if hasattr(settings, 'embedding_dim'):
        config["EMBEDDING_DIM"] = settings.embedding_dim

    return config


def _add_siliconflow_support() -> Dict[str, Any]:
    """添加硅基流动平台支持"""
    config = {}

    # 添加硅基流动平台配置（如果不存在）
    if not hasattr(settings, 'siliconflow_api_key'):
        config["SILICONFLOW_API_KEY"] = ""
        config["SILICONFLOW_BASE_URL"] = "https://api.siliconflow.cn/v1"
        config["SILICONFLOW_LLM_MODEL"] = "Qwen/Qwen2.5-7B-Instruct"
        config["SILICONFLOW_EMBEDDING_MODEL"] = "BAAI/bge-large-zh-v1.5"

    return config


def validate_migrated_config() -> Dict[str, Any]:
    """
    验证迁移后的配置

    Returns:
        验证结果
    """
    validation_result = {
        "success": True,
        "llm_valid": False,
        "embedding_valid": False,
        "errors": [],
        "warnings": []
    }

    try:
        # 验证LLM配置
        try:
            from src.services.llm_factory import create_llm
            create_llm()  # 验证LLM配置
            validation_result["llm_valid"] = True
        except Exception as e:
            validation_result["errors"].append(f"LLM配置验证失败: {str(e)}")

        # 验证Embedding配置
        try:
            from src.services.llm_factory import create_embeddings
            create_embeddings()  # 验证Embedding配置
            validation_result["embedding_valid"] = True
        except Exception as e:
            validation_result["errors"].append(f"Embedding配置验证失败: {str(e)}")

        # 检查混合模型组合
        if settings.llm_provider != settings.embedding_provider:
            validation_result["warnings"].append(
                f"检测到混合模型组合: LLM={settings.llm_provider}, Embedding={settings.embedding_provider}"
            )

        validation_result["success"] = len(validation_result["errors"]) == 0

    except Exception as e:
        validation_result["success"] = False
        validation_result["errors"].append(f"配置验证失败: {str(e)}")

    return validation_result


def generate_migration_report() -> str:
    """
    生成迁移报告

    Returns:
        迁移报告字符串
    """
    report = []
    report.append("# 配置迁移报告")
    report.append("")

    # 执行迁移
    migration_result = migrate_legacy_config()

    if migration_result["success"]:
        report.append("✅ 迁移状态: 成功")
    else:
        report.append("❌ 迁移状态: 失败")

    report.append("")
    report.append("## 变更内容")
    for change in migration_result["changes"]:
        report.append(f"- {change}")

    if migration_result["warnings"]:
        report.append("")
        report.append("## 警告")
        for warning in migration_result["warnings"]:
            report.append(f"- ⚠️ {warning}")

    # 验证配置
    validation_result = validate_migrated_config()

    report.append("")
    report.append("## 配置验证")
    if validation_result["llm_valid"]:
        report.append("✅ LLM配置: 有效")
    else:
        report.append("❌ LLM配置: 无效")

    if validation_result["embedding_valid"]:
        report.append("✅ Embedding配置: 有效")
    else:
        report.append("❌ Embedding配置: 无效")

    if validation_result["errors"]:
        report.append("")
        report.append("## 错误")
        for error in validation_result["errors"]:
            report.append(f"- ❌ {error}")

    if validation_result["warnings"]:
        report.append("")
        report.append("## 配置警告")
        for warning in validation_result["warnings"]:
            report.append(f"- ⚠️ {warning}")

    return "\n".join(report)
