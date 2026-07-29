"""Database-independent, strongly validated game schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from app.schemas.common import PaginationMeta

PriceCategory = Literal["free", "budget", "mid-range", "premium", "unknown"]


class GameBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=250)
    normalized_title: str = ""
    slug: str = ""
    description: str | None = None
    short_description: str | None = None
    genres: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    developer: str | None = None
    publisher: str | None = None
    release_date: date | None = None
    release_year: int | None = Field(default=None, ge=1950, le=2100)
    rating: float | None = Field(default=None, ge=0, le=5)
    rating_count: int | None = Field(default=None, ge=0)
    popularity: float | None = Field(default=None, ge=0)
    tags: list[str] = Field(default_factory=list)
    multiplayer: bool | None = None
    online_multiplayer: bool | None = None
    single_player: bool | None = None
    age_rating: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    price_category: PriceCategory = "unknown"
    image_url: HttpUrl | None = None
    website_url: HttpUrl | None = None
    minimum_requirements: str | None = None
    recommended_requirements: str | None = None
    source: str | None = None
    source_id: str | None = None

    @field_validator(
        "description",
        "short_description",
        "developer",
        "publisher",
        "age_rating",
        "currency",
        "minimum_requirements",
        "recommended_requirements",
        "source",
        "source_id",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def derive_year(self) -> "GameBase":
        if self.release_date and self.release_year is None:
            self.release_year = self.release_date.year
        return self


class GameCreate(GameBase):
    id: str | None = None


class GameUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    description: str | None = None
    genres: list[str] | None = None
    platforms: list[str] | None = None
    developer: str | None = None
    publisher: str | None = None
    release_date: date | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    price: Decimal | None = Field(default=None, ge=0)


class GameResponse(GameBase):
    id: str = Field(min_length=1)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GameListResponse(BaseModel):
    success: bool = True
    items: list[GameResponse]
    pagination: PaginationMeta


class GameSingleResponse(BaseModel):
    success: bool = True
    item: GameResponse


class GameSearchFilters(BaseModel):
    genre: str | None = None
    platform: str | None = None
    developer: str | None = None
    publisher: str | None = None
    release_year: int | None = Field(default=None, ge=1950, le=2100)
    min_rating: float | None = Field(default=None, ge=0, le=5)
    multiplayer: bool | None = None
    single_player: bool | None = None
    tag: str | None = None
    price_category: PriceCategory | None = None
