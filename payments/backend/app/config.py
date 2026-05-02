from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://appt:appt_secret@127.0.0.1:5433/appt_db"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"


settings = Settings()
