"""科大讯飞 ASR 适配器 — 方言识别首选。

讯飞开放平台文档: https://www.xfyun.cn/doc/asr/voicedictation/API.html
"""

from collections.abc import AsyncIterator

from loguru import logger

from app.dialect.adapter import DialectCode
from app.speech.asr.base import ASRResult, BaseASR

# 讯飞方言编码映射
_DIALECT_TO_IFLYTEK = {
    DialectCode.MANDARIN: "zh_cn",
    DialectCode.CANTONESE: "cn_cantonese",
    DialectCode.SICHUAN: "zh_cn",  # 四川话使用普通话引擎 + 方言口音模式
}


class IflytekASR(BaseASR):
    """科大讯飞语音识别引擎。"""

    def __init__(self, app_id: str, api_key: str, api_secret: str):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret

    def supported_dialects(self) -> list[DialectCode]:
        return [DialectCode.MANDARIN, DialectCode.CANTONESE, DialectCode.SICHUAN]

    async def recognize(
        self,
        audio_data: bytes,
        dialect: DialectCode = DialectCode.MANDARIN,
        audio_format: str = "pcm",
        sample_rate: int = 16000,
    ) -> ASRResult:
        language = _DIALECT_TO_IFLYTEK.get(dialect, "zh_cn")
        # TODO: 实现讯飞 WebSocket API 调用
        # 1. 构建鉴权 URL (HMAC-SHA256)
        # 2. WebSocket 连接并发送音频帧
        # 3. 接收识别结果
        logger.info(f"讯飞 ASR 识别: dialect={dialect}, language={language}, audio_size={len(audio_data)}")
        raise NotImplementedError("讯飞 ASR 尚未实现，请配置 API 密钥后实现")

    async def recognize_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        dialect: DialectCode = DialectCode.MANDARIN,
    ) -> AsyncIterator[ASRResult]:
        # TODO: 实现讯飞流式 ASR
        raise NotImplementedError("讯飞流式 ASR 尚未实现")
        yield  # type: ignore[misc]
