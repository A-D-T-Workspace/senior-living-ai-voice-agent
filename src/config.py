from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SeniorLiving AI"
    app_env: Literal["development", "testing", "production"] = "development"
    debug: bool = True

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""

    whisper_model: str = "base"
    piper_voice: str = ""

    database_url: str = "sqlite:///./senior_living.db"

    calendly_access_token: str = ""
    calendly_event_type_uri: str = ""

    google_sheets_id: str = ""
    google_service_account_file: str = ""

    secret_key: str = "development-only-change-me"

@lru_cache
def get_settings() -> Settings:
    return Settings()