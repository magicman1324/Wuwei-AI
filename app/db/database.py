"""数据库引擎与会话管理。"""
from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings


@lru_cache
def get_engine():
    """返回全局 SQLAlchemy engine 单例。"""
    settings = get_settings()
    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        connect_args=connect_args,
    )
    return engine


def init_db() -> None:
    """创建所有表（首次启动或测试时调用）。"""
    # 确保模型被导入注册到 SQLModel metadata
    from app.db import models  # noqa: F401

    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI 依赖：每请求一个 session。"""
    engine = get_engine()
    with Session(engine) as session:
        yield session
