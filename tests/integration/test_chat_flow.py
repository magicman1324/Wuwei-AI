"""集成测试：文本对话端到端。"""
from __future__ import annotations

import os

os.environ["WUWEI_LLM_PROVIDER"] = "mock"
os.environ["WUWEI_DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_cached_settings, get_chat_engine, get_llm, get_memory
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    # 清理依赖缓存，确保环境变量生效
    get_cached_settings.cache_clear()
    get_llm.cache_clear()
    get_memory.cache_clear()
    get_chat_engine.cache_clear()
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    codes = {d["code"] for d in body["dialects"]}
    assert {"cmn", "yue", "cmn-sichuan"} <= codes


def test_dialects_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/dialects")
    assert response.status_code == 200
    codes = {d["code"] for d in response.json()["dialects"]}
    assert "cmn" in codes
    assert "yue" in codes
    assert "cmn-sichuan" in codes


def test_chat_endpoint_mandarin(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "test-user",
            "message": "你好",
            "dialect": "cmn",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["response"]
    assert data["dialect"] == "cmn"


def test_chat_endpoint_cantonese(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "test-user",
            "message": "你好",
            "dialect": "yue",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["response"]
    assert data["dialect"] == "yue"


def test_chat_multi_turn(client: TestClient) -> None:
    for msg in ["你好", "今天天气怎么样", "我想吃饭"]:
        response = client.post(
            "/api/v1/chat",
            json={"user_id": "multi-turn", "message": msg, "dialect": "cmn"},
        )
        assert response.status_code == 200
        assert response.json()["response"]
