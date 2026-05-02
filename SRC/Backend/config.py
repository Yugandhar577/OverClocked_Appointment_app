"""
Backend documentation for `config.py`.

This backend module participates in the appointment platform and is documented to make future changes safer.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Backend note: Groups related backend data or behavior for a single domain concept.
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
    enable_waitlist: bool = False
    enable_booking_cart: bool = False
    enable_variable_duration: bool = False
    enable_recurring_bookings: bool = False
    enable_no_show_protection: bool = False
    enable_smart_assignment: bool = False
    enable_dynamic_pricing: bool = False
    enable_notification_workflows: bool = False
    enable_admin_manual_booking: bool = False
    enable_appointment_analytics: bool = False
    enable_theme_customization: bool = False
    enable_odoo_style_ui: bool = False
    google_client_id: str = ""
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
@lru_cache
def get_settings() -> Settings:
    return Settings()


# Function explanation:
# `get_settings` returns a cached `Settings` instance using `functools.lru_cache`.
# Caching avoids re-parsing environment variables and recreating the settings
# object repeatedly, ensuring a single source of configuration during runtime.
#
# Alternative (commented): allow injecting a `Settings` instance explicitly
# (useful in tests) or use dependency injection via FastAPI's `Depends`.
#
# def get_settings_overridable(overrides: dict | None = None) -> Settings:
#     if overrides:
#         return Settings(**overrides)
#     return get_settings()
