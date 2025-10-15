"""
API 认证与安全

提供 API Key 验证中间件。
"""

from typing import Optional

from fastapi import Header, HTTPException, status

from src.core.config import settings


async def verify_api_key(authorization: Optional[str] = Header(None)) -> None:
    """
    验证 API Key

    Args:
        authorization: HTTP Authorization Header，格式: "Bearer {api_key}"

    Raises:
        HTTPException: API Key 无效或格式错误（返回 403 Forbidden）

    Examples:
        >>> # 正确格式
        >>> await verify_api_key("Bearer sk-agent-12345")

        >>> # 错误格式
        >>> await verify_api_key("sk-agent-12345")  # 缺少 Bearer
        HTTPException: 403 Forbidden
    """
    # 检查是否提供了 Authorization header
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "message": "Missing Authorization header",
                    "type": "invalid_request_error",
                    "code": "missing_authorization",
                }
            },
        )

    # 检查格式: "Bearer {key}"
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "message": "Invalid authorization header format. Expected: 'Bearer {api_key}'",
                    "type": "invalid_request_error",
                    "code": "invalid_authorization_header",
                }
            },
        )

    # 提取 API Key
    api_key = authorization[7:]  # 去掉 "Bearer " 前缀

    # 验证 API Key
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "message": "Invalid API key",
                    "type": "invalid_request_error",
                    "code": "invalid_api_key",
                }
            },
        )

