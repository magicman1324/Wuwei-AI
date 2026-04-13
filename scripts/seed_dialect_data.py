"""方言词典验证 + 数据库初始化脚本。

用法:
    python -m scripts.seed_dialect_data
"""
from __future__ import annotations

import json
from pathlib import Path

from loguru import logger

DIALECT_DATA_DIR = Path(__file__).resolve().parents[1] / "app" / "dialect" / "data"


def validate_dictionaries() -> None:
    """验证所有方言词典 JSON 格式。"""
    logger.info("验证方言词典……")
    for dict_file in DIALECT_DATA_DIR.rglob("dictionary.json"):
        try:
            data = json.loads(dict_file.read_text(encoding="utf-8"))
            assert isinstance(data, dict), f"{dict_file}: 词典应为 JSON 对象"
            for k, v in data.items():
                assert isinstance(k, str) and isinstance(v, str), (
                    f"{dict_file}: 键值必须都是字符串 ({k}→{v})"
                )
            logger.success(f"{dict_file.parent.name}: {len(data)} 条词条 ✓")
        except Exception as e:
            logger.error(f"❌ {dict_file}: {e}")
            raise


def init_database() -> None:
    """初始化数据库表结构。"""
    logger.info("初始化数据库……")
    from app.db.database import init_db

    init_db()
    logger.success("数据库表创建完成")


if __name__ == "__main__":
    validate_dictionaries()
    init_database()
    logger.info("全部完成 🎉")
