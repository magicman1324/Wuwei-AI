"""Pytest 全局 fixtures。"""
from __future__ import annotations

import os

import pytest

# 强制使用 mock LLM，避免测试时调用真实 API
os.environ.setdefault("WUWEI_LLM_PROVIDER", "mock")
os.environ.setdefault("WUWEI_DATABASE_URL", "sqlite:///:memory:")

# 触发方言适配器注册
import app.dialect.dialects  # noqa: E402, F401


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
