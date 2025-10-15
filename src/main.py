"""
FastAPI 应用入口

启动命令:
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.exceptions import AppException

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理

    启动时:
    - 初始化 Milvus 连接
    - 初始化 Redis 连接
    - 创建 Milvus Collections（如果不存在）

    关闭时:
    - 关闭所有连接
    """
    logger.info("🚀 Starting Website Live Chat Agent...")
    logger.info(f"📊 LLM Provider: {settings.llm_provider}")
    logger.info(f"📊 LLM Model: {settings.llm_model_name}")
    logger.info(f"🗄️  Milvus Host: {settings.milvus_host}:{settings.milvus_port}")
    logger.info(f"💾 Redis Host: {settings.redis_host}:{settings.redis_port}")

    # 初始化 Milvus
    try:
        from src.services.milvus_service import milvus_service
        await milvus_service.initialize()
        logger.info("✅ Milvus initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Milvus: {e}")
        logger.warning("⚠️  Continuing without Milvus (some features will not work)")

    # 预编译 LangGraph App
    try:
        from src.agent.graph import get_agent_app
        get_agent_app()
        logger.info("✅ LangGraph Agent compiled successfully")
    except Exception as e:
        logger.error(f"❌ Failed to compile LangGraph Agent: {e}")

    yield

    # 清理资源
    logger.info("🛑 Shutting down Website Live Chat Agent...")
    try:
        from src.services.milvus_service import milvus_service
        await milvus_service.close()
    except Exception as e:
        logger.error(f"Error closing Milvus: {e}")


# 创建 FastAPI 应用
app = FastAPI(
    title="Website Live Chat Agent API",
    description="基于 LangGraph + Milvus + DeepSeek 的智能客服 Agent",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException) -> JSONResponse:
    """处理自定义应用异常"""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": exc.message,
                "type": "server_error",
                "code": exc.code,
            }
        },
    )


# 注册路由
# ruff: noqa: E402 - 导入必须在app创建后，避免循环依赖
from src.api.v1 import knowledge, openai_compat
from src.services.milvus_service import milvus_service

app.include_router(openai_compat.router, prefix="/v1", tags=["Chat"])
app.include_router(knowledge.router, prefix="/api/v1", tags=["Knowledge"])


# 健康检查端点
@app.get("/api/v1/health", tags=["Health"])
async def health_check() -> dict:
    """健康检查"""
    milvus_healthy = milvus_service.health_check()

    return {
        "status": "healthy" if milvus_healthy else "degraded",
        "services": {
            "milvus": {
                "status": "healthy" if milvus_healthy else "unhealthy",
                "host": settings.milvus_host,
            },
            "redis": {
                "status": "healthy",  # TODO: 实际检查 Redis
                "host": settings.redis_host,
            },
        },
        "timestamp": int(__import__("time").time()),
    }


# 根路径
@app.get("/", tags=["Root"])
async def root() -> dict:
    """API 根路径"""
    return {
        "message": "Website Live Chat Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model_name,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )

