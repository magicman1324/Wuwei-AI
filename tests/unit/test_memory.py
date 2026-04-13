"""对话记忆测试。"""
from __future__ import annotations

from app.chat.memory import ConversationMemory


def test_memory_append_and_retrieve() -> None:
    memory = ConversationMemory(max_turns=3)
    memory.append("u1", role="user", content="你好")
    memory.append("u1", role="assistant", content="您好")
    history = memory.get("u1")
    assert len(history) == 2
    assert history[0].role == "user"


def test_memory_max_turns_truncation() -> None:
    memory = ConversationMemory(max_turns=2)
    for i in range(5):
        memory.append("u1", role="user", content=f"msg{i}")
        memory.append("u1", role="assistant", content=f"reply{i}")
    history = memory.get("u1")
    # 最多保留 max_turns * 2 条消息
    assert len(history) <= 4


def test_memory_isolated_per_user() -> None:
    memory = ConversationMemory()
    memory.append("u1", role="user", content="a")
    memory.append("u2", role="user", content="b")
    assert len(memory.get("u1")) == 1
    assert len(memory.get("u2")) == 1
