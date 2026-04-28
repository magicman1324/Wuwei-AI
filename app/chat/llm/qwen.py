"""通义千问 (Qwen) LLM 适配器。

使用 OpenAI 兼容接口调用通义千问 API。
"""

from collections.abc import AsyncIterator

import httpx
from loguru import logger

from app.chat.llm.base import BaseLLM, LLMMessage, LLMResponse

_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class QwenLLM(BaseLLM):
    provider_name = "qwen"

    def __init__(
        self,
        api_key: str,
        model: str = "qwen-max",
        base_url: str = "",
        enable_search: bool = False,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or _DEFAULT_BASE_URL
        self.enable_search = enable_search
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0,
        )

    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self.enable_search:
            payload["enable_search"] = True

        resp = await self._client.post("/chat/completions", json=payload)
        if resp.status_code != 200:
            logger.error(
                f"Qwen API 错误: status={resp.status_code}, body={resp.text}"
            )
            resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.model),
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if self.enable_search:
            payload["enable_search"] = True

        async with self._client.stream("POST", "/chat/completions", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    import json

                    data = json.loads(data_str)
                    delta = data["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except Exception:
                    logger.debug(f"跳过无法解析的 SSE 行: {data_str}")

    async def close(self):
        await self._client.aclose()
