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

from src.agent.main.state import AgentState
from src.core.config import settings
from src.services.llm_factory import create_llm

logger = logging.getLogger(__name__)


def _is_valid_user_query(query: str) -> bool:
    """
    验证是否为有效的用户查询

    过滤外部指令模板和异常消息，确保只有真正的用户查询才能进入检索流程。

    Args:
        query: 待验证的查询文本

    Returns:
        bool: True表示是有效的用户查询，False表示应该被过滤
    """
    # 检查是否启用消息过滤
    if not settings.message_filter_enabled:
        return True

    # 检查长度限制（防止超长指令模板）
    if len(query) > settings.message_max_length:
        logger.warning(f"Query too long: {len(query)} chars (max: {settings.message_max_length})")
        return False

    # 获取配置的指令关键词
    instruction_keywords = [kw.strip() for kw in settings.instruction_keywords.split(",") if kw.strip()]

    # 检查是否包含指令模板关键词
    query_lower = query.lower()
    for keyword in instruction_keywords:
        if keyword.lower() in query_lower:
            logger.warning(f"Instruction template detected: {keyword}")
            return False

    # 检查是否以指令开头
    instruction_starts = ["You are", "Your role", "Please", "Convert", "Transform"]
    if query.strip().startswith(tuple(instruction_starts)):
        logger.warning("Query starts with instruction pattern")
        return False

    # 检查是否包含过多的技术术语（可能是系统消息）
    technical_terms = [term.strip() for term in settings.technical_terms.split(",") if term.strip()]
    technical_count = sum(1 for term in technical_terms if term.lower() in query_lower)
    if technical_count >= settings.technical_terms_threshold:
        logger.warning(f"Too many technical terms detected: {technical_count} (threshold: {settings.technical_terms_threshold})")
        return False

    return True


def _get_filter_reason(query: str) -> str:
    """
    获取消息过滤的具体原因

    Args:
        query: 待验证的查询文本

    Returns:
        str: 过滤原因
    """
    # 检查长度限制
    if len(query) > settings.message_max_length:
        return "message_too_long"

    # 获取配置的指令关键词
    instruction_keywords = [kw.strip() for kw in settings.instruction_keywords.split(",") if kw.strip()]

    # 检查是否包含指令模板关键词
    query_lower = query.lower()
    for keyword in instruction_keywords:
        if keyword.lower() in query_lower:
            return "instruction_template_detected"

    # 检查是否以指令开头
    instruction_starts = ["You are", "Your role", "Please", "Convert", "Transform"]
    if query.strip().startswith(tuple(instruction_starts)):
        return "instruction_pattern_detected"

    # 检查是否包含过多的技术术语
    technical_terms = [term.strip() for term in settings.technical_terms.split(",") if term.strip()]
    technical_count = sum(1 for term in technical_terms if term.lower() in query_lower)
    if technical_count >= settings.technical_terms_threshold:
        return "too_many_technical_terms"

    return "unknown"


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

    # 注意：消息验证已在API层进行，这里不再需要过滤

    # 使用召回Agent进行多源检索
    from src.agent.recall.graph import invoke_recall_agent
    from src.agent.recall.schema import RecallRequest
    from src.core.utils import generate_trace_id

    # 构建召回请求
    recall_request = RecallRequest(
        query=query,
        session_id=state.get("session_id", "unknown"),
        trace_id=generate_trace_id(),
        user_profile=state.get("user_profile"),
        context=state.get("context"),
        experiment_id=state.get("experiment_id"),
        top_k=settings.vector_top_k,
    )

    # 调用召回Agent
    try:
        recall_result = await invoke_recall_agent(recall_request)
    except Exception as e:
        logger.error(f"❌ Recall agent failed: {e}")
        return {
            "retrieved_docs": [], 
            "confidence_score": 0.0,
            "recall_metrics": {
                "latency_ms": 0.0,
                "degraded": True,
                "sources": [],
                "trace_id": recall_request.trace_id,
            },
            "tool_calls": state.get("tool_calls", []) + [
                {
                    "node": "retrieve",
                    "results_count": 0,
                    "top_score": 0.0,
                    "recall_sources": [],
                    "latency_ms": 0.0,
                    "degraded": True,
                    "error": str(e)
                }
            ]
        }

    if not recall_result.hits:
        logger.info(f"📭 Retrieve node: no results found for '{query}'")
        return {
            "retrieved_docs": [], 
            "confidence_score": 0.0,
            "recall_metrics": {
                "latency_ms": recall_result.latency_ms,
                "degraded": recall_result.degraded,
                "sources": [],
                "trace_id": recall_result.trace_id,
            },
            "tool_calls": state.get("tool_calls", []) + [
                {
                    "node": "retrieve",
                    "results_count": 0,
                    "top_score": 0.0,
                    "recall_sources": [],
                    "latency_ms": recall_result.latency_ms,
                    "degraded": recall_result.degraded
                }
            ]
        }

    # 格式化召回结果
    formatted_docs = []
    for i, hit in enumerate(recall_result.hits, 1):
        metadata = hit.metadata
        title = metadata.get("title", "未命名文档")
        url = metadata.get("url", "")
        source = hit.source

        doc_text = f"[文档{i}] {title}"
        if url:
            doc_text += f" (来源: {url})"
        doc_text += f" [召回源: {source}]"
        doc_text += f"\n{hit.content}"

        formatted_docs.append(doc_text)

    # 计算置信度（使用最高分）
    confidence = recall_result.hits[0].score if recall_result.hits else 0.0

    # 记录召回指标
    logger.info(
        f"✅ Retrieve node: found {len(recall_result.hits)} documents, "
        f"confidence={confidence:.2f}, latency={recall_result.latency_ms:.1f}ms, "
        f"degraded={recall_result.degraded}, sources={[hit.source for hit in recall_result.hits]}"
    )

    return {
        "retrieved_docs": formatted_docs,
        "confidence_score": confidence,
        "recall_metrics": {
            "latency_ms": recall_result.latency_ms,
            "degraded": recall_result.degraded,
            "sources": [hit.source for hit in recall_result.hits],
            "trace_id": recall_result.trace_id,
        },
        "tool_calls": state.get("tool_calls", []) + [
            {
                "node": "retrieve",
                "results_count": len(recall_result.hits),
                "top_score": confidence,
                "recall_sources": [hit.source for hit in recall_result.hits],
                "latency_ms": recall_result.latency_ms,
                "degraded": recall_result.degraded
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
        # retrieved_docs 是字符串列表，直接使用
        # 添加类型检查，确保所有元素都是字符串
        context_parts = []
        for doc in retrieved_docs:
            if isinstance(doc, str):
                context_parts.append(doc)
            elif isinstance(doc, dict):
                # 如果是字典类型，提取text字段
                text = doc.get("text", str(doc))
                context_parts.append(text)
            else:
                # 其他类型，转换为字符串
                context_parts.append(str(doc))
        context = "\n\n".join(context_parts)
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

