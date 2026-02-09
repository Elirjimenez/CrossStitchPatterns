from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://user:pass@localhost:5432/crossstitch"
    max_pattern_size: int = 500
    default_aida_count: int = 14
    app_version: str = "0.1.0"

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
