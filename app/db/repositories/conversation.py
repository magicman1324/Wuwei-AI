"""对话与消息数据访问层。"""
from __future__ import annotations

from typing import Optional

from sqlmodel import Session, select

from app.db.models import Conversation, Message


class ConversationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, user_id: str, dialect_used: str = "mandarin") -> Conversation:
        conv = Conversation(user_id=user_id, dialect_used=dialect_used)
        self.session.add(conv)
        self.session.commit()
        self.session.refresh(conv)
        return conv

    def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        return self.session.get(Conversation, conversation_id)

    def list_by_user(self, user_id: str, limit: int = 50) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.started_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(stmt).all())

    def add_message(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        content_normalized: Optional[str] = None,
        dialect: str = "mandarin",
        audio_path: Optional[str] = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            content_normalized=content_normalized,
            dialect=dialect,
            audio_path=audio_path,
        )
        self.session.add(msg)
        self.session.commit()
        self.session.refresh(msg)
        return msg

    def get_messages(self, conversation_id: str, limit: int = 100) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(self.session.exec(stmt).all())
