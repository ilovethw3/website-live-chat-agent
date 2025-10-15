# 模型配置分离指南

## 概述

本指南介绍如何配置独立的LLM和Embedding模型，实现混合模型组合使用。通过插件化架构，系统支持灵活的模型提供商选择和配置。

## 配置原理

### 传统配置 vs 分离配置

**传统配置（单一提供商）**:
```bash
# 所有模型使用同一提供商
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_MODEL=deepseek-chat
EMBEDDING_PROVIDER=deepseek  # 必须相同
EMBEDDING_MODEL=deepseek-embedding
```

**分离配置（混合提供商）**:
```bash
# LLM和Embedding可以独立选择提供商
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-key
DEEPSEEK_MODEL=deepseek-chat

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
EMBEDDING_MODEL=text-embedding-3-small
```

### 独立URL配置原理

系统支持Embedding模型的独立URL配置，实现LLM和Embedding的完全独立部署：

**智能优先级机制**:
1. **独立URL** (最高优先级): `EMBEDDING_BASE_URL`
2. **提供商特定URL**: `DEEPSEEK_EMBEDDING_BASE_URL`, `OPENAI_EMBEDDING_BASE_URL` 等
3. **共享URL** (最低优先级): 传统的 `DEEPSEEK_BASE_URL`, `SILICONFLOW_BASE_URL` 等

**配置示例**:
```bash
# 使用独立URL（最高优先级）
EMBEDDING_BASE_URL=https://custom-embedding-api.com/v1

# 或使用提供商特定URL
DEEPSEEK_EMBEDDING_BASE_URL=https://embedding.deepseek.com/v1
OPENAI_EMBEDDING_BASE_URL=https://api.openai.com/v1

# 或回退到共享URL（向后兼容）
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

## 配置示例

### 1. 基础配置分离

#### DeepSeek LLM + OpenAI Embedding
```bash
# LLM配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# Embedding配置
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
EMBEDDING_MODEL=text-embedding-3-small
```

#### OpenAI LLM + DeepSeek Embedding
```bash
# LLM配置
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o-mini

# Embedding配置
EMBEDDING_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
EMBEDDING_MODEL=deepseek-embedding
```

### 2. 硅基流动平台配置

#### 完全使用硅基流动
```bash
# LLM配置
LLM_PROVIDER=siliconflow
SILICONFLOW_API_KEY=your-sf-key
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct

# Embedding配置
EMBEDDING_PROVIDER=siliconflow
SILICONFLOW_EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

#### 混合使用硅基流动
```bash
# DeepSeek LLM + 硅基流动 Embedding
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_MODEL=deepseek-chat

EMBEDDING_PROVIDER=siliconflow
SILICONFLOW_API_KEY=your-sf-key
SILICONFLOW_EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

### 3. 独立URL配置

#### 使用独立URL（最高优先级）
```bash
# LLM配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# Embedding配置 - 使用独立URL
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
EMBEDDING_BASE_URL=https://custom-embedding-api.com/v1  # 独立URL
EMBEDDING_MODEL=text-embedding-3-small
```

#### 使用提供商特定URL
```bash
# LLM配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# Embedding配置 - 使用提供商特定URL
EMBEDDING_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_EMBEDDING_BASE_URL=https://embedding.deepseek.com/v1  # 提供商特定URL
EMBEDDING_MODEL=deepseek-embedding
```

#### 混合URL配置
```bash
# LLM使用默认URL，Embedding使用独立URL
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o-mini

# Embedding使用独立URL
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_EMBEDDING_BASE_URL=https://custom-openai-embedding.com/v1
EMBEDDING_MODEL=text-embedding-3-small
```

### 4. 高级配置

#### 性能优化配置
```bash
# 使用高性能LLM + 经济型Embedding
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o  # 高性能模型

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
EMBEDDING_MODEL=text-embedding-3-small  # 经济型模型
```

#### 成本优化配置
```bash
# 使用经济型LLM + 高性能Embedding
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_MODEL=deepseek-chat  # 经济型模型

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
EMBEDDING_MODEL=text-embedding-3-large  # 高性能模型
```

#### 完全独立部署配置
```bash
# LLM和Embedding完全独立部署
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://llm-api.company.com/v1
DEEPSEEK_MODEL=deepseek-chat

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
EMBEDDING_BASE_URL=https://embedding-api.company.com/v1
EMBEDDING_MODEL=text-embedding-3-small
```

## 配置验证

### 自动验证

系统提供自动配置验证功能：

```python
from src.core.config import settings

# 验证配置
validation_results = settings.validate_configuration()
print(validation_results)

# 输出示例:
# {
#     "llm_valid": True,
#     "embedding_valid": True,
#     "llm_error": None,
#     "embedding_error": None
# }
```

### 手动验证

```python
from src.services.llm_factory import create_llm, create_embeddings

try:
    # 测试LLM配置
    llm = create_llm()
    print("✅ LLM配置有效")
except Exception as e:
    print(f"❌ LLM配置错误: {e}")

try:
    # 测试Embedding配置
    embeddings = create_embeddings()
    print("✅ Embedding配置有效")
except Exception as e:
    print(f"❌ Embedding配置错误: {e}")
