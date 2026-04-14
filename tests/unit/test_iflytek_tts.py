"""讯飞 TTS 单元测试（Mock websockets，不联网）。"""
from __future__ import annotations

import base64
import json
from unittest.mock import patch

import pytest

from app.speech.tts.iflytek import (
    IflytekTTS,
    _audio_format_to_aue,
    _to_iflytek_scale,
)


# ---- 辅助：伪造讯飞 WebSocket ----

class FakeWS:
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


def _audio_frame(chunk: bytes, status: int = 1) -> dict:
    return {
        "code": 0,
        "message": "success",
        "data": {
            "audio": base64.b64encode(chunk).decode("ascii"),
            "status": status,
        },
    }


# ---- 纯函数映射测试 ----

def test_to_iflytek_scale_midpoint() -> None:
    assert _to_iflytek_scale(1.0) == 50


def test_to_iflytek_scale_slow() -> None:
    assert _to_iflytek_scale(0.85) == 42  # round(42.5) = 42 (banker's)


def test_to_iflytek_scale_clamps_high() -> None:
    assert _to_iflytek_scale(5.0) == 100


def test_to_iflytek_scale_clamps_low() -> None:
    assert _to_iflytek_scale(-1.0) == 0


def test_audio_format_to_aue_mp3() -> None:
    assert _audio_format_to_aue("mp3") == "lame"


def test_audio_format_to_aue_pcm() -> None:
    assert _audio_format_to_aue("pcm") == "raw"


def test_audio_format_to_aue_unsupported() -> None:
    with pytest.raises(ValueError, match="不支持的音频格式"):
        _audio_format_to_aue("flac")


# ---- synthesize() 行为测试 ----

@pytest.mark.asyncio
async def test_synthesize_single_frame() -> None:
    tts = IflytekTTS(app_id="a", api_key="k", api_secret="s")
    fake = FakeWS(recv_script=[_audio_frame(b"\x01\x02\x03", status=2)])

    with patch("app.speech.tts.iflytek.websockets.connect", return_value=fake):
        result = await tts.synthesize("你好世界", voice_name="xiaoyan")

    assert result.audio_data == b"\x01\x02\x03"
    assert result.audio_format == "mp3"
    assert result.sample_rate == 16000


@pytest.mark.asyncio
async def test_synthesize_multi_frame_concatenates_audio() -> None:
    tts = IflytekTTS(app_id="a", api_key="k", api_secret="s")
    fake = FakeWS(
        recv_script=[
            _audio_frame(b"AAA", status=0),
            _audio_frame(b"BBB", status=1),
            _audio_frame(b"CCC", status=2),
        ]
    )
    with patch("app.speech.tts.iflytek.websockets.connect", return_value=fake):
        result = await tts.synthesize("hello")

    assert result.audio_data == b"AAABBBCCC"


@pytest.mark.asyncio
async def test_synthesize_request_payload_fields() -> None:
    tts = IflytekTTS(app_id="my_app", api_key="k", api_secret="s")
    fake = FakeWS(recv_script=[_audio_frame(b"x", status=2)])

    with patch("app.speech.tts.iflytek.websockets.connect", return_value=fake):
        await tts.synthesize(
            "你好",
            voice_name="xiaomei",
            speed=0.85,
            volume=1.2,
            audio_format="mp3",
        )

    assert len(fake.sent) == 1
    payload = json.loads(fake.sent[0])
    assert payload["common"]["app_id"] == "my_app"
    biz = payload["business"]
    assert biz["vcn"] == "xiaomei"
    assert biz["aue"] == "lame"
    assert biz["sfl"] == 1  # lame 必须加流式标记
    assert biz["tte"] == "UTF8"
    assert biz["speed"] == 42   # 0.85 * 50
    assert biz["volume"] == 60  # 1.2 * 50
    # text 必须 base64
    assert base64.b64decode(payload["data"]["text"]).decode("utf-8") == "你好"
    assert payload["data"]["status"] == 2


@pytest.mark.asyncio
async def test_synthesize_pcm_uses_raw_aue_and_no_sfl() -> None:
    tts = IflytekTTS(app_id="a", api_key="k", api_secret="s")
    fake = FakeWS(recv_script=[_audio_frame(b"pcm", status=2)])
    with patch("app.speech.tts.iflytek.websockets.connect", return_value=fake):
        result = await tts.synthesize("hi", audio_format="pcm")

    biz = json.loads(fake.sent[0])["business"]
    assert biz["aue"] == "raw"
    assert "sfl" not in biz
    assert result.audio_format == "pcm"


@pytest.mark.asyncio
async def test_synthesize_empty_text_skips_network() -> None:
    tts = IflytekTTS(app_id="a", api_key="k", api_secret="s")
    with patch("app.speech.tts.iflytek.websockets.connect") as mock_connect:
        result = await tts.synthesize("   ")
    mock_connect.assert_not_called()
    assert result.audio_data == b""


@pytest.mark.asyncio
async def test_synthesize_server_error_raises() -> None:
    tts = IflytekTTS(app_id="a", api_key="k", api_secret="s")
    error = {"code": 10005, "message": "invalid app_id", "data": {"status": 2}}
    fake = FakeWS(recv_script=[error])

    with patch("app.speech.tts.iflytek.websockets.connect", return_value=fake):
        with pytest.raises(RuntimeError, match="讯飞 TTS 错误"):
            await tts.synthesize("你好")


@pytest.mark.asyncio
async def test_synthesize_uses_default_voice_when_empty() -> None:
    tts = IflytekTTS(
        app_id="a", api_key="k", api_secret="s",
        default_voice="aisjiuxu",
    )
    fake = FakeWS(recv_script=[_audio_frame(b"x", status=2)])
    with patch("app.speech.tts.iflytek.websockets.connect", return_value=fake):
        await tts.synthesize("hi", voice_name="")

    biz = json.loads(fake.sent[0])["business"]
    assert biz["vcn"] == "aisjiuxu"
