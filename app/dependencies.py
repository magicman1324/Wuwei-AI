"""FastAPI 依赖注入：集中管理全局单例对象。"""

from functools import lru_cache

from app.chat.engine import ChatEngine
from app.chat.llm.factory import LLMFactory
from app.chat.memory import ConversationMemory
from app.config import Settings, get_settings
from app.dialect.adapter import DialectRegistry
from app.speech.pipeline import SpeechPipeline


@lru_cache
def get_cached_settings() -> Settings:
    """FastAPI 依赖：获取缓存的配置实例。"""
    return get_settings()


@lru_cache
def get_memory() -> ConversationMemory:
    """FastAPI 依赖：获取全局共享的对话记忆管理器。

    当数据库可用时自动注入 session_factory 实现对话持久化。
    """
    try:
        from app.db.database import get_engine

        from sqlmodel import Session

        engine = get_engine()

        def session_factory() -> Session:
            return Session(engine)

        return ConversationMemory(session_factory=session_factory)
    except Exception:
        return ConversationMemory()


@lru_cache
def get_llm():
    """FastAPI 依赖：获取全局 LLM 实例。\n\n    若未配置 API key，自动回退到 MockLLM 以便本地开发。
    """
    s = get_cached_settings()
    provider = s.llm_provider
    if provider != "mock" and not s.llm_api_key:
        provider = "mock"
    return LLMFactory.create(
        provider,
        api_key=s.llm_api_key,
        model=s.llm_model,
        enable_search=s.llm_enable_search,
    )


@lru_cache
def get_chat_engine() -> ChatEngine:
    """FastAPI 依赖：获取全局对话引擎。"""
    return ChatEngine(
        llm=get_llm(),
        memory=get_memory(),
        dialect_registry=DialectRegistry,
    )


@lru_cache
def get_speech_pipeline() -> SpeechPipeline:
    """FastAPI 依赖：获取全局语音管道。"""
    return SpeechPipeline(settings=get_cached_settings())
