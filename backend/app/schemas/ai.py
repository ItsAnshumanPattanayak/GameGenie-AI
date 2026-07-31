"""Typed API-neutral contracts shared by GameGenie's AI services."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AIWarning(BaseModel):
    code: str
    message: str
    fields: list[str] = Field(default_factory=list)


class MatchedTerm(BaseModel):
    source: str
    canonical: str
    category: str | None = None


class NormalizedPrompt(BaseModel):
    original: str
    normalized: str
    tokens: list[str] = Field(default_factory=list)
    matched_phrases: list[MatchedTerm] = Field(default_factory=list)
    unmatched_tokens: list[str] = Field(default_factory=list)


class ExtractedPreferences(BaseModel):
    model_config = ConfigDict(frozen=True)

    genres: tuple[str, ...] = ()
    platforms: tuple[str, ...] = ()
    modes: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    themes: tuple[str, ...] = ()
    moods: tuple[str, ...] = ()
    visual_styles: tuple[str, ...] = ()
    difficulty: str | None = None
    price_type: str | None = None
    hardware_level: str | None = None
    session_length: int | None = Field(default=None, ge=1, description="Requested session length in minutes")
    player_count: int | None = Field(default=None, ge=1, le=100)
    hard_filters: tuple[str, ...] = ()
    warnings: tuple[AIWarning, ...] = ()
    matched_terms: tuple[MatchedTerm, ...] = ()
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    free_text: str = ""


class InterpretRequest(BaseModel):
    prompt: str | None = Field(max_length=2000)
    query: str | None = Field(default=None, min_length=3, max_length=500)

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_query(cls, value: Any) -> Any:
        if isinstance(value, dict) and "prompt" not in value and "query" in value:
            return {**value, "prompt": value["query"]}
        return value


class InterpretationResponse(BaseModel):
    success: bool = True
    query: str | None = None
    prompt: NormalizedPrompt
    preferences: ExtractedPreferences


class SemanticCandidate(BaseModel):
    game_id: str
    semantic_score: float = Field(ge=0.0, le=1.0)


class ScoreBreakdown(BaseModel):
    semantic_score: float = Field(ge=0.0, le=1.0)
    genre_score: float = Field(ge=0.0, le=1.0)
    platform_score: float = Field(ge=0.0, le=1.0)
    mode_score: float = Field(ge=0.0, le=1.0)
    theme_score: float = Field(ge=0.0, le=1.0)
    mood_score: float = Field(ge=0.0, le=1.0)
    price_score: float = Field(ge=0.0, le=1.0)
    difficulty_score: float = Field(ge=0.0, le=1.0)
    hardware_score: float = Field(ge=0.0, le=1.0)
    final_score: float = Field(ge=0.0, le=1.0)


class TemplateSelection(BaseModel):
    template: Literal["space_shooter"] | None = None
    supported: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str


class GameConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template: Literal["space_shooter"] = "space_shooter"
    title: str = Field(default="Star Defender", min_length=1, max_length=60)
    theme: str = "space"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    player_speed: int = Field(default=7, ge=3, le=10)
    enemy_speed: int = Field(default=4, ge=1, le=8)
    enemy_spawn_interval: float = Field(default=2.0, ge=0.5, le=5.0)
    lives: int = Field(default=3, ge=1, le=5)
    difficulty_scaling: bool = False

    @field_validator("title")
    @classmethod
    def safe_title(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if any(char in cleaned for char in "<>`{}[];\\"):
            raise ValueError("title contains unsafe characters")
        return cleaned


class GeneratorRequest(BaseModel):
    prompt: str | None = Field(default=None, max_length=2000)
    selected_game_id: str | None = None
    overrides: dict[str, object] = Field(default_factory=dict)


class GeneratorResponse(BaseModel):
    success: bool
    selection: TemplateSelection
    configuration: GameConfiguration | None = None
    warnings: list[AIWarning] = Field(default_factory=list)
