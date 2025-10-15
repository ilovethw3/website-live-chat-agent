"""
应用配置管理

使用 Pydantic Settings 从环境变量加载配置。
所有配置项都有类型检查和默认值。
"""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置（从环境变量自动加载）"""

    # ===== LLM 配置 =====
    llm_provider: Literal["openai", "anthropic", "deepseek"] = Field(
        default="deepseek", description="LLM 提供商"
    )

    # DeepSeek 配置
    deepseek_api_key: str | None = Field(default=None, description="DeepSeek API Key")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1", description="DeepSeek API Base URL"
    )
    deepseek_model: str = Field(default="deepseek-chat", description="DeepSeek 模型名称")

    # OpenAI 配置
    openai_api_key: str | None = Field(default=None, description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI 模型名称")

    # Anthropic 配置
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API Key")
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022", description="Anthropic 模型名称"
    )

    # ===== 模型别名配置 =====
    model_alias_enabled: bool = Field(
        default=False,
        description="是否启用模型别名功能（⚠️警告：启用后将使用OpenAI品牌名称，存在商标风险）"
    )
    model_alias_name: str = Field(
        default="gpt-4o-mini",
        description="对外显示的模型别名（默认：gpt-4o-mini）"
    )
    model_alias_owned_by: str = Field(
        default="openai",
        description="模型所有者标识（在/v1/models中返回）"
    )
    hide_embedding_models: bool = Field(
        default=True,
        description="在/v1/models中隐藏embedding模型（仅返回聊天模型）"
    )

    # ===== Embedding 配置 =====
    embedding_provider: Literal["openai", "deepseek", "local"] = Field(
        default="deepseek", description="Embedding 提供商"
    )
    embedding_model: str = Field(
        default="deepseek-embedding", description="Embedding 模型名称"
    )
    embedding_dim: int = Field(default=1536, description="Embedding 维度")

    # ===== Milvus 配置 =====
    milvus_host: str = Field(..., description="Milvus 服务器地址（必填）")
    milvus_port: int = Field(default=19530, description="Milvus 端口")
    milvus_user: str = Field(default="root", description="Milvus 用户名")
    milvus_password: str = Field(default="", description="Milvus 密码")
    milvus_database: str = Field(default="default", description="Milvus 数据库名称")

    milvus_knowledge_collection: str = Field(
        default="knowledge_base", description="知识库 Collection 名称"
    )
    milvus_history_collection: str = Field(
        default="conversation_history", description="对话历史 Collection 名称"
    )

    # ===== Redis 配置 =====
    redis_host: str = Field(default="localhost", description="Redis 服务器地址")
    redis_port: int = Field(default=6379, description="Redis 端口")
    redis_password: str = Field(default="", description="Redis 密码")
    redis_db: int = Field(default=0, ge=0, le=15, description="Redis 数据库编号")
    redis_max_connections: int = Field(default=10, ge=1, description="Redis 连接池大小")

    # ===== API 配置 =====
    api_key: str = Field(..., description="API 认证密钥（必填）")
    cors_origins: str = Field(
        default="*", description="CORS 允许的域名（逗号分隔，* 表示全部）"
    )

    # ===== 应用配置 =====
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="日志级别"
    )
    port: int = Field(default=8000, ge=1024, le=65535, description="服务端口")

    # ===== LangGraph 配置 =====
    langgraph_max_iterations: int = Field(
        default=10, ge=1, le=50, description="Agent 最大迭代次数"
    )
    langgraph_checkpointer: Literal["memory", "redis"] = Field(
        default="redis", description="Checkpointer 类型"
    )

    # ===== RAG 配置 =====
    rag_top_k: int = Field(default=3, ge=1, le=10, description="知识库检索 Top-K")
    rag_score_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="相似度分数阈值"
    )
    rag_chunk_size: int = Field(
        default=500, ge=100, le=2000, description="文档切片大小（tokens）"
    )
    rag_chunk_overlap: int = Field(
        default=50, ge=0, le=500, description="文档切片重叠（tokens）"
    )

    # ===== 性能配置 =====
    llm_temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="LLM 温度参数"
    )
    llm_max_tokens: int = Field(
        default=2000, ge=1, le=10000, description="LLM 最大 Token 数"
    )
    cache_ttl: int = Field(default=300, ge=0, description="缓存 TTL（秒）")

    # ===== Pydantic 配置 =====
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # 环境变量不区分大小写
        extra="ignore",  # 忽略额外的环境变量
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """解析 CORS 域名列表"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def llm_api_key(self) -> str:
        """根据 LLM 提供商返回对应的 API Key"""
        if self.llm_provider == "deepseek":
            if not self.deepseek_api_key:
                raise ValueError("DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek")
            return self.deepseek_api_key
        elif self.llm_provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
            return self.openai_api_key
        elif self.llm_provider == "anthropic":
            if not self.anthropic_api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
                )
            return self.anthropic_api_key
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    @property
    def llm_model_name(self) -> str:
        """根据 LLM 提供商返回对应的模型名称"""
        if self.llm_provider == "deepseek":
            return self.deepseek_model
        elif self.llm_provider == "openai":
            return self.openai_model
        elif self.llm_provider == "anthropic":
            return self.anthropic_model
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")


# 全局配置实例（单例）
settings = Settings()

