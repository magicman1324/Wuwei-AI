"""文本对话 API。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.chat.engine import ChatEngine
from app.dependencies import get_chat_engine
from app.dialect.adapter import DialectCode

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str
    message: str
    dialect: DialectCode = DialectCode.MANDARIN
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    dialect: DialectCode
    conversation_id: str | None = None


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    engine: ChatEngine = Depends(get_chat_engine),
):
    """文本对话接口。"""
    result = await engine.chat_text(
        text=request.message,
        user_id=request.user_id,
        dialect=request.dialect,
    )
    return ChatResponse(
        response=result.text,
        dialect=result.dialect,
        conversation_id=request.conversation_id,
    )
