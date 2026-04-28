"""集成测试：验证 CORS 配置和 Gradio 路径迁移。"""
from __future__ import annotations

import os

os.environ["WUWEI_LLM_PROVIDER"] = "mock"
os.environ["WUWEI_DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_engine
from app.dependencies import (
    get_cached_settings,
    get_chat_engine,
    get_llm,
    get_memory,
    get_speech_pipeline,
)
from app.dialect.adapter import DialectCode
from app.main import create_app


def _reset_caches() -> None:
    get_cached_settings.cache_clear()
    get_llm.cache_clear()
    get_memory.cache_clear()
    get_chat_engine.cache_clear()
    get_speech_pipeline.cache_clear()
    get_engine.cache_clear()


class _FakePipeline:
    async def process_voice(self, audio_data, audio_format="pcm", sample_rate=16000,
                             user_id="", dialect_hint=None):
        return "测试识别", "测试识别", DialectCode.MANDARIN

    async def synthesize_response(self, text, dialect):
        raise RuntimeError("TTS 未配置")


@pytest.fixture
def client() -> TestClient:
    _reset_caches()
    app = create_app()
    app.dependency_overrides[get_speech_pipeline] = lambda: _FakePipeline()
    with TestClient(app) as c:
        yield c


def test_cors_header_present(client: TestClient) -> None:
    resp = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers


def test_cors_preflight(client: TestClient) -> None:
    resp = client.options(
        "/api/v1/chat",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code in (200, 204)
    assert "access-control-allow-origin" in resp.headers


def test_voice_endpoint_accepts_audio_format_param(client: TestClient) -> None:
    """voice 端点应接受 audio_format 和 sample_rate form 字段（即使 ASR 未配置）。"""
    dummy_audio = b"\x00" * 3200  # 假 PCM
    resp = client.post(
        "/api/v1/voice",
        data={"user_id": "test", "dialect_hint": "cmn",
              "audio_format": "pcm", "sample_rate": "16000"},
        files={"audio": ("test.pcm", dummy_audio, "audio/octet-stream")},
    )
    # ASR 未配置时返回 500，但不应是 422（参数校验错误）
    assert resp.status_code != 422
