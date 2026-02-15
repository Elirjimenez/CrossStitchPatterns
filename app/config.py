from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://user:pass@localhost:5432/crossstitch"
    storage_dir: str = "storage"
    max_pattern_size: int = 500
    default_aida_count: int = 14
    app_version: str = "0.1.0"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
