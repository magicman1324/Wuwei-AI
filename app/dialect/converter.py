"""方言转换器：基于词典的普通话 ↔ 方言互转。

实现要点：
- 同时扫描所有候选词，按"最长匹配优先"避免子串误替换。
- 单遍扫描（O(n·k)，k=字典最大词长），不会因替换顺序改变结果。
"""

import json
from pathlib import Path

from loguru import logger

from app.dialect.adapter import DialectCode


def _replace_longest_match(text: str, mapping: dict[str, str]) -> str:
    """单遍扫描，最长匹配优先替换。

    例：mapping = {"食": "吃", "食饭": "吃饭"}，"食饭" → "吃饭"（而非 "吃饭"）。
    空字符串或空字典直接返回原文。
    """
    if not text or not mapping:
        return text

    max_len = max(len(k) for k in mapping)
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        matched = False
        # 从最长可能的子串开始尝试
        for length in range(min(max_len, n - i), 0, -1):
            substr = text[i : i + length]
            if substr in mapping:
                out.append(mapping[substr])
                i += length
                matched = True
                break
        if not matched:
            out.append(text[i])
            i += 1
    return "".join(out)


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
        # 反向映射时若多个方言词映射到同一普通话词，后者覆盖前者（保留字典后定义项）
        self._from_mandarin_map = {v: k for k, v in mapping.items()}

    def to_mandarin(self, text: str) -> str:
        """方言文本 → 普通话文本（最长匹配替换）。"""
        return _replace_longest_match(text, self._to_mandarin_map)

    def from_mandarin(self, text: str) -> str:
        """普通话文本 → 方言化表达（最长匹配替换）。"""
        return _replace_longest_match(text, self._from_mandarin_map)
