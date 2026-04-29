"""老年电台节目生成器：LLM 写稿 → TTS 合成 → 落库。

幂等：若 (date, category, dialect) 已有 status='ready' 的记录则跳过；
失败时写入 status='failed' 行便于重试与监控。
"""
from __future__ import annotations

import io
import re
from datetime import date as date_cls
from datetime import datetime
from pathlib import Path

from loguru import logger
from sqlmodel import Session, select

from app.chat.llm.base import BaseLLM, LLMMessage
from app.db.database import get_engine
from app.db.models import RadioEpisode
from app.dialect.adapter import DialectCode
from app.radio.topics import pick_health_topic, pick_nostalgia_topic
from app.speech.pipeline import SpeechPipeline

RADIO_ROOT = Path("data/radio")

# 讯飞精品音色（x4_*）对单次合成文本长度有授权限制，超过会 11200 licc failed。
# 实测 ≤80 个汉字稳定。电台稿按句切段，逐段合成后拼接。
_TTS_CHUNK_MAX_CHARS = 80
_SENTENCE_SPLIT = re.compile(r"(?<=[。！？!?；;\n])")


def _split_for_tts(text: str, max_chars: int = _TTS_CHUNK_MAX_CHARS) -> list[str]:
    """按句子边界切段，每段 ≤ max_chars 个字符。"""
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    chunks: list[str] = []
    buf = ""
    for s in sentences:
        # 单句若已超长，硬切
        while len(s) > max_chars:
            head, s = s[:max_chars], s[max_chars:]
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.append(head)
        if len(buf) + len(s) <= max_chars:
            buf += s
        else:
            if buf:
                chunks.append(buf)
            buf = s
    if buf:
        chunks.append(buf)
    return chunks


def _build_prompt(category: str, subtopic: str | None, title: str) -> tuple[str, str]:
    """返回 (system_prompt, user_prompt)。

    目标时长 3-4 分钟，约 800-1200 个汉字（讯飞 TTS 约 5 字/秒）。
    """
    if category == "health":
        system = (
            "你是中老年人电台健康栏目的主播，语气温暖亲切、像邻里大姐当面唠家常讲常识。"
            "请写一段 800–1200 字的电台口播稿，结构是："
            "「开场打招呼并点题（约 80 字）→ 把主题拆成 3-4 个具体小要点，每点用一段、配一两个生活化的小例子或比喻、再点出一个常被忽略的误区（每段约 150-220 字）→ 收尾两三句叮嘱与告别（约 80 字）」。"
            "整段要像一个人在话筒前自然说话，多用『咱们』『您』『记着啊』这种亲切语气词，"
            "避免医学术语和拗口的长句；不要用 markdown、序号、列表符号、括号、注释或拼音；"
            "也不要写「主播说：」「停顿」「片头音乐」之类的提示语，直接给可朗读的正文。"
        )
        user = f"今天的主题是「{title}」。请直接给出主播口播稿全文。"
        return system, user

    # nostalgia: old_life | opera
    if subtopic == "opera":
        system = (
            "你是中老年人电台戏曲栏目的主播，语气怀旧亲切，像和老朋友泡着茶聊一段戏。"
            "请写一段 800–1200 字的电台口播稿，结构是："
            "「开场打招呼并点出今天聊哪一出戏（约 80 字）→ 讲剧种与剧目背景、当年红的角儿与名段（约 250-350 字）→ 挑出戏里最动人的一两个唱段或情节细细说，配上一两句白描或唱词意境（约 250-350 字）→ 谈这出戏在那个年代里的味道与今天再听的感受（约 150 字）→ 收尾邀请听众一起回味（约 50-80 字）」。"
            "用接地气的口语，避免学术腔；不要 markdown、序号、列表符号、括号、注释或拼音；"
            "不要写舞台提示，直接给可朗读的正文。"
        )
        user = f"今天我们聊「{title}」。请直接给出主播口播稿全文。"
        return system, user

    system = (
        "你是中老年人电台怀旧栏目的主播，语气怀旧亲切，唤起六七八十年代的生活记忆。"
        "请写一段 800–1200 字的电台口播稿，结构是："
        "「开场打招呼并点题（约 80 字）→ 用画面感的语言勾画当年那个场景：声音、气味、街景、人（约 250-350 字）→ 讲一两个具体的小故事或细节，让听众跟着回到那一刻（约 250-350 字）→ 谈这段记忆里藏着的情感和今天回望的感受（约 150 字）→ 收尾一句温暖的话（约 50-80 字）」。"
        "整段像一个人在话筒前慢慢说话，多用『记得吗』『那时候啊』这种语气；"
        "不要 markdown、序号、列表符号、括号、注释或拼音；不要写舞台提示，直接给可朗读的正文。"
    )
    user = f"今天我们聊「{title}」。请直接给出主播口播稿全文。"
    return system, user


async def _write_text(llm: BaseLLM, system: str, user: str) -> str:
    resp = await llm.chat(
        messages=[
            LLMMessage(role="system", content=system),
            LLMMessage(role="user", content=user),
        ],
        temperature=0.85,
        max_tokens=2400,
    )
    return resp.content.strip()


