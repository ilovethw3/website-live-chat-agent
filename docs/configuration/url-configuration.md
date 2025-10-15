# URL配置指南

## 概述

本指南详细介绍Embedding模型URL的独立配置功能，包括智能优先级机制、配置解析器使用说明、高级配置技巧和常见问题解答。

## URL配置优先级机制

### 优先级层次

系统采用三层优先级机制，确保URL配置的灵活性和向后兼容性：

1. **独立URL** (最高优先级)
   - 环境变量: `EMBEDDING_BASE_URL`
   - 适用于所有提供商
   - 优先级最高，会覆盖其他所有URL配置

2. **提供商特定URL** (中等优先级)
   - 环境变量: `{PROVIDER}_EMBEDDING_BASE_URL`
   - 仅适用于特定提供商
   - 优先级高于共享URL

3. **共享URL** (最低优先级)
   - 环境变量: `{PROVIDER}_BASE_URL`
   - 传统配置方式
   - 向后兼容性保证

### 优先级示例

```bash
# 配置示例
EMBEDDING_BASE_URL=https://custom-embedding.com/v1          # 优先级1
DEEPSEEK_EMBEDDING_BASE_URL=https://embedding.deepseek.com/v1  # 优先级2
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1               # 优先级3

# 结果: 系统会使用 EMBEDDING_BASE_URL
```

## 配置解析器详解

### URLConfigParser类

配置解析器是URL配置的核心组件，负责智能解析和验证：

```python
from src.core.config_parser import URLConfigParser, URLPriority

# 创建解析器
config_dict = {
    "embedding_base_url": "https://custom.com/v1",
    "deepseek_embedding_base_url": "https://embedding.deepseek.com/v1",
    "deepseek_base_url": "https://api.deepseek.com/v1"
}
parser = URLConfigParser(config_dict)

# 解析URL
url = parser.resolve_embedding_url("deepseek")
print(url)  # 输出: https://custom.com/v1

# 获取优先级
priority = parser.get_url_priority("deepseek")
print(priority)  # 输出: URLPriority.INDEPENDENT
```

### 主要方法

#### resolve_embedding_url(provider)
解析指定提供商的embedding URL，按优先级返回。

**参数**:
- `provider`: 提供商名称 (openai, deepseek, siliconflow, anthropic)

**返回**:
- `Optional[str]`: 解析后的URL，如果未配置则返回None

**示例**:
```python
# 解析DeepSeek的embedding URL
url = parser.resolve_embedding_url("deepseek")
```

#### validate_url(url)
验证URL格式和有效性。

**参数**:
- `url`: 要验证的URL

**返回**:
- `Dict[str, Any]`: 验证结果，包含valid和error字段

**示例**:
```python
result = parser.validate_url("https://api.example.com/v1")
if result["valid"]:
    print("URL格式正确")
else:
    print(f"URL错误: {result['error']}")
```

#### get_url_priority(provider)
获取当前配置的URL优先级。

**参数**:
- `provider`: 提供商名称

**返回**:
- `URLPriority`: 当前使用的URL优先级

**示例**:
```python
priority = parser.get_url_priority("deepseek")
if priority == URLPriority.INDEPENDENT:
    print("使用独立URL")
elif priority == URLPriority.PROVIDER_SPECIFIC:
    print("使用提供商特定URL")
else:
    print("使用共享URL")
```

## 配置示例

### 1. 基础配置

#### 使用独立URL
```bash
# 所有embedding使用同一个独立URL
EMBEDDING_BASE_URL=https://custom-embedding-api.com/v1
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
EMBEDDING_MODEL=text-embedding-3-small
```

#### 使用提供商特定URL
```bash
# 为不同提供商配置特定URL
DEEPSEEK_EMBEDDING_BASE_URL=https://embedding.deepseek.com/v1
OPENAI_EMBEDDING_BASE_URL=https://api.openai.com/v1
SILICONFLOW_EMBEDDING_BASE_URL=https://embedding.siliconflow.cn/v1

EMBEDDING_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key
EMBEDDING_MODEL=deepseek-embedding
```

#### 使用共享URL（向后兼容）
```bash
# 传统配置方式，继续有效
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
EMBEDDING_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key
EMBEDDING_MODEL=deepseek-embedding
```

