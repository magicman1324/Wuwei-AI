"""TTS (语音合成) 抽象基类。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TTSResult:
    audio_data: bytes
    audio_format: str  # "mp3" | "wav" | "pcm"
    sample_rate: int
    duration_ms: int | None = None


class BaseTTS(ABC):
    """TTS 引擎抽象基类。"""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_name: str = "",
        speed: float = 1.0,
        volume: float = 1.0,
        audio_format: str = "mp3",
    ) -> TTSResult:
        """将文本合成为语音。"""
