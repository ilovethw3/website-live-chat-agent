# 从旧配置迁移到插件化架构指南

## 概述

本指南帮助用户从传统的单一提供商配置迁移到新的插件化架构，支持模型配置分离和混合模型组合。

## 迁移优势

### 传统架构限制
- ❌ LLM和Embedding必须使用同一提供商
- ❌ 配置僵化，难以优化成本
- ❌ 平台选择有限
- ❌ 难以实现混合模型组合

### 插件化架构优势
- ✅ LLM和Embedding可独立配置不同提供商
- ✅ 支持成本优化和性能调优
- ✅ 支持硅基流动等新平台
- ✅ 灵活的混合模型组合

## 迁移步骤

### 步骤1: 备份现有配置

```bash
# 备份当前配置
cp .env .env.backup

# 记录当前配置
echo "当前配置:" > migration.log
echo "LLM_PROVIDER=$LLM_PROVIDER" >> migration.log
echo "DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY" >> migration.log
echo "DEEPSEEK_MODEL=$DEEPSEEK_MODEL" >> migration.log
```

### 步骤2: 检查兼容性

```python
# 检查当前配置是否兼容
from src.core.config import settings

print(f"当前LLM提供商: {settings.llm_provider}")
print(f"当前Embedding提供商: {settings.embedding_provider}")

# 验证配置有效性
try:
    from src.services.llm_factory import create_llm, create_embeddings
    llm = create_llm()
    embeddings = create_embeddings()
    print("✅ 当前配置兼容插件化架构")
except Exception as e:
    print(f"❌ 配置不兼容: {e}")
```

### 步骤3: 执行自动迁移

```python
# 使用迁移工具
from src.core.migration import migrate_legacy_config, generate_migration_report

# 执行迁移
migration_result = migrate_legacy_config()
print(f"迁移成功: {migration_result['success']}")

# 查看变更
for change in migration_result['changes']:
    print(f"- {change}")

# 生成详细报告
report = generate_migration_report()
print(report)
```

### 步骤4: 验证迁移结果

```python
# 验证迁移后的配置
from src.core.migration import validate_migrated_config

validation_result = validate_migrated_config()
print(f"LLM配置有效: {validation_result['llm_valid']}")
print(f"Embedding配置有效: {validation_result['embedding_valid']}")

if validation_result['errors']:
    for error in validation_result['errors']:
        print(f"❌ 错误: {error}")
```

## 迁移场景

### 场景1: 保持现有配置（向后兼容）

**目标**: 保持现有功能不变，仅升级架构

```bash
# 现有配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_MODEL=deepseek-chat
EMBEDDING_PROVIDER=deepseek
EMBEDDING_MODEL=deepseek-embedding

# 迁移后（无需修改）
# 配置保持不变，系统自动适配插件化架构
```

**验证**:
```python
# 验证功能正常
from src.services.llm_factory import create_llm, create_embeddings

llm = create_llm()
embeddings = create_embeddings()
print("✅ 现有配置继续工作")
```

### 场景2: 实现配置分离

**目标**: 将LLM和Embedding配置分离，使用不同提供商

```bash
# 原始配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_MODEL=deepseek-chat
EMBEDDING_PROVIDER=deepseek
EMBEDDING_MODEL=deepseek-embedding

# 迁移后配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-key
DEEPSEEK_MODEL=deepseek-chat

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
EMBEDDING_MODEL=text-embedding-3-small
```

**优势**:
- 使用DeepSeek的经济型LLM
- 使用OpenAI的高质量Embedding
- 实现成本优化

### 场景3: 添加硅基流动平台支持

**目标**: 集成硅基流动平台，实现混合模型组合

```bash
# 原始配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_MODEL=deepseek-chat

# 迁移后配置
LLM_PROVIDER=siliconflow
SILICONFLOW_API_KEY=your-sf-key
SILICONFLOW_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
EMBEDDING_MODEL=text-embedding-3-small
```

**优势**:
- 使用硅基流动的高性能LLM
- 使用OpenAI的稳定Embedding
- 实现性能优化

### 场景4: 完全重构配置

**目标**: 重新设计配置架构，实现最佳性能

```bash
# 原始配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_MODEL=deepseek-chat

# 新配置设计
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini

EMBEDDING_PROVIDER=siliconflow
SILICONFLOW_API_KEY=your-sf-key
SILICONFLOW_EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

**优势**:
- 使用OpenAI的稳定LLM
- 使用硅基流动的高质量中文Embedding
- 实现最佳性能组合

## 迁移工具使用

### 自动迁移工具

```python
from src.core.migration import (
    migrate_legacy_config,
    validate_migrated_config,
    generate_migration_report
)

# 1. 执行迁移
migration_result = migrate_legacy_config()

# 2. 验证结果
validation_result = validate_migrated_config()

