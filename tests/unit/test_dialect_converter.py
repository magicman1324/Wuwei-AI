"""方言转换器：最长匹配 + 词边界测试。"""
from __future__ import annotations

from app.dialect.converter import _replace_longest_match


def test_longest_match_prefers_longer_key() -> None:
    mapping = {"食": "吃", "食饭": "吃饭"}
    assert _replace_longest_match("我食饭", mapping) == "我吃饭"


def test_no_partial_overlap_collision() -> None:
    # "食" 单独映射, 但 "食饭" 更长 → 整句应走长词
    mapping = {"食": "吃", "食饭": "吃饭"}
    # "不食饭" 中 "食饭" 命中 → "不吃饭"
    assert _replace_longest_match("不食饭", mapping) == "不吃饭"


def test_non_matching_text_unchanged() -> None:
    mapping = {"食饭": "吃饭"}
    assert _replace_longest_match("今天天气很好", mapping) == "今天天气很好"


def test_empty_inputs() -> None:
    assert _replace_longest_match("", {"a": "b"}) == ""
    assert _replace_longest_match("abc", {}) == "abc"


def test_multiple_substitutions() -> None:
    mapping = {"食饭": "吃饭", "唔该": "谢谢"}
    assert _replace_longest_match("食饭唔该", mapping) == "吃饭谢谢"


def test_adjacent_keys() -> None:
    mapping = {"AB": "12", "CD": "34"}
    assert _replace_longest_match("ABCD", mapping) == "1234"


def test_chained_longest_priority() -> None:
    # 三层候选，确保最长优先
    mapping = {"好": "1", "好好": "2", "好好的": "3"}
    assert _replace_longest_match("好好的", mapping) == "3"
    assert _replace_longest_match("好好", mapping) == "2"
    assert _replace_longest_match("好", mapping) == "1"
