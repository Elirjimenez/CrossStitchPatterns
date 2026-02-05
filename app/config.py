from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    max_pattern_size: int = 500
    default_aida_count: int = 14

    class Config:
        env_file = ".env"


settings = Settings()