async def _synthesize(
    pipeline: SpeechPipeline,
    text: str,
    dialect: DialectCode,
    out_path: Path,
    voice_name: str | None = None,
    provider: str | None = None,
) -> tuple[str, int]:
    """合成 TTS 写盘，返回 (audio_format, duration_ms)。

    长文按句切段、逐段合成、再用 pydub 拼接为单个 MP3，绕开讯飞精品音色单次
    文本长度授权限制（11200 licc failed）。
    """
    from pydub import AudioSegment

    chunks = _split_for_tts(text)
    if not chunks:
        raise RuntimeError("文本为空，无法合成")

    segments: list[AudioSegment] = []
    fmt = "mp3"
    for i, chunk in enumerate(chunks):
        audio_bytes, fmt = await pipeline.synthesize_response(
            text=chunk, dialect=dialect, voice_name=voice_name, provider=provider
        )
        if not audio_bytes:
            logger.warning(f"分段 {i} 合成返回空音频，跳过: {chunk[:20]}…")
            continue
        try:
            seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)
        except Exception:
            seg = AudioSegment.from_file(io.BytesIO(audio_bytes))
        segments.append(seg)

    if not segments:
        raise RuntimeError("所有分段合成失败")

    # 段间留 200ms 短停顿，听起来更像电台朗读
    silence = AudioSegment.silent(duration=200)
    combined = segments[0]
    for seg in segments[1:]:
        combined += silence + seg

    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.export(out_path, format="mp3")
    return "mp3", len(combined)


async def generate_episode(
    *,
    pipeline: SpeechPipeline,
    llm: BaseLLM,
    target_date: date_cls,
    category: str,  # 'health' | 'nostalgia'
    dialect: DialectCode = DialectCode.MANDARIN,
    voice_name: str | None = None,
    provider: str | None = None,
    force: bool = False,
) -> RadioEpisode:
    """生成单个节目。已存在 ready 记录直接复用，除非 force=True。"""
    if category not in {"health", "nostalgia"}:
        raise ValueError(f"未知分类: {category}")

    date_str = target_date.isoformat()
    dialect_code = dialect.value

    engine = get_engine()
    with Session(engine) as session:
        existing = session.exec(
            select(RadioEpisode).where(
                RadioEpisode.date == date_str,
                RadioEpisode.category == category,
                RadioEpisode.dialect == dialect_code,
            )
        ).first()
        if existing and existing.status == "ready" and not force:
            return existing

    # 选题
    if category == "health":
        title = pick_health_topic(target_date)
        subtopic: str | None = None
    else:
        subtopic, title = pick_nostalgia_topic(target_date)

    system_prompt, user_prompt = _build_prompt(category, subtopic, title)

    # 生成文稿
    try:
        text = await _write_text(llm, system_prompt, user_prompt)
    except Exception as exc:
        logger.exception(f"电台 LLM 失败: {category} {date_str} {dialect_code}")
        return _persist(
            date_str=date_str,
            category=category,
            subtopic=subtopic,
            dialect=dialect_code,
            title=title,
            text=f"[生成失败] {exc}",
            audio_path=None,
            duration_ms=0,
            status="failed",
            force=force,
        )

    # 合成音频
    audio_rel: str | None = None
    duration_ms = 0
    try:
        out_path = RADIO_ROOT / date_str / f"{category}_{dialect_code}.mp3"
        _, duration_ms = await _synthesize(
            pipeline, text, dialect, out_path,
            voice_name=voice_name, provider=provider,
        )
        audio_rel = f"{date_str}/{category}_{dialect_code}.mp3"
        status = "ready"
    except Exception as exc:
        logger.exception(f"电台 TTS 失败: {category} {date_str} {dialect_code}")
        status = "failed"
        # 文稿仍保留，便于稍后只补音频

    return _persist(
        date_str=date_str,
        category=category,
        subtopic=subtopic,
        dialect=dialect_code,
        title=title,
        text=text,
        audio_path=audio_rel,
        duration_ms=duration_ms,
        status=status,
        force=force,
    )


def _persist(
    *,
    date_str: str,
    category: str,
    subtopic: str | None,
    dialect: str,
    title: str,
    text: str,
    audio_path: str | None,
    duration_ms: int,
    status: str,
    force: bool,
) -> RadioEpisode:
    engine = get_engine()
    with Session(engine) as session:
        existing = session.exec(
            select(RadioEpisode).where(
                RadioEpisode.date == date_str,
                RadioEpisode.category == category,
                RadioEpisode.dialect == dialect,
            )
        ).first()
        if existing:
            existing.subtopic = subtopic
            existing.title = title
            existing.text = text
            existing.audio_path = audio_path
            existing.duration_ms = duration_ms
            existing.status = status
            existing.created_at = datetime.utcnow()
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

        ep = RadioEpisode(
            date=date_str,
            category=category,
            subtopic=subtopic,
            dialect=dialect,
            title=title,
            text=text,
            audio_path=audio_path,
            duration_ms=duration_ms,
            status=status,
        )
        session.add(ep)
        session.commit()
        session.refresh(ep)
        return ep


async def generate_today(
    *,
    pipeline: SpeechPipeline,
    llm: BaseLLM,
    target_date: date_cls | None = None,
    dialect: DialectCode = DialectCode.MANDARIN,
    voice_name: str | None = None,
    provider: str | None = None,
    force: bool = False,
) -> list[RadioEpisode]:
    """生成当日两期（健康 + 怀旧）。"""
    target_date = target_date or date_cls.today()
    out: list[RadioEpisode] = []
    for category in ("health", "nostalgia"):
        ep = await generate_episode(
            pipeline=pipeline,
            llm=llm,
            target_date=target_date,
            category=category,
            dialect=dialect,
            voice_name=voice_name,
            provider=provider,
            force=force,
        )
        out.append(ep)
    return out
