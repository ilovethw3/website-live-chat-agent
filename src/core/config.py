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
    llm_provider: Literal["openai", "anthropic", "deepseek", "siliconflow"] = Field(
        default="deepseek", description="LLM 提供商"
    )

    # ===== LLM URL 配置 =====
    # 通用独立URL配置（最高优先级）
    llm_base_url_field: str | None = Field(
        default=None, description="独立LLM Base URL（优先级最高）"
    )

    # 提供商特定URL配置
    openai_llm_base_url: str | None = Field(
        default=None, description="OpenAI LLM Base URL"
    )
    deepseek_llm_base_url: str | None = Field(
        default=None, description="DeepSeek LLM Base URL"
    )
    siliconflow_llm_base_url: str | None = Field(
        default=None, description="SiliconFlow LLM Base URL"
    )
    anthropic_llm_base_url: str | None = Field(
        default=None, description="Anthropic LLM Base URL"
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

    # 硅基流动配置
    siliconflow_api_key: str | None = Field(default=None, description="硅基流动 API Key")
    siliconflow_base_url: str = Field(
        default="https://api.siliconflow.cn/v1", description="硅基流动 API Base URL"
    )
    siliconflow_llm_model: str = Field(
        default="Qwen/Qwen2.5-7B-Instruct", description="硅基流动 LLM 模型名称"
    )
    siliconflow_embedding_model: str = Field(
        default="BAAI/bge-large-zh-v1.5", description="硅基流动 Embedding 模型名称"
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
    embedding_provider: Literal["openai", "deepseek", "local", "siliconflow"] = Field(
        default="deepseek", description="Embedding 提供商"
    )
    embedding_model: str = Field(
        default="deepseek-embedding", description="Embedding 模型名称"
    )
    embedding_dim: int = Field(default=1536, description="Embedding 维度")

    # ===== Embedding API Key 配置 =====
    # 通用独立API Key配置（最高优先级）
    embedding_api_key_field: str | None = Field(
        default=None, description="独立Embedding API Key（优先级最高）"
    )

    # 提供商特定API Key配置
    openai_embedding_api_key: str | None = Field(
        default=None, description="OpenAI Embedding API Key"
    )
    deepseek_embedding_api_key: str | None = Field(
        default=None, description="DeepSeek Embedding API Key"
    )
    siliconflow_embedding_api_key: str | None = Field(
        default=None, description="SiliconFlow Embedding API Key"
    )
    anthropic_embedding_api_key: str | None = Field(
        default=None, description="Anthropic Embedding API Key"
    )

    # ===== Embedding URL 配置 =====
    # 通用独立URL配置（最高优先级）
    embedding_base_url: str | None = Field(
        default=None, description="独立Embedding Base URL（优先级最高）"
    )

    # 提供商特定URL配置
    openai_embedding_base_url: str | None = Field(
        default=None, description="OpenAI Embedding Base URL"
    )
    deepseek_embedding_base_url: str | None = Field(
        default=None, description="DeepSeek Embedding Base URL"
    )
    siliconflow_embedding_base_url: str | None = Field(
        default=None, description="SiliconFlow Embedding Base URL"
    )
    anthropic_embedding_base_url: str | None = Field(
        default=None, description="Anthropic Embedding Base URL"
    )

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

    # ===== 向量召回配置 =====
    # 注意：rag_* 配置项已迁移为 vector_*，通过 validation_alias 保持向后兼容
    vector_top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="向量召回 Top-K",
        validation_alias="RAG_TOP_K"
    )
    vector_score_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="向量召回相似度分数阈值",
        validation_alias="RAG_SCORE_THRESHOLD"
    )
    vector_chunk_size: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="向量召回文档切片大小（tokens）",
        validation_alias="RAG_CHUNK_SIZE"
    )
    vector_chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=500,
        description="向量召回文档切片重叠（tokens）",
        validation_alias="RAG_CHUNK_OVERLAP"
    )

    # ===== 性能配置 =====
    llm_temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="LLM 温度参数"
    )
    llm_max_tokens: int = Field(
        default=2000, ge=1, le=10000, description="LLM 最大 Token 数"
    )
    cache_ttl: int = Field(default=300, ge=0, description="缓存 TTL（秒）")

    # ===== 消息过滤配置 =====
    message_filter_enabled: bool = Field(
        default=True, description="是否启用消息过滤"
    )
    message_max_length: int = Field(
        default=1000, ge=100, le=5000, description="消息最大长度（字符）"
    )
    instruction_keywords: str = Field(
        default="You are an AI,Your role is to,Follow these guidelines,Use user's language,Always return,Always wrap,You are a helpful assistant,Your task is to,Please rephrase,Convert the following,Transform this query",
        description="指令模板关键词（逗号分隔）"
    )
    technical_terms_threshold: int = Field(
        default=3, ge=1, le=10, description="技术术语阈值（超过此数量将被过滤）"
    )
    technical_terms: str = Field(
        default="API,endpoint,function,method,parameter,response,request",
        description="技术术语列表（逗号分隔）"
    )

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
        default=3000,
        ge=100, le=10000,
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
        elif self.llm_provider == "siliconflow":
            if not self.siliconflow_api_key:
                raise ValueError("SILICONFLOW_API_KEY is required when LLM_PROVIDER=siliconflow")
            return self.siliconflow_api_key
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
        elif self.llm_provider == "siliconflow":
            return self.siliconflow_llm_model
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    @property
    def llm_base_url(self) -> str | None:
        """根据 LLM 提供商返回对应的 Base URL（智能优先级）"""
        # 优先级1: 通用独立URL（最高优先级）
        if self.llm_base_url_field:
            return self.llm_base_url_field

        # 优先级2: 提供商特定URL
        if self.llm_provider == "deepseek":
            if self.deepseek_llm_base_url:
                return self.deepseek_llm_base_url
            return self.deepseek_base_url
        elif self.llm_provider == "openai":
            if self.openai_llm_base_url:
                return self.openai_llm_base_url
            return None  # OpenAI 使用默认 URL
        elif self.llm_provider == "anthropic":
            if self.anthropic_llm_base_url:
                return self.anthropic_llm_base_url
            return None  # Anthropic 使用默认 URL
        elif self.llm_provider == "siliconflow":
            if self.siliconflow_llm_base_url:
                return self.siliconflow_llm_base_url
            return self.siliconflow_base_url
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    @property
    def embedding_api_key(self) -> str:
        """根据 Embedding 提供商返回对应的 API Key（智能优先级）"""
        # 本地模型不需要 API Key
        if self.embedding_provider == "local":
            return ""

        # 优先级1: 通用独立API Key（最高优先级）
        if self.embedding_api_key_field:
            return self.embedding_api_key_field

        # 优先级2: 提供商特定API Key
        if self.embedding_provider == "deepseek":
            if self.deepseek_embedding_api_key:
                return self.deepseek_embedding_api_key
            if not self.deepseek_api_key:
                raise ValueError("DEEPSEEK_API_KEY is required when EMBEDDING_PROVIDER=deepseek")
            return self.deepseek_api_key
        elif self.embedding_provider == "openai":
            if self.openai_embedding_api_key:
                return self.openai_embedding_api_key
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
            return self.openai_api_key
        elif self.embedding_provider == "siliconflow":
            if self.siliconflow_embedding_api_key:
                return self.siliconflow_embedding_api_key
            if not self.siliconflow_api_key:
                raise ValueError("SILICONFLOW_API_KEY is required when EMBEDDING_PROVIDER=siliconflow")
            return self.siliconflow_api_key
        elif self.embedding_provider == "anthropic":
            if self.anthropic_embedding_api_key:
                return self.anthropic_embedding_api_key
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required when EMBEDDING_PROVIDER=anthropic")
            return self.anthropic_api_key
        else:
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")

    def get_embedding_base_url(self) -> str | None:
        """根据 Embedding 提供商返回对应的 Base URL（智能优先级）"""
        from src.core.config_parser import URLConfigParser

        # 构建配置字典
        config_dict = {
            "embedding_base_url": self.embedding_base_url,
            "openai_embedding_base_url": self.openai_embedding_base_url,
            "deepseek_embedding_base_url": self.deepseek_embedding_base_url,
            "siliconflow_embedding_base_url": self.siliconflow_embedding_base_url,
            "anthropic_embedding_base_url": self.anthropic_embedding_base_url,
            # 传统共享URL配置
            "deepseek_base_url": self.deepseek_base_url,
            "siliconflow_base_url": self.siliconflow_base_url,
        }

        # 使用配置解析器
        parser = URLConfigParser(config_dict)
        return parser.resolve_embedding_url(self.embedding_provider)

    @property
    def embedding_model_name(self) -> str:
        """根据 Embedding 提供商返回对应的模型名称"""
        if self.embedding_provider == "deepseek":
            return self.embedding_model
        elif self.embedding_provider == "openai":
            return self.embedding_model
        elif self.embedding_provider == "local":
            return self.embedding_model
        elif self.embedding_provider == "siliconflow":
            return self.siliconflow_embedding_model
        else:
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")

    def validate_configuration(self) -> dict[str, bool]:
        """验证配置的有效性（增强版）"""
        results = {}

        # 验证所有embedding URL配置
        from src.core.config_parser import URLConfigParser

        url_parser = URLConfigParser({
            "embedding_base_url": self.embedding_base_url,
            "openai_embedding_base_url": self.openai_embedding_base_url,
            "deepseek_embedding_base_url": self.deepseek_embedding_base_url,
            "siliconflow_embedding_base_url": self.siliconflow_embedding_base_url,
            "anthropic_embedding_base_url": self.anthropic_embedding_base_url,
        })

        # 验证embedding URL
        try:
            embedding_url = self.get_embedding_base_url()
            url_validation = url_parser.validate_url(embedding_url)
            results["embedding_url_valid"] = url_validation["valid"]
            if not url_validation["valid"]:
                results["embedding_url_error"] = url_validation["error"]
        except Exception as e:
            results["embedding_url_valid"] = False
            results["embedding_url_error"] = str(e)

        # 验证LLM配置
        try:
            from src.services.llm_factory import create_llm
            create_llm()  # 验证LLM配置
            results["llm_valid"] = True
        except Exception as e:
            results["llm_valid"] = False
            results["llm_error"] = str(e)

        # 验证Embedding配置
        try:
            from src.services.llm_factory import create_embeddings
            create_embeddings()  # 验证Embedding配置
            results["embedding_valid"] = True
        except Exception as e:
            results["embedding_valid"] = False
            results["embedding_error"] = str(e)

        return results

    # ===== 向后兼容别名（已废弃，请使用 vector_* 配置项） =====
    @property
    def rag_top_k(self) -> int:
        """向后兼容别名，已废弃，请使用 vector_top_k"""
        return self.vector_top_k

    @property
    def rag_score_threshold(self) -> float:
        """向后兼容别名，已废弃，请使用 vector_score_threshold"""
        return self.vector_score_threshold

    @property
    def rag_chunk_size(self) -> int:
        """向后兼容别名，已废弃，请使用 vector_chunk_size"""
        return self.vector_chunk_size

    @property
    def rag_chunk_overlap(self) -> int:
        """向后兼容别名，已废弃，请使用 vector_chunk_overlap"""
        return self.vector_chunk_overlap


# 全局配置实例（单例）
settings = Settings()

