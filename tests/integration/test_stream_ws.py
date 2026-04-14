"""集成测试：WebSocket /api/v1/ws/voice-stream 流式对话。

策略：
- 用 FakeSpeechPipeline 替代真实讯飞（不走网络）
- 覆盖 FakeASR (recognize_stream) 生成 partial/final
- 让 get_llm() 回退到 MockLLM（chat_stream 会逐字符 yield）
- 用 TestClient.websocket_connect 断言事件顺序
"""
from __future__ import annotations

import base64
import json
import os
from collections.abc import AsyncIterator

os.environ["WUWEI_LLM_PROVIDER"] = "mock"
os.environ["WUWEI_DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from app.dependencies import (
    get_cached_settings,
    get_chat_engine,
    get_llm,
    get_memory,
    get_speech_pipeline,
)
from app.dialect.adapter import DialectCode
from app.main import create_app
from app.speech.asr.base import ASRResult
from app.speech.normalizer import DialectNormalizer


class FakeStreamASR:
    """模拟讯飞 IAT 流式识别。"""

    def __init__(
        self,
        *,
        partials: list[str] | None = None,
        final_text: str = "我食咗饭喇",
    ):
        self.partials = partials or ["我", "我食", "我食咗饭", "我食咗饭喇"]
        self.final_text = final_text
        self.received_chunks: list[bytes] = []

    async def recognize(
        self,
        audio_data: bytes,
        dialect: DialectCode = DialectCode.MANDARIN,
        audio_format: str = "pcm",
        sample_rate: int = 16000,
    ) -> ASRResult:
        return ASRResult(
            text=self.final_text, confidence=0.9, dialect_detected=dialect
        )

    async def recognize_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        dialect: DialectCode = DialectCode.MANDARIN,
    ) -> AsyncIterator[ASRResult]:
        # 先耗掉音频流（保持与真实实现相同的背压语义）
        async for chunk in audio_stream:
            self.received_chunks.append(chunk)
        # 再逐一吐出识别结果
        for idx, text in enumerate(self.partials):
            is_final = idx == len(self.partials) - 1
            yield ASRResult(
                text=text,
                confidence=0.95 if is_final else 0.7,
                dialect_detected=dialect,
            )


class FakeSpeechPipeline:
    """带流式能力的 FakeSpeechPipeline（供 stream.py 使用）。"""

    def __init__(
        self,
        *,
        asr: FakeStreamASR | None = None,
        tts_audio: bytes = b"\xff\xfbfake_mp3_audio",
        tts_format: str = "mp3",
    ):
        self._asr = asr or FakeStreamASR()
        self.tts_audio = tts_audio
        self.tts_format = tts_format
        self.normalizer = DialectNormalizer()
        self.synth_calls: list[dict] = []

    def get_asr(self, dialect: DialectCode):  # noqa: ANN201
        return self._asr

    def get_tts(self, dialect: DialectCode):  # noqa: ANN201
        raise NotImplementedError  # stream.py 用 synthesize_response 不直接取

    async def synthesize_response(
        self, *, text: str, dialect: DialectCode
    ) -> tuple[bytes, str]:
        self.synth_calls.append({"text": text, "dialect": dialect})
        return self.tts_audio, self.tts_format


def _reset_dep_caches() -> None:
    get_cached_settings.cache_clear()
    get_llm.cache_clear()
    get_memory.cache_clear()
    get_chat_engine.cache_clear()
    get_speech_pipeline.cache_clear()


@pytest.fixture
def fake_pipeline() -> FakeSpeechPipeline:
    return FakeSpeechPipeline()


@pytest.fixture
def client(fake_pipeline: FakeSpeechPipeline) -> TestClient:
    _reset_dep_caches()
    app = create_app()
    app.dependency_overrides[get_speech_pipeline] = lambda: fake_pipeline
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _drain_until(ws, stop_types: set[str], max_events: int = 500) -> list[dict]:
    """从 ws 中接收 JSON 事件直到遇到 stop_types 之一或达到上限。"""
    events: list[dict] = []
    for _ in range(max_events):
        raw = ws.receive_text()
        payload = json.loads(raw)
        events.append(payload)
        if payload.get("type") in stop_types:
            return events
    raise AssertionError(
        f"未在 {max_events} 个事件内收到 {stop_types}，已收事件: {events}"
    )