```

## 迁移指南

### 从旧配置迁移

#### 1. 保持现有配置（向后兼容）
```bash
# 现有配置继续工作
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_MODEL=deepseek-chat
```

#### 2. 逐步添加独立配置
```bash
# 添加Embedding独立配置
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
EMBEDDING_MODEL=text-embedding-3-small
```

#### 3. 测试新配置
```python
# 验证配置
from src.core.config import settings
results = settings.validate_configuration()
assert results["llm_valid"] and results["embedding_valid"]
```

#### 4. 切换到新配置
```bash
# 完全切换到新配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-key
DEEPSEEK_MODEL=deepseek-chat

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
EMBEDDING_MODEL=text-embedding-3-small
```

### 使用迁移工具

```python
from src.core.migration import migrate_legacy_config, generate_migration_report

# 执行迁移
migration_result = migrate_legacy_config()
print(f"迁移成功: {migration_result['success']}")

# 生成迁移报告
report = generate_migration_report()
print(report)
```

## 最佳实践

### 1. 配置管理

#### 环境变量管理
```bash
# .env 文件
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
DEEPSEEK_MODEL=deepseek-chat

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=${OPENAI_API_KEY}
EMBEDDING_MODEL=text-embedding-3-small
```

#### 配置模板
```bash
# 开发环境
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=dev-key
DEEPSEEK_MODEL=deepseek-chat

# 生产环境
LLM_PROVIDER=openai
OPENAI_API_KEY=prod-key
OPENAI_MODEL=gpt-4o
```

### 2. 性能优化

#### 模型选择策略
- **LLM**: 根据任务复杂度选择模型
  - 简单任务: gpt-3.5-turbo, deepseek-chat
  - 复杂任务: gpt-4o, Qwen/Qwen2.5-72B-Instruct

- **Embedding**: 根据语言和精度需求选择
  - 中文: BAAI/bge-large-zh-v1.5
  - 英文: text-embedding-3-large
  - 多语言: text-embedding-3-small

#### 成本优化
```bash
# 成本敏感配置
LLM_PROVIDER=deepseek  # 经济型LLM
DEEPSEEK_MODEL=deepseek-chat

EMBEDDING_PROVIDER=openai  # 高质量Embedding
EMBEDDING_MODEL=text-embedding-3-small
```

### 3. 安全考虑

#### API密钥管理
```bash
# 使用环境变量
export DEEPSEEK_API_KEY="sk-your-key"
export OPENAI_API_KEY="sk-your-key"

# 或使用密钥管理服务
export DEEPSEEK_API_KEY=$(aws ssm get-parameter --name "/app/deepseek-key" --query "Parameter.Value" --output text)
```

#### 访问控制
```python
# 实现API密钥轮换
def rotate_api_keys():
    # 轮换逻辑
    pass
```

## 故障排除

### 常见问题

#### 1. 配置错误
```bash
# 错误: 缺少必需的API密钥
ValueError: DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek

# 解决: 添加API密钥
DEEPSEEK_API_KEY=your-key
```

#### 2. 连接失败
```bash
# 错误: 网络连接问题
ConnectionError: Failed to connect to api.deepseek.com

# 解决: 检查网络和API状态
curl -H "Authorization: Bearer your-key" https://api.deepseek.com/v1/models
```

#### 3. 模型不支持
```bash
# 错误: 模型不存在
ModelError: Model 'invalid-model' not found

# 解决: 使用支持的模型
DEEPSEEK_MODEL=deepseek-chat  # 正确
```

#### 4. URL配置冲突
```bash
# 错误: URL格式不正确
ValueError: Invalid URL format: invalid-url. Must start with http:// or https://

# 解决: 使用正确的URL格式
EMBEDDING_BASE_URL=https://api.example.com/v1  # 正确
```

#### 5. 优先级配置问题
```bash
# 问题: 同时配置了多个URL，不确定使用哪个
EMBEDDING_BASE_URL=https://custom-api.com/v1
DEEPSEEK_EMBEDDING_BASE_URL=https://embedding.deepseek.com/v1
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 解决: 系统会按优先级选择 EMBEDDING_BASE_URL
# 优先级: 独立URL > 提供商特定URL > 共享URL
```

#### 6. 向后兼容性问题
```bash
# 问题: 现有配置可能不工作
# 旧配置
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
EMBEDDING_PROVIDER=deepseek

# 新配置需要明确指定
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
EMBEDDING_PROVIDER=deepseek
# 或者使用新的独立URL配置
DEEPSEEK_EMBEDDING_BASE_URL=https://embedding.deepseek.com/v1
```

### 调试工具

#### 启用详细日志
```python
import logging
logging.getLogger("src.services.providers").setLevel(logging.DEBUG)
```

#### 测试连接
```python
from src.services.providers import create_provider

# 测试OpenAI连接
provider = create_provider("openai_llm", {"api_key": "test-key"})
is_valid = provider.validate_connection()
print(f"OpenAI连接有效: {is_valid}")
```

#### 配置检查
```python
from src.core.config import settings

# 检查当前配置
print(f"LLM提供商: {settings.llm_provider}")
print(f"Embedding提供商: {settings.embedding_provider}")
print(f"LLM模型: {settings.llm_model_name}")
print(f"Embedding模型: {settings.embedding_model_name}")
```

## 相关文档

- [插件系统架构](../architecture/plugin-system.md)
- [迁移指南](../migration/legacy-to-plugin.md)
- [API文档](../../api/openapi.yaml)
