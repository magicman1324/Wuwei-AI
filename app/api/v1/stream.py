"""​WebSocket 实时语音流接口。

协议
----
客户端 → 服务端:
  - 二进制帧 (PCM16 16kHz 单声道)
  - 文本帧  {"type": "end"}        表示一轮说话结束
  - 文本帧  {"type": "close"}      主动关闭连接

服务端 → 客户端:
  - {"type": "asr_partial", "text": "...", "is_final": false}
  - {"type": "asr_final",   "text": "...", "dialect_detected": "yue"}
  - {"type": "llm_chunk",   "text": "..."}
  - {"type": "tts_audio",   "audio": "<base64>", "format": "mp3"}
  - {"type": "done",        "full_response": "..."}
  - {"type": "error",       "reason": "..."}

一个 WebSocket 连接支持多轮对话：客户端发送音频帧 → "end" 控制帧，
服务端依次返回 asr_partial* → asr_final → llm_chunk* → tts_audio → done，
然后进入下一轮等待。
"""
from __future__ import annotations

import asyncio
import base64
import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from app.chat.engine import ChatEngine
from app.chat.llm.base import LLMMessage
from app.chat.prompt.system_prompts import build_system_prompt
from app.dependencies import get_chat_engine, get_speech_pipeline
from app.dialect.adapter import DialectCode, DialectRegistry
from app.speech.pipeline import SpeechPipeline

router = APIRouter()


def _coerce_dialect(value: str) -> DialectCode:
    try:
        return DialectCode(value)
    except ValueError:
        return DialectCode.MANDARIN


async def _queue_to_async_iter(
    queue: asyncio.Queue[bytes | None],
) -> AsyncIterator[bytes]:
    """把 asyncio.Queue 转为 AsyncIterator；None 为结束哨兵。"""
    while True:
        chunk = await queue.get()
        if chunk is None:
            return
        yield chunk


class _UtteranceReceiver:
    """在后台任务里从 WebSocket 收音频，喂给 queue；遇到 end 控制帧或断开时放哨兵。"""

    def __init__(self, websocket: WebSocket, queue: asyncio.Queue[bytes | None]):
        self._ws = websocket
        self._queue = queue
        self.ended = False
        self.disconnected = False
        self.close_requested = False

    async def run(self) -> None:
        try:
            while True:
                message = await self._ws.receive()
                msg_type = message.get("type")
                if msg_type == "websocket.disconnect":
                    self.disconnected = True
                    break
                data_bytes = message.get("bytes")
                if data_bytes:
                    await self._queue.put(bytes(data_bytes))
                    continue
                text = message.get("text")
                if text:
                    try:
                        ctrl = json.loads(text)
                    except json.JSONDecodeError:
                        logger.warning(f"收到非 JSON 控制帧: {text!r}")
                        continue
                    ctrl_type = ctrl.get("type")
                    if ctrl_type == "end":
                        self.ended = True
                        break
                    if ctrl_type == "close":
                        self.close_requested = True
                        break
        finally:
            await self._queue.put(None)


async def _run_asr_stream(
    speech_pipeline: SpeechPipeline,
    websocket: WebSocket,
    queue: asyncio.Queue[bytes | None],
    dialect: DialectCode,
) -> str:
    """驱动讯飞流式识别，推送 asr_partial，返回最终文本。"""
    asr = speech_pipeline.get_asr(dialect)
    audio_iter = _queue_to_async_iter(queue)
    final_text = ""
    async for result in asr.recognize_stream(audio_iter, dialect):
        final_text = result.text
        await websocket.send_json(
            {
                "type": "asr_partial",
                "text": result.text,
                "is_final": False,
            }
        )
    return final_text


async def _run_llm_stream(
    chat_engine: ChatEngine,
    websocket: WebSocket,
    user_id: str,
    dialect: DialectCode,
    normalized_input: str,
) -> str:
    """驱动 LLM 流式输出，推送 llm_chunk，返回完整回复（未方言化）。"""
    adapter = DialectRegistry.get(dialect)
    system_prompt = build_system_prompt(adapter.get_system_prompt_addition())
    history = chat_engine.memory.get_recent(user_id)
    messages = [
        LLMMessage("system", system_prompt),
        *history,
        LLMMessage("user", normalized_input),
    ]
    pieces: list[str] = []
    async for chunk in chat_engine.llm.chat_stream(messages):
        if not chunk:
            continue
        pieces.append(chunk)
        await websocket.send_json({"type": "llm_chunk", "text": chunk})
    return "".join(pieces)


