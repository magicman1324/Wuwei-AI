"""集成测试：REST /api/v1/voice 端到端。

使用 FastAPI 的 dependency_overrides 注入 Fake SpeechPipeline，
避免真实调用讯飞 WebSocket。
"""
from __future__ import annotations

import base64
import io
import os

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


class FakeSpeechPipeline:
    """不依赖任何外部服务的 SpeechPipeline 测试替身。"""

    def __init__(
        self,
        *,
        asr_text: str = "我食咗饭喇",
        normalized_text: str = "我吃了饭了",
        detected_dialect: DialectCode = DialectCode.CANTONESE,
        tts_audio: bytes = b"\xff\xfbfake_mp3",
        tts_format: str = "mp3",
    ):
        self.asr_text = asr_text
        self.normalized_text = normalized_text
        self.detected_dialect = detected_dialect
        self.tts_audio = tts_audio
        self.tts_format = tts_format
        self.process_calls: list[dict] = []
        self.synth_calls: list[dict] = []

    async def process_voice(
        self,
        *,
        audio_data: bytes,
        user_id: str = "",
        dialect_hint: DialectCode | None = None,
        **_,
    ) -> tuple[str, str, DialectCode]:
        self.process_calls.append(
            {
                "audio_size": len(audio_data),
                "user_id": user_id,
                "dialect_hint": dialect_hint,
            }
        )
        dialect = dialect_hint or self.detected_dialect
        return self.asr_text, self.normalized_text, dialect

    async def synthesize_response(
        self,
        *,
        text: str,
        dialect: DialectCode,
    ) -> tuple[bytes, str]:
        self.synth_calls.append({"text": text, "dialect": dialect})
        return self.tts_audio, self.tts_format


def _reset_dependency_caches() -> None:
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
    _reset_dependency_caches()
    app = create_app()
    app.dependency_overrides[get_speech_pipeline] = lambda: fake_pipeline
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _audio_part(name: str = "test.wav", content: bytes = b"RIFF\x00\x00\x00\x00WAVEfake") -> dict:
    return {"audio": (name, io.BytesIO(content), "audio/wav")}


# ---- 基本请求 ----

def test_voice_endpoint_returns_full_response(
    client: TestClient, fake_pipeline: FakeSpeechPipeline
) -> None:
    response = client.post(
        "/api/v1/voice",
        files=_audio_part(),
        data={"user_id": "grandpa", "dialect_hint": "yue"},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["recognized_text"] == "我食咗饭喇"
    assert body["normalized_text"] == "我吃了饭了"
    assert body["response_text"]  # mock LLM 返回非空
    assert body["dialect_detected"] == "yue"
    # TTS 被成功调用 → audio_base64 非空
    assert body["audio_base64"]
    assert base64.b64decode(body["audio_base64"]) == b"\xff\xfbfake_mp3"
    assert body["audio_format"] == "mp3"


def test_voice_endpoint_forwards_dialect_hint(
    client: TestClient, fake_pipeline: FakeSpeechPipeline
) -> None:
    client.post(
        "/api/v1/voice",
        files=_audio_part(),
        data={"user_id": "u1", "dialect_hint": "cmn-sichuan"},
    )
    assert len(fake_pipeline.process_calls) == 1
    assert fake_pipeline.process_calls[0]["dialect_hint"] == DialectCode.SICHUAN
    assert fake_pipeline.process_calls[0]["user_id"] == "u1"


def test_voice_endpoint_without_dialect_hint_defaults_to_mandarin(
    client: TestClient, fake_pipeline: FakeSpeechPipeline
) -> None:
    fake_pipeline.detected_dialect = DialectCode.MANDARIN
    response = client.post(
        "/api/v1/voice",
        files=_audio_part(),
        data={"user_id": "u2"},
    )
    assert response.status_code == 200
    assert fake_pipeline.process_calls[0]["dialect_hint"] is None
    assert response.json()["dialect_detected"] == "cmn"


def test_voice_endpoint_calls_tts_with_llm_reply(
    client: TestClient, fake_pipeline: FakeSpeechPipeline
) -> None:
    response = client.post(
        "/api/v1/voice",
        files=_audio_part(),
        data={"user_id": "u3", "dialect_hint": "yue"},
    )
    assert response.status_code == 200
    assert len(fake_pipeline.synth_calls) == 1
    call = fake_pipeline.synth_calls[0]
    assert call["dialect"] == DialectCode.CANTONESE
    # TTS 输入应该是 LLM 返回的回复（mock LLM 非空）
    assert call["text"]
    assert call["text"] == response.json()["response_text"]


# ---- 降级路径 ----

def test_voice_endpoint_gracefully_handles_tts_failure(
    client: TestClient, fake_pipeline: FakeSpeechPipeline
) -> None:
    """TTS 报错时接口不应 500，audio_base64 返回 None。"""

    async def boom(*, text, dialect):  # noqa: ANN001
        raise RuntimeError("TTS 未配置")

    fake_pipeline.synthesize_response = boom  # type: ignore[assignment]

    response = client.post(
        "/api/v1/voice",
        files=_audio_part(),
        data={"user_id": "u4", "dialect_hint": "cmn"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["response_text"]  # 文本回复仍在
    assert body["audio_base64"] is None


def test_voice_endpoint_tts_not_implemented_also_degrades(
    client: TestClient, fake_pipeline: FakeSpeechPipeline
) -> None:
    async def not_impl(*, text, dialect):  # noqa: ANN001
        raise NotImplementedError

    fake_pipeline.synthesize_response = not_impl  # type: ignore[assignment]

    response = client.post(
        "/api/v1/voice",
        files=_audio_part(),
        data={"user_id": "u5"},
    )
    assert response.status_code == 200
    assert response.json()["audio_base64"] is None


# ---- 错误输入 ----

def test_voice_endpoint_rejects_missing_audio(client: TestClient) -> None:
    response = client.post("/api/v1/voice", data={"user_id": "u6"})
    assert response.status_code == 422  # FastAPI validation
