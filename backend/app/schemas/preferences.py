"""Controlled user-preference contracts aligned with the AI taxonomy."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.ai.taxonomy import TAXONOMY
from app.schemas.ai import ExtractedPreferences

Difficulty = Literal["easy", "medium", "hard"]
PricePreference = Literal["free", "paid"]
HardwareLevel = Literal["low-end", "mid-range", "high-end"]


class PreferenceValues(BaseModel):
    preferred_genres: list[str] = Field(default_factory=list)
    preferred_platforms: list[str] = Field(default_factory=list)
    preferred_modes: list[str] = Field(default_factory=list)
    preferred_moods: list[str] = Field(default_factory=list)
    preferred_difficulty: Difficulty | None = None
    price_preference: PricePreference | None = None
    hardware_level: HardwareLevel | None = None

    @field_validator("preferred_genres", "preferred_platforms", "preferred_modes", "preferred_moods")
    @classmethod
    def validate_taxonomy_list(cls, value: list[str], info: ValidationInfo) -> list[str]:
        field_name = info.field_name
        assert field_name is not None
        category = {
            "preferred_genres": "genres",
            "preferred_platforms": "platforms",
            "preferred_modes": "modes",
            "preferred_moods": "moods",
        }[field_name]
        allowed = TAXONOMY[category]
        requested = {item.casefold() for item in value}
        unknown = [item for item in value if item.casefold() not in {candidate.casefold() for candidate in allowed}]
        if unknown:
            raise ValueError(f"unsupported {category}: {', '.join(unknown)}")
        return [item for item in allowed if item.casefold() in requested]

    def to_ai_preferences(self) -> ExtractedPreferences:
        """Return the normalized shape consumed by the existing ranking layer."""
        return ExtractedPreferences(
            genres=tuple(self.preferred_genres),
            platforms=tuple(self.preferred_platforms),
            modes=tuple(self.preferred_modes),
            moods=tuple(self.preferred_moods),
            difficulty=self.preferred_difficulty,
            price_type=self.price_preference,
            hardware_level=self.hardware_level,
        )


class PreferenceUpdate(PreferenceValues):
    pass


class UserPreferenceResponse(PreferenceValues):
    user_id: str
    updated_at: datetime


class PreferenceEnvelope(BaseModel):
    success: bool = True
    preferences: UserPreferenceResponse
