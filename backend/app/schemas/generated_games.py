"""Generated-game persistence and sharing contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.ai import GameConfiguration

GameTemplate = Literal["space_shooter", "endless_runner", "maze_escape"]
CURRENT_CONFIG_VERSION = "1.1"


class GeneratedGameCreate(BaseModel):
    title: str = Field(min_length=1, max_length=60)
    prompt: str = Field(min_length=1, max_length=2000)
    template_type: GameTemplate
    configuration: dict[str, Any]
    config_version: str = Field(default=CURRENT_CONFIG_VERSION, min_length=1, max_length=16)


class GeneratedGameUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=60)
    prompt: str | None = Field(default=None, min_length=1, max_length=2000)
    template_type: GameTemplate | None = None
    configuration: dict[str, Any] | None = None
    config_version: str | None = Field(default=None, min_length=1, max_length=16)

    @model_validator(mode="after")
    def require_change(self) -> "GeneratedGameUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one generated-game field must be supplied.")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Generated-game update fields cannot be null.")
        return self


class GeneratedGameResponse(BaseModel):
    id: str
    title: str
    prompt: str
    template_type: GameTemplate
    configuration: GameConfiguration
    config_version: str
    migrated_from_version: str | None = None
    public_slug: str | None
    is_public: bool
    created_at: datetime
    updated_at: datetime


class GeneratedGameEnvelope(BaseModel):
    success: bool = True
    item: GeneratedGameResponse


class GeneratedGameListResponse(BaseModel):
    success: bool = True
    items: list[GeneratedGameResponse]


class GeneratedGameDeleteResponse(BaseModel):
    success: bool = True
    deleted_id: str


class PublicGeneratedGameResponse(BaseModel):
    title: str
    template_type: GameTemplate
    configuration: GameConfiguration
    config_version: str
    migrated_from_version: str | None = None
    public_slug: str
    created_at: datetime
    updated_at: datetime


class PublicGeneratedGameEnvelope(BaseModel):
    success: bool = True
    item: PublicGeneratedGameResponse
