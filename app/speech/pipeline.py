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

    def _init_engines(self) -> None:
        """根据 settings 中的凭据初始化可用的 ASR/TTS 引擎。

        行为：
        - 讯飞凭据齐全 → 注册 iflytek ASR/TTS
        - 阿里云凭据齐全 → 注册 aliyun ASR（TTS 暂无实现）
        - 若 dialect 指定的 provider 未配置，fallback 到 iflytek
        - 两者都空 → 保持空 dict，get_asr/get_tts 调用时会 raise（voice.py 做降级）
        """
        s = self.settings

        if s.iflytek_app_id and s.iflytek_api_key and s.iflytek_api_secret:
            from app.speech.asr.iflytek import IflytekASR
            from app.speech.tts.iflytek import IflytekTTS

            self._asr_engines["iflytek"] = IflytekASR(
                app_id=s.iflytek_app_id,
                api_key=s.iflytek_api_key,
                api_secret=s.iflytek_api_secret,
            )
            self._tts_engines["iflytek"] = IflytekTTS(
                app_id=s.iflytek_app_id,
                api_key=s.iflytek_api_key,
                api_secret=s.iflytek_api_secret,
            )
            logger.info("讯飞 ASR/TTS 引擎已初始化")

        if s.volcano_app_id and s.volcano_access_token:
            from app.speech.tts.volcano import VolcanoTTS

            self._tts_engines["volcano"] = VolcanoTTS(
                app_id=s.volcano_app_id,
                access_token=s.volcano_access_token,
                cluster=s.volcano_tts_cluster,
            )
            logger.info("火山引擎 BigTTS 已初始化")

        if s.aliyun_access_key and s.aliyun_access_secret:
            try:
                from app.speech.asr.aliyun import AliyunASR

                self._asr_engines["aliyun"] = AliyunASR(
                    access_key=s.aliyun_access_key,
                    access_secret=s.aliyun_access_secret,
                    app_key=s.aliyun_asr_app_key,
                )
                logger.info("阿里云 ASR 引擎已初始化")
            except (NotImplementedError, ImportError) as exc:
                logger.warning(f"阿里云 ASR 未启用: {exc}")

        # Fallback: 某些 adapter 可能仍配置 provider=aliyun，
        # 若未注册，则别名到 iflytek（普通话场景 iflytek 本身就支持）。
        if "iflytek" in self._asr_engines and "aliyun" not in self._asr_engines:
            self._asr_engines["aliyun"] = self._asr_engines["iflytek"]
        if "iflytek" in self._tts_engines and "aliyun" not in self._tts_engines:
            self._tts_engines["aliyun"] = self._tts_engines["iflytek"]

        if not self._asr_engines:
            logger.warning("未配置任何 ASR 凭据，语音识别功能不可用")
        if not self._tts_engines:
            logger.warning("未配置任何 TTS 凭据，语音合成功能不可用")

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
        voice_name: str | None = None,
        provider: str | None = None,
    ) -> tuple[bytes, str]:
        """
        将回复文本合成为方言语音。

        流程:
        1. 方言化处理
        2. TTS 合成（voice_name / provider 可选覆盖默认）
        """
        # 1. 方言化
        dialect_text = self.normalizer.denormalize(text, dialect)

        # 2. 选 TTS 引擎
        adapter = DialectRegistry.get(dialect)
        tts_config = adapter.get_tts_config()
        if provider:
            if provider not in self._tts_engines:
                logger.warning(
                    f"TTS provider '{provider}' 未配置，回退到方言默认引擎"
                )
                tts = self.get_tts(dialect)
            else:
                tts = self._tts_engines[provider]
        else:
            tts = self.get_tts(dialect)

        result = await tts.synthesize(
            text=dialect_text,
            voice_name=voice_name or tts_config.get("voice_name", ""),
            speed=tts_config.get("speed", self.settings.tts_default_speed),
            volume=tts_config.get("volume", self.settings.tts_default_volume),
        )
        return result.audio_data, result.audio_format
