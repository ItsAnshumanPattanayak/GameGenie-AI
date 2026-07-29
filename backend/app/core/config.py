"""Environment-driven application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings with safe local-development defaults."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env", env_file_encoding="utf-8", extra="ignore", enable_decoding=False
    )

    app_name: str = "GameGenie AI Backend"
    app_env: str = "development"
    app_version: str = "1.0.0"
    debug: bool = False
    api_prefix: str = "/api"
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    raw_dataset_path: Path = Path("data/raw/games.json")
    processed_dataset_path: Path = Path("data/processed/games.json")
    log_level: str = "INFO"
    default_page_size: int = Field(default=20, ge=1, le=100)
    max_page_size: int = Field(default=100, ge=1, le=500)

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("api_prefix")
    @classmethod
    def normalize_prefix(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith("/"):
            value = f"/{value}"
        return value.rstrip("/")

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    def resolve_data_path(self, path: Path) -> Path:
        """Resolve a configured path and refuse paths outside the backend root."""
        candidate = path if path.is_absolute() else BACKEND_ROOT / path
        resolved = candidate.resolve()
        try:
            resolved.relative_to(BACKEND_ROOT.resolve())
        except ValueError as exc:
            raise ValueError("Dataset paths must stay inside the backend directory") from exc
        return resolved

    @property
    def raw_data_path(self) -> Path:
        return self.resolve_data_path(self.raw_dataset_path)

    @property
    def processed_data_path(self) -> Path:
        return self.resolve_data_path(self.processed_dataset_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()
