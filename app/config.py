from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_key: str = "dev-secret-change-me"
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60
    hevy_api_key: str = ""
    leetcode_username: str = ""
    cache_ttl_seconds: int = 300
    app_name: str = "locked-in"


@lru_cache
def get_settings() -> Settings:
    return Settings()
