"""SQLModel ORM 模型。

核心实体：
- User：用户及适老化偏好
- Conversation：一次对话会话
- Message：一条消息（用户或 AI）
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


def _uuid() -> str:
    return str(uuid.uuid4())


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=_uuid, primary_key=True)
    phone: Optional[str] = Field(default=None, index=True, unique=True)
    device_id: Optional[str] = Field(default=None, index=True)
    display_name: str = Field(default="用户")

    # 适老化偏好
    dialect_preference: str = Field(default="mandarin")
    tts_speed: float = Field(default=1.0)
    tts_volume: float = Field(default=1.0)
    font_size: str = Field(default="large")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: str = Field(default_factory=_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    dialect_used: str = Field(default="mandarin")
    summary: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None


class RadioEpisode(SQLModel, table=True):
    """老年电台节目：每日每方言每分类一期。"""
    __tablename__ = "radio_episodes"

    id: str = Field(default_factory=_uuid, primary_key=True)
    date: str = Field(index=True)               # ISO 日期 'YYYY-MM-DD'
    category: str = Field(index=True)           # 'health' | 'nostalgia'
    subtopic: Optional[str] = None              # 怀旧细分: 'old_life' | 'opera'
    dialect: str = Field(default="cmn", index=True)
    title: str
    text: str                                   # 全文文稿
    audio_path: Optional[str] = None            # 服务器本地路径（相对 data/radio/）
    duration_ms: int = Field(default=0)
    status: str = Field(default="ready")        # 'ready' | 'failed' | 'pending'
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: str = Field(default_factory=_uuid, primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id", index=True)
    role: str  # "user" | "assistant" | "system"
    content: str
    content_normalized: Optional[str] = None  # 规范化为普通话的文本
    dialect: str = Field(default="mandarin")
    audio_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
