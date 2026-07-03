from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_service_key: str


    supabase_anon_key: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None

    encryption_key: str

    env: str = "development"
    cors_origins: str = "http://localhost:5173"

    resend_api_key: Optional[str] = None
    resend_from: str = "Cadence <onboarding@resend.dev>"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
