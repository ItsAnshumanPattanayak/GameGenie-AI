"""Contracts reserved for the Phase 3 recommendation engine."""

from pydantic import BaseModel, Field

from app.schemas.game import GameResponse


class RecommendationRequest(BaseModel):
    preference_text: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=10, ge=1, le=50)
    excluded_game_ids: list[str] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    game: GameResponse
    score: float = Field(ge=0, le=1)
    explanation: str


class RecommendationResponse(BaseModel):
    success: bool = True
    items: list[RecommendationItem]