### 2. 高级配置

#### 混合优先级配置
```bash
# 同时配置多个URL，系统按优先级选择
EMBEDDING_BASE_URL=https://global-embedding.com/v1
DEEPSEEK_EMBEDDING_BASE_URL=https://embedding.deepseek.com/v1
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 结果: 使用 EMBEDDING_BASE_URL (最高优先级)
```

#### 条件配置
```bash
# 根据环境使用不同URL
if [ "$ENVIRONMENT" = "production" ]; then
    EMBEDDING_BASE_URL=https://prod-embedding-api.com/v1
else
    EMBEDDING_BASE_URL=https://dev-embedding-api.com/v1
fi
```

#### 多环境配置
```bash
# 开发环境
EMBEDDING_BASE_URL=https://dev-embedding.company.com/v1

# 测试环境
EMBEDDING_BASE_URL=https://test-embedding.company.com/v1

# 生产环境
EMBEDDING_BASE_URL=https://prod-embedding.company.com/v1
```

### 3. 企业级配置

#### 完全独立部署
```bash
# LLM和Embedding完全独立部署
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-llm-key
DEEPSEEK_BASE_URL=https://llm-api.company.com/v1

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-embedding-key
EMBEDDING_BASE_URL=https://embedding-api.company.com/v1
```

#### 负载均衡配置
```bash
# 使用负载均衡器
EMBEDDING_BASE_URL=https://embedding-lb.company.com/v1

# 或者使用多个URL（需要应用层处理）
EMBEDDING_BASE_URL=https://embedding-1.company.com/v1,https://embedding-2.company.com/v1
```

## 高级配置技巧

### 1. 动态URL配置

#### 使用环境变量
```bash
# 从环境变量动态获取URL
EMBEDDING_BASE_URL=${EMBEDDING_API_URL:-https://default-embedding.com/v1}
```

#### 使用配置文件
```python
# config.py
import os
from urllib.parse import urljoin

def get_embedding_url():
    base_url = os.getenv("EMBEDDING_BASE_URL")
    if base_url:
        return urljoin(base_url, "/v1/embeddings")
    return None
```

### 2. URL验证和测试

#### 配置验证
```python
from src.core.config import settings

# 验证配置
results = settings.validate_configuration()
if results.get("embedding_url_valid"):
    print("✅ Embedding URL配置有效")
else:
    print(f"❌ Embedding URL错误: {results.get('embedding_url_error')}")
```

#### URL测试
```python
import requests

def test_embedding_url(url, api_key):
    """测试embedding URL是否可用"""
    try:
        response = requests.get(
            f"{url}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False

# 测试URL
url = "https://api.example.com/v1"
api_key = "sk-your-key"
if test_embedding_url(url, api_key):
    print("URL可用")
else:
    print("URL不可用")
```

### 3. 性能优化

#### 连接池配置
```python
# 在provider中配置连接池
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key="sk-your-key",
    openai_api_base="https://api.example.com/v1",
    # 连接池配置
    request_timeout=30,
    max_retries=3
)
```

#### 缓存配置
```bash
# 启用embedding缓存
EMBEDDING_CACHE_ENABLED=true
EMBEDDING_CACHE_TTL=3600
```

## 故障排除

### 常见问题

#### 1. URL格式错误
```bash
# 错误
EMBEDDING_BASE_URL=api.example.com/v1

# 正确
EMBEDDING_BASE_URL=https://api.example.com/v1
```

#### 2. 优先级混乱
```bash
# 问题: 不确定使用哪个URL
EMBEDDING_BASE_URL=https://custom.com/v1
DEEPSEEK_EMBEDDING_BASE_URL=https://embedding.deepseek.com/v1

# 解决: 检查优先级
from src.core.config_parser import URLConfigParser
parser = URLConfigParser(config_dict)
priority = parser.get_url_priority("deepseek")
print(f"当前优先级: {priority}")
```

#### 3. 向后兼容性问题
```bash
# 问题: 旧配置不工作
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
EMBEDDING_PROVIDER=deepseek

# 解决: 确保配置完整
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=sk-your-key
EMBEDDING_PROVIDER=deepseek
EMBEDDING_MODEL=deepseek-embedding
```

