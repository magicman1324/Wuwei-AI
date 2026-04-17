"""ConversationMemory 持久化到 SQLite 的单元测试。"""
from __future__ import annotations

import os

os.environ["WUWEI_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["WUWEI_LLM_PROVIDER"] = "mock"

from sqlmodel import Session, SQLModel, create_engine, select

from app.chat.memory import ConversationMemory
from app.db.models import Conversation, Message


def _in_memory_engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


def _session_factory(engine):
    def factory():
        return Session(engine)
    return factory


def test_add_persists_messages_to_db() -> None:
    engine = _in_memory_engine()
    mem = ConversationMemory(session_factory=_session_factory(engine))

    mem.add("user1", "你好", "你好呀")
    mem.add("user1", "天气好", "是啊")

    with Session(engine) as s:
        msgs = list(s.exec(select(Message).order_by(Message.created_at)).all())
        assert len(msgs) == 4
        assert msgs[0].role == "user"
        assert msgs[0].content == "你好"
        assert msgs[1].role == "assistant"
        assert msgs[1].content == "你好呀"


def test_reuses_conversation_within_one_hour() -> None:
    engine = _in_memory_engine()
    mem = ConversationMemory(session_factory=_session_factory(engine))

    mem.add("user1", "第一轮", "回复1")
    mem.add("user1", "第二轮", "回复2")

    with Session(engine) as s:
        convs = list(s.exec(select(Conversation)).all())
        assert len(convs) == 1  # 同一个会话


def test_different_users_get_separate_conversations() -> None:
    engine = _in_memory_engine()
    mem = ConversationMemory(session_factory=_session_factory(engine))

    mem.add("alice", "你好", "嗨")
    mem.add("bob", "你好", "嗨")

    with Session(engine) as s:
        convs = list(s.exec(select(Conversation)).all())
        assert len(convs) == 2
        user_ids = {c.user_id for c in convs}
        assert user_ids == {"alice", "bob"}


def test_no_session_factory_still_works_in_memory() -> None:
    mem = ConversationMemory()
    mem.add("user1", "你好", "你好呀")
    recent = mem.get_recent("user1")
    assert len(recent) == 2
    assert recent[0].content == "你好"


def test_clear_removes_active_conversation_cache() -> None:
    engine = _in_memory_engine()
    mem = ConversationMemory(session_factory=_session_factory(engine))

    mem.add("user1", "你好", "嗨")
    assert "user1" in mem._active_conversations
    mem.clear("user1")
    assert "user1" not in mem._active_conversations
    assert mem.get_turn_count("user1") == 0
