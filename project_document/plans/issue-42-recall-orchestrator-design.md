# Issue #42 召回编排层（多 Agent 架构）设计草案

## 1. 概览
- **目标**：构建独立的召回编排 Agent，并由主对话 Agent 调用，实现多源召回、统一排序、降级与实验支持。
- **范围**：主对话 Agent（LangGraph）检索节点、召回源适配器、召回 Agent 子图、配置与监控接口、实验接入。
- **不在范围**：运营后台 UI、配置中心实现、实验看板（由后续迭代承接）。

## 2. 架构组件
- **主对话 Agent (Conversation Agent)**：保留原 LangGraph 状态机结构，检索节点调用召回 Agent。
- **召回编排 Agent (Recall Agent)**：独立 LangGraph 子图，主流程：输入 → 并行召回源 → 汇总排序 → 降级 → 输出。
- **召回源适配器**：统一接口 `RecallSource`，实现向量（Milvus）、关键词/规则、FAQ、业务 API 等，支持并行调用。
- **配置与实验模块**：从 `settings` 读取默认配置，预留配置中心 & 实验平台钩子（如 GrowthBook ID）；缓存最新版本。
- **监控与日志**：使用统一 `trace_id`/`experiment_id` 字段，输出召回源耗时、成功率、降级次数等指标。

## 3. 工作流
1. 主 Agent 在 `retrieve_node` 组装 `RecallRequest`（query、session_id、context、experiment_id、trace_id 等）。
2. 调用召回 Agent（函数调用或 `invoke_sub_agent`）。
3. 召回 Agent 将请求分发到各召回源适配器（并行），收集结果，按权重与策略排序，并进行去重/降级。
4. 返回 `RecallResult` 列表（包含来源、分值、置信度、命中原因、payload）；主 Agent 根据结果决定生成或兜底。

## 4. 接口设计
```python
@dataclass
class RecallRequest:
    query: str
    session_id: str
    user_profile: dict[str, Any] | None
    context: list[str] | None
    experiment_id: str | None
    trace_id: str
    top_k: int = 5

@dataclass
class RecallHit:
    source: str
    score: float
    confidence: float
    reason: str
    content: str
    metadata: dict[str, Any]

@dataclass
class RecallResult:
    hits: list[RecallHit]
    latency_ms: float
    degraded: bool
    trace_id: str
    experiment_id: str | None
```
- **主 Agent → 召回 Agent**：`RecallResult recall_agent.invoke(RecallRequest)`
- **召回源适配器接口**：`async def acquire(request: RecallRequest) -> list[RecallHit]`

## 5. 召回 Agent 子图（LangGraph）
- **Nodes**：
  - `prepare_node`: 处理上下文、实验配置选择。
  - `fanout_node`: 并行触发源 `vector`, `keyword`, `faq`, `biz_api`。
  - `merge_node`: 汇总结果，调用排序/去重策略。
  - `fallback_node`: 若结果为空或低于阈值，执行降级（FAQ 兜底/规则提醒）。
  - `output_node`: 组装 `RecallResult`。
- **Edges**：
  - `prepare -> fanout`（并行子节点）。
  - 各源返回结果后流向 `merge`；
  - `merge -> fallback`（条件：结果不足/异常）；
  - `merge/fallback -> output`。

## 6. 排序与去重策略
- 排序分值：`weighted_score = source_weight * normalized_score`；权重来自配置/实验。
- 去重：按文档 ID 或内容哈希；若重复，保留分值高的，同时合并来源信息。
- 降级策略：
  - 结果为空：触发 FAQ/提示人工；
  - 某源连续超时：触发熔断，记录告警。

## 7. 配置与实验
- `settings` 扩展：
  - `recall_sources`（源列表、开关、默认权重、超时）
  - `recall_timeout_ms`, `recall_retry` 等。
- 强制加载前校验；配置可热更新（后续配合配置中心实现）。
- 实验：读取 `experiment_id`，根据实验配置调整权重/源组合；输出埋点 `recall_experiment_result`。

## 8. 监控与日志
- 日志字段：`trace_id`, `experiment_id`, `session_id`, `source`, `score`, `latency_ms`, `status`。
- 指标：
  - `recall_total_latency_ms`, `recall_source_latency_ms`
  - `recall_success_rate`, `recall_degrade_count`
  - `recall_timeout_count`, `recall_experiment_bucket`。
- 告警：召回总失败率 > 阈值、源超时率 > 阈值、降级次数突增。

## 9. 风险与缓解
| 风险 | 缓解 |
| --- | --- |
| 调用链延迟增加 | 并行执行、缓存、配置超时；评估 P99 延迟，必要时降级或限制源数量 |
| 配置误操作 | 配置校验、默认模板、灰度发布、回滚机制 |
| 召回 Agent 失败影响对话 | 设置熔断和降级策略，主 Agent 需有兜底流程 |
| 实验/配置不一致 | 使用统一配置中心，并在日志中透传 config_version |

