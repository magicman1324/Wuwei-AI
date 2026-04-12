"""用户管理 API。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db.database import get_session
from app.db.repositories.user import UserRepository

router = APIRouter()


class CreateUserRequest(BaseModel):
    phone: str | None = None
    device_id: str | None = None
    display_name: str = "用户"
    dialect_preference: str = "cmn"


class UpdatePreferencesRequest(BaseModel):
    dialect_preference: str | None = None
    tts_speed: float | None = None
    tts_volume: float | None = None
    font_size: str | None = None


class UserResponse(BaseModel):
    id: str
    display_name: str
    dialect_preference: str
    tts_speed: float
    tts_volume: float
    font_size: str


@router.post("", response_model=UserResponse)
def create_user(
    request: CreateUserRequest,
    session: Session = Depends(get_session),
):
    """创建用户。"""
    repo = UserRepository(session)
    user = repo.create(**request.model_dump())
    return UserResponse(
        id=user.id,
        display_name=user.display_name,
        dialect_preference=user.dialect_preference,
        tts_speed=user.tts_speed,
        tts_volume=user.tts_volume,
        font_size=user.font_size,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    session: Session = Depends(get_session),
):
    """获取用户信息。"""
    repo = UserRepository(session)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserResponse(
        id=user.id,
        display_name=user.display_name,
        dialect_preference=user.dialect_preference,
        tts_speed=user.tts_speed,
        tts_volume=user.tts_volume,
        font_size=user.font_size,
    )


@router.patch("/{user_id}/preferences", response_model=UserResponse)
def update_preferences(
    user_id: str,
    request: UpdatePreferencesRequest,
    session: Session = Depends(get_session),
):
    """更新用户偏好设置。"""
    repo = UserRepository(session)
    user = repo.update_preferences(user_id, **request.model_dump(exclude_unset=True))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserResponse(
        id=user.id,
        display_name=user.display_name,
        dialect_preference=user.dialect_preference,
        tts_speed=user.tts_speed,
        tts_volume=user.tts_volume,
        font_size=user.font_size,
    )
