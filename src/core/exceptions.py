"""
自定义异常定义

所有业务异常都继承自 AppException，方便统一处理。
"""


class AppException(Exception):
    """应用基础异常"""

    def __init__(self, message: str, code: str | None = None) -> None:
        self.message = message
        self.code = code or "app_error"
        super().__init__(self.message)


class ConfigurationError(AppException):
    """配置错误"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="configuration_error")


class MilvusConnectionError(AppException):
    """Milvus 连接错误"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="milvus_connection_error")


class RedisConnectionError(AppException):
    """Redis 连接错误"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="redis_connection_error")


class AuthenticationError(AppException):
    """认证错误（API Key 无效）"""

    def __init__(self, message: str = "Invalid API key") -> None:
        super().__init__(message, code="invalid_api_key")


class ValidationError(AppException):
    """请求参数验证错误"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class LLMError(AppException):
    """LLM 调用错误"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="llm_error")


class AgentExecutionError(AppException):
    """Agent 执行错误"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="agent_execution_error")

