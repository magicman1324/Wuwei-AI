"""LLM 工厂与 mock 实现测试。"""
from __future__ import annotations

import pytest

from app.chat.llm.base import LLMMessage
from app.chat.llm.factory import LLMFactory


def test_factory_creates_mock() -> None:
    llm = LLMFactory.create("mock")
    assert llm is not None


def test_factory_unknown_provider_raises() -> None:
    with pytest.raises(ValueError):
        LLMFactory.create("nonexistent-provider")


@pytest.mark.asyncio
async def test_mock_llm_responds() -> None:
    llm = LLMFactory.create("mock")
    response = await llm.chat(
        messages=[LLMMessage(role="user", content="你好")]
    )
    assert response.content
    assert isinstance(response.content, str)
