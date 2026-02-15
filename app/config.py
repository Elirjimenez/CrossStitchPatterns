from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:pass@localhost:5432/crossstitch"

    # File Storage
    storage_dir: str = "storage"
    max_filename_length: int = 255  # Maximum filename length for filesystem compatibility
    allowed_file_extensions: str = ".png,.jpg,.jpeg,.pdf"  # Comma-separated allowed extensions

    # Pattern Generation
    max_pattern_size: int = 500
    default_aida_count: int = 14

    # Application
    app_version: str = "0.1.0"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
