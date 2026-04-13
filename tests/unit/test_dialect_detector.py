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
    assert result.dialect == DialectCode.CANTONESE
    assert result.source == "user_preference"


def test_fallback_to_mandarin() -> None:
    detector = DialectDetector()
    result = detector.detect(text="你好")
    assert result.dialect == DialectCode.MANDARIN
    assert result.source == "default"


def test_text_feature_detects_cantonese() -> None:
    detector = DialectDetector()
    result = detector.detect(text="你喺边度嘅？我嚟咗呢度")
    assert result.dialect == DialectCode.CANTONESE
    assert result.source == "text_feature"
