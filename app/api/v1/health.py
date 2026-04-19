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
