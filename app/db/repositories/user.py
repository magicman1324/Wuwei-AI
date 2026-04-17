"""用户数据访问层。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.db.models import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_by_phone(self, phone: str) -> Optional[User]:
        stmt = select(User).where(User.phone == phone)
        return self.session.exec(stmt).first()

    def create(
        self,
        *,
        phone: Optional[str] = None,
        device_id: Optional[str] = None,
        display_name: str = "用户",
        dialect_preference: str = "mandarin",
    ) -> User:
        user = User(
            phone=phone,
            device_id=device_id,
            display_name=display_name,
            dialect_preference=dialect_preference,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_preferences(
        self,
        user_id: str,
        *,
        dialect_preference: Optional[str] = None,
        tts_speed: Optional[float] = None,
        tts_volume: Optional[float] = None,
        font_size: Optional[str] = None,
    ) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        if dialect_preference is not None:
            user.dialect_preference = dialect_preference
        if tts_speed is not None:
            user.tts_speed = tts_speed
        if tts_volume is not None:
            user.tts_volume = tts_volume
        if font_size is not None:
            user.font_size = font_size
        user.updated_at = datetime.utcnow()
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
