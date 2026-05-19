"""Centralised configuration loaded from environment variables and .env files."""

from pathlib import Path
from typing import Final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WP_",
        extra="ignore",
    )

    # Storage
    data_dir: Path = Field(default=Path("./data"))
    database_url: str = Field(default="sqlite:///./data/properties.db")

    # Scraper behaviour
    max_properties_per_combination: int = 500
    delay_seconds_between_combinations: int = 10
    http_max_attempts: int = 4
    http_max_concurrent: int = 5
    http_timeout_seconds: float = 30.0

    # Logging
    log_level: str = "INFO"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def clean_dir(self) -> Path:
        return self.data_dir / "clean"


settings: Final[Settings] = Settings()
