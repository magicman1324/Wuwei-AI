"""对话引擎：编排 LLM 调用、方言处理、记忆管理。"""

from dataclasses import dataclass

from loguru import logger

from app.chat.llm.base import BaseLLM, LLMMessage
from app.chat.memory import ConversationMemory
from app.chat.prompt.system_prompts import build_system_prompt
from app.dialect.adapter import DialectCode, DialectRegistry


@dataclass
class ChatResult:
    text: str
    dialect: DialectCode
    raw_llm_response: str


class ChatEngine:
    """对话引擎，串联方言处理 → LLM → 回复方言化。"""

    def __init__(
        self,
        llm: BaseLLM,
        memory: ConversationMemory,
        dialect_registry: type[DialectRegistry],
    ):
        self.llm = llm
        self.memory = memory
        self.dialect_registry = dialect_registry

    async def chat(
        self,
        user_input: str,
        user_id: str,
        dialect: DialectCode = DialectCode.MANDARIN,
    ) -> ChatResult:
        """
        处理一轮对话。

        1. 获取方言适配器
        2. 构建消息列表（system prompt + 历史 + 用户输入）
        3. 调用 LLM
        4. 方言化处理回复
        5. 保存到记忆
        """
        # 1. 获取方言适配器
        adapter = self.dialect_registry.get(dialect)

        # 2. 构建消息列表
        system_prompt = build_system_prompt(adapter.get_system_prompt_addition())
        history = self.memory.get_recent(user_id)
        messages = [
            LLMMessage("system", system_prompt),
            *history,
            LLMMessage("user", user_input),
        ]

        # 3. 调用 LLM
        logger.info(f"对话请求: user={user_id}, dialect={dialect}, input='{user_input[:50]}'")
        response = await self.llm.chat(messages)

        # 4. 方言化处理
        dialect_response = adapter.from_mandarin(response.content)

        # 5. 保存记忆
        self.memory.add(user_id, user_input, dialect_response)

        logger.info(f"对话完成: response='{dialect_response[:50]}'")
        return ChatResult(
            text=dialect_response,
            dialect=dialect,
            raw_llm_response=response.content,
        )

    async def chat_text(
        self,
        text: str,
        user_id: str,
        dialect: DialectCode = DialectCode.MANDARIN,
    ) -> ChatResult:
        """文本对话入口（方言文本 → 普通话 → LLM → 方言回复）。"""
        # 先规范化用户输入
        adapter = self.dialect_registry.get(dialect)
        normalized = adapter.to_mandarin(text)
        return await self.chat(normalized, user_id, dialect)
