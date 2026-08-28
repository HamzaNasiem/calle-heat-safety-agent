"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "sqlite+aiosqlite:///thermashift.db"

    # FortyGuard
    fortyguard_api_key: str = "489e4282aa24d9c7d074195751e3faf6"

    # CALL-E (HeyCall-E) Voice Agent
    calle_api_key: str = "iams_live_0UvYeesXBhr5GamQNqqc_b8da836ba3458377b7e17ca3dff69d76527d686f5c889839ea65c6096a0c90ec"
    calle_base_url: str = "https://api.heycall-e.com/v1"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    # App
    environment: str = "development"
    frontend_url: str = "http://localhost:5173"

    # Polling config
    default_poll_interval_minutes: int = 10
    alert_cooldown_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
