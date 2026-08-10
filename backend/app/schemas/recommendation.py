"""Public contracts for prompt-driven recommendations."""

from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.schemas.ai import ExtractedPreferences, NormalizedPrompt, ScoreBreakdown
from app.schemas.game import GameResponse


class RecommendationRequest(BaseModel):
    preference_text: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=10, ge=1, le=50)
    excluded_game_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def accept_prompt_alias(cls, value: Any) -> Any:
        if isinstance(value, dict) and "preference_text" not in value and "prompt" in value:
            return {**value, "preference_text": value["prompt"]}
        return value


class RecommendationItem(BaseModel):
    game: GameResponse
    score: float = Field(ge=0, le=1)
    score_breakdown: ScoreBreakdown
    explanation: str
    matched_attributes: list[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    success: bool = True
    items: list[RecommendationItem]
    normalized_prompt: NormalizedPrompt
    preferences: ExtractedPreferences
    search_id: str | None = None
