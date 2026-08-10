"""User search-history, favourite, and recommendation-feedback contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.game import GameResponse

FeedbackType = Literal["relevant", "not_relevant", "interested", "already_played"]


class SearchHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query: str
    extracted_preferences: dict[str, Any]
    result_count: int = Field(ge=0)
    processing_time_ms: float = Field(ge=0)
    created_at: datetime


class SearchHistoryListResponse(BaseModel):
    success: bool = True
    items: list[SearchHistoryResponse]


class SearchHistorySingleResponse(BaseModel):
    success: bool = True
    item: SearchHistoryResponse


class DeleteActivityResponse(BaseModel):
    success: bool = True
    deleted_count: int = Field(default=0, ge=0)


class FavouriteResponse(BaseModel):
    id: str
    game_id: str
    created_at: datetime
    game: GameResponse


class FavouriteListResponse(BaseModel):
    success: bool = True
    items: list[FavouriteResponse]


class FavouriteMutationResponse(BaseModel):
    success: bool = True
    created: bool
    item: FavouriteResponse


class FeedbackCreateRequest(BaseModel):
    game_id: str = Field(min_length=1, max_length=128)
    search_id: str | None = Field(default=None, min_length=1, max_length=36)
    feedback_type: FeedbackType


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    game_id: str
    search_id: str | None
    feedback_type: FeedbackType
    created_at: datetime


class FeedbackSingleResponse(BaseModel):
    success: bool = True
    item: FeedbackResponse


class FeedbackListResponse(BaseModel):
    success: bool = True
    items: list[FeedbackResponse]
