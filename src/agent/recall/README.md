# 召回Agent服务文档

## 概述

召回Agent是一个独立的LangGraph子图，负责多源召回、统一排序、降级策略和实验支持。主对话Agent通过标准接口调用召回Agent，实现知识检索的编排和优化。

## 架构设计

### 多Agent架构

```
主对话Agent (LangGraph)
    ↓ 调用
召回Agent (LangGraph子图)
    ↓ 并行调用
召回源适配器
    ├── 向量召回源 (Milvus)
    ├── FAQ召回源 (关键词匹配)
    └── 关键词召回源 (规则匹配)
```

### 核心组件

- **召回Agent**: LangGraph子图，协调整个召回流程
- **召回源**: 实现`RecallSource`接口的适配器
- **数据模型**: `RecallRequest`、`RecallHit`、`RecallResult`
- **配置管理**: 统一的配置加载和验证

## 配置指南

### 环境变量配置

在`.env`文件中配置召回参数：

```bash
# ===== 召回编排层配置 =====
RECALL_SOURCES=["vector", "faq", "keyword"]
RECALL_SOURCE_WEIGHTS="vector:1.0,faq:0.8,keyword:0.6"
RECALL_TIMEOUT_MS=500
RECALL_RETRY=1
RECALL_MERGE_STRATEGY="weighted"
RECALL_DEGRADE_THRESHOLD=0.5
RECALL_FALLBACK_ENABLED=True
RECALL_EXPERIMENT_ENABLED=False
RECALL_EXPERIMENT_PLATFORM=None
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `RECALL_SOURCES` | list[str] | `["vector"]` | 启用的召回源列表 |
| `RECALL_SOURCE_WEIGHTS` | str | `"vector:1.0"` | 召回源权重配置 |
| `RECALL_TIMEOUT_MS` | int | `500` | 召回超时时间（毫秒） |
| `RECALL_RETRY` | int | `1` | 召回失败重试次数 |
| `RECALL_MERGE_STRATEGY` | str | `"weighted"` | 召回结果合并策略 |
| `RECALL_DEGRADE_THRESHOLD` | float | `0.5` | 召回结果置信度降级阈值 |
| `RECALL_FALLBACK_ENABLED` | bool | `True` | 是否启用召回降级策略 |
| `RECALL_EXPERIMENT_ENABLED` | bool | `False` | 是否启用召回实验功能 |
| `RECALL_EXPERIMENT_PLATFORM` | str | `None` | 实验平台类型 |

## 使用指南

### 基本调用

```python
from src.agent.recall.graph import invoke_recall_agent
from src.agent.recall.schema import RecallRequest

# 构建召回请求
request = RecallRequest(
    query="你们的退货政策是什么？",
    session_id="session-123",
    trace_id="trace-456",
    top_k=5
)

# 调用召回Agent
result = await invoke_recall_agent(request)

# 处理召回结果
for hit in result.hits:
    print(f"来源: {hit.source}, 分数: {hit.score}")
    print(f"内容: {hit.content}")
```

### 召回源扩展

#### 1. 实现召回源适配器

```python
from src.agent.recall.sources.base import RecallSource
from src.agent.recall.schema import RecallHit, RecallRequest

class CustomRecallSource(RecallSource):
    @property
    def source_name(self) -> str:
        return "custom"
    
    async def acquire(self, request: RecallRequest) -> list[RecallHit]:
        # 实现自定义召回逻辑
        hits = []
        # ... 召回逻辑
        return hits
```

#### 2. 注册召回源

在`src/agent/recall/nodes.py`的`fanout_node`中添加：

```python
if "custom" in sources:
    from src.agent.recall.sources.custom_source import CustomRecallSource
    source_instances["custom"] = CustomRecallSource()
