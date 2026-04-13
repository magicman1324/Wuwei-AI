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

from app.chat.engine import ChatEngine
from app.dialect.adapter import DialectCode

_CSS_PATH = Path(__file__).parent / "static" / "css" / "elderly.css"


def _load_css() -> str:
    if _CSS_PATH.exists():
        return _CSS_PATH.read_text(encoding="utf-8")
    return ""


def create_gradio_ui(chat_engine: ChatEngine) -> gr.Blocks:
    """构造 Gradio Blocks 应用，由 FastAPI 挂载。

    Args:
        chat_engine: 从 FastAPI 依赖注入获取的对话引擎。
    """

    async def _on_text_submit(
        message: str,
        history: list[list[str]],
        dialect: str,
        user_id: str,
    ) -> tuple[list[list[str]], str]:
        if not message.strip():
            return history, ""
        try:
            code = DialectCode(dialect)
        except ValueError:
            code = DialectCode.MANDARIN
        reply, _ = await chat_engine.chat_text(
            user_id=user_id or "anonymous",
            text=message,
            dialect=code,
        )
        history = history + [[message, reply]]
        return history, ""

    async def _on_voice_submit(
        audio_path: Optional[str],
        history: list[list[str]],
        dialect: str,
        user_id: str,
    ) -> list[list[str]]:
        # TODO: 接入语音管道 (SpeechPipeline)
        # 当前仅占位，填充后调用 ASR → chat → TTS
        if not audio_path:
            return history
        placeholder = "[语音功能开发中，暂无法识别]"
        history = history + [[placeholder, "请先用文字与我交流啦～"]]
        return history

    with gr.Blocks(
        title="无为AI · 方言聊天",
        css=_load_css(),
        theme=gr.themes.Soft(),
    ) as demo:
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
            send_btn = gr.Button("发送", variant="primary", scale=1, elem_classes="big-button")

        with gr.Row():
            audio_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="按住说话",
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
            outputs=[chatbot],
        )

    return demo
