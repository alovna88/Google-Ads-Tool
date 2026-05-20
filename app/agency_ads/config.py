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

    # Comma-separated email allowlist for staff login.
    # `auth_allowed_email_domains` is the common case: "yourshop.com".
    # `auth_allowed_emails` is for individual exceptions (contractors, etc.).
    # If BOTH are empty AND environment != production, any Google account
    # can log in — convenient for dev. In production both empty means
    # nobody can log in (fail closed).
    auth_allowed_email_domains: str = ""
    auth_allowed_emails: str = ""
    auth_session_max_age_hours: int = 24 * 7  # 1 week

    google_ads_developer_token: str = ""
    google_ads_client_id: str = ""
    google_ads_client_secret: str = ""
    google_ads_login_customer_id: str = ""

    # LinkedIn Marketing API. Create an app at
    # https://www.linkedin.com/developers/apps and add the
    # "Advertising API" product (requires approval). Scopes used:
    # r_ads (read campaigns), r_ads_reporting (analytics), rw_ads
    # (mutations — leave off until write features ship). Refresh
    # tokens require the "Marketing Developer Platform" tier.
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_oauth_scopes: str = "r_ads,r_ads_reporting,r_basicprofile"
    # Versioned LinkedIn REST API header. Format YYYYMM. Bump every
    # few months; LinkedIn rolls older versions off on a known cadence.
    linkedin_api_version: str = "202405"
    # Refresh tokens with less than this many seconds left until expiry
    # get rotated by the background job.
    linkedin_refresh_skew_seconds: int = 7 * 24 * 3600

    # Static bearer token used by trusted local processes (the LinkedIn
    # MCP server, ops scripts) to call /linkedin/mcp/* without a user
    # session. Empty disables that auth path entirely — recommended in
    # production unless the MCP runs in the same network as the API.
    agency_service_token: str = ""

    anthropic_api_key: str = ""

    @property
    def linkedin_scopes(self) -> list[str]:
        return [s.strip() for s in self.linkedin_oauth_scopes.split(",") if s.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def allowed_email_domains(self) -> list[str]:
        return [d.strip().lower() for d in self.auth_allowed_email_domains.split(",") if d.strip()]

    @property
    def allowed_emails(self) -> list[str]:
        return [e.strip().lower() for e in self.auth_allowed_emails.split(",") if e.strip()]

    def is_email_allowed(self, email: str) -> bool:
        email = email.strip().lower()
        domains = self.allowed_email_domains
        emails = self.allowed_emails
        if not domains and not emails:
            return not self.is_production
        if email in emails:
            return True
        try:
            return email.split("@", 1)[1] in domains
        except IndexError:
            return False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
