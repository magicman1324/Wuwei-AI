"""集成测试：文本对话端到端。"""
from __future__ import annotations

import os

os.environ["WUWEI_LLM_PROVIDER"] = "mock"
os.environ["WUWEI_DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dialects_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/dialects")
    assert response.status_code == 200
    data = response.json()
    assert "mandarin" in data["dialects"]
    assert "cantonese" in data["dialects"]
    assert "sichuan" in data["dialects"]


def test_chat_endpoint_mandarin(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "test-user",
            "text": "你好",
            "dialect": "mandarin",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["dialect"] == "mandarin"


def test_chat_endpoint_cantonese(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "test-user",
            "text": "你好",
            "dialect": "cantonese",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dialect"] == "cantonese"
