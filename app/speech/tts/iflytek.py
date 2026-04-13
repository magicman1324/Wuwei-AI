"""科大讯飞 TTS 适配器 — 方言语音合成。"""

from loguru import logger

from app.speech.tts.base import BaseTTS, TTSResult


class IflytekTTS(BaseTTS):
    """科大讯飞语音合成引擎。"""

    def __init__(self, app_id: str, api_key: str, api_secret: str):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret

    async def synthesize(
        self,
        text: str,
        voice_name: str = "xiaoyan",
        speed: float = 1.0,
        volume: float = 1.0,
        audio_format: str = "mp3",
    ) -> TTSResult:
        # TODO: 实现讯飞 TTS WebSocket API 调用
        # 1. 构建鉴权 URL
        # 2. 发送合成请求
        # 3. 接收音频数据
        logger.info(f"讯飞 TTS 合成: text_len={len(text)}, voice={voice_name}")
        raise NotImplementedError("讯飞 TTS 尚未实现")
