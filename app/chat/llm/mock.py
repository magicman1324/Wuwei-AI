"""Mock LLM 适配器 — 用于无 API key 的本地开发与测试。"""

from collections.abc import AsyncIterator

from app.chat.llm.base import BaseLLM, LLMMessage, LLMResponse

_CANNED_RESPONSES = [
    "您好呀！我是无维，很高兴认识您。",
    "您说的这件事我听到了，要不要再多说一点呢？",
    "今天过得怎么样？有什么开心的事吗？",
    "您放心，我会一直陪着您的。",
    "这个问题问得好，让我想想怎么回答您。",
]


class MockLLM(BaseLLM):
    """模拟 LLM，根据输入返回预设回复。用于开发和测试。"""

    provider_name = "mock"

    def __init__(self, api_key: str = "", model: str = "mock-v1"):
        self.api_key = api_key
        self.model = model
        self._counter = 0

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        # 取用户最后一条消息用于生成回复
        last_user_msg = ""
        for m in reversed(messages):
            if m.role == "user":
                last_user_msg = m.content
                break

        reply = _CANNED_RESPONSES[self._counter % len(_CANNED_RESPONSES)]
        self._counter += 1

        # 回显用户内容，让回复看起来有相关性
        if last_user_msg:
            snippet = last_user_msg[:30]
            reply = f"{reply}（您刚说的是：{snippet}）"

        return LLMResponse(
            content=reply,
            model=self.model,
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            finish_reason="stop",
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        response = await self.chat(messages, temperature, max_tokens)
        for char in response.content:
            yield char
