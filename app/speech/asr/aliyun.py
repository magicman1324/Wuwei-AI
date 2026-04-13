"""阿里云智能语音 ASR 适配器。

阿里云语音文档: https://help.aliyun.com/product/30413.html
"""

from collections.abc import AsyncIterator

from loguru import logger

from app.dialect.adapter import DialectCode
from app.speech.asr.base import ASRResult, BaseASR


class AliyunASR(BaseASR):
    """阿里云语音识别引擎（主要用于普通话）。"""

    def __init__(self, access_key: str, access_secret: str, app_key: str):
        self.access_key = access_key
        self.access_secret = access_secret
        self.app_key = app_key

    def supported_dialects(self) -> list[DialectCode]:
        return [DialectCode.MANDARIN]

    async def recognize(
        self,
        audio_data: bytes,
        dialect: DialectCode = DialectCode.MANDARIN,
        audio_format: str = "pcm",
        sample_rate: int = 16000,
    ) -> ASRResult:
        # TODO: 实现阿里云 NLS SDK 调用
        logger.info(f"阿里云 ASR 识别: audio_size={len(audio_data)}")
        raise NotImplementedError("阿里云 ASR 尚未实现")

    async def recognize_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        dialect: DialectCode = DialectCode.MANDARIN,
    ) -> AsyncIterator[ASRResult]:
        # TODO: 实现阿里云流式 ASR
        raise NotImplementedError("阿里云流式 ASR 尚未实现")
        yield  # type: ignore[misc]
