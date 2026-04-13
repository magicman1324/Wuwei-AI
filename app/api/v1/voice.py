"""语音对话 API（上传完整音频文件）。"""

import base64

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from app.chat.engine import ChatEngine
from app.dependencies import get_chat_engine, get_speech_pipeline
from app.dialect.adapter import DialectCode
from app.speech.pipeline import SpeechPipeline

router = APIRouter()


class VoiceResponse(BaseModel):
    recognized_text: str
    normalized_text: str
    response_text: str
    dialect_detected: str
    audio_base64: str | None = None
    audio_format: str = "mp3"


@router.post("", response_model=VoiceResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    user_id: str = Form(""),
    dialect_hint: str = Form(""),
    pipeline: SpeechPipeline = Depends(get_speech_pipeline),
    engine: ChatEngine = Depends(get_chat_engine),
):
    """
    语音对话接口：上传音频文件，返回文本回复 + 语音回复。

    流程: ASR → 规范化 → LLM → 方言化 → TTS
    """
    audio_data = await audio.read()
    dialect = DialectCode(dialect_hint) if dialect_hint else None

    # 1. ASR + 规范化
    raw_text, normalized_text, detected_dialect = await pipeline.process_voice(
        audio_data=audio_data,
        user_id=user_id,
        dialect_hint=dialect,
    )

    # 2. LLM 对话
    result = await engine.chat(
        user_input=normalized_text,
        user_id=user_id,
        dialect=detected_dialect,
    )

    # 3. TTS 合成
    audio_response = None
    audio_fmt = "mp3"
    try:
        audio_bytes, audio_fmt = await pipeline.synthesize_response(
            text=result.text,
            dialect=detected_dialect,
        )
        audio_response = base64.b64encode(audio_bytes).decode()
    except (NotImplementedError, RuntimeError):
        pass  # TTS 未配置时跳过

    return VoiceResponse(
        recognized_text=raw_text,
        normalized_text=normalized_text,
        response_text=result.text,
        dialect_detected=detected_dialect.value,
        audio_base64=audio_response,
        audio_format=audio_fmt,
    )
