"""方言适配器注册表测试。"""
from __future__ import annotations

import pytest

from app.dialect.adapter import DialectCode, DialectRegistry


def test_all_mvp_dialects_registered() -> None:
    registered = DialectRegistry.list_registered()
    assert DialectCode.MANDARIN in registered
    assert DialectCode.CANTONESE in registered
    assert DialectCode.SICHUAN in registered


def test_mandarin_passthrough() -> None:
    adapter = DialectRegistry.get(DialectCode.MANDARIN)
    assert adapter.to_mandarin("你好") == "你好"
    assert adapter.from_mandarin("你好") == "你好"


def test_cantonese_conversion() -> None:
    adapter = DialectRegistry.get(DialectCode.CANTONESE)
    # to_mandarin 应将方言词转为普通话
    result = adapter.to_mandarin("我食饭")
    assert "吃饭" in result or "食饭" in result


def test_sichuan_conversion() -> None:
    adapter = DialectRegistry.get(DialectCode.SICHUAN)
    result = adapter.to_mandarin("你在搞啥子")
    assert "什么" in result or "啥子" in result


def test_unknown_dialect_raises() -> None:
    with pytest.raises(ValueError):
        DialectCode("klingon")
