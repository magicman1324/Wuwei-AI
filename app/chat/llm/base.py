"""LLM 提供商抽象基类。"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict = field(default_factory=dict)
    finish_reason: str = "stop"


class BaseLLM(ABC):
    """​LLM 提供商抽象基类，所有适配器需实现此接口。"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供商名称。"""

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """同步对话，返回完整回复。"""

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """流式对话，逐 token 返回。"""