# 3. 生成报告
report = generate_migration_report()
print(report)
```

### 手动迁移步骤

#### 1. 分析现有配置
```python
from src.core.config import settings

print("=== 当前配置分析 ===")
print(f"LLM提供商: {settings.llm_provider}")
print(f"LLM模型: {settings.llm_model_name}")
print(f"Embedding提供商: {settings.embedding_provider}")
print(f"Embedding模型: {settings.embedding_model_name}")
```

#### 2. 设计新配置
```python
# 根据需求设计新配置
new_config = {
    "LLM_PROVIDER": "deepseek",  # 或 "openai", "siliconflow"
    "DEEPSEEK_API_KEY": "your-key",
    "DEEPSEEK_MODEL": "deepseek-chat",
    
    "EMBEDDING_PROVIDER": "openai",  # 或 "deepseek", "siliconflow"
    "OPENAI_API_KEY": "your-openai-key",
    "EMBEDDING_MODEL": "text-embedding-3-small"
}
```

#### 3. 测试新配置
```python
# 临时设置新配置进行测试
import os
for key, value in new_config.items():
    os.environ[key] = value

# 重新加载配置
from src.core.config import settings
settings = Settings()

# 验证配置
results = settings.validate_configuration()
print(f"配置验证结果: {results}")
```

#### 4. 应用新配置
```bash
# 更新 .env 文件
echo "LLM_PROVIDER=deepseek" >> .env
echo "DEEPSEEK_API_KEY=your-key" >> .env
echo "DEEPSEEK_MODEL=deepseek-chat" >> .env
echo "EMBEDDING_PROVIDER=openai" >> .env
echo "OPENAI_API_KEY=your-openai-key" >> .env
echo "EMBEDDING_MODEL=text-embedding-3-small" >> .env
```

## 常见问题解决

### 问题1: 配置验证失败

**错误信息**:
```
ValueError: DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek
```

**解决方案**:
```bash
# 检查API密钥是否正确设置
echo $DEEPSEEK_API_KEY

# 如果为空，设置正确的密钥
export DEEPSEEK_API_KEY="sk-your-actual-key"
```

### 问题2: 模型不支持

**错误信息**:
```
ModelError: Model 'invalid-model' not found
```

**解决方案**:
```python
# 检查支持的模型
from src.services.providers import create_provider

provider = create_provider("deepseek_llm", {"api_key": "test", "base_url": "test"})
models = provider.get_models()
print(f"支持的模型: {models}")

# 使用支持的模型
DEEPSEEK_MODEL=deepseek-chat  # 正确
```

### 问题3: 连接失败

**错误信息**:
```
ConnectionError: Failed to connect to api.deepseek.com
```

**解决方案**:
```bash
# 测试网络连接
curl -H "Authorization: Bearer your-key" https://api.deepseek.com/v1/models

# 检查防火墙设置
ping api.deepseek.com

# 使用代理（如果需要）
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
```

### 问题4: 性能下降

**症状**: 响应时间增加，吞吐量下降

**解决方案**:
```python
# 性能分析
import time
from src.services.llm_factory import create_llm

# 测试LLM性能
start_time = time.time()
llm = create_llm()
# 执行测试请求
end_time = time.time()
print(f"LLM创建时间: {end_time - start_time:.2f}秒")

# 优化配置
# 1. 使用更快的模型
# 2. 调整并发设置
# 3. 启用缓存
```

## 回滚方案

### 紧急回滚

```bash
# 恢复备份配置
cp .env.backup .env

# 重启服务
systemctl restart your-service
```

### 渐进式回滚

```python
# 逐步回滚到稳定配置
rollback_config = {
    "LLM_PROVIDER": "deepseek",
    "DEEPSEEK_API_KEY": "stable-key",
    "DEEPSEEK_MODEL": "deepseek-chat",
    "EMBEDDING_PROVIDER": "deepseek",
    "EMBEDDING_MODEL": "deepseek-embedding"
}

# 应用回滚配置
for key, value in rollback_config.items():
    os.environ[key] = value
```

## 最佳实践

### 1. 迁移前准备
- ✅ 备份现有配置
- ✅ 测试迁移工具
- ✅ 准备回滚方案
- ✅ 通知相关团队

### 2. 迁移过程
- ✅ 分阶段迁移
- ✅ 充分测试
- ✅ 监控性能
- ✅ 记录变更

### 3. 迁移后验证
- ✅ 功能测试
- ✅ 性能测试
- ✅ 安全测试
- ✅ 用户验收

### 4. 持续优化
- ✅ 监控使用情况
- ✅ 优化配置
- ✅ 更新文档
- ✅ 培训团队

## 相关文档

- [模型配置分离指南](../configuration/model-separation.md)
- [插件系统架构](../architecture/plugin-system.md)
- [API文档](../../api/openapi.yaml)
