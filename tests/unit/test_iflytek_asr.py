"""讯飞 ASR 单元测试（Mock websockets，不联网）。"""
from __future__ import annotations

import base64
import json
from typing import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest

from app.dialect.adapter import DialectCode
from app.speech.asr.iflytek import IflytekASR, _parse_iat_frame


# ---- 辅助：伪造讯飞 WebSocket ----

class FakeWS:
    """模拟 websockets 连接：记录 send 的帧，按脚本回放 recv。"""

    def __init__(self, recv_script: list[dict]):
        self.sent: list[str] = []
        self._recv_script = list(recv_script)

    async def send(self, data: str) -> None:
        self.sent.append(data)

    async def recv(self) -> str:
        if not self._recv_script:
            raise RuntimeError("FakeWS recv queue empty")
        return json.dumps(self._recv_script.pop(0))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def _frame(text: str, status: int = 1) -> dict:
    """构造一个讯飞 IAT 返回的单帧。"""
    return {
        "code": 0,
        "message": "success",
        "data": {
            "status": status,
            "result": {
                "ws": [
                    {"cw": [{"w": text}]}
                ]
            },
        },
    }


# ---- 测试 _parse_iat_frame ----

def test_parse_iat_frame_extracts_text_and_status() -> None:
    text, status = _parse_iat_frame(_frame("你好", status=1))
    assert text == "你好"
    assert status == 1


def test_parse_iat_frame_final_status() -> None:
    _, status = _parse_iat_frame(_frame("", status=2))
    assert status == 2


def test_parse_iat_frame_missing_fields() -> None:
    text, status = _parse_iat_frame({"data": {}})
    assert text == ""
    assert status == 1


# ---- 测试 recognize() ----

@pytest.mark.asyncio
async def test_recognize_single_frame_audio() -> None:
    asr = IflytekASR(app_id="a", api_key="k", api_secret="s", frame_interval_ms=0)
    fake = FakeWS(
        recv_script=[
            _frame("你好", status=1),
            _frame("，世界", status=2),
        ]
    )
    with patch("app.speech.asr.iflytek.websockets.connect", return_value=fake):
        result = await asr.recognize(b"\x00" * 500, dialect=DialectCode.MANDARIN)

    assert result.text == "你好，世界"
    assert result.dialect_detected == DialectCode.MANDARIN
    # 单帧音频应发送一条 status=2 的首帧（含 common/business）
    assert len(fake.sent) == 1
    first = json.loads(fake.sent[0])
    assert first["common"]["app_id"] == "a"
    assert first["business"]["language"] == "zh_cn"
    assert first["business"]["accent"] == "mandarin"
    assert first["data"]["status"] == 2


@pytest.mark.asyncio
async def test_recognize_multi_frame_audio() -> None:
    asr = IflytekASR(
        app_id="a", api_key="k", api_secret="s",
        frame_size=100, frame_interval_ms=0,
    )
    # 300 bytes → 3 帧
    fake = FakeWS(recv_script=[_frame("ok", status=2)])
    with patch("app.speech.asr.iflytek.websockets.connect", return_value=fake):
        result = await asr.recognize(b"\x01" * 300)

    assert result.text == "ok"
    assert len(fake.sent) == 3
    frames = [json.loads(f) for f in fake.sent]
    # 首帧 status=0 + common/business
    assert frames[0]["data"]["status"] == 0
    assert "common" in frames[0]
    # 中间帧 status=1，无 common
    assert frames[1]["data"]["status"] == 1
    assert "common" not in frames[1]
    # 末帧 status=2
    assert frames[-1]["data"]["status"] == 2


@pytest.mark.asyncio
async def test_recognize_empty_audio_returns_empty() -> None:
    asr = IflytekASR(app_id="a", api_key="k", api_secret="s")
    with patch("app.speech.asr.iflytek.websockets.connect") as mock_connect:
        result = await asr.recognize(b"")
    # 空音频直接返回，不应发起连接
    mock_connect.assert_not_called()
    assert result.text == ""
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_recognize_cantonese_dialect_params() -> None:
    asr = IflytekASR(app_id="a", api_key="k", api_secret="s", frame_interval_ms=0)
    fake = FakeWS(recv_script=[_frame("唔该", status=2)])
    with patch("app.speech.asr.iflytek.websockets.connect", return_value=fake):
        result = await asr.recognize(b"\x00" * 100, dialect=DialectCode.CANTONESE)

    first = json.loads(fake.sent[0])
    assert first["business"]["accent"] == "cantonese"
    assert result.text == "唔该"
    assert result.dialect_detected == DialectCode.CANTONESE


@pytest.mark.asyncio
async def test_recognize_server_error_raises() -> None:
    asr = IflytekASR(app_id="a", api_key="k", api_secret="s", frame_interval_ms=0)
    error_frame = {"code": 10163, "message": "auth failed", "data": {"status": 2}}
    fake = FakeWS(recv_script=[error_frame])
    with patch("app.speech.asr.iflytek.websockets.connect", return_value=fake):
        with pytest.raises(RuntimeError, match="讯飞 ASR 错误"):
            await asr.recognize(b"\x00" * 100)


# ---- 测试 recognize_stream() ----

async def _audio_chunks() -> AsyncIterator[bytes]:
    for _ in range(3):
        yield b"\x00" * 1280


@pytest.mark.asyncio
async def test_recognize_stream_yields_partials_and_final() -> None:
    asr = IflytekASR(app_id="a", api_key="k", api_secret="s", frame_interval_ms=0)
    fake = FakeWS(
        recv_script=[
            _frame("你", status=1),
            _frame("好", status=1),
            _frame("吗", status=2),
        ]
    )
    with patch("app.speech.asr.iflytek.websockets.connect", return_value=fake):
        texts: list[str] = []
        async for res in asr.recognize_stream(_audio_chunks(), dialect=DialectCode.MANDARIN):
            texts.append(res.text)

    assert texts[-1] == "你好吗"
    assert len(texts) == 3  # 累积式：你 / 你好 / 你好吗
    assert texts == ["你", "你好", "你好吗"]


# ---- 确保发送的音频是 base64 编码 ----

@pytest.mark.asyncio
async def test_sent_audio_is_base64_encoded() -> None:
    asr = IflytekASR(
        app_id="a", api_key="k", api_secret="s",
        frame_size=50, frame_interval_ms=0,
    )
    fake = FakeWS(recv_script=[_frame("x", status=2)])
    raw = b"\xff" * 50
    with patch("app.speech.asr.iflytek.websockets.connect", return_value=fake):
        await asr.recognize(raw)

    sent_frame = json.loads(fake.sent[0])
    audio_b64 = sent_frame["data"]["audio"]
    assert base64.b64decode(audio_b64) == raw
