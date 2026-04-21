"""健康检查端点。"""

from fastapi import APIRouter

from app.dialect.adapter import DialectRegistry

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "无维AI",
        "dialects": DialectRegistry.list_dialect_info(),
    }


@router.get("/dialects")
async def list_dialects():
    """返回所有支持的方言列表。"""
    return {"dialects": DialectRegistry.list_dialect_info()}


@router.get("/debug/llm")
async def debug_llm():
    """调试：直接测试 LLM 是否可用，返回原始错误信息。"""
    from app.dependencies import get_llm
    from app.chat.llm.base import LLMMessage

    llm = get_llm()
    try:
        result = await llm.chat(
            messages=[LLMMessage(role="user", content="你好，请回复OK")],
            max_tokens=20,
        )
        return {"status": "ok", "provider": type(llm).__name__, "reply": result.content}
    except Exception as e:
        return {"status": "error", "provider": type(llm).__name__, "error": str(e)}