## 10. 开发与测试计划（概要）
- 开发阶段：
  1. 接口契约与数据结构实现；
  2. 召回 Agent 子图 + 源适配器；
  3. 主 Agent 集成；
  4. 配置/实验接入；
  5. 监控埋点；
  6. 测试 & 文档。
- 测试：单元测试（源调用、排序）、集成测试（多源链路、降级）、性能验证（并行调度）、实验灰度演练。

---
*编写：AR (Architect AI)  
更新时间：2025-10-18*

## 11. 目录结构建议
```
src/
  agent/
    recall/
      __init__.py
      graph.py          # LangGraph 子图入口
      nodes.py          # 重写、召回、排序、降级等节点
      schema.py         # RecallRequest / RecallResult 等数据模型
      config.py         # 模块默认配置加载
      sources/
        __init__.py
        base.py         # RecallSource基类定义
        vector_source.py
        keyword_source.py
        faq_source.py
        biz_api_source.py
  services/
    __init__.py
    milvus_service.py  # 向量召回底层服务
    faq_service.py     # FAQ 数据访问
  core/
    config.py          # 全局配置拓展
    logging.py         # 日志/trace 透传

tests/
  unit/agent/recall/
    test_graph.py
    test_sources.py
  integration/recall_agent/
    test_end_to_end.py

project_document/
  research/issue-42-recall-orchestration-layer.md
  plans/issue-42-recall-orchestrator-design.md
```
- `src/agent/recall/` 聚焦召回 Agent 架构（与现有单数命名保持一致）；
- `src/agent/recall/sources/` 统一管理召回源适配器；
- `src/core/config.py` 承载与其他模块共享的配置；
- 测试建议按单元/集成维度放入对应目录。

## 12. 配置项详细定义

基于AR确认的配置项，在`src/core/config.py`中添加：

```python
# ===== 召回编排层配置 =====
recall_sources: list[str] = Field(
    default=["vector"],
    description="启用的召回源列表"
)
recall_source_weights: str = Field(
    default="vector:1.0",
    description="召回源权重配置（逗号分隔，如 vector:1.0,keyword:0.8）"
)
recall_timeout_ms: int = Field(
    default=500,
    ge=100, le=2000,
    description="召回超时时间（毫秒）"
)
recall_retry: int = Field(
    default=1,
    ge=0, le=3,
    description="召回失败重试次数"
)
recall_merge_strategy: Literal["weighted", "rrf", "custom"] = Field(
    default="weighted",
    description="召回结果合并策略"
)
recall_degrade_threshold: float = Field(
    default=0.5,
    ge=0.0, le=1.0,
    description="召回结果置信度降级阈值"
)
recall_fallback_enabled: bool = Field(
    default=True,
    description="是否启用召回降级策略"
)
recall_experiment_enabled: bool = Field(
    default=False,
    description="是否启用召回实验"
)
recall_experiment_platform: str | None = Field(
    default=None,
    description="实验平台类型（None/internal/growthbook等）"
)
```

## 13. OpenAPI Schema定义

在`docs/api/openapi.yaml`中添加召回相关数据模型：

```yaml
RecallRequest:
  type: object
  required: [query, session_id, trace_id]
  properties:
    query: {type: string}
    session_id: {type: string}
    trace_id: {type: string}
    user_profile: {type: object, nullable: true}
    context: {type: array, items: {type: string}, nullable: true}
    experiment_id: {type: string, nullable: true}
    top_k: {type: integer, default: 5}

RecallHit:
  type: object
  properties:
    source: {type: string}
    score: {type: number}
    confidence: {type: number}
    reason: {type: string}
    content: {type: string}
    metadata: {type: object}

RecallResult:
  type: object
  properties:
    hits: {type: array, items: {$ref: '#/components/schemas/RecallHit'}}
    latency_ms: {type: number}
    degraded: {type: boolean}
    trace_id: {type: string}
    experiment_id: {type: string, nullable: true}
```

## 12. 配置项清单（MVP）
新增配置集中于 `settings`：
```python
class Settings(BaseSettings):
    recall_sources: list[str] = Field(default=["vector", "keyword", "faq"])
    recall_source_weights: dict[str, float] = Field(default={"vector": 0.6, "keyword": 0.3, "faq": 0.1})
    recall_timeout_ms: int = Field(default=800)
    recall_retry: int = Field(default=1)
    recall_merge_strategy: str = Field(default="weighted")  # weighted | rrf | custom
    recall_degrade_threshold: float = Field(default=0.4)
    recall_fallback_enabled: bool = Field(default=True)
    recall_experiment_enabled: bool = Field(default=False)
    recall_experiment_platform: str | None = None
```
- `.env.example` 需同步示例配置；
- 实验/配置中心暂不接入，预留字段供后续扩展。

## 13. OpenAPI Schema 拓展
在 `docs/api/openapi.yaml` 中新增：
- `RecallRequest`, `RecallResult`, `RecallHit` 的组件 Schema；
- 可选：内部调试端点（如 `/internal/recall/test`）仅用于集成测试，可视上线策略决定。
