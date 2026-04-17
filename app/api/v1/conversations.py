"""对话历史 API — 查询、删除用户的对话记录。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db.database import get_session
from app.db.repositories.conversation import ConversationRepository

router = APIRouter()


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    dialect: str
    created_at: datetime


class ConversationOut(BaseModel):
    id: str
    dialect_used: str
    started_at: datetime
    message_count: int


class ConversationDetailOut(BaseModel):
    id: str
    dialect_used: str
    started_at: datetime
    messages: list[MessageOut]


@router.get("/{user_id}", response_model=list[ConversationOut])
def list_conversations(
    user_id: str,
    limit: int = 50,
    session: Session = Depends(get_session),
):
    """列出用户的所有对话（最新在前）。"""
    repo = ConversationRepository(session)
    convs = repo.list_by_user(user_id, limit=limit)
    return [
        ConversationOut(
            id=c.id,
            dialect_used=c.dialect_used,
            started_at=c.started_at,
            message_count=len(repo.get_messages(c.id)),
        )
        for c in convs
    ]


@router.get(
    "/{user_id}/{conversation_id}",
    response_model=ConversationDetailOut,
)
def get_conversation(
    user_id: str,
    conversation_id: str,
    session: Session = Depends(get_session),
):
    """获取单个对话的详情（含所有消息）。"""
    repo = ConversationRepository(session)
    conv = repo.get_by_id(conversation_id)
    if not conv or conv.user_id != user_id:
        raise HTTPException(status_code=404, detail="对话不存在")
    messages = repo.get_messages(conversation_id)
    return ConversationDetailOut(
        id=conv.id,
        dialect_used=conv.dialect_used,
        started_at=conv.started_at,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                dialect=m.dialect,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete("/{user_id}/{conversation_id}", status_code=204)
def delete_conversation(
    user_id: str,
    conversation_id: str,
    session: Session = Depends(get_session),
):
    """删除指定对话及其所有消息。"""
    repo = ConversationRepository(session)
    conv = repo.get_by_id(conversation_id)
    if not conv or conv.user_id != user_id:
        raise HTTPException(status_code=404, detail="对话不存在")
    for msg in repo.get_messages(conversation_id):
        session.delete(msg)
    session.delete(conv)
    session.commit()
