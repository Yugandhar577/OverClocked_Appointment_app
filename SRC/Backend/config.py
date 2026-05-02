from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "OverClocked Appointment App"
    env: str = "dev"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/appointments"
    jwt_secret: str = Field(default="change-me-to-a-32-character-minimum-secret")
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_seconds: int = 28_800
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from: str = "noreply@appointments.local"
    app_base_url: str = "http://localhost:5173"
    frontend_origin: str = "http://localhost:5173"
    future_days_limit_default: int = 30
    otp_ttl_seconds: int = 600
    reset_token_ttl_seconds: int = 900


@lru_cache
def get_settings() -> Settings:
    return Settings()
