"""Application configuration — reads from .env file."""

from __future__ import annotations

import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Core ──────────────────────────────────────────────────────────────────
    project_name: str = "Aurevia API"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./aurevia.db"

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: str = '["http://localhost:3000","null"]'

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            return json.loads(self.cors_origins)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000"]

    # ── Security ──────────────────────────────────────────────────────────────
    secret_key: str = "change-this-in-production"


# Singleton settings instance used throughout the app
settings = Settings()