# ---- 正常一轮对话 ----

def test_stream_full_turn_emits_asr_partial_final_llm_tts_done(
    client: TestClient, fake_pipeline: FakeSpeechPipeline
) -> None:
    with client.websocket_connect(
        "/api/v1/ws/voice-stream?user_id=grandpa&dialect=yue"
    ) as ws:
        ws.send_bytes(b"\x00\x01" * 100)
        ws.send_bytes(b"\x02\x03" * 100)
        ws.send_text(json.dumps({"type": "end"}))

        events = _drain_until(ws, {"done"})
        ws.send_text(json.dumps({"type": "close"}))

    event_types = [e["type"] for e in events]
    # 至少出现一次 asr_partial
    assert "asr_partial" in event_types
    assert "asr_final" in event_types
    assert "llm_chunk" in event_types
    assert "tts_audio" in event_types
    assert event_types[-1] == "done"

    # asr_partial 累积到最后文本
    partials = [e for e in events if e["type"] == "asr_partial"]
    assert partials[-1]["text"] == "我食咗饭喇"

    # asr_final 带方言标签
    final = next(e for e in events if e["type"] == "asr_final")
    assert final["text"] == "我食咗饭喇"
    assert final["dialect_detected"] == "yue"

    # tts_audio base64 能解码出 fake 字节
    tts_event = next(e for e in events if e["type"] == "tts_audio")
    assert base64.b64decode(tts_event["audio"]) == b"\xff\xfbfake_mp3_audio"
    assert tts_event["format"] == "mp3"

    # done 回带完整回复
    done = events[-1]
    assert done["full_response"]

    # TTS 被调用，方言是粤语
    assert len(fake_pipeline.synth_calls) == 1
    assert fake_pipeline.synth_calls[0]["dialect"] == DialectCode.CANTONESE
    # 音频 chunks 真的被喂进 ASR
    assert fake_pipeline._asr.received_chunks  # type: ignore[attr-defined]


def test_stream_llm_chunks_reconstruct_response(
    client: TestClient, fake_pipeline: FakeSpeechPipeline
) -> None:
    with client.websocket_connect(
        "/api/v1/ws/voice-stream?user_id=u1&dialect=cmn"
    ) as ws:
        ws.send_bytes(b"\x00" * 200)
        ws.send_text(json.dumps({"type": "end"}))
        events = _drain_until(ws, {"done"})
        ws.send_text(json.dumps({"type": "close"}))

    chunks = [e["text"] for e in events if e["type"] == "llm_chunk"]
    full_from_chunks = "".join(chunks)
    done = events[-1]
    # MockLLM 无方言化变换，full_response 应等于 chunks 拼接
    assert full_from_chunks
    assert done["full_response"] == full_from_chunks


# ---- 空语音 ----

def test_stream_empty_asr_goes_to_done_without_llm(
    client: TestClient,
) -> None:
    _reset_dep_caches()
    empty_asr = FakeStreamASR(partials=[""], final_text="")
    fake = FakeSpeechPipeline(asr=empty_asr)
    app = create_app()
    app.dependency_overrides[get_speech_pipeline] = lambda: fake
    try:
        with TestClient(app).websocket_connect(
            "/api/v1/ws/voice-stream?user_id=u2&dialect=cmn"
        ) as ws:
            ws.send_bytes(b"\x00" * 100)
            ws.send_text(json.dumps({"type": "end"}))
            events = _drain_until(ws, {"done"})
            ws.send_text(json.dumps({"type": "close"}))
    finally:
        app.dependency_overrides.clear()

    types = [e["type"] for e in events]
    assert "llm_chunk" not in types
    assert "tts_audio" not in types
    # 有 asr_final（空文本）和 done
    final = next(e for e in events if e["type"] == "asr_final")
    assert final["text"] == ""
    assert events[-1]["type"] == "done"
    assert events[-1]["full_response"] == ""


# ---- 多轮对话 ----

