"""阿里云智能语音 ASR 适配器（普通话 fallback）。

使用 DashScope 语音识别 API，仅支持普通话短音频（≤60s）。
文档: https://help.aliyun.com/document_detail/2712536.html
"""
from __future__ import annotations

import base64
import json
from collections.abc import AsyncIterator

import httpx
from loguru import logger

from app.dialect.adapter import DialectCode
from app.speech.asr.base import ASRResult, BaseASR

PARAFORMER_URL = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
REALTIME_URL = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/realtime"


class AliyunASR(BaseASR):
    """阿里云语音识别引擎（普通话 fallback）。"""

    def __init__(self, access_key: str, access_secret: str, app_key: str):
        self.access_key = access_key
        self.access_secret = access_secret
        self.app_key = app_key

    def supported_dialects(self) -> list[DialectCode]:
        return [DialectCode.MANDARIN]

    async def recognize(
        self,
        audio_data: bytes,
        dialect: DialectCode = DialectCode.MANDARIN,
        audio_format: str = "pcm",
        sample_rate: int = 16000,
    ) -> ASRResult:
        if dialect != DialectCode.MANDARIN:
            raise ValueError(f"阿里云 ASR 仅支持普通话，收到: {dialect}")

        audio_b64 = base64.b64encode(audio_data).decode()

        headers = {
            "Authorization": f"Bearer {self.access_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "paraformer-v2",
            "input": {
                "audio": f"data:audio/{audio_format};base64,{audio_b64}",
            },
            "parameters": {
                "sample_rate": sample_rate,
                "language_hints": ["zh"],
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(PARAFORMER_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        text = ""
        confidence = 0.0

        output = data.get("output", {})
        results = output.get("results", [])
        if results:
            sentence = results[0].get("sentence", {})
            text = sentence.get("text", "")
            confidence = sentence.get("confidence", 0.9)

        logger.info(f"阿里云 ASR 识别完成: text={text!r}")
        return ASRResult(
            text=text,
            confidence=confidence,
            dialect_detected=DialectCode.MANDARIN,
        )

    async def recognize_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        dialect: DialectCode = DialectCode.MANDARIN,
    ) -> AsyncIterator[ASRResult]:
        chunks: list[bytes] = []
        async for chunk in audio_stream:
            chunks.append(chunk)

        full_audio = b"".join(chunks)
        if full_audio:
            result = await self.recognize(full_audio, dialect)
            yield result
