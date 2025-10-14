"""
测试 API Key 认证模块

测试 API Key 的验证逻辑和安全性。
"""

import pytest
from fastapi import HTTPException

from src.core.config import settings
from src.core.security import verify_api_key


@pytest.mark.asyncio
async def test_verify_api_key_valid():
    """测试有效的 API Key"""
    authorization = f"Bearer {settings.api_key}"

    # 应该正常通过，不抛出异常
    result = await verify_api_key(authorization)
    assert result is None  # verify_api_key 返回 None 表示成功


@pytest.mark.asyncio
async def test_verify_api_key_invalid():
    """测试无效的 API Key"""
    authorization = "Bearer wrong-key"

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(authorization)

    assert exc_info.value.status_code == 403
    assert "Invalid API key" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_verify_api_key_empty():
    """测试空 API Key"""
    authorization = "Bearer "

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(authorization)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_verify_api_key_missing_bearer():
    """测试缺少 Bearer 前缀"""
    authorization = settings.api_key  # 直接传递 key，没有 Bearer

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(authorization)

    assert exc_info.value.status_code == 403
    assert "authorization header format" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_verify_api_key_wrong_format():
    """测试错误的格式"""
    authorization = f"Token {settings.api_key}"  # 使用 Token 而不是 Bearer

    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(authorization)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_verify_api_key_case_sensitive():
    """测试 API Key 大小写敏感"""
    # API Key 应该是大小写敏感的
    upper_key = settings.api_key.upper()

    if upper_key != settings.api_key:
        authorization = f"Bearer {upper_key}"

        with pytest.raises(HTTPException):
            await verify_api_key(authorization)

