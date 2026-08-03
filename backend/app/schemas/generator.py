"""Schemas for the Phase 9 game generation API."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Template = Literal["space_shooter"]
Difficulty = Literal["easy", "medium", "hard"]


class GeneratorInterpretRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    template: Template = "space_shooter"

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Query cannot be empty after stripping whitespace.")
        return stripped


class SpaceShooterConfig(BaseModel):
    template: Template = "space_shooter"
    title: str = Field(min_length=1, max_length=80)
    theme: str = Field(min_length=1, max_length=40)
    difficulty: Difficulty = "medium"
    player_speed: int = Field(default=6, ge=3, le=10)
    enemy_speed: int = Field(default=3, ge=1, le=8)
    enemy_spawn_interval: float = Field(default=2.0, ge=0.5, le=5.0)
    lives: int = Field(default=3, ge=1, le=5)
    difficulty_scaling: bool = True


class GeneratorInterpretResponse(BaseModel):
    success: bool = True
    query: str
    template: Template
    configuration: SpaceShooterConfig
    warnings: list[str] = Field(default_factory=list)
