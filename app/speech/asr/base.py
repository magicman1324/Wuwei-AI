"""ASR (语音识别) 抽象基类。"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from app.dialect.adapter import DialectCode


@dataclass
class ASRResult:
    text: str
    confidence: float
    dialect_detected: DialectCode
    raw_text: str | None = None
    segments: list[dict] | None = field(default_factory=list)


class BaseASR(ABC):
    """ASR 引擎抽象基类。"""

    @abstractmethod
    def supported_dialects(self) -> list[DialectCode]:
        """该引擎支持的方言列表。"""

    @abstractmethod
    async def recognize(
        self,
        audio_data: bytes,
        dialect: DialectCode = DialectCode.MANDARIN,
        audio_format: str = "pcm",
        sample_rate: int = 16000,
    ) -> ASRResult:
        """单次语音识别。"""

    @abstractmethod
    async def recognize_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        dialect: DialectCode = DialectCode.MANDARIN,
    ) -> AsyncIterator[ASRResult]:
        """流式语音识别。"""
