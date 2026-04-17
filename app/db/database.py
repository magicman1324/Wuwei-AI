"""数据库引擎与会话管理。"""
from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    """如果是 SQLite 文件 URL，确保父目录存在（首次启动体验）。"""
    if not database_url.startswith("sqlite"):
        return
    # sqlite:///./data/db/wuwei.db → ./data/db/wuwei.db
    # sqlite:////abs/path.db      → /abs/path.db
    # sqlite:///:memory: → 跳过
    _, _, path_part = database_url.partition("sqlite:///")
    if not path_part or path_part.startswith(":memory:"):
        return
    db_path = Path(path_part)
    if db_path.parent and not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_engine():
    """返回全局 SQLAlchemy engine 单例。"""
    settings = get_settings()
    _ensure_sqlite_parent_dir(settings.database_url)
    connect_args = {}
    kwargs = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if ":memory:" in settings.database_url:
            kwargs["poolclass"] = StaticPool
    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        connect_args=connect_args,
        **kwargs,
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
