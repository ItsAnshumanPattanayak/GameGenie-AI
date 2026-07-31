"""Similarity helpers and the retained catalogue-scoring protocol."""

from typing import Protocol

from app.schemas.game import GameResponse


def overlap_score(requested: set[str], available: set[str]) -> float:
    """Score requested-value recall; an inactive category is handled by ranking weights."""
    if not requested:
        return 0.0
    return len({value.casefold() for value in requested} & {value.casefold() for value in available}) / len(requested)


class SimilarityCalculator(Protocol):
    def score(self, query_features: set[str], game: GameResponse) -> float:
        """Return a normalized similarity score from zero to one."""
        ...
