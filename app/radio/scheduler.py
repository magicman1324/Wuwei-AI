"""老年电台定时任务：每天 06:00 生成当日两期普通话节目。"""
from __future__ import annotations

import asyncio
from datetime import date as date_cls

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.config import get_settings
from app.dependencies import get_llm, get_speech_pipeline
from app.dialect.adapter import DialectCode
from app.radio.generator import generate_today

_scheduler: AsyncIOScheduler | None = None


async def _job_generate_today() -> None:
    logger.info("[radio] 触发每日节目生成")
    try:
        pipeline = get_speech_pipeline()
        llm = get_llm()
        s = get_settings()
        eps = await generate_today(
            pipeline=pipeline,
            llm=llm,
            target_date=date_cls.today(),
            dialect=DialectCode.MANDARIN,
            voice_name=s.radio_tts_voice or None,
            provider=s.radio_tts_provider or None,
        )
        logger.info(
            "[radio] 生成完成: "
            + ", ".join(f"{e.category}={e.status}" for e in eps)
        )
    except Exception as exc:
        logger.exception(f"[radio] 每日生成失败: {exc}")


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    sched = AsyncIOScheduler(timezone="Asia/Shanghai")
    sched.add_job(
        _job_generate_today,
        trigger=CronTrigger(hour=6, minute=0),
        id="radio_daily",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    sched.start()
    _scheduler = sched
    logger.info("[radio] APScheduler 已启动 (每日 06:00 Asia/Shanghai)")

    # 启动时如当天还没有 ready 节目，后台补一次
    asyncio.create_task(_bootstrap_if_missing())


async def _bootstrap_if_missing() -> None:
    from app.radio.service import get_today

    today = date_cls.today()
    eps = get_today(today, dialect="cmn")
    if len(eps) >= 2:
        return
    logger.info("[radio] 启动时缺当日节目，后台补生成")
    await _job_generate_today()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("[radio] APScheduler 已停止")