#### 4. 网络连接问题
```bash
# 问题: 无法连接到自定义URL
ConnectionError: Failed to connect to custom-embedding.com

# 解决: 检查网络和DNS
ping custom-embedding.com
nslookup custom-embedding.com
curl -I https://custom-embedding.com/v1
```

### 调试工具

#### 启用详细日志
```python
import logging

# 启用URL解析日志
logging.getLogger("src.core.config_parser").setLevel(logging.DEBUG)

# 启用provider日志
logging.getLogger("src.services.providers").setLevel(logging.DEBUG)
```

#### 配置检查工具
```python
from src.core.config import settings
from src.core.config_parser import URLConfigParser

def check_url_config():
    """检查URL配置状态"""
    print(f"当前embedding提供商: {settings.embedding_provider}")
    print(f"解析的URL: {settings.embedding_base_url}")
    
    # 检查所有URL配置
    config_dict = {
        "embedding_base_url": settings.embedding_base_url,
        "deepseek_embedding_base_url": settings.deepseek_embedding_base_url,
        "openai_embedding_base_url": settings.openai_embedding_base_url,
    }
    
    parser = URLConfigParser(config_dict)
    all_urls = parser.get_all_embedding_urls()
    
    print("所有URL配置:")
    for key, url in all_urls.items():
        print(f"  {key}: {url}")

# 运行检查
check_url_config()
```

#### URL测试工具
```python
import requests
import time

def test_all_urls():
    """测试所有配置的URL"""
    from src.core.config import settings
    
    urls_to_test = [
        ("独立URL", settings.embedding_base_url),
        ("DeepSeek特定URL", settings.deepseek_embedding_base_url),
        ("OpenAI特定URL", settings.openai_embedding_base_url),
    ]
    
    for name, url in urls_to_test:
        if url:
            print(f"测试 {name}: {url}")
            try:
                response = requests.get(url, timeout=5)
                print(f"  ✅ 状态码: {response.status_code}")
            except Exception as e:
                print(f"  ❌ 错误: {e}")
        else:
            print(f"  ⚪ {name}: 未配置")

# 运行测试
test_all_urls()
```

## 最佳实践

### 1. 配置管理

#### 环境分离
```bash
# 开发环境
EMBEDDING_BASE_URL=https://dev-embedding.company.com/v1

# 测试环境
EMBEDDING_BASE_URL=https://test-embedding.company.com/v1

# 生产环境
EMBEDDING_BASE_URL=https://prod-embedding.company.com/v1
```

#### 配置模板
```bash
# 创建配置模板
cat > .env.template << EOF
# Embedding URL配置
EMBEDDING_BASE_URL=https://your-embedding-api.com/v1
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
EMBEDDING_MODEL=text-embedding-3-small
EOF
```

### 2. 安全考虑

#### API密钥管理
```bash
# 使用环境变量
export OPENAI_API_KEY="sk-your-key"
export EMBEDDING_BASE_URL="https://api.example.com/v1"

# 或使用密钥管理服务
export OPENAI_API_KEY=$(aws ssm get-parameter --name "/app/openai-key" --query "Parameter.Value" --output text)
```

#### URL验证
```python
def validate_embedding_url(url):
    """验证embedding URL的安全性"""
    if not url.startswith('https://'):
        raise ValueError("Embedding URL必须使用HTTPS")
    
    # 检查是否为可信域名
    trusted_domains = [
        'api.openai.com',
        'api.deepseek.com',
        'api.siliconflow.cn',
        'your-company.com'
    ]
    
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    if domain not in trusted_domains:
        raise ValueError(f"不信任的域名: {domain}")
    
    return True
```

### 3. 性能优化

#### 连接复用
```python
# 使用单例模式复用连接
class EmbeddingService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'embeddings'):
            self.embeddings = create_embeddings()
```

#### 缓存策略
```python
# 实现embedding缓存
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text):
    """获取embedding，带缓存"""
    embeddings = create_embeddings()
    return embeddings.embed_query(text)
```

## 相关文档

- [模型配置分离指南](./model-separation.md)
- [插件系统架构](../architecture/plugin-system.md)
- [API文档](../../api/openapi.yaml)
- [ADR-0006: Embedding模型URL独立配置策略](../adr/0006-embedding-url-independence.md)