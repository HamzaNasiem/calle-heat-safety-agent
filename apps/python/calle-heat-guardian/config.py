"""Configuration loader for CALL-E Heat Guardian."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    calle_api_key: str = "iams_live_0UvYeesXBhr5GamQNqqc_b8da836ba3458377b7e17ca3dff69d76527d686f5c889839ea65c6096a0c90ec"
    calle_base_url: str = "https://api.heycall-e.com/v1"
    default_test_phone: str = "+923172532350"
    port: int = 8000
    host: str = "0.0.0.0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
