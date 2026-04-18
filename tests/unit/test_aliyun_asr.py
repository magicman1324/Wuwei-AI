"""阿里云 ASR 单元测试。"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.dialect.adapter import DialectCode
from app.speech.asr.aliyun import AliyunASR


@pytest.fixture
def asr() -> AliyunASR:
    return AliyunASR(
        access_key="test-key",
        access_secret="test-secret",
        app_key="test-app",
    )


def _mock_response(text: str = "你好", confidence: float = 0.95):
    from unittest.mock import MagicMock

    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = lambda: None
    resp.json.return_value = {
        "output": {
            "results": [
                {"sentence": {"text": text, "confidence": confidence}}
            ]
        }
    }
    return resp


@pytest.mark.asyncio
async def test_recognize_returns_text(asr: AliyunASR) -> None:
    with patch("app.speech.asr.aliyun.httpx.AsyncClient") as mock_cls:
        client = AsyncMock()
        client.post.return_value = _mock_response("今天天气真好")
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await asr.recognize(b"\x00" * 3200)
        assert result.text == "今天天气真好"
        assert result.dialect_detected == DialectCode.MANDARIN


@pytest.mark.asyncio
async def test_recognize_rejects_non_mandarin(asr: AliyunASR) -> None:
    with pytest.raises(ValueError, match="仅支持普通话"):
        await asr.recognize(b"\x00" * 100, dialect=DialectCode.CANTONESE)


@pytest.mark.asyncio
async def test_supported_dialects(asr: AliyunASR) -> None:
    assert asr.supported_dialects() == [DialectCode.MANDARIN]


@pytest.mark.asyncio
async def test_recognize_sends_base64_audio(asr: AliyunASR) -> None:
    with patch("app.speech.asr.aliyun.httpx.AsyncClient") as mock_cls:
        client = AsyncMock()
        client.post.return_value = _mock_response()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await asr.recognize(b"\x01\x02\x03", audio_format="pcm", sample_rate=16000)

        call_args = client.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert "base64" in payload["input"]["audio"]
        assert payload["parameters"]["sample_rate"] == 16000


@pytest.mark.asyncio
async def test_recognize_stream_collects_and_recognizes(asr: AliyunASR) -> None:
    async def _chunks():
        yield b"\x00" * 1600
        yield b"\x00" * 1600

    with patch("app.speech.asr.aliyun.httpx.AsyncClient") as mock_cls:
        client = AsyncMock()
        client.post.return_value = _mock_response("流式测试")
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        results = []
        async for r in asr.recognize_stream(_chunks()):
            results.append(r)

        assert len(results) == 1
        assert results[0].text == "流式测试"
