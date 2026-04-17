"""SpeechPipeline 引擎接线与路由测试。"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.dialect.adapter import DialectCode
from app.speech.asr.base import ASRResult
from app.speech.pipeline import SpeechPipeline
from app.speech.tts.base import TTSResult


def _settings(**overrides) -> Settings:
    base = {
        "iflytek_app_id": "",
        "iflytek_api_key": "",
        "iflytek_api_secret": "",
        "aliyun_access_key": "",
        "aliyun_access_secret": "",
        "aliyun_asr_app_key": "",
        "llm_api_key": "dummy",
    }
    base.update(overrides)
    return Settings(**base)


# ---- _init_engines 行为 ----

def test_init_engines_iflytek_only() -> None:
    s = _settings(
        iflytek_app_id="a", iflytek_api_key="k", iflytek_api_secret="sec",
    )
    p = SpeechPipeline(s)

    assert "iflytek" in p._asr_engines
    assert "iflytek" in p._tts_engines
    # 阿里云未配置 → fallback 别名到 iflytek
    assert p._asr_engines["aliyun"] is p._asr_engines["iflytek"]
    assert p._tts_engines["aliyun"] is p._tts_engines["iflytek"]


def test_init_engines_no_credentials_leaves_empty() -> None:
    p = SpeechPipeline(_settings())
    assert p._asr_engines == {}
    assert p._tts_engines == {}


def test_init_engines_partial_iflytek_credentials() -> None:
    # 只给 app_id 没有 key/secret → 不初始化
    s = _settings(iflytek_app_id="a")
    p = SpeechPipeline(s)
    assert p._asr_engines == {}


# ---- get_asr / get_tts 路由 ----

def test_get_asr_routes_by_provider() -> None:
    s = _settings(
        iflytek_app_id="a", iflytek_api_key="k", iflytek_api_secret="sec",
    )
    p = SpeechPipeline(s)

    # 三种方言都应路由到 iflytek
    assert p.get_asr(DialectCode.MANDARIN) is p._asr_engines["iflytek"]
    assert p.get_asr(DialectCode.CANTONESE) is p._asr_engines["iflytek"]
    assert p.get_asr(DialectCode.SICHUAN) is p._asr_engines["iflytek"]


def test_get_asr_raises_when_unconfigured() -> None:
    p = SpeechPipeline(_settings())
    with pytest.raises(RuntimeError, match="ASR 引擎未初始化"):
        p.get_asr(DialectCode.MANDARIN)


def test_get_tts_raises_when_unconfigured() -> None:
    p = SpeechPipeline(_settings())
    with pytest.raises(RuntimeError, match="TTS 引擎未初始化"):
        p.get_tts(DialectCode.CANTONESE)


# ---- process_voice 端到端（fake ASR） ----

@pytest.mark.asyncio
async def test_process_voice_calls_asr_and_normalizer() -> None:
    s = _settings(
        iflytek_app_id="a", iflytek_api_key="k", iflytek_api_secret="sec",
    )
    p = SpeechPipeline(s)

    fake_asr = AsyncMock()
    fake_asr.recognize = AsyncMock(
        return_value=ASRResult(
            text="我食咗饭喇",
            confidence=0.9,
            dialect_detected=DialectCode.CANTONESE,
        )
    )
    p._asr_engines["iflytek"] = fake_asr

    raw, normalized, dialect = await p.process_voice(
        audio_data=b"\x00" * 100,
        dialect_hint=DialectCode.CANTONESE,
    )

    fake_asr.recognize.assert_awaited_once()
    assert raw == "我食咗饭喇"
    # 规范化后粤语"食"→普通话"吃"
    assert "吃" in normalized
    assert dialect == DialectCode.CANTONESE


@pytest.mark.asyncio
async def test_process_voice_defaults_to_mandarin() -> None:
    s = _settings(
        iflytek_app_id="a", iflytek_api_key="k", iflytek_api_secret="sec",
    )
    p = SpeechPipeline(s)

    fake_asr = AsyncMock()
    fake_asr.recognize = AsyncMock(
        return_value=ASRResult(
            text="你好", confidence=0.9, dialect_detected=DialectCode.MANDARIN,
        )
    )
    p._asr_engines["iflytek"] = fake_asr

    raw, normalized, dialect = await p.process_voice(audio_data=b"x")

    # 未传 hint → 默认普通话
    assert dialect == DialectCode.MANDARIN
    assert raw == "你好"
    assert normalized == "你好"


# ---- synthesize_response 端到端（fake TTS） ----

@pytest.mark.asyncio
async def test_synthesize_response_passes_tts_config() -> None:
    s = _settings(
        iflytek_app_id="a", iflytek_api_key="k", iflytek_api_secret="sec",
    )
    p = SpeechPipeline(s)

    fake_tts = AsyncMock()
    fake_tts.synthesize = AsyncMock(
        return_value=TTSResult(
            audio_data=b"\xff\xfe\xfd",
            audio_format="mp3",
            sample_rate=16000,
        )
    )
    p._tts_engines["iflytek"] = fake_tts

    audio, fmt = await p.synthesize_response("你好吗", DialectCode.CANTONESE)

    assert audio == b"\xff\xfe\xfd"
    assert fmt == "mp3"
    fake_tts.synthesize.assert_awaited_once()
    call_kwargs = fake_tts.synthesize.call_args.kwargs
    assert call_kwargs["voice_name"] == "xiaomei"  # 讯飞小梅（广东话女声）
    assert call_kwargs["speed"] == 0.85            # 适老化默认
    assert call_kwargs["volume"] == 1.2


@pytest.mark.asyncio
async def test_synthesize_response_mandarin_uses_lingbosong() -> None:
    s = _settings(
        iflytek_app_id="a", iflytek_api_key="k", iflytek_api_secret="sec",
    )
    p = SpeechPipeline(s)

    fake_tts = AsyncMock()
    fake_tts.synthesize = AsyncMock(
        return_value=TTSResult(audio_data=b"x", audio_format="mp3", sample_rate=16000)
    )
    p._tts_engines["iflytek"] = fake_tts

    await p.synthesize_response("今天天气不错", DialectCode.MANDARIN)
    assert fake_tts.synthesize.call_args.kwargs["voice_name"] == "lingbosong"


@pytest.mark.asyncio
async def test_synthesize_response_sichuan_uses_xiaorong() -> None:
    s = _settings(
        iflytek_app_id="a", iflytek_api_key="k", iflytek_api_secret="sec",
    )
    p = SpeechPipeline(s)

    fake_tts = AsyncMock()
    fake_tts.synthesize = AsyncMock(
        return_value=TTSResult(audio_data=b"x", audio_format="mp3", sample_rate=16000)
    )
    p._tts_engines["iflytek"] = fake_tts

    await p.synthesize_response("巴适得很", DialectCode.SICHUAN)
    assert fake_tts.synthesize.call_args.kwargs["voice_name"] == "xiaorong"
