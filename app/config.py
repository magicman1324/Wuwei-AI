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

    # 火山引擎 BigTTS（豆包同款），主要给老年电台用
    volcano_app_id: str = ""
    volcano_access_token: str = ""
    volcano_tts_cluster: str = "volcano_tts"

    # 方言
    default_dialect: str = "cmn"
    enabled_dialects: list[str] = ["cmn", "yue", "cmn-sichuan"]

    # TTS (适老化默认值)
    tts_default_speed: float = 0.85
    tts_default_volume: float = 1.2

    # 老年电台 TTS：默认走火山 BigTTS（自然度更高、有播音腔音色）；
    # 若 volcano_* 凭据未填则自动回退到讯飞免费 xiaoyan。
    radio_tts_provider: str = "volcano"
    radio_tts_voice: str = "zh_male_yunzhou_bigtts"  # 火山·云舟，新闻主播腔

    # Redis (可选，MVP 阶段不启用)
    redis_url: str | None = None

    model_config = {"env_file": ".env", "env_prefix": "WUWEI_"}


def get_settings() -> Settings:
    return Settings()
