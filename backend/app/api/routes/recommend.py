"""Phase 5 — Recommendation API."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.preference_parser import KeywordPreferenceParser, ParsedPreferences
from app.api.dependencies import get_game_service, get_history_service, get_preference_parser
from app.schemas.game import GameResponse
from app.schemas.search import (
    ParsedPreferencesResponse,
    RecommendationItem,
    RecommendRequest,
    RecommendResponse,
    ScoreBreakdown,
)
from app.services.game_service import GameService
from app.services.history_service import HistoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

ParserDep = Annotated[KeywordPreferenceParser, Depends(get_preference_parser)]
GameServiceDep = Annotated[GameService, Depends(get_game_service)]
HistoryDep = Annotated[HistoryService, Depends(get_history_service)]


@router.post("/recommend", response_model=RecommendResponse)
def recommend(
    payload: RecommendRequest,
    parser: ParserDep,
    service: GameServiceDep,
    history: HistoryDep,
) -> RecommendResponse:
    start = time.perf_counter()
    parsed = parser.parse(payload.query)

    candidates = _apply_hard_filters(service, payload)
    ranked = _rank_candidates(candidates, parsed)[: payload.limit]

    items = [
        RecommendationItem(
            rank=index,
            game=game,
            scores=scores,
            explanation=_explain(game, scores, parsed),
        )
        for index, (game, scores) in enumerate(ranked, start=1)
    ]

    elapsed_ms = (time.perf_counter() - start) * 1000

    preferences_response = ParsedPreferencesResponse(
        genres=list(parsed.genres),
        platforms=list(parsed.platforms),
        tags=list(parsed.tags),
        free_text=parsed.free_text,
    )

    history.record(
        query=payload.query,
        preferences=preferences_response.model_dump(),
        result_count=len(items),
        processing_time_ms=elapsed_ms,
    )

    logger.info(
        "Recommendation query='%s' results=%d time_ms=%.2f",
        payload.query,
        len(items),
        elapsed_ms,
    )

    return RecommendResponse(
        query=payload.query,
        preferences=preferences_response,
        items=items,
        result_count=len(items),
        processing_time_ms=round(elapsed_ms, 3),
    )


def _apply_hard_filters(service: GameService, payload: RecommendRequest) -> list[GameResponse]:
    page_size = service.count or 1
    catalogue, _ = service.list_games(page=1, page_size=page_size)
    if not payload.filters:
        return list(catalogue)

    filters = payload.filters

    def matches(game: GameResponse) -> bool:
        if filters.platforms and not _has_any(game.platforms, filters.platforms):
            return False
        if filters.genres and not _has_any(game.genres, filters.genres):
            return False
        if filters.tags and not _has_any(game.tags, filters.tags):
            return False
        if filters.price_category and game.price_category != filters.price_category:
            return False
        if filters.min_rating is not None and (game.rating is None or game.rating < filters.min_rating):
            return False
        return True

    return [game for game in catalogue if matches(game)]


def _has_any(actual: list[str], requested: list[str]) -> bool:
    actual_set = {value.casefold() for value in actual}
    return any(value.casefold() in actual_set for value in requested)


def _rank_candidates(
    candidates: list[GameResponse], preferences: ParsedPreferences
) -> list[tuple[GameResponse, ScoreBreakdown]]:
    scored: list[tuple[GameResponse, ScoreBreakdown]] = []
    for game in candidates:
        scores = _score(game, preferences)
        if scores.final > 0:
            scored.append((game, scores))
    scored.sort(key=lambda pair: pair[1].final, reverse=True)
    return scored


def _score(game: GameResponse, preferences: ParsedPreferences) -> ScoreBreakdown:
    genre_score = _overlap(game.genres, preferences.genres)
    platform_score = _overlap(game.platforms, preferences.platforms)
    tag_score = _overlap(game.tags, preferences.tags)
    rating_score = (game.rating or 0.0) / 5.0

    weights = {"genre": 0.40, "platform": 0.20, "tag": 0.25, "rating": 0.15}
    final = (
        weights["genre"] * genre_score
        + weights["platform"] * platform_score
        + weights["tag"] * tag_score
        + weights["rating"] * rating_score
    )

    return ScoreBreakdown(
        semantic=0.0,
        genre=round(genre_score, 3),
        platform=round(platform_score, 3),
        tag=round(tag_score, 3),
        rating=round(rating_score, 3),
        final=round(final, 3),
    )


def _overlap(actual: list[str], requested: tuple[str, ...]) -> float:
    if not requested:
        return 0.0
    actual_set = {value.casefold() for value in actual}
    requested_set = {value.casefold() for value in requested}
    if not requested_set:
        return 0.0
    return len(actual_set & requested_set) / len(requested_set)


def _explain(game: GameResponse, scores: ScoreBreakdown, preferences: ParsedPreferences) -> str:
    parts: list[str] = []
    if scores.genre > 0:
        matched = _matches(game.genres, preferences.genres)
        if matched:
            parts.append(f"matches the {', '.join(matched)} genre")
    if scores.platform > 0:
        matched = _matches(game.platforms, preferences.platforms)
        if matched:
            parts.append(f"is available on {', '.join(matched)}")
    if scores.tag > 0:
        matched = _matches(game.tags, preferences.tags)
        if matched:
            parts.append(f"is tagged {', '.join(matched)}")
    if scores.rating >= 0.8 and game.rating is not None:
        parts.append(f"is highly rated ({game.rating:.1f}/5)")
    if not parts:
        parts.append("is a relevant catalogue entry based on your prompt")
    return "Recommended because it " + " and ".join(parts) + "."


def _matches(actual: list[str], requested: tuple[str, ...]) -> list[str]:
    requested_lower = {value.casefold() for value in requested}
    return [value for value in actual if value.casefold() in requested_lower]
