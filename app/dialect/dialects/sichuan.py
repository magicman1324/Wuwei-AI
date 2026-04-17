"""四川话适配器。"""

from app.dialect.adapter import DialectAdapter, DialectCode, DialectRegistry
from app.dialect.converter import DialectConverter


@DialectRegistry.register
class SichuanAdapter(DialectAdapter):
    def __init__(self):
        self._converter = DialectConverter(DialectCode.SICHUAN, "sichuan")

    @property
    def dialect_code(self) -> DialectCode:
        return DialectCode.SICHUAN

    @property
    def dialect_name(self) -> str:
        return "四川话"

    def to_mandarin(self, text: str) -> str:
        return self._converter.to_mandarin(text)

    def from_mandarin(self, text: str) -> str:
        return self._converter.from_mandarin(text)

    def get_system_prompt_addition(self) -> str:
        return (
            "你正在和一位说四川话的老人家聊天。"
            "请用亲切、口语化的方式回答。"
            "可以适当使用四川话常用表达，如'巴适'(舒服/好)、'要得'(可以)等。"
            "语气要温暖自然，像家人一样。"
        )

    def get_asr_config(self) -> dict:
        return {
            "provider": "iflytek",
            "language": "zh_cn",
            "accent": "lmz",  # 讯飞四川话 accent 内部代号
        }

    def get_tts_config(self) -> dict:
        # x3_yezi_sc = 叶子（四川话 V3.0），自然度高
        return {
            "provider": "iflytek",
            "voice_name": "x3_yezi_sc",
            "speed": 0.85,
            "volume": 1.2,
        }
