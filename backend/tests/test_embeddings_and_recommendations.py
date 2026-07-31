"""Embedding integrity, semantic retrieval, hybrid ranking, and explanation tests."""

import json
from pathlib import Path

import numpy as np
import pytest

from app.ai.embedding_service import (
    DeterministicHashEmbeddingService,
    EmbeddingError,
    EmbeddingStore,
    build_game_text,
    validate_embedding_artifacts,
)
from app.ai.explanation_engine import RecommendationExplanationEngine
from app.ai.preference_extractor import PreferenceExtractor
from app.ai.ranking_engine import HybridRankingEngine, RankedGame, active_weights
from app.ai.recommendation_engine import SemanticRecommendationEngine
from app.schemas.ai import ScoreBreakdown, SemanticCandidate
from app.schemas.game import GameResponse


def _metadata(rows: int, columns: int) -> dict[str, object]:
    return {"game_count": rows, "embedding_dimension": columns}


def test_embedding_integrity_valid_fixture() -> None:
    matrix = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    validate_embedding_artifacts(matrix, ["a", "b"], _metadata(2, 2))


@pytest.mark.parametrize(
    ("matrix", "ids", "metadata"),
    [
        (np.array([1.0, 2.0], dtype=np.float32), ["a"], _metadata(1, 2)),
        (np.array([[1.0], [2.0]], dtype=np.float32), ["a"], _metadata(1, 1)),
        (np.array([[np.nan]], dtype=np.float32), ["a"], _metadata(1, 1)),
        (np.array([[np.inf]], dtype=np.float32), ["a"], _metadata(1, 1)),
        (np.array([[1.0], [2.0]], dtype=np.float32), ["a", "a"], _metadata(2, 1)),
        (np.array([[1.0]], dtype=np.float32), [""], _metadata(1, 1)),
        (np.array([[1.0]], dtype=np.float32), ["a"], _metadata(2, 1)),
        (np.array([[1.0]], dtype=np.float32), ["a"], _metadata(1, 2)),
    ],
)
def test_embedding_integrity_failures(matrix: np.ndarray, ids: list[str], metadata: dict[str, object]) -> None:
    with pytest.raises(EmbeddingError):
        validate_embedding_artifacts(matrix, ids, metadata)


def test_embedding_store_missing_and_corrupt(tmp_path: Path) -> None:
    with pytest.raises(EmbeddingError, match="Missing"):
        EmbeddingStore(tmp_path).load()
    (tmp_path / "game_embeddings.npy").write_bytes(b"broken")
    (tmp_path / "game_ids.json").write_text("[]", encoding="utf-8")
    (tmp_path / "metadata.json").write_text("{}", encoding="utf-8")
    with pytest.raises(EmbeddingError, match="corrupted"):
        EmbeddingStore(tmp_path).load()


def test_embedding_store_loads_once(tmp_path: Path) -> None:
    matrix = np.eye(2, dtype=np.float32)
    with (tmp_path / "game_embeddings.npy").open("wb") as handle:
        np.save(handle, matrix)
    (tmp_path / "game_ids.json").write_text(json.dumps(["a", "b"]), encoding="utf-8")
    (tmp_path / "metadata.json").write_text(json.dumps(_metadata(2, 2)), encoding="utf-8")
    store = EmbeddingStore(tmp_path)
    first = store.load()
    second = store.load()
    assert store.loaded and first[0] is second[0]


def test_hash_embeddings_are_normalized_and_deterministic(sample_games: list[GameResponse]) -> None:
    service = DeterministicHashEmbeddingService(64)
    first = service.embed_games(sample_games)
    second = service.embed_games(sample_games)
    assert first.shape == (3, 64) and np.allclose(first, second)
    assert np.allclose(np.linalg.norm(first, axis=1), 1.0)
    assert "None" not in build_game_text(GameResponse(id="x", title="Empty"))


def test_semantic_retrieval_order_threshold_and_tie_break() -> None:
    matrix = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
    engine = SemanticRecommendationEngine(matrix, ["b", "c", "a"], minimum_threshold=0.6)
    result = engine.retrieve(np.array([1.0, 0.0], dtype=np.float32))
    assert [item.game_id for item in result] == ["a", "b"]
    assert all(0 <= item.semantic_score <= 1 for item in result)


def test_active_weights_redistribute_and_sum_to_one() -> None:
    preferences = PreferenceExtractor().extract("puzzle for PC")
    weights = active_weights(preferences)
    assert sum(weights.values()) == pytest.approx(1.0)
    assert weights["semantic"] > 0.5 and weights["price"] == 0


def test_soft_preference_does_not_become_hard_filter() -> None:
    preferences = PreferenceExtractor().extract("I prefer multiplayer if possible")
    assert "multiplayer" in preferences.modes
    assert "multiplayer" not in preferences.hard_filters


def test_unspecified_categories_do_not_reduce_final_score(sample_games: list[GameResponse]) -> None:
    preferences = PreferenceExtractor().extract("puzzle")
    ranked = HybridRankingEngine().rank(
        [SemanticCandidate(game_id="quest", semantic_score=0.8)], {game.id: game for game in sample_games}, preferences
    )
    assert ranked[0].breakdown.final_score >= 0.8


@pytest.mark.parametrize(
    ("prompt", "game_id"),
    [("free multiplayer only", "alpha"), ("for PC", "alphabet"), ("offline only", "alphabet")],
)
def test_hard_filters_exclude_games(sample_games: list[GameResponse], prompt: str, game_id: str) -> None:
    preferences = PreferenceExtractor().extract(prompt)
    game = next(item for item in sample_games if item.id == game_id)
    assert not HybridRankingEngine.passes_hard_filters(game, preferences)


def _ranked(matches: tuple[str, ...]) -> RankedGame:
    game = GameResponse(id="x", title="X", normalized_title="x")
    breakdown = ScoreBreakdown(
        semantic_score=0.7,
        genre_score=0,
        platform_score=0,
        mode_score=0,
        theme_score=0,
        mood_score=0,
        price_score=0,
        difficulty_score=0,
        hardware_score=0,
        final_score=0.7,
    )
    return RankedGame(game, breakdown, matches)


@pytest.mark.parametrize(
    ("matches", "fragment"),
    [
        ((), "semantically similar"),
        (("genre:puzzle",), "matches the puzzle genre."),
        (("genre:puzzle", "platform:PC"), "genre and supports PC"),
        (("genre:puzzle", "platform:PC", "mood:relaxing"), ", and has a relaxing mood"),
    ],
)
def test_explanation_grammar_and_grounding(matches: tuple[str, ...], fragment: str) -> None:
    explanation = RecommendationExplanationEngine().explain(_ranked(matches))
    assert fragment in explanation
    assert "multiplayer" not in explanation
