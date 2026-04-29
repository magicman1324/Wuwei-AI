"""老年电台 API：节目列表、详情、音频下载、手动触发生成。"""
from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.chat.llm.base import BaseLLM
from app.config import get_settings
from app.dependencies import get_llm, get_speech_pipeline
from app.dialect.adapter import DialectCode
from app.radio import service
from app.radio.generator import RADIO_ROOT, generate_episode, generate_today
from app.speech.pipeline import SpeechPipeline

router = APIRouter()


class EpisodeOut(BaseModel):
    id: str
    date: str
    category: str
    subtopic: str | None = None
    dialect: str
    title: str
    text: str
    audio_url: str | None = None
    duration_ms: int = 0
    status: str
    created_at: datetime


def _to_out(ep) -> EpisodeOut:
    audio_url = f"/api/v1/radio/audio/{ep.id}" if ep.audio_path else None
    return EpisodeOut(
        id=ep.id,
        date=ep.date,
        category=ep.category,
        subtopic=ep.subtopic,
        dialect=ep.dialect,
        title=ep.title,
        text=ep.text,
        audio_url=audio_url,
        duration_ms=ep.duration_ms,
        status=ep.status,
        created_at=ep.created_at,
    )


@router.get("/today", response_model=list[EpisodeOut])
def get_today(dialect: str = "cmn"):
    """返回今日两期节目。普通话优先，缺则其它方言兜底。"""
    eps = service.get_today(date_cls.today(), dialect=dialect)
    return [_to_out(e) for e in eps]


@router.get("/episodes", response_model=list[EpisodeOut])
def list_episodes(days: int = Query(14, ge=1, le=60), dialect: str = "cmn"):
    """近 N 天的节目列表（按日期倒序）。"""
    rows = service.list_episodes(days=days, dialect=dialect)
    return [_to_out(e) for e in rows]


@router.get("/episodes/{episode_id}", response_model=EpisodeOut)
def get_episode(episode_id: str):
    ep = service.get_by_id(episode_id)
    if not ep:
        raise HTTPException(404, "节目不存在")
    return _to_out(ep)


@router.get("/audio/{episode_id}")
def get_audio(episode_id: str):
    ep = service.get_by_id(episode_id)
    if not ep or not ep.audio_path:
        raise HTTPException(404, "音频不存在")
    abs_path = (RADIO_ROOT / ep.audio_path).resolve()
    if not abs_path.is_file():
        raise HTTPException(404, "音频文件已丢失")
    media = "audio/mpeg" if abs_path.suffix.lower() == ".mp3" else "application/octet-stream"
    return FileResponse(str(abs_path), media_type=media, filename=abs_path.name)


class GenerateBody(BaseModel):
    target_date: str | None = None  # 'YYYY-MM-DD'，缺省 today
    dialect: str = "cmn"
    category: str | None = None     # 'health' | 'nostalgia'，缺省两期都生成
    force: bool = False


@router.post("/admin/generate", response_model=list[EpisodeOut])
async def admin_generate(
    body: GenerateBody,
    pipeline: SpeechPipeline = Depends(get_speech_pipeline),
    llm: BaseLLM = Depends(get_llm),
):
    """手动触发生成（运维接口，未做鉴权 — 后续可加 admin token）。"""
    target = (
        date_cls.fromisoformat(body.target_date) if body.target_date else date_cls.today()
    )
    try:
        dialect = DialectCode(body.dialect)
    except ValueError:
        raise HTTPException(400, f"未知方言: {body.dialect}")

    s = get_settings()
    voice = s.radio_tts_voice or None
    provider = s.radio_tts_provider or None

    if body.category:
        ep = await generate_episode(
            pipeline=pipeline,
            llm=llm,
            target_date=target,
            category=body.category,
            dialect=dialect,
            voice_name=voice,
            provider=provider,
            force=body.force,
        )
        return [_to_out(ep)]

    eps = await generate_today(
        pipeline=pipeline,
        llm=llm,
        target_date=target,
        dialect=dialect,
        voice_name=voice,
        provider=provider,
        force=body.force,
    )
    return [_to_out(e) for e in eps]
