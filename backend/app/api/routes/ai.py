"""Thin API adapters for AI-owned interpretation, recommendation, and generator logic."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.game_generator import GameConfigurationGenerator
from app.ai.preference_extractor import PreferenceExtractor
from app.ai.prompt_normalizer import PromptNormalizer
from app.ai.recommender import RecommendationService
from app.api.dependencies import get_game_service, get_recommendation_service
from app.schemas.ai import GeneratorRequest, GeneratorResponse, InterpretationResponse, InterpretRequest
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.game_service import GameService

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
) -> RecommendationResponse:
    prompt = service.normalizer.normalize(request.preference_text)
    preferences = service.extractor.extract_normalized(prompt)
    return RecommendationResponse(items=service.recommend(request), normalized_prompt=prompt, preferences=preferences)


@router.post("/generator/interpret", response_model=GeneratorResponse)
def generate(
    request: GeneratorRequest,
    catalogue: Annotated[GameService, Depends(get_game_service)],
) -> GeneratorResponse:
    selected_game = catalogue.get(request.selected_game_id) if request.selected_game_id else None
    return _generator.generate(request.prompt, selected_game=selected_game, overrides=request.overrides)
