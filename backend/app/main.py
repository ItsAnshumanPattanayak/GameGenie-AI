"""GameGenie AI FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.embedding_service import DeterministicHashEmbeddingService, EmbeddingError
from app.ai.recommender import RecommendationService
from app.api.routes import activity, ai, auth, facets, games, health, preferences
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError, register_exception_handlers
from app.core.logging import configure_logging
from app.data.loader import load_raw_records
from app.data.preprocessing import run_preprocessing
from app.db.session import build_engine, build_session_factory
from app.schemas.game import GameResponse
from app.services.game_service import GameService

logger = logging.getLogger(__name__)


def _load_catalogue(settings: Settings) -> list[GameResponse]:
    processed = settings.processed_data_path
    if processed.is_file():
        try:
            return [GameResponse.model_validate(item) for item in load_raw_records(processed)]
        except (AppError, ValueError) as exc:
            logger.warning("Processed dataset invalid; rebuilding from raw data: %s", type(exc).__name__)
    games, _ = run_preprocessing(settings.raw_data_path, processed)
    return games


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)
    engine = build_engine(app_settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("Application startup environment=%s", app_settings.app_env)
        app.state.game_service = None
        app.state.recommendation_service = None
        try:
            app.state.game_service = GameService(_load_catalogue(app_settings))
            logger.info("Catalogue initialized games=%d", app.state.game_service.count)
            app.state.recommendation_service = RecommendationService(
                app.state.game_service.all(), DeterministicHashEmbeddingService()
            )
            logger.info("Offline recommendation index initialized games=%d", app.state.game_service.count)
        except (AppError, ValueError, OSError) as exc:
            logger.error("Catalogue initialization failed type=%s", type(exc).__name__)
        except EmbeddingError as exc:
            logger.error("Recommendation initialization failed: %s", exc)
        yield
        engine.dispose()
        logger.info("Application shutdown")

    application = FastAPI(
        title=app_settings.app_name,
        description="Catalogue API and AI foundation for GameGenie AI.",
        version=app_settings.app_version,
        debug=app_settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.state.settings = app_settings
    application.state.db_engine = engine
    application.state.db_session_factory = build_session_factory(engine)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health.router)
    application.include_router(games.router, prefix=app_settings.api_prefix)
    application.include_router(facets.router, prefix=app_settings.api_prefix)
    application.include_router(ai.router, prefix=app_settings.api_prefix)
    application.include_router(auth.router, prefix=app_settings.api_prefix)
    application.include_router(preferences.router, prefix=app_settings.api_prefix)
    application.include_router(activity.router, prefix=app_settings.api_prefix)
    register_exception_handlers(application)
    return application


app = create_app()
