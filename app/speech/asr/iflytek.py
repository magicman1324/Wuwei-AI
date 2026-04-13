"""科大讯飞 ASR 适配器 — 方言识别首选。

讯飞开放平台文档：
- IAT (语音听写): https://www.xfyun.cn/doc/asr/voicedictation/API.html

数据帧协议（JSON）：
- 首帧  status=0, common + business + data
- 中间帧 status=1, data
- 末尾帧 status=2, data（content 可为空）
服务端回包：
- data.status ∈ {0,1,2}；data.result.ws[].cw[].w 为文本
"""
from __future__ import annotations

import asyncio
import base64
import json
from collections.abc import AsyncIterator

import websockets
from loguru import logger

from app.dialect.adapter import DialectCode
from app.speech.asr.base import ASRResult, BaseASR
from app.speech.iflytek_common import DEFAULT_FRAME_SIZE, build_auth_url, chunk_pcm

_IAT_URL = "wss://iat-api.xfyun.cn/v2/iat"

# 讯飞方言编码映射
# language 取值参见讯飞 IAT 文档 business 部分
_DIALECT_TO_IFLYTEK: dict[DialectCode, dict[str, str]] = {
    DialectCode.MANDARIN: {"language": "zh_cn", "accent": "mandarin"},
    DialectCode.CANTONESE: {"language": "zh_cn", "accent": "cantonese"},
    DialectCode.SICHUAN: {"language": "zh_cn", "accent": "lmz"},  # 四川方言 accent
}


def _parse_iat_frame(payload: dict) -> tuple[str, int]:
    """解析讯飞 IAT 返回的单帧 JSON，返回 (text, status)。

    status: 0=识别中, 1=继续识别, 2=识别结束。
    """
    data = payload.get("data") or {}
    status = int(data.get("status", 1))
    result = data.get("result") or {}
    ws_list = result.get("ws") or []
    parts: list[str] = []
    for ws in ws_list:
        for cw in ws.get("cw") or []:
            w = cw.get("w")
            if w:
                parts.append(w)
    return "".join(parts), status


