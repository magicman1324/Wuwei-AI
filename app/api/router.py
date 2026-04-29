"""API 总路由注册。"""

from fastapi import APIRouter

from app.api.v1 import chat, conversations, health, radio, stream, user, voice

api_router = APIRouter()

api_router.include_router(health.router, tags=["健康检查"])
api_router.include_router(chat.router, prefix="/chat", tags=["文本对话"])
api_router.include_router(voice.router, prefix="/voice", tags=["语音对话"])
api_router.include_router(stream.router, tags=["实时语音流"])
api_router.include_router(user.router, prefix="/users", tags=["用户管理"])
api_router.include_router(
    conversations.router, prefix="/conversations", tags=["对话历史"]
)
api_router.include_router(radio.router, prefix="/radio", tags=["老年电台"])
