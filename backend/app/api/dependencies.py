"""Testable request dependencies."""

from fastapi import Request

from app.core.exceptions import CatalogueInitializationError
from app.services.game_service import GameService


def get_game_service(request: Request) -> GameService:
    service = getattr(request.app.state, "game_service", None)
    if service is None:
        raise CatalogueInitializationError()
    return service
