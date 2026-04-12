"""LLM 工厂：按配置创建对应的 LLM 适配器实例。"""

from app.chat.llm.base import BaseLLM


class LLMFactory:
    _registry: dict[str, type[BaseLLM]] = {}

    @classmethod
    def register(cls, name: str):
        """装饰器：注册 LLM 适配器。"""

        def decorator(llm_class: type[BaseLLM]):
            cls._registry[name] = llm_class
            return llm_class

        return decorator

    @classmethod
    def create(cls, provider: str, **kwargs) -> BaseLLM:
        """按提供商名称创建 LLM 实例。"""
        if provider not in cls._registry:
            raise ValueError(
                f"不支持的 LLM 提供商: {provider}，"
                f"可选: {list(cls._registry.keys())}"
            )
        return cls._registry[provider](**kwargs)

    @classmethod
    def available_providers(cls) -> list[str]:
        return list(cls._registry.keys())


# 注册内置适配器
def _register_builtin():
    from app.chat.llm.mock import MockLLM
    from app.chat.llm.qwen import QwenLLM

    LLMFactory.register("qwen")(QwenLLM)
    LLMFactory.register("mock")(MockLLM)


_register_builtin()
