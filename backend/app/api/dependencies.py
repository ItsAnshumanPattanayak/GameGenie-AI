"""Testable request dependencies."""

from fastapi import Request

from app.ai.preference_parser import KeywordPreferenceParser
from app.ai.recommender import RecommendationService
from app.core.exceptions import AppError, CatalogueInitializationError
from app.services.game_service import GameService
from app.services.generator_service import GeneratorService
from app.services.history_service import HistoryService


def get_game_service(request: Request) -> GameService:
    service = getattr(request.app.state, "game_service", None)
    if service is None:
        raise CatalogueInitializationError()
    return service


def get_recommendation_service(request: Request) -> RecommendationService:
    service = getattr(request.app.state, "recommendation_service", None)
    if service is None:
        raise AppError("AI_SERVICE_UNAVAILABLE", "The recommendation service is unavailable.", 503)
    return service


def get_preference_parser(request: Request) -> KeywordPreferenceParser:
    service = get_game_service(request)
    return KeywordPreferenceParser(
        known_genres=(item.name for item in service.genres()),
        known_platforms=(item.name for item in service.platforms()),
        known_tags=(item.name for item in service.tags()),
    )


def get_history_service(request: Request) -> HistoryService:
    service = getattr(request.app.state, "history_service", None)
    if service is None:
        raise AppError("HISTORY_UNAVAILABLE", "Search history service is unavailable.", 503)
    return service


def get_generator_service(request: Request) -> GeneratorService:
    service = getattr(request.app.state, "generator_service", None)
    if service is None:
        raise AppError("GENERATOR_UNAVAILABLE", "Generator service is unavailable.", 503)
    return service
