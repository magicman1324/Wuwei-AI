"""方言文本规范化器：方言 ASR 输出 ↔ 标准普通话。"""

from app.dialect.adapter import DialectCode, DialectRegistry


class DialectNormalizer:
    """
    将方言 ASR 输出的文本转换为标准普通话文本，使 LLM 能正确理解。

    示例:
      粤语: "我想食饭" → 普通话: "我想吃饭"
      四川话: "啊子东西嘛" → 普通话: "什么东西啊"
    """

    def normalize(self, text: str, dialect: DialectCode) -> str:
        """方言文本 → 标准普通话文本。"""
        adapter = DialectRegistry.get(dialect)
        return adapter.to_mandarin(text)

    def denormalize(self, text: str, dialect: DialectCode) -> str:
        """标准普通话文本 → 方言化表达（用于 TTS 前处理）。"""
        adapter = DialectRegistry.get(dialect)
        return adapter.from_mandarin(text)
