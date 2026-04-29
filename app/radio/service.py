"""老年电台数据查询服务。"""
from __future__ import annotations

from datetime import date as date_cls
from datetime import timedelta

from sqlmodel import Session, select

from app.db.database import get_engine
from app.db.models import RadioEpisode


def get_today(target_date: date_cls, dialect: str = "cmn") -> list[RadioEpisode]:
    """返回当日所有 ready 节目。普通话优先，缺则任意方言兜底。"""
    date_str = target_date.isoformat()
    engine = get_engine()
    with Session(engine) as session:
        rows = session.exec(
            select(RadioEpisode)
            .where(RadioEpisode.date == date_str)
            .where(RadioEpisode.status == "ready")
        ).all()

    by_cat: dict[str, RadioEpisode] = {}
    for r in rows:
        if r.dialect == dialect:
            by_cat[r.category] = r
    for r in rows:
        by_cat.setdefault(r.category, r)
    # 排序：health 先于 nostalgia
    return [by_cat[c] for c in ("health", "nostalgia") if c in by_cat]


def list_episodes(
    days: int = 14,
    until: date_cls | None = None,
    dialect: str = "cmn",
) -> list[RadioEpisode]:
    """近 N 天的节目列表，按日期倒序。"""
    until = until or date_cls.today()
    start = until - timedelta(days=days - 1)
    engine = get_engine()
    with Session(engine) as session:
        rows = session.exec(
            select(RadioEpisode)
            .where(RadioEpisode.date >= start.isoformat())
            .where(RadioEpisode.date <= until.isoformat())
            .where(RadioEpisode.status == "ready")
            .where(RadioEpisode.dialect == dialect)
        ).all()
    rows.sort(key=lambda r: (r.date, r.category), reverse=True)
    return rows


def get_by_id(episode_id: str) -> RadioEpisode | None:
    engine = get_engine()
    with Session(engine) as session:
        return session.get(RadioEpisode, episode_id)
