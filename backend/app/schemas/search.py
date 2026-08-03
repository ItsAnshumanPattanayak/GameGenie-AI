"""Schemas for the Phase 3 prompt interpretation and Phase 5 recommendation APIs."""

from pydantic import BaseModel, Field, field_validator

from app.schemas.game import GameResponse


class InterpretRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)


class ParsedPreferencesResponse(BaseModel):
    genres: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    free_text: str = ""


class InterpretResponse(BaseModel):
    success: bool = True
    query: str
    preferences: ParsedPreferencesResponse


class RecommendFilters(BaseModel):
    platforms: list[str] | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    price_category: str | None = None
    min_rating: float | None = Field(default=None, ge=0, le=5)


class RecommendRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    limit: int = Field(default=10, ge=1, le=20)
    filters: RecommendFilters | None = None

    @field_validator("query")
    @classmethod
    def strip_query(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 3:
            raise ValueError("Query must contain at least 3 non-whitespace characters.")
        return stripped


class ScoreBreakdown(BaseModel):
    semantic: float = Field(default=0.0, ge=0, le=1)
    genre: float = Field(default=0.0, ge=0, le=1)
    platform: float = Field(default=0.0, ge=0, le=1)
    tag: float = Field(default=0.0, ge=0, le=1)
    rating: float = Field(default=0.0, ge=0, le=1)
    final: float = Field(default=0.0, ge=0, le=1)


class RecommendationItem(BaseModel):
    rank: int = Field(ge=1)
    game: GameResponse
    scores: ScoreBreakdown
    explanation: str


class RecommendResponse(BaseModel):
    success: bool = True
    query: str
    preferences: ParsedPreferencesResponse
    items: list[RecommendationItem]
    result_count: int = Field(ge=0)
    processing_time_ms: float = Field(ge=0)
