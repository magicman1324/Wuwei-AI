"""​WebSocket 实时语音流接口。"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()


@router.websocket("/ws/voice-stream")
async def voice_stream(websocket: WebSocket):
    """
    实时语音流 WebSocket 端点。

    协议:
      客户端 → 服务端: 二进制帧 (PCM 16bit 16kHz 音频块)
      服务端 → 客户端: JSON 文本帧
        - {"type": "asr_partial", "text": "...", "is_final": false}
        - {"type": "asr_final", "text": "...", "dialect_detected": "yue"}
        - {"type": "llm_chunk", "text": "..."}
        - {"type": "tts_audio", "audio": "<base64>", "format": "mp3"}
        - {"type": "done", "full_response": "..."}
    """
    await websocket.accept()

    # 从查询参数获取用户信息
    user_id = websocket.query_params.get("user_id", "anonymous")
    dialect = websocket.query_params.get("dialect", "cmn")

    logger.info(f"WebSocket 连接: user={user_id}, dialect={dialect}")

    try:
        while True:
            data = await websocket.receive()

            if "bytes" in data:
                # 收到音频数据
                audio_chunk = data["bytes"]
                # TODO: 实现流式处理
                # 1. 将音频块送入 ASR 流式识别
                # 2. 收到识别结果后送入 LLM
                # 3. LLM 流式回复 → 客户端
                # 4. 累积回复 → TTS → 客户端
                await websocket.send_json({
                    "type": "asr_partial",
                    "text": "(流式识别待实现)",
                    "is_final": False,
                })

            elif "text" in data:
                # 收到控制消息
                msg = json.loads(data["text"])
                if msg.get("type") == "end":
                    await websocket.send_json({"type": "done", "full_response": ""})

    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开: user={user_id}")
