"""
配置管理 - 从 .env 文件读取环境变量
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 现有的配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:chang@localhost:5432/sleepmind"
    DEBUG: bool = True

    # --- 数据库 ---
    sync_database_url: str = "postgresql+psycopg2://postgres:chang@localhost:5432/sleepmind"
    secret_key: str = "sleepmind-dev-secret-key-2026"

    # --- AIHubMix LLM ---
    OPENAI_API_BASE: str = "https://aihubmix.com/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # 允许 .env 中存在类中没定义的额外变量，防止以后增加配置又报错
        extra = "ignore" 


settings = Settings()