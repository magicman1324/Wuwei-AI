"""音频格式转换工具单元测试。"""
from __future__ import annotations

import pytest

from app.speech.audio_convert import to_pcm16_16k


def test_pcm_passthrough():
    raw = b"\x00\x01" * 100
    assert to_pcm16_16k(raw, "pcm") is raw


def test_pcm_case_insensitive():
    raw = b"\x00\x01" * 100
    assert to_pcm16_16k(raw, "PCM") is raw


def test_pcm_with_dot_prefix():
    raw = b"\x00\x01" * 100
    assert to_pcm16_16k(raw, ".pcm") is raw


def test_non_pcm_requires_pydub(monkeypatch):
    """非 PCM 格式在无 pydub 时应抛出 RuntimeError。"""
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "pydub":
            raise ImportError("mock: pydub not available")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    with pytest.raises(RuntimeError, match="pydub 未安装"):
        to_pcm16_16k(b"\x00" * 100, "mp3")
