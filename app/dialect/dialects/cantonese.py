"""粤语适配器。"""

from app.dialect.adapter import DialectAdapter, DialectCode, DialectRegistry
from app.dialect.converter import DialectConverter


@DialectRegistry.register
class CantoneseAdapter(DialectAdapter):
    def __init__(self):
        self._converter = DialectConverter(DialectCode.CANTONESE, "cantonese")

    @property
    def dialect_code(self) -> DialectCode:
        return DialectCode.CANTONESE

    @property
    def dialect_name(self) -> str:
        return "粤语"

    def to_mandarin(self, text: str) -> str:
        return self._converter.to_mandarin(text)

    def from_mandarin(self, text: str) -> str:
        return self._converter.from_mandarin(text)

    def get_system_prompt_addition(self) -> str:
        return (
            "你正在和一位说粤语的老人家聊天。"
            "请用亲切、口语化的方式回答。"
            "可以适当使用粤语常用表达，如'系咪'(是不是)、'点解'(为什么)等。"
            "语气要温暖，像晚辈和长辈说话一样。"
        )

    def get_asr_config(self) -> dict:
        return {
            "provider": "iflytek",
            "language": "cantonese",
            "accent": "guangdong",
        }

    def get_tts_config(self) -> dict:
        return {
            "provider": "iflytek",
            "voice_name": "xiaoyan_cantonese",
            "speed": 0.85,
            "volume": 1.2,
        }