```

#### 3. 更新配置

```bash
RECALL_SOURCES=["vector", "faq", "keyword", "custom"]
RECALL_SOURCE_WEIGHTS="vector:1.0,faq:0.8,keyword:0.6,custom:0.4"
```

## 监控指标

### 日志字段

召回Agent会记录以下结构化日志：

```json
{
  "trace_id": "trace-123",
  "experiment_id": "exp-v2",
  "session_id": "session-456",
  "query": "用户查询内容",
  "sources": ["vector", "faq"],
  "hits_count": 5,
  "latency_ms": 245.5,
  "degraded": false,
  "avg_score": 0.85,
  "max_score": 0.92,
  "top_hit_source": "vector"
}
```

### 关键指标

- **召回延迟**: `latency_ms` - 召回总耗时
- **召回成功率**: 基于`degraded`字段计算
- **召回源分布**: `sources` - 使用的召回源
- **结果质量**: `avg_score`、`max_score` - 平均分和最高分
- **降级率**: `degraded` - 是否发生降级

### 告警规则

建议配置以下告警：

- 召回成功率 < 99%
- P99延迟 > 800ms
- 降级次数突增
- 召回源超时率 > 阈值

## 实验支持

### 实验配置

召回Agent支持A/B实验，通过`experiment_id`参数控制：

```python
request = RecallRequest(
    query="查询内容",
    experiment_id="exp-recall-v2",  # 实验ID
    # ... 其他参数
)
```

### 实验示例

#### 实验1: 多源召回
- **实验ID**: `exp-recall-v2`
- **配置**: 启用vector+faq+keyword三源召回
- **权重**: vector:0.6, faq:0.3, keyword:0.1

#### 实验2: 权重调整
- **实验ID**: `exp-weight-adjust`
- **配置**: 调整vector和faq的权重比例
- **权重**: vector:0.4, faq:0.6

### 实验分析

通过日志中的`experiment_id`字段，可以分析不同实验的效果：

- 召回质量对比
- 延迟性能对比
- 用户满意度对比

## 故障排查

### 常见问题

#### 1. 召回结果为空

**可能原因**:
- 召回源配置错误
- 召回源服务不可用
- 查询内容不匹配

**排查步骤**:
1. 检查`RECALL_SOURCES`配置
2. 查看召回源日志
3. 验证查询内容格式

#### 2. 召回延迟过高

**可能原因**:
- 召回源响应慢
- 超时配置过小
- 并发调用过多

**排查步骤**:
1. 检查`RECALL_TIMEOUT_MS`配置
2. 监控召回源性能
3. 调整并发策略

#### 3. 降级频繁触发

**可能原因**:
- 召回源质量下降
- 降级阈值设置过低
- 查询内容质量差

**排查步骤**:
1. 检查`RECALL_DEGRADE_THRESHOLD`配置
2. 分析召回源质量
3. 优化查询内容

### 调试模式

启用详细日志：

```python
import logging
logging.getLogger("src.agent.recall").setLevel(logging.DEBUG)
```

## 性能优化

### 召回源优化

1. **向量召回**: 优化Milvus查询参数
2. **FAQ召回**: 优化关键词匹配算法
3. **关键词召回**: 优化规则匹配性能

### 并发优化

1. **并行调用**: 所有召回源并行执行
2. **超时控制**: 避免慢召回源影响整体性能
3. **重试策略**: 指数退避重试机制

### 缓存策略

1. **查询缓存**: 缓存相同查询的结果
2. **配置缓存**: 缓存召回源配置
3. **结果缓存**: 缓存召回结果

## 版本历史

- **v1.0.0**: 初始版本，支持向量+FAQ召回
- **v1.1.0**: 添加关键词召回源
- **v1.2.0**: 添加实验支持
- **v1.3.0**: 优化监控和日志

## 贡献指南

### 开发环境

1. 克隆项目
2. 安装依赖: `pip install -e .[dev]`
3. 配置环境变量
4. 运行测试: `pytest tests/unit/agent/recall/`

### 代码规范

1. 遵循PEP 8规范
2. 添加类型提示
3. 编写单元测试
4. 更新文档

### 提交规范

使用Conventional Commits格式：

```
feat(recall): 添加新的召回源
fix(recall): 修复召回延迟问题
docs(recall): 更新配置文档
```

## 联系方式

如有问题或建议，请：

1. 提交Issue到项目仓库
2. 联系开发团队
3. 查看项目文档
