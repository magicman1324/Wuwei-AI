"""集成测试：对话历史 API /api/v1/conversations。"""
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


def _send_chat(client: TestClient, user_id: str, message: str) -> dict:
    resp = client.post(
        "/api/v1/chat",
        json={"user_id": user_id, "message": message, "dialect": "cmn"},
    )
    assert resp.status_code == 200
    return resp.json()


def test_conversations_list_empty_initially(client: TestClient) -> None:
    resp = client.get("/api/v1/conversations/nobody")
    assert resp.status_code == 200
    assert resp.json() == []


def test_chat_creates_conversation_visible_in_list(client: TestClient) -> None:
    _send_chat(client, "grandpa", "你好啊")
    _send_chat(client, "grandpa", "今天天气怎么样")

    resp = client.get("/api/v1/conversations/grandpa")
    assert resp.status_code == 200
    convs = resp.json()
    assert len(convs) == 1
    assert convs[0]["message_count"] == 4  # 2 轮 × 2 条


def test_conversation_detail_shows_messages(client: TestClient) -> None:
    _send_chat(client, "user2", "早上好")

    convs = client.get("/api/v1/conversations/user2").json()
    conv_id = convs[0]["id"]

    resp = client.get(f"/api/v1/conversations/user2/{conv_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert len(detail["messages"]) == 2
    assert detail["messages"][0]["role"] == "user"
    assert detail["messages"][0]["content"] == "早上好"
    assert detail["messages"][1]["role"] == "assistant"


def test_delete_conversation(client: TestClient) -> None:
    _send_chat(client, "user3", "测试删除")

    convs = client.get("/api/v1/conversations/user3").json()
    conv_id = convs[0]["id"]

    resp = client.delete(f"/api/v1/conversations/user3/{conv_id}")
    assert resp.status_code == 204

    convs_after = client.get("/api/v1/conversations/user3").json()
    assert len(convs_after) == 0


def test_delete_nonexistent_conversation_returns_404(client: TestClient) -> None:
    resp = client.delete("/api/v1/conversations/user4/fake-id")
    assert resp.status_code == 404


def test_different_users_isolated(client: TestClient) -> None:
    _send_chat(client, "alice", "你好")
    _send_chat(client, "bob", "你好")

    alice_convs = client.get("/api/v1/conversations/alice").json()
    bob_convs = client.get("/api/v1/conversations/bob").json()
    assert len(alice_convs) == 1
    assert len(bob_convs) == 1
    assert alice_convs[0]["id"] != bob_convs[0]["id"]
