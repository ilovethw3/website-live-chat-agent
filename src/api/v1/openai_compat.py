"""
OpenAI 兼容的 Chat Completions API

提供完全兼容 OpenAI 格式的 /v1/chat/completions 端点。
"""

import logging
import time
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage

from src.agent.graph import get_agent_app
from src.core.config import settings
from src.core.security import verify_api_key
from src.models.openai_schema import (
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    ChatMessage,
    OpenAIModelList,
    OpenAIModelRef,
)

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/models")
async def list_models() -> OpenAIModelList:
    """
    OpenAI 兼容的模型列表端点 (/v1/models)。

    支持混合模型组合：
    - LLM 和 Embedding 可以来自不同提供商
    - 支持模型别名功能
    - 支持硅基流动平台等新提供商

    ⚠️ 当启用模型别名功能时（MODEL_ALIAS_ENABLED=true）：
    - 返回配置的别名模型（如 gpt-4o-mini）
    - owned_by 字段为配置的值（如 openai）
    - 仅返回聊天模型（不返回 embedding 模型）

    当禁用时（默认）：
    - 返回实际模型名称（如 deepseek-chat）
    - owned_by 显示实际提供商（如 provider:deepseek）
    """
    now_ts = int(time.time())
    id_to_ref: dict[str, OpenAIModelRef] = {}

    # 判断是否启用别名
    if settings.model_alias_enabled:
        # 使用别名模型
        logger.info(
            f"🎭 Model alias enabled: returning alias '{settings.model_alias_name}' "
            f"(actual: {settings.llm_model_name})"
        )
        id_to_ref[settings.model_alias_name] = OpenAIModelRef(
            id=settings.model_alias_name,
            created=now_ts,
            owned_by=settings.model_alias_owned_by,
        )

        # 如果配置为不隐藏 embedding 模型，添加它
        if not settings.hide_embedding_models:
            try:
                embedding_id = settings.embedding_model_name
                if embedding_id and embedding_id not in id_to_ref:
                    id_to_ref[embedding_id] = OpenAIModelRef(
                        id=embedding_id,
                        created=now_ts,
                        owned_by=f"provider:{settings.embedding_provider}",
                    )
            except Exception:
                pass
    else:
        # 返回实际模型名（支持混合模型组合）
        chat_model_id = settings.llm_model_name
        id_to_ref[chat_model_id] = OpenAIModelRef(
            id=chat_model_id,
            created=now_ts,
            owned_by=f"provider:{settings.llm_provider}",
        )

        # 添加 Embedding 模型（如果配置显示）
        if not settings.hide_embedding_models:
            try:
                embedding_id = settings.embedding_model_name
                if embedding_id and embedding_id not in id_to_ref:
                    id_to_ref[embedding_id] = OpenAIModelRef(
                        id=embedding_id,
                        created=now_ts,
                        owned_by=f"provider:{settings.embedding_provider}",
                    )
            except Exception:
                pass

    return OpenAIModelList(data=list(id_to_ref.values()))

@router.post("/chat/completions", response_model=None)
async def chat_completions(
    request: ChatCompletionRequest,
) -> ChatCompletionResponse | StreamingResponse:
    """
    OpenAI 兼容的 Chat Completions 端点

    支持流式和非流式响应。
    """
    logger.info(
        f"📨 Received chat completion request: "
        f"messages={len(request.messages)}, stream={request.stream}"
    )

    # 模型别名映射（支持接受别名请求）
    actual_model = settings.llm_model_name  # 实际使用的模型
    requested_model = request.model  # 用户请求的模型

    if settings.model_alias_enabled:
        if requested_model == settings.model_alias_name:
            logger.info(
                f"🎭 Model alias mapping: request='{requested_model}' → actual='{actual_model}'"
            )
        else:
            logger.warning(
                f"⚠️ Unexpected model requested: '{requested_model}' "
                f"(expected alias: '{settings.model_alias_name}'). "
                f"Still using actual model: '{actual_model}'"
            )
    else:
        # 别名未启用，直接使用请求的模型名（但实际仍用配置的模型）
        logger.debug(f"Model requested: '{requested_model}', actual: '{actual_model}'")

    # 生成唯一 ID
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created_timestamp = int(time.time())

    # 提取用户消息（最后一条）
    last_message = request.messages[-1]
    if last_message.role != "user":
        # 如果最后一条不是用户消息，使用倒数第二条
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            # 没有用户消息，返回错误
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": "No user message found in request",
                        "type": "invalid_request_error",
                        "code": "no_user_message",
                    }
                },
            )
        user_message = user_messages[-1].content
    else:
        user_message = last_message.content

    # 生成 session_id（可选：从请求中提取）
    session_id = f"session-{uuid.uuid4().hex[:12]}"

    # 流式响应
    if request.stream:
        return StreamingResponse(
            _stream_response(
                user_message=user_message,
                session_id=session_id,
                completion_id=completion_id,
                created_timestamp=created_timestamp,
                model=request.model,
                requested_model=requested_model,
            ),
            media_type="text/event-stream",
        )

    # 非流式响应
    return await _non_stream_response(
        user_message=user_message,
        session_id=session_id,
        completion_id=completion_id,
        created_timestamp=created_timestamp,
        model=request.model,
        requested_model=requested_model,
    )


