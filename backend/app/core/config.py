"""Environment-driven application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator, model_validator
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
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    raw_dataset_path: Path = Path("data/raw/games.json")
    processed_dataset_path: Path = Path("data/processed/games.json")
    log_level: str = "INFO"
    default_page_size: int = Field(default=20, ge=1, le=100)
    max_page_size: int = Field(default=100, ge=1, le=500)
    database_url: str = "sqlite:///data/gamegenie.db"
    auth_secret_key: SecretStr | None = None
    access_token_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_days: int = Field(default=30, ge=1, le=365)
    personalisation_base_weight: float = Field(default=0.80, ge=0, le=1)
    personalisation_explicit_weight: float = Field(default=0.10, ge=0, le=1)
    personalisation_favourite_weight: float = Field(default=0.04, ge=0, le=1)
    personalisation_feedback_weight: float = Field(default=0.04, ge=0, le=1)
    personalisation_recent_search_weight: float = Field(default=0.02, ge=0, le=1)
    personalisation_total_cap: float = Field(default=0.20, ge=0, le=1)
    personalisation_prompt_overlap_factor: float = Field(default=0.25, ge=0, le=1)

    @model_validator(mode="after")
    def validate_personalisation_weights(self) -> Settings:
        total = (
            self.personalisation_base_weight
            + self.personalisation_explicit_weight
            + self.personalisation_favourite_weight
            + self.personalisation_feedback_weight
            + self.personalisation_recent_search_weight
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError("personalisation component weights must sum to one")
        return self

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