def test_stream_supports_multiple_turns_on_one_connection(
    client: TestClient, fake_pipeline: FakeSpeechPipeline
) -> None:
    with client.websocket_connect(
        "/api/v1/ws/voice-stream?user_id=multi&dialect=cmn"
    ) as ws:
        # 第一轮
        ws.send_bytes(b"\x01" * 100)
        ws.send_text(json.dumps({"type": "end"}))
        events1 = _drain_until(ws, {"done"})
        # 第二轮
        ws.send_bytes(b"\x02" * 100)
        ws.send_text(json.dumps({"type": "end"}))
        events2 = _drain_until(ws, {"done"})
        ws.send_text(json.dumps({"type": "close"}))

    assert events1[-1]["type"] == "done"
    assert events2[-1]["type"] == "done"
    # 两轮都调用了 TTS
    assert len(fake_pipeline.synth_calls) == 2


# ---- 错误路径 ----

def test_stream_errors_when_asr_engine_missing() -> None:
    """没有任何 ASR 引擎时应返回 error 并关闭。"""
    _reset_dep_caches()

    class EmptyPipeline:
        normalizer = DialectNormalizer()

        def get_asr(self, dialect):  # noqa: ANN001, ANN201
            raise RuntimeError("ASR 引擎未初始化: iflytek")

        async def synthesize_response(self, *, text, dialect):  # noqa: ANN001
            raise NotImplementedError

    app = create_app()
    app.dependency_overrides[get_speech_pipeline] = lambda: EmptyPipeline()
    try:
        with TestClient(app).websocket_connect(
            "/api/v1/ws/voice-stream?user_id=u3&dialect=cmn"
        ) as ws:
            raw = ws.receive_text()
            payload = json.loads(raw)
            assert payload["type"] == "error"
            assert "未就绪" in payload["reason"]
    finally:
        app.dependency_overrides.clear()


def test_stream_asr_failure_sends_error_event(client: TestClient) -> None:
    """ASR 抛异常时服务端应发 error 并终止。"""
    _reset_dep_caches()

    class ExplodingASR(FakeStreamASR):
        async def recognize_stream(  # type: ignore[override]
            self, audio_stream, dialect=DialectCode.MANDARIN
        ):
            async for _ in audio_stream:
                pass
            raise RuntimeError("iflytek auth failed")
            yield  # pragma: no cover  — 让函数保持 async generator

    fake = FakeSpeechPipeline(asr=ExplodingASR())
    app = create_app()
    app.dependency_overrides[get_speech_pipeline] = lambda: fake
    try:
        with TestClient(app).websocket_connect(
            "/api/v1/ws/voice-stream?user_id=u4&dialect=cmn"
        ) as ws:
            ws.send_bytes(b"\x00" * 50)
            ws.send_text(json.dumps({"type": "end"}))
            # 可能先收到 0..N 个 partial，最终一定有 error
            events: list[dict] = []
            for _ in range(50):
                raw = ws.receive_text()
                payload = json.loads(raw)
                events.append(payload)
                if payload.get("type") == "error":
                    break
            assert events[-1]["type"] == "error"
            assert "ASR 失败" in events[-1]["reason"]
    finally:
        app.dependency_overrides.clear()


def test_stream_tts_failure_still_sends_done_with_text(
    client: TestClient, fake_pipeline: FakeSpeechPipeline
) -> None:
    """TTS 失败时仍应返回 done（纯文字降级）。"""

    async def boom(*, text, dialect):  # noqa: ANN001
        raise RuntimeError("vcn 11200")

    fake_pipeline.synthesize_response = boom  # type: ignore[assignment]

    with client.websocket_connect(
        "/api/v1/ws/voice-stream?user_id=u5&dialect=cmn"
    ) as ws:
        ws.send_bytes(b"\x00" * 100)
        ws.send_text(json.dumps({"type": "end"}))
        events = _drain_until(ws, {"done"})
        ws.send_text(json.dumps({"type": "close"}))

    types = [e["type"] for e in events]
    assert "tts_audio" not in types
    assert events[-1]["type"] == "done"
    assert events[-1]["full_response"]
