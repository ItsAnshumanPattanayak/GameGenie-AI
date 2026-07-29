from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, Request

from app.api.dependencies import get_game_service
from app.core.exceptions import AppError
from app.schemas.game import GameListResponse, GameSearchFilters, GameSingleResponse
from app.services.game_service import GameService

router = APIRouter(prefix="/games", tags=["games"])


def filters_from_query(
    genre: str | None = None,
    platform: str | None = None,
    developer: str | None = None,
    publisher: str | None = None,
    release_year: int | None = Query(default=None, ge=1950, le=2100),
    min_rating: float | None = Query(default=None, ge=0, le=5),
    multiplayer: bool | None = None,
    single_player: bool | None = None,
    tag: str | None = None,
    price_category: Literal["free", "budget", "mid-range", "premium", "unknown"] | None = None,
) -> GameSearchFilters:
    return GameSearchFilters(
        genre=genre,
        platform=platform,
        developer=developer,
        publisher=publisher,
        release_year=release_year,
        min_rating=min_rating,
        multiplayer=multiplayer,
        single_player=single_player,
        tag=tag,
        price_category=price_category,
    )


FiltersDep = Annotated[GameSearchFilters, Depends(filters_from_query)]
ServiceDep = Annotated[GameService, Depends(get_game_service)]


def pagination_from_query(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int | None = Query(default=None, ge=1),
) -> tuple[int, int]:
    settings = request.app.state.settings
    effective_size = page_size or settings.default_page_size
    if effective_size > settings.max_page_size:
        raise AppError("INVALID_PAGE_SIZE", f"Page size cannot exceed {settings.max_page_size}.", 422)
    return page, effective_size


PaginationDep = Annotated[tuple[int, int], Depends(pagination_from_query)]


@router.get("/search", response_model=GameListResponse)
def search_games(
    filters: FiltersDep,
    service: ServiceDep,
    pagination: PaginationDep,
    q: str = Query(min_length=1, max_length=200),
) -> GameListResponse:
    if not q.strip():
        raise AppError("INVALID_QUERY", "Search query cannot be empty.", 400)
    page, page_size = pagination
    items, pagination_meta = service.search(q, page=page, page_size=page_size, filters=filters)
    return GameListResponse(items=items, pagination=pagination_meta)


@router.get("", response_model=GameListResponse)
def list_games(
    filters: FiltersDep,
    service: ServiceDep,
    pagination: PaginationDep,
    sort_by: Literal["title", "release_year", "rating", "popularity", "price"] = "title",
    sort_direction: Literal["asc", "desc"] = "asc",
) -> GameListResponse:
    page, page_size = pagination
    items, pagination_meta = service.list_games(
        page=page, page_size=page_size, sort_by=sort_by, sort_direction=sort_direction, filters=filters
    )
    return GameListResponse(items=items, pagination=pagination_meta)


@router.get("/{game_id}", response_model=GameSingleResponse)
def get_game(
    service: ServiceDep,
    game_id: str = Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"),
) -> GameSingleResponse:
    return GameSingleResponse(item=service.get(game_id))
