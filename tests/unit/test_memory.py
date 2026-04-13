"""对话记忆测试。"""
from __future__ import annotations

from app.chat.memory import ConversationMemory


def test_memory_add_and_retrieve() -> None:
    memory = ConversationMemory(max_turns=3)
    memory.add("u1", user_input="你好", assistant_response="您好")
    history = memory.get_recent("u1")
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[0].content == "你好"
    assert history[1].role == "assistant"
    assert history[1].content == "您好"


def test_memory_max_turns_truncation() -> None:
    memory = ConversationMemory(max_turns=2)
    for i in range(5):
        memory.add("u1", user_input=f"msg{i}", assistant_response=f"reply{i}")
    history = memory.get_recent("u1")
    # 最多保留 max_turns * 2 条消息
    assert len(history) <= 4
    # 保留的应是最近的两轮
    assert history[-1].content == "reply4"


def test_memory_isolated_per_user() -> None:
    memory = ConversationMemory()
    memory.add("u1", user_input="a", assistant_response="A")
    memory.add("u2", user_input="b", assistant_response="B")
    assert len(memory.get_recent("u1")) == 2
    assert len(memory.get_recent("u2")) == 2
    assert memory.get_recent("u1")[0].content == "a"
    assert memory.get_recent("u2")[0].content == "b"


def test_memory_turn_count() -> None:
    memory = ConversationMemory()
    memory.add("u1", user_input="a", assistant_response="A")
    memory.add("u1", user_input="b", assistant_response="B")
    assert memory.get_turn_count("u1") == 2


def test_memory_clear() -> None:
    memory = ConversationMemory()
    memory.add("u1", user_input="a", assistant_response="A")
    memory.clear("u1")
    assert memory.get_recent("u1") == []
