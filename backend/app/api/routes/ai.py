"""Thin API adapters for AI-owned interpretation, recommendation, and generator logic."""

from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.game_generator import GameConfigurationGenerator
from app.ai.preference_extractor import PreferenceExtractor
from app.ai.prompt_normalizer import PromptNormalizer
from app.ai.recommender import RecommendationService
from app.api.dependencies import DbDep, OptionalUserDep, get_game_service, get_recommendation_service
from app.db.models import SearchHistory
from app.schemas.ai import GeneratorRequest, GeneratorResponse, InterpretationResponse, InterpretRequest
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.game_service import GameService
from app.services.personalisation_service import build_personalisation_profile

router = APIRouter(tags=["ai"])
_normalizer = PromptNormalizer()
_extractor = PreferenceExtractor(_normalizer)
_generator = GameConfigurationGenerator(_normalizer)


@router.post("/search/interpret", response_model=InterpretationResponse)
def interpret(request: InterpretRequest) -> InterpretationResponse:
    prompt = _normalizer.normalize(request.prompt)
    return InterpretationResponse(
        query=request.query or request.prompt,
        prompt=prompt,
        preferences=_extractor.extract_normalized(prompt),
    )


@router.post("/search/recommend", response_model=RecommendationResponse)
def recommend(
    request: RecommendationRequest,
    service: Annotated[RecommendationService, Depends(get_recommendation_service)],
    current_user: OptionalUserDep,
    db: DbDep,
) -> RecommendationResponse:
    started = perf_counter()
    prompt = service.normalizer.normalize(request.preference_text)
    preferences = service.extractor.extract_normalized(prompt)
    profile = (
        build_personalisation_profile(db, current_user.id, service.extractor) if current_user is not None else None
    )
    items = service.recommend(request, profile)
    search_id = None
    if current_user is not None:
        history = SearchHistory(
            user_id=current_user.id,
            query=request.preference_text,
            extracted_preferences=preferences.model_dump(mode="json"),
            result_count=len(items),
            processing_time_ms=round((perf_counter() - started) * 1000, 3),
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        search_id = history.id
    return RecommendationResponse(
        items=items,
        normalized_prompt=prompt,
        preferences=preferences,
        search_id=search_id,
    )


@router.post("/generator/interpret", response_model=GeneratorResponse)
def generate(
    request: GeneratorRequest,
    catalogue: Annotated[GameService, Depends(get_game_service)],
) -> GeneratorResponse:
    selected_game = catalogue.get(request.selected_game_id) if request.selected_game_id else None
    return _generator.generate(request.prompt, selected_game=selected_game, overrides=request.overrides)
