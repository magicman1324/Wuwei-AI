"""语音处理管道：编排从音频输入到音频输出的完整流程。"""

from dataclasses import dataclass

from loguru import logger

from app.config import Settings
from app.dialect.adapter import DialectCode, DialectRegistry
from app.dialect.detector import DialectDetector
from app.speech.asr.base import BaseASR
from app.speech.normalizer import DialectNormalizer
from app.speech.tts.base import BaseTTS


@dataclass
class VoiceResponse:
    recognized_text: str
    normalized_text: str
    response_text: str
    dialect_detected: DialectCode
    audio_data: bytes
    audio_format: str


class SpeechPipeline:
    """语音处理管道，串联 ASR → 规范化 → LLM → 方言化 → TTS。"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.detector = DialectDetector()
        self.normalizer = DialectNormalizer()
        self._asr_engines: dict[str, BaseASR] = {}
        self._tts_engines: dict[str, BaseTTS] = {}
        self._init_engines()

    def _init_engines(self):
        """根据配置初始化 ASR/TTS 引擎。"""
        # TODO: 根据 settings 中的 API 密钥初始化讯飞/阿里云引擎
        logger.info("语音引擎初始化（待配置 API 密钥）")

    def get_asr(self, dialect: DialectCode) -> BaseASR:
        """根据方言获取对应的 ASR 引擎。"""
        adapter = DialectRegistry.get(dialect)
        asr_config = adapter.get_asr_config()
        provider = asr_config["provider"]
        if provider not in self._asr_engines:
            raise RuntimeError(f"ASR 引擎未初始化: {provider}")
        return self._asr_engines[provider]

    def get_tts(self, dialect: DialectCode) -> BaseTTS:
        """根据方言获取对应的 TTS 引擎。"""
        adapter = DialectRegistry.get(dialect)
        tts_config = adapter.get_tts_config()
        provider = tts_config["provider"]
        if provider not in self._tts_engines:
            raise RuntimeError(f"TTS 引擎未初始化: {provider}")
        return self._tts_engines[provider]

    async def process_voice(
        self,
        audio_data: bytes,
        audio_format: str = "pcm",
        sample_rate: int = 16000,
        user_id: str = "",
        dialect_hint: DialectCode | None = None,
    ) -> tuple[str, str, DialectCode]:
        """
        处理语音输入，返回 (ASR 原文, 规范化为普通话后的文本, 检测到的方言)。

        完整流程:
        1. 方言检测（若无 hint）
        2. ASR 识别
        3. 文本规范化（方言 → 普通话）
        """
        # 1. 确定方言
        dialect = dialect_hint or DialectCode.MANDARIN

        # 2. ASR 识别
        asr = self.get_asr(dialect)
        result = await asr.recognize(audio_data, dialect, audio_format, sample_rate)

        # 3. 文本规范化
        normalized = self.normalizer.normalize(result.text, result.dialect_detected)

        logger.info(
            f"语音识别完成: dialect={result.dialect_detected}, "
            f"raw='{result.text}', normalized='{normalized}'"
        )
        return result.text, normalized, result.dialect_detected

    async def synthesize_response(
        self,
        text: str,
        dialect: DialectCode,
    ) -> tuple[bytes, str]:
        """
        将回复文本合成为方言语音。

        流程:
        1. 方言化处理
        2. TTS 合成
        """
        # 1. 方言化
        dialect_text = self.normalizer.denormalize(text, dialect)

        # 2. TTS 合成
        adapter = DialectRegistry.get(dialect)
        tts_config = adapter.get_tts_config()
        tts = self.get_tts(dialect)

        result = await tts.synthesize(
            text=dialect_text,
            voice_name=tts_config.get("voice_name", ""),
            speed=tts_config.get("speed", self.settings.tts_default_speed),
            volume=tts_config.get("volume", self.settings.tts_default_volume),
        )
        return result.audio_data, result.audio_format
