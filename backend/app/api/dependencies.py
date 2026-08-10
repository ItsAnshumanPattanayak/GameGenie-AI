"""Testable request dependencies."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from app.ai.preference_parser import KeywordPreferenceParser
from app.ai.recommender import RecommendationService
from app.core.exceptions import AppError, CatalogueInitializationError
from app.core.security import decode_token
from app.db.models import User
from app.services.game_service import GameService

bearer_scheme = HTTPBearer(auto_error=False)


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


def get_db(request: Request) -> Generator[Session, None, None]:
    factory: sessionmaker[Session] = request.app.state.db_session_factory
    with factory() as session:
        yield session


DbDep = Annotated[Session, Depends(get_db)]
BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_optional_current_user(request: Request, db: DbDep, credentials: BearerDep) -> User | None:
    if credentials is None:
        if request.headers.get("Authorization"):
            raise AppError("INVALID_TOKEN", "The authentication token is malformed or invalid.", 401)
        return None
    if credentials.scheme.casefold() != "bearer":
        raise AppError("INVALID_TOKEN", "The authentication token is malformed or invalid.", 401)
    payload = decode_token(credentials.credentials, "access", request.app.state.settings)
    user = db.get(User, payload["sub"])
    if user is None:
        raise AppError("INVALID_TOKEN", "The authentication token does not identify a user.", 401)
    if not user.is_active:
        raise AppError("USER_INACTIVE", "This account is inactive.", 403)
    return user


OptionalUserDep = Annotated[User | None, Depends(get_optional_current_user)]


def get_current_user(user: OptionalUserDep) -> User:
    if user is None:
        raise AppError("AUTHENTICATION_REQUIRED", "Authentication is required.", 401)
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