async def _non_stream_response(
    user_message: str,
    session_id: str,
    completion_id: str,
    created_timestamp: int,
    model: str,
    requested_model: str,
) -> ChatCompletionResponse:
    """非流式响应"""
    # 调用 Agent
    app = get_agent_app()

    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": session_id,
        "next_step": None,
        "error": None,
        "confidence_score": None,
    }

    config = {"configurable": {"thread_id": session_id}}

    try:
        result = await app.ainvoke(initial_state, config)

        # 提取 AI 响应
        ai_message = result["messages"][-1]
        if isinstance(ai_message, AIMessage):
            response_content = ai_message.content
        else:
            response_content = str(ai_message)

        # 计算 Token 使用（简化版，使用字符数估算）
        prompt_tokens = len(user_message) // 4
        completion_tokens = len(response_content) // 4
        total_tokens = prompt_tokens + completion_tokens

        # 构建 OpenAI 格式响应
        return ChatCompletionResponse(
            id=completion_id,
            created=created_timestamp,
            model=requested_model,  # 返回用户请求的模型名（保持一致性）
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=response_content),
                    finish_reason="stop",
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            ),
        )

    except Exception as e:
        logger.error(f"❌ Agent execution failed: {e}")
        # 返回错误响应
        return ChatCompletionResponse(
            id=completion_id,
            created=created_timestamp,
            model=requested_model,  # 返回用户请求的模型名（保持一致性）
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant", content="抱歉，系统遇到了问题，请稍后再试。"
                    ),
                    finish_reason="stop",
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=0, completion_tokens=0, total_tokens=0
            ),
        )


async def _stream_response(
    user_message: str,
    session_id: str,
    completion_id: str,
    created_timestamp: int,
    model: str,
    requested_model: str,
) -> AsyncGenerator[str, None]:
    """流式响应（SSE）"""
    app = get_agent_app()

    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": session_id,
        "next_step": None,
        "error": None,
        "confidence_score": None,
    }

    config = {"configurable": {"thread_id": session_id}}

    try:
        # 发送初始 chunk（role）
        first_chunk = ChatCompletionChunk(
            id=completion_id,
            created=created_timestamp,
            model=requested_model,  # 返回用户请求的模型名（保持一致性）
            choices=[
                ChatCompletionChunkChoice(
                    index=0,
                    delta=ChatCompletionChunkDelta(role="assistant"),
                    finish_reason=None,
                )
            ],
        )
        yield f"data: {first_chunk.model_dump_json()}\n\n"

        # 流式执行 Agent
        async for chunk in app.astream(initial_state, config):
            # 检查是否有新的 AI 消息
            if "llm" in chunk:  # LLM 节点的输出
                llm_output = chunk["llm"]
                messages = llm_output.get("messages", [])
                if messages:
                    ai_message = messages[-1]
                    if isinstance(ai_message, AIMessage):
                        content = ai_message.content

                        # 发送内容 chunk
                        # 注意：这里发送完整内容，实际应该发送增量
                        # 为了简化，我们一次性发送（LangGraph 不原生支持 token-by-token 流式）
                        content_chunk = ChatCompletionChunk(
                            id=completion_id,
                            created=created_timestamp,
                            model=requested_model,  # 返回用户请求的模型名（保持一致性）
                            choices=[
                                ChatCompletionChunkChoice(
                                    index=0,
                                    delta=ChatCompletionChunkDelta(content=content),
                                    finish_reason=None,
                                )
                            ],
                        )
                        yield f"data: {content_chunk.model_dump_json()}\n\n"

        # 发送结束 chunk
        final_chunk = ChatCompletionChunk(
            id=completion_id,
            created=created_timestamp,
            model=requested_model,  # 返回用户请求的模型名（保持一致性）
            choices=[
                ChatCompletionChunkChoice(
                    index=0,
                    delta=ChatCompletionChunkDelta(),
                    finish_reason="stop",
                )
            ],
        )
        yield f"data: {final_chunk.model_dump_json()}\n\n"

        # 发送 [DONE]
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"❌ Streaming failed: {e}")
        # 发送错误 chunk
        error_chunk = ChatCompletionChunk(
            id=completion_id,
            created=created_timestamp,
            model=requested_model,  # 返回用户请求的模型名（保持一致性）
            choices=[
                ChatCompletionChunkChoice(
                    index=0,
                    delta=ChatCompletionChunkDelta(content="系统错误，请稍后再试。"),
                    finish_reason="stop",
                )
            ],
        )
        yield f"data: {error_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

