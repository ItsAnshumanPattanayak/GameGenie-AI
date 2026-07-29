"""Similarity abstraction; concrete vector scoring arrives in Phase 3."""

from typing import Protocol

from app.schemas.game import GameResponse


class SimilarityCalculator(Protocol):
    def score(self, query_features: set[str], game: GameResponse) -> float:
        """Return a normalized similarity score from zero to one."""
        ...
