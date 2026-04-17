"""普通话适配器（默认/回退）。"""

from app.dialect.adapter import DialectAdapter, DialectCode, DialectRegistry


@DialectRegistry.register
class MandarinAdapter(DialectAdapter):
    @property
    def dialect_code(self) -> DialectCode:
        return DialectCode.MANDARIN

    @property
    def dialect_name(self) -> str:
        return "普通话"

    def to_mandarin(self, text: str) -> str:
        return text

    def from_mandarin(self, text: str) -> str:
        return text

    def get_system_prompt_addition(self) -> str:
        return "请用标准普通话回答，语言简洁清晰。"

    def get_asr_config(self) -> dict:
        # 默认 iflytek，若配置了阿里云凭据 SpeechPipeline 可在运行期重写
        return {
            "provider": "iflytek",
            "language": "zh_cn",
            "accent": "mandarin",
        }

    def get_tts_config(self) -> dict:
        # lingbosong = 聆伯松（普通话男声），自然度高
        return {
            "provider": "iflytek",
            "voice_name": "lingbosong",
            "speed": 0.85,
            "volume": 1.2,
        }
