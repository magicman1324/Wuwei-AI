"""方言检测器测试。"""
from __future__ import annotations

from app.dialect.adapter import DialectCode
from app.dialect.detector import DialectDetector


def test_user_preference_takes_priority() -> None:
    detector = DialectDetector()
    result = detector.detect(
        text="你好，今天天气不错",
        user_preference=DialectCode.CANTONESE,
    )
    assert result == DialectCode.CANTONESE


def test_fallback_to_mandarin() -> None:
    detector = DialectDetector()
    result = detector.detect(text="你好")
    assert result == DialectCode.MANDARIN
