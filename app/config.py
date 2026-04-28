"""统一配置管理，基于 pydantic-settings，支持 .env 文件加载。"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用
    app_name: str = "无维AI"
    debug: bool = False
    log_level: str = "INFO"

    # 数据库
    database_url: str = "sqlite:///./data/db/wuwei.db"
    db_echo: bool = False

    # LLM
    llm_provider: str = "qwen"
    llm_api_key: str = ""
    llm_model: str = "qwen-max"
    llm_base_url: str = ""
    llm_enable_search: bool = False  # DashScope 内置联网搜索（仅 qwen 闭源模型支持）

    # 科大讯飞
    iflytek_app_id: str = ""
    iflytek_api_key: str = ""
    iflytek_api_secret: str = ""

    # 阿里云语音
    aliyun_access_key: str = ""
    aliyun_access_secret: str = ""
    aliyun_asr_app_key: str = ""

    # 方言
    default_dialect: str = "cmn"
    enabled_dialects: list[str] = ["cmn", "yue", "cmn-sichuan"]

    # TTS (适老化默认值)
    tts_default_speed: float = 0.85
    tts_default_volume: float = 1.2

    # Redis (可选，MVP 阶段不启用)
    redis_url: str | None = None

    model_config = {"env_file": ".env", "env_prefix": "WUWEI_"}


def get_settings() -> Settings:
    return Settings()
