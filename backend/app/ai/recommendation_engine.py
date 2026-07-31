"""Vectorized cosine candidate retrieval independent from hybrid ranking."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from app.ai.embedding_service import EmbeddingError, EmbeddingStore
from app.schemas.ai import SemanticCandidate


class SemanticRecommendationEngine:
    def __init__(
        self,
        embeddings: NDArray[np.float32] | EmbeddingStore,
        game_ids: Sequence[str] | None = None,
        *,
        candidate_count: int = 30,
        minimum_threshold: float = 0.0,
    ) -> None:
        if candidate_count < 1:
            raise ValueError("candidate_count must be positive")
        if not 0 <= minimum_threshold <= 1:
            raise ValueError("minimum_threshold must be between zero and one")
        self._source = embeddings
        self._game_ids = tuple(game_ids or ())
        self.candidate_count = candidate_count
        self.minimum_threshold = minimum_threshold

    def _data(self) -> tuple[NDArray[np.float32], tuple[str, ...]]:
        if isinstance(self._source, EmbeddingStore):
            matrix, ids, _ = self._source.load()
            return matrix, ids
        matrix = np.asarray(self._source, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[0] != len(self._game_ids):
            raise EmbeddingError("In-memory embedding matrix and IDs are inconsistent.")
        return matrix, self._game_ids

    def retrieve(self, query_embedding: NDArray[np.float32], *, limit: int | None = None) -> list[SemanticCandidate]:
        matrix, game_ids = self._data()
        query = np.asarray(query_embedding, dtype=np.float32).reshape(-1)
        if matrix.shape[1] != query.shape[0]:
            raise EmbeddingError("Query and game embedding dimensions differ.")
        query_norm = float(np.linalg.norm(query))
        row_norms = np.linalg.norm(matrix, axis=1)
        denominators = row_norms * query_norm
        raw = np.divide(
            matrix @ query,
            denominators,
            out=np.zeros(matrix.shape[0], dtype=np.float32),
            where=denominators != 0,
        )
        # Cosine lies in [-1, 1]. Response scores use one documented 0..1 scale.
        scores = np.clip((raw + 1.0) / 2.0, 0.0, 1.0)
        unique: dict[str, float] = {}
        for game_id, value in zip(game_ids, scores, strict=True):
            score = float(value)
            if np.isfinite(score) and score >= self.minimum_threshold:
                unique[game_id] = max(score, unique.get(game_id, 0.0))
        ordered = sorted(unique.items(), key=lambda item: (-item[1], item[0]))
        effective_limit = min(limit or self.candidate_count, self.candidate_count)
        return [
            SemanticCandidate(game_id=game_id, semantic_score=round(score, 6))
            for game_id, score in ordered[:effective_limit]
        ]
