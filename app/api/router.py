"""API 总路由注册。"""

from fastapi import APIRouter

from app.api.v1 import chat, health, user, voice

api_router = APIRouter()

api_router.include_router(health.router, tags=["健康检查"])
api_router.include_router(chat.router, prefix="/chat", tags=["文本对话"])
api_router.include_router(voice.router, prefix="/voice", tags=["语音对话"])
api_router.include_router(user.router, prefix="/users", tags=["用户管理"])