async def _safe_send(websocket: WebSocket, payload: dict[str, Any]) -> None:
    try:
        await websocket.send_json(payload)
    except Exception as exc:  # 连接可能已断
        logger.debug(f"WebSocket 发送失败: {exc}")


@router.websocket("/ws/voice-stream")
async def voice_stream(
    websocket: WebSocket,
    chat_engine: ChatEngine = Depends(get_chat_engine),
    speech_pipeline: SpeechPipeline = Depends(get_speech_pipeline),
) -> None:
    """实时语音流对话端点。"""
    await websocket.accept()

    user_id = websocket.query_params.get("user_id", "anonymous")
    dialect_param = websocket.query_params.get("dialect", "cmn")
    dialect = _coerce_dialect(dialect_param)

    logger.info(
        f"WebSocket 连接建立: user={user_id}, dialect={dialect.value}"
    )

    # 预检查 ASR 引擎是否可用，尽早告知前端
    try:
        speech_pipeline.get_asr(dialect)
    except RuntimeError as exc:
        await _safe_send(
            websocket,
            {"type": "error", "reason": f"语音识别未就绪: {exc}"},
        )
        await websocket.close()
        return

    try:
        while True:
            queue: asyncio.Queue[bytes | None] = asyncio.Queue()
            receiver = _UtteranceReceiver(websocket, queue)
            recv_task = asyncio.create_task(receiver.run())

            # ---- ASR ----
            try:
                final_asr_text = await _run_asr_stream(
                    speech_pipeline, websocket, queue, dialect
                )
            except Exception as exc:
                logger.exception("ASR 流式识别失败")
                await _safe_send(
                    websocket,
                    {"type": "error", "reason": f"ASR 失败: {exc}"},
                )
                recv_task.cancel()
                try:
                    await recv_task
                except (asyncio.CancelledError, WebSocketDisconnect):
                    pass
                break

            # 等待 receiver 自然结束（通常 queue 已收到 None 后立刻返回）
            try:
                await recv_task
            except WebSocketDisconnect:
                receiver.disconnected = True

            if receiver.disconnected:
                logger.info(f"客户端已断开: user={user_id}")
                break
            if receiver.close_requested:
                logger.info(f"客户端请求关闭: user={user_id}")
                await websocket.close()
                return

            # 空识别：提示客户端并进入下一轮
            if not final_asr_text.strip():
                await _safe_send(
                    websocket,
                    {
                        "type": "asr_final",
                        "text": "",
                        "dialect_detected": dialect.value,
                    },
                )
                await _safe_send(
                    websocket,
                    {"type": "done", "full_response": ""},
                )
                continue

            # 方言文本 → 规范化为普通话
            normalized = speech_pipeline.normalizer.normalize(
                final_asr_text, dialect
            )
            await _safe_send(
                websocket,
                {
                    "type": "asr_final",
                    "text": final_asr_text,
                    "dialect_detected": dialect.value,
                },
            )

            # ---- LLM ----
            try:
                raw_reply = await _run_llm_stream(
                    chat_engine, websocket, user_id, dialect, normalized
                )
            except Exception as exc:
                logger.exception("LLM 流式失败")
                await _safe_send(
                    websocket,
                    {"type": "error", "reason": f"LLM 失败: {exc}"},
                )
                continue

            adapter = DialectRegistry.get(dialect)
            dialect_reply = adapter.from_mandarin(raw_reply)
            # 记忆追加（与 REST 路径保持一致）
            chat_engine.memory.add(user_id, normalized, dialect_reply)

            # ---- TTS ----
            try:
                audio_bytes, audio_fmt = await speech_pipeline.synthesize_response(
                    text=dialect_reply,
                    dialect=dialect,
                )
                if audio_bytes:
                    await _safe_send(
                        websocket,
                        {
                            "type": "tts_audio",
                            "audio": base64.b64encode(audio_bytes).decode(
                                "ascii"
                            ),
                            "format": audio_fmt,
                        },
                    )
            except Exception as exc:
                logger.warning(f"TTS 失败，降级为纯文字: {exc}")

            await _safe_send(
                websocket,
                {"type": "done", "full_response": dialect_reply},
            )

    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开: user={user_id}")
    except Exception as exc:
        logger.exception("WebSocket 处理异常")
        await _safe_send(
            websocket,
            {"type": "error", "reason": f"服务器错误: {exc}"},
        )
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
