"""方言适配器抽象基类与注册表。

采用注册表模式 + 策略模式，新增方言只需实现 DialectAdapter 子类并注册即可。
"""

from abc import ABC, abstractmethod
from enum import Enum


class DialectCode(str, Enum):
    """方言编码，遵循 ISO 639-3 + 自定义扩展。"""

    MANDARIN = "cmn"
    CANTONESE = "yue"
    SICHUAN = "cmn-sichuan"
    # 未来扩展:
    # HOKKIEN = "nan"         # 闽南语
    # SHANGHAINESE = "wuu"    # 上海话
    # HAKKA = "hak"           # 客家话


class DialectAdapter(ABC):
    """方言适配器抽象基类，每种方言实现一个子类。"""

    @property
    @abstractmethod
    def dialect_code(self) -> DialectCode:
        """方言标识码。"""

    @property
    @abstractmethod
    def dialect_name(self) -> str:
        """方言中文名称，如 '粤语'、'四川话'。"""

    @abstractmethod
    def to_mandarin(self, text: str) -> str:
        """方言文本 → 普通话文本。"""

    @abstractmethod
    def from_mandarin(self, text: str) -> str:
        """普通话文本 → 方言化表达。"""

    @abstractmethod
    def get_system_prompt_addition(self) -> str:
        """返回注入 LLM system prompt 的方言角色说明。"""

    @abstractmethod
    def get_asr_config(self) -> dict:
        """返回该方言对应的 ASR 引擎配置。"""

    @abstractmethod
    def get_tts_config(self) -> dict:
        """返回该方言对应的 TTS 引擎配置。"""


class DialectRegistry:
    """方言注册表，管理所有已注册的方言适配器。"""

    _adapters: dict[DialectCode, DialectAdapter] = {}

    @classmethod
    def register(cls, adapter_class: type[DialectAdapter]):
        """装饰器：注册方言适配器。"""
        instance = adapter_class()
        cls._adapters[instance.dialect_code] = instance
        return adapter_class

    @classmethod
    def get(cls, dialect: DialectCode) -> DialectAdapter:
        """获取方言适配器，未注册时回退到普通话。"""
        if dialect not in cls._adapters:
            return cls._adapters[DialectCode.MANDARIN]
        return cls._adapters[dialect]

    @classmethod
    def available_dialects(cls) -> list[DialectCode]:
        """返回所有已注册的方言列表。"""
        return list(cls._adapters.keys())

    @classmethod
    def list_dialect_info(cls) -> list[dict]:
        """返回所有方言的名称和编码信息。"""
        return [
            {"code": a.dialect_code.value, "name": a.dialect_name}
            for a in cls._adapters.values()
        ]
