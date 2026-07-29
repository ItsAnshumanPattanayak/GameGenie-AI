"""Recommendation orchestration interface reserved for Phase 3."""

from typing import Protocol

from app.schemas.recommendation import RecommendationItem, RecommendationRequest


class Recommender(Protocol):
    def recommend(self, request: RecommendationRequest) -> list[RecommendationItem]:
        """Rank catalogue candidates and provide explanations."""
        ...