class IflytekASR(BaseASR):
    """科大讯飞语音识别引擎（WebSocket IAT 协议）。"""

    def __init__(
        self,
        app_id: str,
        api_key: str,
        api_secret: str,
        *,
        frame_size: int = DEFAULT_FRAME_SIZE,
        frame_interval_ms: int = 40,
        recv_timeout_s: float = 10.0,
    ):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.frame_size = frame_size
        self.frame_interval_ms = frame_interval_ms
        self.recv_timeout_s = recv_timeout_s

    def supported_dialects(self) -> list[DialectCode]:
        return [DialectCode.MANDARIN, DialectCode.CANTONESE, DialectCode.SICHUAN]

    def _business_params(self, dialect: DialectCode) -> dict:
        cfg = _DIALECT_TO_IFLYTEK.get(dialect, _DIALECT_TO_IFLYTEK[DialectCode.MANDARIN])
        return {
            "language": cfg["language"],
            "domain": "iat",
            "accent": cfg["accent"],
            "vad_eos": 3000,
        }

    def _build_frame(
        self,
        *,
        status: int,
        audio_chunk: bytes,
        dialect: DialectCode,
        audio_format: str,
        sample_rate: int,
        include_common: bool,
    ) -> str:
        """构造一帧发送给讯飞 IAT 的 JSON 字符串。"""
        data = {
            "status": status,
            "format": f"audio/L16;rate={sample_rate}" if audio_format == "pcm" else audio_format,
            "audio": base64.b64encode(audio_chunk).decode("ascii"),
            "encoding": "raw",
        }
        frame: dict = {"data": data}
        if include_common:
            frame["common"] = {"app_id": self.app_id}
            frame["business"] = self._business_params(dialect)
        return json.dumps(frame, ensure_ascii=False)

    async def _stream_audio(
        self,
        ws,
        frames: list[bytes],
        dialect: DialectCode,
        audio_format: str,
        sample_rate: int,
    ) -> None:
        """逐帧发送，最后一帧 status=2。"""
        total = len(frames)
        for idx, chunk in enumerate(frames):
            if idx == 0 and total == 1:
                status = 2  # 单帧情况直接收尾
            elif idx == 0:
                status = 0  # 首帧
            elif idx == total - 1:
                status = 2  # 末帧
            else:
                status = 1  # 中间帧
            payload = self._build_frame(
                status=status,
                audio_chunk=chunk,
                dialect=dialect,
                audio_format=audio_format,
                sample_rate=sample_rate,
                include_common=(idx == 0),
            )
            await ws.send(payload)
            if status != 2:
                await asyncio.sleep(self.frame_interval_ms / 1000)

    async def _collect_results(self, ws) -> str:
        """累积接收识别结果，直到 status=2 或连接关闭。"""
        pieces: list[str] = []
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=self.recv_timeout_s)
            except asyncio.TimeoutError as exc:
                raise RuntimeError("讯飞 ASR 接收超时") from exc
            payload = json.loads(raw)
            code = payload.get("code", 0)
            if code != 0:
                raise RuntimeError(
                    f"讯飞 ASR 错误: code={code} message={payload.get('message')}"
                )
            text, status = _parse_iat_frame(payload)
            if text:
                pieces.append(text)
            if status == 2:
                break
        return "".join(pieces)

    async def recognize(
        self,
        audio_data: bytes,
        dialect: DialectCode = DialectCode.MANDARIN,
        audio_format: str = "pcm",
        sample_rate: int = 16000,
    ) -> ASRResult:
        if not audio_data:
            return ASRResult(text="", confidence=0.0, dialect_detected=dialect)

        url = build_auth_url(_IAT_URL, self.api_key, self.api_secret)
        frames = list(chunk_pcm(audio_data, self.frame_size))

        logger.debug(
            f"讯飞 ASR 连接: dialect={dialect.value} frames={len(frames)} "
            f"bytes={len(audio_data)}"
        )

        async with websockets.connect(url) as ws:
            await self._stream_audio(ws, frames, dialect, audio_format, sample_rate)
            text = await self._collect_results(ws)

        return ASRResult(
            text=text,
            confidence=0.9,
            dialect_detected=dialect,
            raw_text=text,
        )

    async def recognize_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        dialect: DialectCode = DialectCode.MANDARIN,
    ) -> AsyncIterator[ASRResult]:
        """流式识别：边收音频帧边回 partial / final。"""
        url = build_auth_url(_IAT_URL, self.api_key, self.api_secret)
        async with websockets.connect(url) as ws:
            send_done = asyncio.Event()

            async def sender() -> None:
                first = True
                last_chunk: bytes | None = None
                async for chunk in audio_stream:
                    if not chunk:
                        continue
                    if last_chunk is not None:
                        payload = self._build_frame(
                            status=0 if first else 1,
                            audio_chunk=last_chunk,
                            dialect=dialect,
                            audio_format="pcm",
                            sample_rate=16000,
                            include_common=first,
                        )
                        await ws.send(payload)
                        first = False
                    last_chunk = chunk
                # 末帧（或单帧情况）
                if last_chunk is not None:
                    payload = self._build_frame(
                        status=2 if not first else 2,
                        audio_chunk=last_chunk,
                        dialect=dialect,
                        audio_format="pcm",
                        sample_rate=16000,
                        include_common=first,
                    )
                    await ws.send(payload)
                send_done.set()

            async def receiver() -> AsyncIterator[ASRResult]:
                accumulated: list[str] = []
                while True:
                    try:
                        raw = await asyncio.wait_for(
                            ws.recv(), timeout=self.recv_timeout_s
                        )
                    except asyncio.TimeoutError:
                        if send_done.is_set():
                            break
                        continue
                    payload = json.loads(raw)
                    code = payload.get("code", 0)
                    if code != 0:
                        raise RuntimeError(
                            f"讯飞 ASR 错误: code={code} "
                            f"message={payload.get('message')}"
                        )
                    text, status = _parse_iat_frame(payload)
                    if text:
                        accumulated.append(text)
                        yield ASRResult(
                            text="".join(accumulated),
                            confidence=0.7 if status != 2 else 0.95,
                            dialect_detected=dialect,
                        )
                    if status == 2:
                        break

            sender_task = asyncio.create_task(sender())
            try:
                async for result in receiver():
                    yield result
            finally:
                await sender_task
