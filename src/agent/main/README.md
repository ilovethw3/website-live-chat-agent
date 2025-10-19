# 主对话Agent (Main Conversation Agent)

## 概述

主对话Agent是基于LangGraph构建的智能对话系统，负责处理用户请求、协调知识检索和生成回复。

## 架构设计

### 工作流程

```
用户输入 → Router节点 → 判断是否需要检索
                    ↓
            需要检索 → Retrieve节点 → 调用召回Agent
                    ↓
            不需要检索 → 直接调用LLM
                    ↓
                生成回复 → 返回用户
```

### 核心组件

#### 1. Graph (graph.py)
- **功能**: 定义LangGraph工作流
- **主要函数**: `get_agent_app()` - 获取编译后的Agent应用
- **节点**: router_node, retrieve_node, call_llm_node
- **边**: route_after_llm - 路由逻辑

#### 2. Nodes (nodes.py)
- **router_node**: 判断用户请求是否需要知识库检索
- **retrieve_node**: 调用召回Agent进行知识检索
- **call_llm_node**: 调用LLM生成最终回复

#### 3. State (state.py)
- **AgentState**: 定义Agent运行时状态
- **字段**: messages, retrieved_docs, tool_calls, session_id等

#### 4. Tools (tools.py)
- **knowledge_search_tool**: 知识库检索工具（已被召回Agent替代）

#### 5. Edges (edges.py)
- **route_after_llm**: 判断是否需要继续对话或结束

## 使用指南

### 基本调用

```python
from src.agent.main.graph import get_agent_app
from langchain_core.messages import HumanMessage

# 获取Agent应用
app = get_agent_app()

# 构建初始状态
initial_state = {
    "messages": [HumanMessage(content="你们的退货政策是什么？")],
    "session_id": "session-123",
}

# 调用Agent
config = {"configurable": {"thread_id": "session-123"}}
result = await app.ainvoke(initial_state, config)

# 获取回复
print(result["messages"][-1].content)
```

### 流式调用

```python
# 流式输出
async for chunk in app.astream(initial_state, config):
    if "messages" in chunk:
        print(chunk["messages"][-1].content, end="")
```

## 与召回Agent的集成

主Agent通过`retrieve_node`调用召回Agent：

```python
# 在 retrieve_node 中
from src.agent.recall.graph import invoke_recall_agent
from src.agent.recall.schema import RecallRequest

# 构建召回请求
recall_request = RecallRequest(
    query=query,
    session_id=state.get("session_id", "unknown"),
    trace_id=generate_trace_id(),
    top_k=settings.vector_top_k,
)

# 调用召回Agent
recall_result = await invoke_recall_agent(recall_request)
```

## 状态管理

### AgentState结构

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    retrieved_docs: list[str]
    tool_calls: list[dict]
    session_id: str
    confidence_score: float
    recall_metrics: dict  # 召回指标
```

### 状态更新

- **messages**: 自动追加（使用add_messages）
- **retrieved_docs**: 替换式更新
- **tool_calls**: 追加式更新
- **recall_metrics**: 记录召回性能指标

## 路由逻辑

### Router节点判断

```python
# 需要检索的情况
- 用户询问产品信息
- 用户询问政策规则
- 用户询问FAQ

# 不需要检索的情况
- 简单问候
- 闲聊对话
- 已有足够上下文
```

### 判断依据

- 消息内容分析
- 关键词匹配
- LLM辅助判断（可选）

## 监控与日志

### 关键指标

- **路由准确率**: Router节点的判断准确性
- **检索命中率**: Retrieve节点的成功率
- **端到端延迟**: 从请求到回复的总时间
- **LLM调用次数**: 每次对话的LLM调用统计

### 日志记录

```python
# 在各节点中记录关键信息
logger.info(f"Router node: query='{query}', needs_retrieval={needs_retrieval}")
logger.info(f"Retrieve node: found {len(docs)} documents, confidence={confidence}")
logger.info(f"LLM node: generated response, length={len(response)}")
```

## 配置项

主Agent使用以下配置（来自`src/core/config.py`）：

```python
# LangGraph配置
LANGGRAPH_MAX_ITERATIONS=10
LANGGRAPH_CHECKPOINTER=redis

# 向量检索配置
VECTOR_TOP_K=3
VECTOR_SCORE_THRESHOLD=0.7

# 召回配置
RECALL_SOURCES=["vector"]
RECALL_TIMEOUT_MS=3000
```

## 测试

### 单元测试

```bash
# 测试节点函数
pytest tests/unit/test_agent_nodes.py -v

# 测试边函数
pytest tests/unit/test_agent_edges.py -v

# 测试状态管理
pytest tests/unit/test_agent_state.py -v
```

### 集成测试

```bash
# 测试完整工作流
pytest tests/integration/test_agent_graph.py -v

# 测试与召回Agent的集成
pytest tests/integration/recall_agent/test_main_agent.py -v
```

## 扩展开发

### 添加新节点

```python
# 在 nodes.py 中定义新节点
async def custom_node(state: AgentState) -> dict:
    """自定义节点逻辑"""
    # 处理逻辑
    return {"field": value}

# 在 graph.py 中注册节点
workflow.add_node("custom", custom_node)
workflow.add_edge("router", "custom")
```

### 修改路由逻辑

```python
# 在 edges.py 中修改路由条件
def route_after_llm(state: AgentState) -> str:
    """自定义路由逻辑"""
    # 添加新的路由条件
    if custom_condition:
        return "custom_node"
    return END
```

## 性能优化

### 缓存策略

- **会话缓存**: 使用Redis存储会话状态
- **检索缓存**: 缓存相同查询的检索结果
- **LLM缓存**: 缓存相似问题的回复

### 并发控制

- **限流**: 控制并发请求数量
- **超时**: 设置合理的超时时间
- **降级**: 检索失败时的降级策略

## 常见问题

### Q: 如何调整检索阈值？
A: 修改`VECTOR_SCORE_THRESHOLD`配置项，范围0-1。

### Q: 如何禁用知识检索？
A: 在router_node中始终返回`needs_retrieval=False`。

### Q: 如何添加自定义工具？
A: 在tools.py中定义新工具，并在nodes.py中调用。

## 版本历史

- **v1.0.0**: 初始版本，基础对话功能
- **v1.1.0**: 集成召回Agent
- **v1.2.0**: 添加流式输出支持
- **v2.0.0**: 目录结构重构（当前版本）

## 相关文档

- [召回Agent文档](../recall/README.md)
- [API文档](../../api/README.md)
- [配置说明](../../core/config.py)
