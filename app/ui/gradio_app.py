"""Gradio 适老化 UI。

设计原则：
- 大字体、大按钮、高对比度
- 语音优先：按住说话
- 方言切换下拉
- 最少文字操作
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import gradio as gr
import numpy as np
from loguru import logger

from app.chat.engine import ChatEngine
from app.dialect.adapter import DialectCode
from app.speech.audio_utils import to_pcm16_16k_mono, write_audio_tempfile
from app.speech.pipeline import SpeechPipeline

_CSS_PATH = Path(__file__).parent / "static" / "css" / "elderly.css"


def _load_css() -> str:
    if _CSS_PATH.exists():
        return _CSS_PATH.read_text(encoding="utf-8")
    return ""


def get_ui_theme() -> gr.themes.ThemeClass:
    """Gradio 6 的主题已从 Blocks() 移到 mount_gradio_app()。"""
    return gr.themes.Soft()


def get_ui_css() -> str:
    """Gradio 6 的自定义 CSS 已从 Blocks() 移到 mount_gradio_app()。"""
    return _load_css()


def _coerce_dialect(value: str) -> DialectCode:
    try:
        return DialectCode(value)
    except ValueError:
        return DialectCode.MANDARIN


def _voice_enabled(pipeline: SpeechPipeline | None) -> bool:
    return (
        pipeline is not None
        and bool(pipeline._asr_engines)
        and bool(pipeline._tts_engines)
    )


def _msg(role: str, content: str) -> dict[str, str]:
    """构造 Gradio Chatbot(type='messages') 期望的消息字典。"""
    return {"role": role, "content": content}


async def handle_text_chat(
    message: str,
    history: list[dict],
    dialect: str,
    user_id: str,
    *,
    chat_engine: ChatEngine,
) -> tuple[list[dict], str]:
    """文字消息 handler — 模块级以便单测。

    返回 OpenAI messages 格式: [{"role":"user|assistant","content":"..."}, ...]
    """
    if not message.strip():
        return history, ""
    code = _coerce_dialect(dialect)
    result = await chat_engine.chat_text(
        text=message,
        user_id=user_id or "anonymous",
        dialect=code,
    )
    return history + [_msg("user", message), _msg("assistant", result.text)], ""


async def handle_voice_chat(
    audio: Optional[tuple[int, np.ndarray]],
    history: list[dict],
    dialect: str,
    user_id: str,
    *,
    chat_engine: ChatEngine,
    speech_pipeline: SpeechPipeline | None,
) -> tuple[list[dict], Optional[str]]:
    """麦克风录音 → ASR → LLM → TTS → 播放。模块级 handler，便于单测。"""
    if audio is None:
        return history, None

    if not _voice_enabled(speech_pipeline):
        return (
            history
            + [
                _msg("user", "🎤 [语音]"),
                _msg("assistant", "语音功能未配置，请填写讯飞凭据后重试。"),
            ],
            None,
        )

    assert speech_pipeline is not None  # for type checker

    sample_rate, samples = audio
    pcm = to_pcm16_16k_mono(sample_rate, samples)
    if not pcm:
        return history, None

    code = _coerce_dialect(dialect)
    uid = user_id or "anonymous"

    try:
        raw_text, normalized, detected = await speech_pipeline.process_voice(
            audio_data=pcm,
            audio_format="pcm",
            sample_rate=16000,
            user_id=uid,
            dialect_hint=code,
        )
    except Exception as exc:
        logger.exception("ASR 失败")
        return (
            history
            + [
                _msg("user", "🎤 [语音识别失败]"),
                _msg("assistant", f"出错了：{exc}"),
            ],
            None,
        )

    if not raw_text.strip():
        return (
            history
            + [
                _msg("user", "🎤 [未识别到内容]"),
                _msg("assistant", "请再说一次～"),
            ],
            None,
        )

    # LLM 用规范化后的普通话文本，但聊天记录展示 ASR 原文
    chat_result = await chat_engine.chat(
        user_input=normalized,
        user_id=uid,
        dialect=detected,
    )

    # TTS 合成（失败可降级为纯文字）
    audio_path: Optional[str] = None
    try:
        audio_bytes, audio_fmt = await speech_pipeline.synthesize_response(
            text=chat_result.text,
            dialect=detected,
        )
        if audio_bytes:
            audio_path = write_audio_tempfile(audio_bytes, suffix=f".{audio_fmt}")
    except Exception as exc:
        logger.warning(f"TTS 合成失败，仅返回文字: {exc}")

    return (
        history
        + [_msg("user", raw_text), _msg("assistant", chat_result.text)],
        audio_path,
    )


def create_gradio_ui(
    chat_engine: ChatEngine,
    speech_pipeline: SpeechPipeline | None = None,
) -> gr.Blocks:
    """构造 Gradio Blocks 应用，由 FastAPI 挂载。

    Args:
        chat_engine: 对话引擎。
        speech_pipeline: 可选语音管道；为 None 时麦克风按钮显示降级提示。
    """

    async def _on_text_submit(message, history, dialect, user_id):
        return await handle_text_chat(
            message, history, dialect, user_id, chat_engine=chat_engine
        )

    async def _on_voice_submit(audio, history, dialect, user_id):
        return await handle_voice_chat(
            audio,
            history,
            dialect,
            user_id,
            chat_engine=chat_engine,
            speech_pipeline=speech_pipeline,
        )

    with gr.Blocks(title="无为AI · 方言聊天") as demo:
        gr.Markdown(
            """
            # 🌿 无为AI
            ### 专为长辈设计的方言聊天助手
            按住麦克风说话，或直接打字聊天。
            """,
            elem_classes="header",
        )

        with gr.Row():
            dialect_selector = gr.Dropdown(
                choices=[
                    ("普通话", DialectCode.MANDARIN.value),
                    ("粤语", DialectCode.CANTONESE.value),
                    ("四川话", DialectCode.SICHUAN.value),
                ],
                value=DialectCode.MANDARIN.value,
                label="选择方言",
                elem_classes="big-dropdown",
            )
            user_id_box = gr.Textbox(
                value="anonymous",
                label="用户 ID",
                visible=False,
            )

        chatbot = gr.Chatbot(
            label="聊天记录",
            height=500,
            elem_classes="big-chatbot",
        )

        with gr.Row():
            text_input = gr.Textbox(
                placeholder="在这里输入您想说的话……",
                label="文字输入",
                scale=4,
                elem_classes="big-input",
            )
            send_btn = gr.Button(
                "发送", variant="primary", scale=1, elem_classes="big-button"
            )

        with gr.Row():
            audio_input = gr.Audio(
                sources=["microphone"],
                type="numpy",
                label="按住说话",
                elem_classes="big-audio",
            )
            audio_output = gr.Audio(
                label="语音回复",
                type="filepath",
                autoplay=True,
                interactive=False,
                elem_classes="big-audio",
            )

        send_btn.click(
            _on_text_submit,
            inputs=[text_input, chatbot, dialect_selector, user_id_box],
            outputs=[chatbot, text_input],
        )
        text_input.submit(
            _on_text_submit,
            inputs=[text_input, chatbot, dialect_selector, user_id_box],
            outputs=[chatbot, text_input],
        )
        audio_input.stop_recording(
            _on_voice_submit,
            inputs=[audio_input, chatbot, dialect_selector, user_id_box],
            outputs=[chatbot, audio_output],
        )

    return demo
