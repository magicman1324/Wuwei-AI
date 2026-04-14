"""FastAPI 应用入口，注册路由并挂载 Gradio UI。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

# 导入方言适配器以触发自动注册 (必须在 api_router 之前)
import app.dialect.dialects  # noqa: F401
from app.api.router import api_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库，关闭时清理资源。"""
    settings = get_settings()

    # 启动：初始化数据库表
    try:
        from app.db.database import init_db

        init_db()
        logger.info("数据库表已就绪")
    except Exception as e:
        logger.warning(f"数据库初始化失败: {e}")

    logger.info(f"{settings.app_name} 启动完成")
    logger.info(f"已启用方言: {settings.enabled_dialects}")

    yield

    logger.info(f"{settings.app_name} 已关闭")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="面向中老年的方言语音聊天助手",
        lifespan=lifespan,
    )

    # 注册 API 路由
    app.include_router(api_router, prefix="/api/v1")

    # 挂载 Gradio UI
    try:
        import gradio as gr

        from app.dependencies import get_chat_engine, get_speech_pipeline
        from app.ui.gradio_app import create_gradio_ui

        gradio_app = create_gradio_ui(
            chat_engine=get_chat_engine(),
            speech_pipeline=get_speech_pipeline(),
        )
        app = gr.mount_gradio_app(app, gradio_app, path="/")
        logger.info("Gradio UI 已挂载到 /")
    except ImportError:
        logger.warning("Gradio 未安装，跳过 UI 挂载")

    return app
