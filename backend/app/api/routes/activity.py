"""Ownership-scoped search history, favourites, and recommendation feedback."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUserDep, DbDep, get_game_service
from app.core.exceptions import AppError
from app.db.models import FavouriteGame, RecommendationFeedback, SearchHistory
from app.schemas.activity import (
    DeleteActivityResponse,
    FavouriteListResponse,
    FavouriteMutationResponse,
    FavouriteResponse,
    FeedbackCreateRequest,
    FeedbackListResponse,
    FeedbackResponse,
    FeedbackSingleResponse,
    SearchHistoryListResponse,
    SearchHistoryResponse,
    SearchHistorySingleResponse,
)
from app.services.game_service import GameService

router = APIRouter(tags=["user activity"])
CatalogueDep = Annotated[GameService, Depends(get_game_service)]


def _owned_search(db: DbDep, user_id: str, search_id: str) -> SearchHistory:
    history = db.scalar(select(SearchHistory).where(SearchHistory.id == search_id, SearchHistory.user_id == user_id))
    if history is None:
        raise AppError("SEARCH_HISTORY_NOT_FOUND", "The search-history entry was not found.", 404)
    return history


@router.get("/history/searches", response_model=SearchHistoryListResponse)
def list_searches(
    user: CurrentUserDep,
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=100),
) -> SearchHistoryListResponse:
    items = db.scalars(
        select(SearchHistory)
        .where(SearchHistory.user_id == user.id)
        .order_by(SearchHistory.created_at.desc(), SearchHistory.id.desc())
        .limit(limit)
    ).all()
    return SearchHistoryListResponse(items=[SearchHistoryResponse.model_validate(item) for item in items])


@router.get("/history/searches/{search_id}", response_model=SearchHistorySingleResponse)
def get_search(search_id: str, user: CurrentUserDep, db: DbDep) -> SearchHistorySingleResponse:
    return SearchHistorySingleResponse(item=SearchHistoryResponse.model_validate(_owned_search(db, user.id, search_id)))


@router.delete("/history/searches/{search_id}", response_model=DeleteActivityResponse)
def delete_search(search_id: str, user: CurrentUserDep, db: DbDep) -> DeleteActivityResponse:
    db.delete(_owned_search(db, user.id, search_id))
    db.commit()
    return DeleteActivityResponse(deleted_count=1)


@router.delete("/history/searches", response_model=DeleteActivityResponse)
def delete_all_searches(user: CurrentUserDep, db: DbDep) -> DeleteActivityResponse:
    search_ids = db.scalars(select(SearchHistory.id).where(SearchHistory.user_id == user.id)).all()
    db.execute(delete(SearchHistory).where(SearchHistory.user_id == user.id))
    db.commit()
    return DeleteActivityResponse(deleted_count=len(search_ids))


def _favourite_response(favourite: FavouriteGame, catalogue: GameService) -> FavouriteResponse:
    return FavouriteResponse(
        id=favourite.id,
        game_id=favourite.game_id,
        created_at=favourite.created_at,
        game=catalogue.get(favourite.game_id),
    )


@router.get("/favourites", response_model=FavouriteListResponse)
def list_favourites(user: CurrentUserDep, db: DbDep, catalogue: CatalogueDep) -> FavouriteListResponse:
    rows = db.scalars(
        select(FavouriteGame)
        .where(FavouriteGame.user_id == user.id)
        .order_by(FavouriteGame.created_at.desc(), FavouriteGame.id.desc())
    ).all()
    games = {game.id: game for game in catalogue.all()}
    return FavouriteListResponse(
        items=[
            FavouriteResponse(id=row.id, game_id=row.game_id, created_at=row.created_at, game=games[row.game_id])
            for row in rows
            if row.game_id in games
        ]
    )


@router.post("/favourites/{game_id}", response_model=FavouriteMutationResponse)
def add_favourite(game_id: str, user: CurrentUserDep, db: DbDep, catalogue: CatalogueDep) -> FavouriteMutationResponse:
    catalogue.get(game_id)
    existing = db.scalar(
        select(FavouriteGame).where(FavouriteGame.user_id == user.id, FavouriteGame.game_id == game_id)
    )
    if existing is not None:
        return FavouriteMutationResponse(created=False, item=_favourite_response(existing, catalogue))
    favourite = FavouriteGame(user_id=user.id, game_id=game_id)
    db.add(favourite)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(FavouriteGame).where(FavouriteGame.user_id == user.id, FavouriteGame.game_id == game_id)
        )
        if existing is None:
            raise
        return FavouriteMutationResponse(created=False, item=_favourite_response(existing, catalogue))
    db.refresh(favourite)
    return FavouriteMutationResponse(created=True, item=_favourite_response(favourite, catalogue))


@router.delete("/favourites/{game_id}", response_model=DeleteActivityResponse)
def remove_favourite(game_id: str, user: CurrentUserDep, db: DbDep) -> DeleteActivityResponse:
    favourite = db.scalar(
        select(FavouriteGame).where(FavouriteGame.user_id == user.id, FavouriteGame.game_id == game_id)
    )
    if favourite is None:
        raise AppError("FAVOURITE_NOT_FOUND", "The favourite game was not found.", 404)
    db.delete(favourite)
    db.commit()
    return DeleteActivityResponse(deleted_count=1)


@router.post("/feedback", response_model=FeedbackSingleResponse, status_code=201)
def create_feedback(
    payload: FeedbackCreateRequest,
    user: CurrentUserDep,
    db: DbDep,
    catalogue: CatalogueDep,
) -> FeedbackSingleResponse:
    catalogue.get(payload.game_id)
    if payload.search_id is not None:
        _owned_search(db, user.id, payload.search_id)
    feedback = RecommendationFeedback(user_id=user.id, **payload.model_dump())
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return FeedbackSingleResponse(item=FeedbackResponse.model_validate(feedback))


@router.get("/feedback", response_model=FeedbackListResponse)
def list_feedback(
    user: CurrentUserDep,
    db: DbDep,
    limit: int = Query(default=100, ge=1, le=200),
) -> FeedbackListResponse:
    items = db.scalars(
        select(RecommendationFeedback)
        .where(RecommendationFeedback.user_id == user.id)
        .order_by(RecommendationFeedback.created_at.desc(), RecommendationFeedback.id.desc())
        .limit(limit)
    ).all()
    return FeedbackListResponse(items=[FeedbackResponse.model_validate(item) for item in items])
