"""方言检测器：根据用户偏好、文本特征词检测方言类型。"""

from dataclasses import dataclass

from app.dialect.adapter import DialectCode

# 各方言特征词集合
_DIALECT_FEATURES: dict[DialectCode, set[str]] = {
    DialectCode.CANTONESE: {"嘅", "咧", "唏", "嚟", "喺", "噉", "咁", "佢", "嗰", "乜"},
    DialectCode.SICHUAN: {"啊子", "巴适", "安逸", "莫得", "要得", "啦个", "龟儿", "瓜娃子", "扎起"},
}


@dataclass
class DialectDetectionResult:
    dialect: DialectCode
    confidence: float
    source: str  # "user_preference" | "text_feature" | "asr_detection" | "default"


class DialectDetector:
    """
    方言检测策略（按优先级）：
    1. 用户档案中的方言偏好设置（最高优先）
    2. 基于文本特征词的规则检测
    3. 回退到普通话
    """

    def detect(
        self,
        text: str | None = None,
        user_preference: DialectCode | None = None,
    ) -> DialectDetectionResult:
        # 优先使用用户偏好
        if user_preference:
            return DialectDetectionResult(
                dialect=user_preference,
                confidence=1.0,
                source="user_preference",
            )

        # 基于文本特征词检测
        if text:
            result = self._detect_from_text(text)
            if result:
                return result

        # 回退到普通话
        return DialectDetectionResult(
            dialect=DialectCode.MANDARIN,
            confidence=0.5,
            source="default",
        )

    def _detect_from_text(self, text: str) -> DialectDetectionResult | None:
        """基于特征词匹配检测方言。"""
        best_dialect = None
        best_score = 0

        for dialect, features in _DIALECT_FEATURES.items():
            score = sum(1 for f in features if f in text)
            if score > best_score:
                best_score = score
                best_dialect = dialect

        if best_dialect and best_score > 0:
            confidence = min(best_score / 3.0, 1.0)
            return DialectDetectionResult(
                dialect=best_dialect,
                confidence=confidence,
                source="text_feature",
            )
        return None
