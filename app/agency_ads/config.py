"""Runtime configuration loaded from environment.

Use `from agency_ads.config import settings` from any module.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    database_url: str
    redis_url: str

    api_base_url: str = "http://localhost:8000"
    web_base_url: str = "http://localhost:3000"
    session_secret: str = Field(default="dev-only-not-for-production")

    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""

    google_ads_developer_token: str = ""
    google_ads_client_id: str = ""
    google_ads_client_secret: str = ""
    google_ads_login_customer_id: str = ""

    anthropic_api_key: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
