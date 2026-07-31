"""Testable request dependencies."""

from fastapi import Request

from app.ai.recommender import RecommendationService
from app.core.exceptions import CatalogueInitializationError
from app.services.game_service import GameService


def get_game_service(request: Request) -> GameService:
    service = getattr(request.app.state, "game_service", None)
    if service is None:
        raise CatalogueInitializationError()
    return service


def get_recommendation_service(request: Request) -> RecommendationService:
    service = getattr(request.app.state, "recommendation_service", None)
    if service is None:
        from app.core.exceptions import AppError

        raise AppError("AI_SERVICE_UNAVAILABLE", "The recommendation service is unavailable.", 503)
    return service
