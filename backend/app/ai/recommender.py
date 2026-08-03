"""Recommendation orchestration across interpretation, retrieval, ranking, and explanation."""

from collections.abc import Sequence
from typing import Protocol

from app.ai.embedding_service import DeterministicHashEmbeddingService, SentenceTransformerEmbeddingService
from app.ai.explanation_engine import RecommendationExplanationEngine
from app.ai.preference_extractor import PreferenceExtractor
from app.ai.prompt_normalizer import PromptNormalizer
from app.ai.ranking_engine import HybridRankingEngine
from app.ai.recommendation_engine import SemanticRecommendationEngine
from app.schemas.game import GameResponse
from app.schemas.recommendation import RecommendationItem, RecommendationRequest


class Recommender(Protocol):
    def recommend(self, request: RecommendationRequest) -> list[RecommendationItem]:
        """Rank catalogue candidates and provide explanations."""
        ...


class RecommendationService:
    """In-memory catalogue adapter; a database layer can supply the same game sequence later."""

    def __init__(
        self,
        games: Sequence[GameResponse],
        embedding_service: SentenceTransformerEmbeddingService | DeterministicHashEmbeddingService,
        *,
        candidate_count: int = 30,
        minimum_threshold: float = 0.0,
    ) -> None:
        self._games = tuple(games)
        self._by_id = {game.id: game for game in games}
        self._embedding_service = embedding_service
        matrix = embedding_service.embed_games(self._games)
        self._semantic = SemanticRecommendationEngine(
            matrix,
            [game.id for game in self._games],
            candidate_count=candidate_count,
            minimum_threshold=minimum_threshold,
        )
        self.normalizer = PromptNormalizer()
        self.extractor = PreferenceExtractor(self.normalizer)
        self.ranker = HybridRankingEngine(self.extractor)
        self.explanations = RecommendationExplanationEngine()

    def recommend(self, request: RecommendationRequest) -> list[RecommendationItem]:
        normalized = self.normalizer.normalize(request.preference_text)
        preferences = self.extractor.extract_normalized(normalized)
        query = self._embedding_service.embed_query(normalized.normalized)
        candidates = self._semantic.retrieve(query)
        if request.excluded_game_ids:
            excluded = set(request.excluded_game_ids)
            candidates = [candidate for candidate in candidates if candidate.game_id not in excluded]
        ranked = self.ranker.rank(candidates, self._by_id, preferences, limit=request.limit)
        return [
            RecommendationItem(
                game=item.game,
                score=item.breakdown.final_score,
                score_breakdown=item.breakdown,
                explanation=self.explanations.explain(item),
                matched_attributes=list(item.matched_attributes),
            )
            for item in ranked
        ]
