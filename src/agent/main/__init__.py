"""主对话Agent模块

本模块实现基于LangGraph的主对话Agent，负责：
- 路由用户请求（知识库检索 vs 直接对话）
- 调用召回Agent进行知识检索
- 生成最终回复

主要组件：
- graph.py: LangGraph工作流定义
- nodes.py: 节点函数（router, retrieve, call_llm）
- edges.py: 边函数（路由逻辑）
- state.py: Agent状态定义
- tools.py: Agent工具（知识检索等）
"""

from src.agent.main.graph import get_agent_app
from src.agent.main.state import AgentState

__all__ = ["get_agent_app", "AgentState"]
