"""方言转换器：基于词典的普通话 ↔ 方言互转。"""

import json
from pathlib import Path

from loguru import logger

from app.dialect.adapter import DialectCode


class DialectConverter:
    """加载方言词典并执行文本替换转换。"""

    def __init__(self, dialect: DialectCode, data_folder: str):
        self.dialect = dialect
        self.data_folder = data_folder
        self._to_mandarin_map: dict[str, str] = {}
        self._from_mandarin_map: dict[str, str] = {}
        self._load_dictionary()

    def _load_dictionary(self):
        """从 JSON 文件加载方言词典。"""
        data_dir = Path(__file__).parent / "data" / self.data_folder
        dict_path = data_dir / "dictionary.json"

        if not dict_path.exists():
            logger.warning(f"方言词典不存在: {dict_path}")
            return

        with open(dict_path, encoding="utf-8") as f:
            mapping = json.load(f)

        # dictionary.json 格式: {"方言词": "普通话词", ...}
        self._to_mandarin_map = mapping
        self._from_mandarin_map = {v: k for k, v in mapping.items()}

    def to_mandarin(self, text: str) -> str:
        """方言文本 → 普通话文本（基于词典替换）。"""
        result = text
        for dialect_word, mandarin_word in self._to_mandarin_map.items():
            result = result.replace(dialect_word, mandarin_word)
        return result

    def from_mandarin(self, text: str) -> str:
        """普通话文本 → 方言化表达（基于词典替换）。"""
        result = text
        for mandarin_word, dialect_word in self._from_mandarin_map.items():
            result = result.replace(mandarin_word, dialect_word)
        return result
