"""Schemas for the Phase 3 prompt interpretation endpoint."""

from pydantic import BaseModel, Field


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
