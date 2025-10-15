"""
LangGraph Agent 节点函数

定义 Agent 工作流中的各个节点：
- router: 路由决策（是否需要检索知识库）
- retrieve: 知识库检索
- call_llm: 调用 LLM 生成响应
"""

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agent.state import AgentState
from src.agent.tools import search_knowledge_for_agent
from src.core.config import settings
from src.services.llm_factory import create_llm

logger = logging.getLogger(__name__)


async def router_node(state: AgentState) -> dict[str, Any]:
    """
    路由节点：判断是否需要检索知识库

    策略：
    1. 检查消息中是否包含特定关键词（产品、政策、价格等）
    2. 检查问题类型（疑问句、指令等）
    3. 简单打招呼 → 直接回答
    4. 复杂问题 → 检索知识库

    Args:
        state: 当前 Agent 状态

    Returns:
        更新的状态（包含 next_step 和 tool_calls）
    """
    # 获取最后一条用户消息
    last_message = state["messages"][-1]
    if not isinstance(last_message, HumanMessage):
        # 如果不是用户消息，直接跳过检索
        return {"next_step": "direct", "tool_calls": []}

    query = last_message.content

    # 关键词检测（需要检索的关键词）
    knowledge_keywords = [
        "产品", "价格", "政策", "如何", "什么", "哪里", "怎么",
        "退货", "保修", "发货", "配送", "支付", "订单",
        "功能", "参数", "规格", "优惠", "活动"
    ]

    # 简单打招呼关键词（不需要检索）
    greeting_keywords = ["你好", "您好", "hi", "hello", "早上好", "晚上好"]

    # 判断是否为简单打招呼
    is_greeting = any(kw in query.lower() for kw in greeting_keywords)
    if is_greeting and len(query) < 20:  # 短消息且是打招呼
        logger.info("🎯 Router: Direct response (greeting)")
        return {
            "next_step": "direct",
            "tool_calls": [{"node": "router", "decision": "direct", "reason": "greeting"}]
        }

    # 判断是否需要知识库检索
    needs_retrieval = any(kw in query for kw in knowledge_keywords)

    if needs_retrieval:
        logger.info("🎯 Router: Retrieve from knowledge base (keywords matched)")
        return {
            "next_step": "retrieve",
            "tool_calls": [{"node": "router", "decision": "retrieve", "reason": "keywords"}]
        }
    else:
        logger.info("🎯 Router: Direct response (no keywords)")
        return {
            "next_step": "direct",
            "tool_calls": [{"node": "router", "decision": "direct", "reason": "no_keywords"}]
        }


async def retrieve_node(state: AgentState) -> dict[str, Any]:
    """
    知识库检索节点

    从 Milvus 检索相关知识库文档。

    Args:
        state: 当前 Agent 状态

    Returns:
        更新的状态（包含 retrieved_docs 和 confidence_score）
    """
    # 获取查询
    if not state["messages"]:
        logger.warning("⚠️ Retrieve node: empty messages")
        return {"retrieved_docs": [], "confidence_score": 0.0}

    last_message = state["messages"][-1]
    query = last_message.content if isinstance(last_message, HumanMessage) else ""

    if not query:
        logger.warning("⚠️ Retrieve node: empty query")
        return {"retrieved_docs": [], "confidence_score": 0.0}

    # 执行检索
    results = await search_knowledge_for_agent(query, top_k=settings.rag_top_k)

    if not results:
        logger.info(f"📭 Retrieve node: no results found for '{query}'")
        return {"retrieved_docs": [], "confidence_score": 0.0}

    # 格式化检索结果
    formatted_docs = []
    for i, result in enumerate(results, 1):
        metadata = result.get("metadata", {})
        title = metadata.get("title", "未命名文档")
        url = metadata.get("url", "")

        doc_text = f"[文档{i}] {title}"
        if url:
            doc_text += f" (来源: {url})"
        doc_text += f"\n{result['text']}"

        formatted_docs.append(doc_text)

    # 计算置信度（使用最高分数）
    confidence = results[0]["score"] if results else 0.0

    logger.info(
        f"✅ Retrieve node: found {len(results)} documents, "
        f"confidence={confidence:.2f}"
    )

    return {
        "retrieved_docs": formatted_docs,
        "confidence_score": confidence,
        "tool_calls": state.get("tool_calls", []) + [
            {
                "node": "retrieve",
                "results_count": len(results),
                "top_score": confidence
            }
        ]
    }


async def call_llm_node(state: AgentState) -> dict[str, Any]:
    """
    LLM 生成节点

    调用 LLM 生成最终响应。

    策略：
    - 如果有检索到的文档（retrieved_docs），使用 RAG 模式
    - 如果没有文档，直接对话模式

    Args:
        state: 当前 Agent 状态

    Returns:
        更新的状态（包含新的 AI 消息）
    """
    retrieved_docs = state.get("retrieved_docs", [])

    # 构建系统提示词
    if retrieved_docs:
        # RAG 模式
        # retrieved_docs 是字典列表，需要提取 text 字段
        context = "\n\n".join([doc.get("text", str(doc)) for doc in retrieved_docs])
        system_prompt = f"""你是一个专业的网站客服助手。

**知识库上下文**:
{context}

**回答要求**:
1. **优先使用知识库信息**回答问题
2. 引用知识库时，说明来源（如："根据我们的退货政策..."）
3. 如果知识库信息不足以回答问题，基于常识礼貌回答
4. **不确定时，诚实告知**（如："抱歉，我在知识库中未找到相关信息"）
5. 保持专业、友好的语气

**禁止**:
- 不要编造知识库中不存在的信息
- 不要给出与知识库矛盾的答案
"""
    else:
        # 直接对话模式
        system_prompt = """你是一个专业、友好的网站客服助手。

**回答要求**:
1. 保持礼貌、专业的语气
2. 简洁明了地回答问题
3. 如果问题涉及具体的产品、政策等信息，建议用户查看官网或联系人工客服
4. 不要编造具体的产品信息或政策细节
"""

    # 构建消息列表
    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"]
    ]

    # 调用 LLM
    try:
        llm = create_llm()
        response = await llm.ainvoke(messages)

        logger.info(f"🤖 LLM response generated (mode: {'RAG' if retrieved_docs else 'direct'})")

        return {
            "messages": [response],
            "tool_calls": state.get("tool_calls", []) + [
                {
                    "node": "call_llm",
                    "mode": "RAG" if retrieved_docs else "direct",
                    "response_length": len(response.content) if hasattr(response, 'content') else 0
                }
            ]
        }

    except Exception as e:
        logger.error(f"❌ LLM call failed: {e}")

        # 返回错误消息
        error_message = AIMessage(
            content="抱歉，系统遇到了一些问题，请稍后再试。"
        )

        return {
            "messages": [error_message],
            "error": str(e),
            "tool_calls": state.get("tool_calls", []) + [
                {"node": "call_llm", "error": str(e)}
            ]
        }

