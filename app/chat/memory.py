"""对话记忆管理：短期内存缓存 + 长期持久化。"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from app.chat.llm.base import LLMMessage


@dataclass
class MemoryEntry:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationMemory:
    """
    对话记忆管理器。

    MVP 阶段使用内存字典存储，后续可迁移到 Redis。
    - 短期记忆: 最近 N 轮对话，用于 LLM 上下文
    - 长期记忆: 通过 Repository 持久化到数据库
    """

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self._store: dict[str, list[MemoryEntry]] = defaultdict(list)

    def get_recent(self, user_id: str, limit: int | None = None) -> list[LLMMessage]:
        """获取最近 N 轮对话，转为 LLMMessage 格式。"""
        entries = self._store.get(user_id, [])
        n = limit or self.max_turns
        recent = entries[-n * 2 :]  # 每轮2条消息 (user + assistant)
        return [LLMMessage(role=e.role, content=e.content) for e in recent]

    def add(self, user_id: str, user_input: str, assistant_response: str):
        """追加一轮对话（用户 + 助手）。"""
        entries = self._store[user_id]
        entries.append(MemoryEntry(role="user", content=user_input))
        entries.append(MemoryEntry(role="assistant", content=assistant_response))

        # 超过上限时裁剪
        max_entries = self.max_turns * 2
        if len(entries) > max_entries:
            self._store[user_id] = entries[-max_entries:]

    def clear(self, user_id: str):
        """清除用户的对话记忆。"""
        self._store.pop(user_id, None)

    def get_turn_count(self, user_id: str) -> int:
        """获取用户的对话轮数。"""
        return len(self._store.get(user_id, [])) // 2
