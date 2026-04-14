"""科大讯飞 TTS 适配器 — 方言语音合成。

讯飞在线 TTS WebSocket API:
https://www.xfyun.cn/doc/tts/online_tts/API.html

协议要点：
- 一次性发送完整文本（text base64），status=2
- 服务端按帧推 data.audio（base64），data.status=2 时合成结束
- aue: lame=MP3, raw=PCM16, speex=speex
"""
from __future__ import annotations

import asyncio
import base64
import json

import websockets
from loguru import logger

from app.speech.iflytek_common import build_auth_url
from app.speech.tts.base import BaseTTS, TTSResult

_TTS_URL = "wss://tts-api.xfyun.cn/v2/tts"

# 讯飞 speed / volume 取值 0-100，50 对应"正常"。
# 我们内部用 float 相对值（1.0 = normal），做线性映射。
_IFLYTEK_MIDPOINT = 50
_IFLYTEK_MAX = 100


def _to_iflytek_scale(value: float) -> int:
    """float 相对值 → 讯飞 0-100 整数（1.0 映射为 50）。"""
    raw = int(round(value * _IFLYTEK_MIDPOINT))
    return max(0, min(_IFLYTEK_MAX, raw))


def _audio_format_to_aue(audio_format: str) -> str:
    fmt = audio_format.lower()
    if fmt == "mp3":
        return "lame"
    if fmt == "pcm":
        return "raw"
    if fmt == "speex":
        return "speex"
    raise ValueError(f"不支持的音频格式: {audio_format}")


class IflytekTTS(BaseTTS):
    """科大讯飞语音合成引擎（WebSocket /v2/tts）。"""

    def __init__(
        self,
        app_id: str,
        api_key: str,
        api_secret: str,
        *,
        default_voice: str = "xiaoyan",
        recv_timeout_s: float = 15.0,
    ):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.default_voice = default_voice
        self.recv_timeout_s = recv_timeout_s

    def _build_request(
        self,
        *,
        text: str,
        voice_name: str,
        speed: float,
        volume: float,
        audio_format: str,
    ) -> str:
        business = {
            "aue": _audio_format_to_aue(audio_format),
            "vcn": voice_name or self.default_voice,
            "speed": _to_iflytek_scale(speed),
            "volume": _to_iflytek_scale(volume),
            "pitch": _IFLYTEK_MIDPOINT,
            "tte": "UTF8",
        }
        # MP3 流式需要加 sfl=1 让讯飞分片推送
        if business["aue"] == "lame":
            business["sfl"] = 1

        payload = {
            "common": {"app_id": self.app_id},
            "business": business,
            "data": {
                "status": 2,  # TTS 一次性发送完整文本
                "text": base64.b64encode(text.encode("utf-8")).decode("ascii"),
            },
        }
        return json.dumps(payload, ensure_ascii=False)

    async def _collect_audio(self, ws) -> bytes:
        """累积接收音频帧，直到 data.status=2。"""
        buffer = bytearray()
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=self.recv_timeout_s)
            except asyncio.TimeoutError as exc:
                raise RuntimeError("讯飞 TTS 接收超时") from exc

            payload = json.loads(raw)
            code = payload.get("code", 0)
            if code != 0:
                raise RuntimeError(
                    f"讯飞 TTS 错误: code={code} message={payload.get('message')}"
                )

            data = payload.get("data") or {}
            audio_b64 = data.get("audio")
            if audio_b64:
                buffer.extend(base64.b64decode(audio_b64))

            if int(data.get("status", 1)) == 2:
                break
        return bytes(buffer)

    async def synthesize(
        self,
        text: str,
        voice_name: str = "xiaoyan",
        speed: float = 1.0,
        volume: float = 1.0,
        audio_format: str = "mp3",
    ) -> TTSResult:
        if not text.strip():
            return TTSResult(audio_data=b"", audio_format=audio_format, sample_rate=16000)

        url = build_auth_url(_TTS_URL, self.api_key, self.api_secret)
        request_frame = self._build_request(
            text=text,
            voice_name=voice_name,
            speed=speed,
            volume=volume,
            audio_format=audio_format,
        )

        logger.debug(
            f"讯飞 TTS 合成: voice={voice_name} len={len(text)} "
            f"speed={speed} volume={volume} format={audio_format}"
        )

        async with websockets.connect(url) as ws:
            await ws.send(request_frame)
            audio = await self._collect_audio(ws)

        return TTSResult(
            audio_data=audio,
            audio_format=audio_format,
            sample_rate=16000,
        )
