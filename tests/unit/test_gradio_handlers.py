"""Gradio handler 单元测试 — 不渲染 Blocks，直接调用模块级 handler。"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock

import numpy as np
import pytest

import app.dialect.dialects  # noqa: F401  触发方言注册
from app.chat.engine import ChatResult
from app.dialect.adapter import DialectCode
from app.ui.gradio_app import handle_text_chat, handle_voice_chat


# ---- handle_text_chat ----

def _fake_chat_engine(reply_text: str = "你好呀") -> AsyncMock:
    engine = AsyncMock()
    engine.chat_text = AsyncMock(
        return_value=ChatResult(
            text=reply_text, dialect=DialectCode.MANDARIN, raw_llm_response=reply_text,
        )
    )
    engine.chat = AsyncMock(
        return_value=ChatResult(
            text=reply_text, dialect=DialectCode.MANDARIN, raw_llm_response=reply_text,
        )
    )
    return engine


@pytest.mark.asyncio
async def test_text_chat_appends_to_history() -> None:
    engine = _fake_chat_engine("我很好")
    history, cleared = await handle_text_chat(
        "你好", [], "cmn", "u1", chat_engine=engine,
    )
    assert history == [["你好", "我很好"]]
    assert cleared == ""
    engine.chat_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_text_chat_empty_message_no_op() -> None:
    engine = _fake_chat_engine()
    history, cleared = await handle_text_chat(
        "   ", [["前轮", "前回复"]], "cmn", "u1", chat_engine=engine,
    )
    assert history == [["前轮", "前回复"]]
    assert cleared == ""
    engine.chat_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_text_chat_invalid_dialect_falls_back() -> None:
    engine = _fake_chat_engine()
    await handle_text_chat("hi", [], "not-a-dialect", "u1", chat_engine=engine)
    call = engine.chat_text.call_args
    assert call.kwargs["dialect"] == DialectCode.MANDARIN


# ---- handle_voice_chat ----

def _fake_pipeline(
    *,
    raw="我食咗饭",
    normalized="我吃了饭",
    detected=DialectCode.CANTONESE,
    audio_bytes=b"fake_mp3",
    audio_fmt="mp3",
) -> AsyncMock:
    pipeline = AsyncMock()
    pipeline._asr_engines = {"iflytek": object()}
    pipeline._tts_engines = {"iflytek": object()}
    pipeline.process_voice = AsyncMock(return_value=(raw, normalized, detected))
    pipeline.synthesize_response = AsyncMock(return_value=(audio_bytes, audio_fmt))
    return pipeline


@pytest.mark.asyncio
async def test_voice_chat_no_audio_returns_history_unchanged() -> None:
    history, audio_path = await handle_voice_chat(
        None, [["a", "b"]], "cmn", "u1",
        chat_engine=_fake_chat_engine(),
        speech_pipeline=_fake_pipeline(),
    )
    assert history == [["a", "b"]]
    assert audio_path is None


@pytest.mark.asyncio
async def test_voice_chat_pipeline_unconfigured_returns_hint() -> None:
    audio = (16000, np.zeros(1600, dtype=np.float32))
    engine = _fake_chat_engine()
    history, audio_path = await handle_voice_chat(
        audio, [], "cmn", "u1",
        chat_engine=engine, speech_pipeline=None,
    )
    assert audio_path is None
    assert "未配置" in history[-1][1]
    engine.chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_voice_chat_full_path_appends_history_and_returns_audio_path() -> None:
    audio = (16000, np.zeros(1600, dtype=np.float32))
    engine = _fake_chat_engine("吃过了就好")
    pipeline = _fake_pipeline()

    history, audio_path = await handle_voice_chat(
        audio, [], "yue", "u1",
        chat_engine=engine, speech_pipeline=pipeline,
    )

    pipeline.process_voice.assert_awaited_once()
    pv_kwargs = pipeline.process_voice.call_args.kwargs
    assert pv_kwargs["audio_format"] == "pcm"
    assert pv_kwargs["sample_rate"] == 16000
    assert pv_kwargs["dialect_hint"] == DialectCode.CANTONESE
    assert isinstance(pv_kwargs["audio_data"], bytes) and len(pv_kwargs["audio_data"]) > 0

    # LLM 收到的是规范化后的普通话
    engine.chat.assert_awaited_once()
    assert engine.chat.call_args.kwargs["user_input"] == "我吃了饭"
    assert engine.chat.call_args.kwargs["dialect"] == DialectCode.CANTONESE

    # 历史展示 ASR 原文 + LLM 回复
    assert history[-1] == ["我食咗饭", "吃过了就好"]

    # 音频路径已写入
    assert audio_path and os.path.exists(audio_path)
    with open(audio_path, "rb") as f:
        assert f.read() == b"fake_mp3"
    os.unlink(audio_path)


@pytest.mark.asyncio
async def test_voice_chat_empty_asr_text_prompts_retry() -> None:
    audio = (16000, np.zeros(1600, dtype=np.float32))
    pipeline = _fake_pipeline(raw="", normalized="")
    engine = _fake_chat_engine()

    history, audio_path = await handle_voice_chat(
        audio, [], "cmn", "u1",
        chat_engine=engine, speech_pipeline=pipeline,
    )
    assert audio_path is None
    assert "再说一次" in history[-1][1]
    engine.chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_voice_chat_asr_failure_shows_error_in_history() -> None:
    audio = (16000, np.zeros(1600, dtype=np.float32))
    pipeline = _fake_pipeline()
    pipeline.process_voice = AsyncMock(side_effect=RuntimeError("auth failed"))

    history, audio_path = await handle_voice_chat(
        audio, [], "cmn", "u1",
        chat_engine=_fake_chat_engine(), speech_pipeline=pipeline,
    )
    assert audio_path is None
    assert "语音识别失败" in history[-1][0]
    assert "auth failed" in history[-1][1]


@pytest.mark.asyncio
async def test_voice_chat_tts_failure_still_returns_text_reply() -> None:
    audio = (16000, np.zeros(1600, dtype=np.float32))
    pipeline = _fake_pipeline()
    pipeline.synthesize_response = AsyncMock(side_effect=RuntimeError("vcn 11200"))
    engine = _fake_chat_engine("好的")

    history, audio_path = await handle_voice_chat(
        audio, [], "cmn", "u1",
        chat_engine=engine, speech_pipeline=pipeline,
    )
    # 文字回复仍在历史里，audio_path 为空
    assert history[-1] == ["我食咗饭", "好的"]
    assert audio_path is None
