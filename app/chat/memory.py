"""对话记忆管理：短期内存缓存 + 长期 SQLite 持久化。"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from loguru import logger
from sqlmodel import Session

from app.chat.llm.base import LLMMessage


@dataclass
class MemoryEntry:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationMemory:
    """对话记忆管理器。

    双层存储：
    - 短期：内存 dict，用于 LLM 上下文窗口（最近 N 轮）
    - 长期：SQLite 持久化（通过 session_factory 注入，可选）

    当 session_factory 为 None 时退化为纯内存模式（测试/无数据库场景）。
    """

    def __init__(
        self,
        max_turns: int = 10,
        session_factory: Callable[[], Session] | None = None,
    ):
        self.max_turns = max_turns
        self._session_factory = session_factory
        self._store: dict[str, list[MemoryEntry]] = defaultdict(list)
        self._active_conversations: dict[str, str] = {}

    def get_recent(self, user_id: str, limit: int | None = None) -> list[LLMMessage]:
        """获取最近 N 轮对话，转为 LLMMessage 格式。"""
        entries = self._store.get(user_id, [])
        n = limit or self.max_turns
        recent = entries[-n * 2 :]
        return [LLMMessage(role=e.role, content=e.content) for e in recent]

    def add(self, user_id: str, user_input: str, assistant_response: str) -> None:
        """追加一轮对话（用户 + 助手），同时写入 SQLite。"""
        entries = self._store[user_id]
        entries.append(MemoryEntry(role="user", content=user_input))
        entries.append(MemoryEntry(role="assistant", content=assistant_response))

        max_entries = self.max_turns * 2
        if len(entries) > max_entries:
            self._store[user_id] = entries[-max_entries:]

        self._persist(user_id, user_input, assistant_response)

    def _persist(
        self, user_id: str, user_input: str, assistant_response: str
    ) -> None:
        """写入 SQLite（有 session_factory 时）。"""
        if self._session_factory is None:
            return
        try:
            from app.db.models import Conversation, Message

            session = self._session_factory()
            try:
                conv_id = self._get_or_create_conversation(session, user_id)
                session.add(
                    Message(
                        conversation_id=conv_id,
                        role="user",
                        content=user_input,
                    )
                )
                session.add(
                    Message(
                        conversation_id=conv_id,
                        role="assistant",
                        content=assistant_response,
                    )
                )
                session.commit()
            finally:
                session.close()
        except Exception as exc:
            logger.warning(f"对话持久化失败（不影响功能）: {exc}")

    def _get_or_create_conversation(
        self, session: Session, user_id: str
    ) -> str:
        """复用 1 小时内的活跃会话，超时则新建。"""
        from sqlmodel import select

        from app.db.models import Conversation

        cached_id = self._active_conversations.get(user_id)
        if cached_id:
            conv = session.get(Conversation, cached_id)
            if conv and (datetime.utcnow() - conv.started_at) < timedelta(hours=1):
                return cached_id

        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.started_at.desc())
            .limit(1)
        )
        latest = session.exec(stmt).first()
        if latest and (datetime.utcnow() - latest.started_at) < timedelta(hours=1):
            self._active_conversations[user_id] = latest.id
            return latest.id

        conv = Conversation(user_id=user_id)
        session.add(conv)
        session.commit()
        session.refresh(conv)
        self._active_conversations[user_id] = conv.id
        return conv.id

    def clear(self, user_id: str) -> None:
        """清除用户的对话记忆。"""
        self._store.pop(user_id, None)
        self._active_conversations.pop(user_id, None)

    def get_turn_count(self, user_id: str) -> int:
        """获取用户的对话轮数。"""
        return len(self._store.get(user_id, [])) // 2
