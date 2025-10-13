"""
测试 API Key 认证模块

测试 API Key 的验证逻辑和安全性。
"""

import pytest
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials

from src.core.security import api_key_auth
from src.core.config import settings


def test_api_key_auth_valid():
    """测试有效的 API Key"""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=settings.api_key
    )

    # 应该正常通过，不抛出异常
    result = api_key_auth(credentials)
    assert result == credentials


def test_api_key_auth_invalid():
    """测试无效的 API Key"""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong-key")

    with pytest.raises(HTTPException) as exc_info:
        api_key_auth(credentials)

    assert exc_info.value.status_code == 403
    assert "Invalid API Key" in exc_info.value.detail


def test_api_key_auth_empty():
    """测试空 API Key"""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")

    with pytest.raises(HTTPException) as exc_info:
        api_key_auth(credentials)

    assert exc_info.value.status_code == 403


def test_api_key_auth_none():
    """测试 None API Key"""
    with pytest.raises(HTTPException) as exc_info:
        api_key_auth(None)  # type: ignore

    assert exc_info.value.status_code == 403


def test_api_key_auth_case_sensitive():
    """测试 API Key 大小写敏感"""
    # API Key 应该是大小写敏感的
    upper_key = settings.api_key.upper()

    if upper_key != settings.api_key:
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=upper_key)

        with pytest.raises(HTTPException):
            api_key_auth(credentials)

