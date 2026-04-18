"""集成测试：用户管理 API /api/v1/users。"""
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
from app.main import create_app


def _reset_caches() -> None:
    get_cached_settings.cache_clear()
    get_llm.cache_clear()
    get_memory.cache_clear()
    get_chat_engine.cache_clear()
    get_speech_pipeline.cache_clear()
    get_engine.cache_clear()


@pytest.fixture
def client() -> TestClient:
    _reset_caches()
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_create_user_default_fields(client: TestClient) -> None:
    resp = client.post("/api/v1/users", json={"phone": "13800000001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "用户"
    assert data["dialect_preference"] == "cmn"
    assert data["font_size"] == "large"
    assert data["tts_speed"] == 1.0


def test_create_user_custom_name(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/users",
        json={"display_name": "张爷爷", "dialect_preference": "yue"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "张爷爷"
    assert data["dialect_preference"] == "yue"


def test_get_user_by_id(client: TestClient) -> None:
    create_resp = client.post("/api/v1/users", json={"phone": "13800000002"})
    user_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == user_id


def test_get_nonexistent_user_returns_404(client: TestClient) -> None:
    resp = client.get("/api/v1/users/nonexistent-id")
    assert resp.status_code == 404


def test_update_preferences(client: TestClient) -> None:
    create_resp = client.post("/api/v1/users", json={"phone": "13800000003"})
    user_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/v1/users/{user_id}/preferences",
        json={"tts_speed": 0.7, "font_size": "extra-large"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["tts_speed"] == 0.7
    assert data["font_size"] == "extra-large"


def test_update_nonexistent_user_returns_404(client: TestClient) -> None:
    resp = client.patch(
        "/api/v1/users/nonexistent-id/preferences",
        json={"tts_speed": 0.5},
    )
    assert resp.status_code == 404
