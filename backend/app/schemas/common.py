"""Shared response schemas."""

from typing import Any

from pydantic import BaseModel, Field, model_validator


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_items: int = Field(ge=0)
    total_pages: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def calculate_total_pages(self) -> "PaginationMeta":
        self.total_pages = 0 if self.total_items == 0 else (self.total_items + self.page_size - 1) // self.page_size
        return self


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class FacetItem(BaseModel):
    name: str
    count: int = Field(ge=0)


class FacetResponse(BaseModel):
    success: bool = True
    items: list[FacetItem]
