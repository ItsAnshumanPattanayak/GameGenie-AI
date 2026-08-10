"""Bounded personalisation profile and reranking tests."""

from datetime import UTC, datetime, timedelta

import pytest

from app.ai.embedding_service import DeterministicHashEmbeddingService
from app.ai.personalisation import (
    FeedbackEvent,
    PersonalisationProfile,
    PersonalisationWeights,
    PersonalisedRankingEngine,
)
from app.ai.ranking_engine import HybridRankingEngine
from app.ai.recommender import RecommendationService
from app.schemas.ai import ExtractedPreferences, ScoreBreakdown
from app.schemas.game import GameResponse
from app.schemas.recommendation import RecommendationItem, RecommendationRequest

NOW = datetime(2026, 8, 10, tzinfo=UTC)


@pytest.fixture
def catalogue() -> list[GameResponse]:
    return [
        GameResponse(
            id="alpha",
            title="Alpha Arena",
            normalized_title="alpha arena",
            genres=["action"],
            platforms=["PC"],
            description="An intense hard cyberpunk competitive game for low-end hardware.",
            tags=["intense", "cyberpunk", "competitive"],
            multiplayer=True,
            online_multiplayer=True,
            single_player=False,
            price=0,
            price_category="free",
            minimum_requirements="low-end PC",
        ),
        GameResponse(
            id="beta",
            title="Beta Story",
            normalized_title="beta story",
            genres=["role-playing"],
            platforms=["PlayStation 5"],
            description="A relaxing easy fantasy role-playing journey for high-end hardware.",
            tags=["relaxing", "fantasy", "emotional"],
            multiplayer=False,
            online_multiplayer=False,
            single_player=True,
            price=30,
            price_category="mid-range",
            minimum_requirements="high-end hardware",
        ),
        GameResponse(
            id="gamma",
            title="Gamma Tactics",
            normalized_title="gamma tactics",
            genres=["strategy"],
            platforms=["PC", "Nintendo Switch"],
            description="An atmospheric medium strategy game with cooperative multiplayer.",
            tags=["atmospheric", "cooperative"],
            multiplayer=True,
            online_multiplayer=False,
            single_player=True,
            price=12,
            price_category="budget",
            minimum_requirements="mid-range hardware",
        ),
    ]


def _breakdown(score: float) -> ScoreBreakdown:
    return ScoreBreakdown(
        semantic_score=score,
        genre_score=0,
        platform_score=0,
        mode_score=0,
        theme_score=0,
        mood_score=0,
        price_score=0,
        difficulty_score=0,
        hardware_score=0,
        final_score=score,
    )


def _item(game: GameResponse, score: float = 0.5) -> RecommendationItem:
    return RecommendationItem(
        game=game,
        score=score,
        score_breakdown=_breakdown(score),
        explanation="Base explanation.",
    )


def _rerank(
    catalogue: list[GameResponse],
    profile: PersonalisationProfile,
    *,
    prompt: ExtractedPreferences | None = None,
    scores: tuple[float, ...] = (0.5, 0.5, 0.5),
    weights: PersonalisationWeights | None = None,
) -> list[RecommendationItem]:
    games = {game.id: game for game in catalogue}
    ranker = HybridRankingEngine()
    profiles = {game.id: ranker.game_profile(game) for game in catalogue}
    return PersonalisedRankingEngine(weights).rerank(
        [_item(game, score) for game, score in zip(catalogue, scores, strict=True)],
        profile,
        prompt or ExtractedPreferences(),
        games,
        profiles,
        limit=len(catalogue),
        now=NOW,
    )


def _by_id(items: list[RecommendationItem], game_id: str) -> RecommendationItem:
    return next(item for item in items if item.game.id == game_id)


def test_empty_profile_preserves_base_items_exactly(catalogue: list[GameResponse]) -> None:
    original = [_item(game, score) for game, score in zip(catalogue, (0.8, 0.6, 0.4), strict=True)]
    games = {game.id: game for game in catalogue}
    profiles = {game.id: HybridRankingEngine().game_profile(game) for game in catalogue}
    result = PersonalisedRankingEngine().rerank(
        original, PersonalisationProfile(), ExtractedPreferences(), games, profiles, limit=3
    )
    assert result == original


@pytest.mark.parametrize(
    "kwargs",
    [
        {"base": 0.7},
        {"explicit": -0.1},
        {"total_cap": 1.1},
        {"prompt_overlap_factor": -0.1},
    ],
)
def test_invalid_weight_configuration_is_rejected(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        PersonalisationWeights(**kwargs)


@pytest.mark.parametrize(
    ("preferences", "game_id", "reason"),
    [
        (ExtractedPreferences(genres=("action",)), "alpha", "genre"),
        (ExtractedPreferences(platforms=("PC",)), "alpha", "platform"),
        (ExtractedPreferences(modes=("multiplayer",)), "alpha", "mode"),
        (ExtractedPreferences(moods=("relaxing",)), "beta", "mood"),
        (ExtractedPreferences(difficulty="easy"), "beta", "difficulty"),
        (ExtractedPreferences(price_type="free"), "alpha", "price preference"),
        (ExtractedPreferences(hardware_level="mid-range"), "gamma", "hardware level"),
    ],
)
def test_explicit_preference_categories_raise_matching_games(
    catalogue: list[GameResponse], preferences: ExtractedPreferences, game_id: str, reason: str
) -> None:
    result = _rerank(catalogue, PersonalisationProfile(explicit_preferences=preferences))
    item = _by_id(result, game_id)
    assert item.score > 0.5
    assert item.personalisation_reasons is not None
    assert any(reason in value for value in item.personalisation_reasons)


def test_prompt_overlap_reduces_stored_preference_influence(catalogue: list[GameResponse]) -> None:
    profile = PersonalisationProfile(explicit_preferences=ExtractedPreferences(genres=("action",)))
    normal = _by_id(_rerank(catalogue, profile), "alpha")
    overlapping = _by_id(_rerank(catalogue, profile, prompt=ExtractedPreferences(genres=("action",))), "alpha")
    assert 0 < (overlapping.score - 0.5) < (normal.score - 0.5)


def test_conflicting_prompt_remains_stronger_than_profile(catalogue: list[GameResponse]) -> None:
    profile = PersonalisationProfile(explicit_preferences=ExtractedPreferences(genres=("action",)))
    result = _rerank(catalogue, profile, prompt=ExtractedPreferences(genres=("role-playing",)))
    assert _by_id(result, "alpha").personalisation_score == pytest.approx(1.25)


def test_direct_favourite_is_a_bounded_positive_signal(catalogue: list[GameResponse]) -> None:
    result = _rerank(catalogue, PersonalisationProfile(favourite_game_ids=("alpha",)))
    alpha = _by_id(result, "alpha")
    assert alpha.score == pytest.approx(0.52)
    assert alpha.personalisation_reasons == ["Similar to games in your favourites"]


def test_several_favourites_use_bounded_top_similarity(catalogue: list[GameResponse]) -> None:
    result = _rerank(catalogue, PersonalisationProfile(favourite_game_ids=("alpha", "gamma", "beta")))
    assert all(abs(item.personalisation_score or 0) <= 4 for item in result)


def test_removed_favourite_has_no_remaining_signal(catalogue: list[GameResponse]) -> None:
    with_favourite = _by_id(_rerank(catalogue, PersonalisationProfile(favourite_game_ids=("alpha",))), "alpha")
    without_favourite = _by_id(_rerank(catalogue, PersonalisationProfile()), "alpha")
    assert with_favourite.score > without_favourite.score == 0.5


@pytest.mark.parametrize(
    ("feedback_type", "direction"),
    [("relevant", 1), ("interested", 1), ("already_played", 1), ("not_relevant", -1)],
)
def test_supported_feedback_has_expected_direction(
    catalogue: list[GameResponse], feedback_type: str, direction: int
) -> None:
    profile = PersonalisationProfile(feedback_events=(FeedbackEvent("alpha", feedback_type, NOW),))
    delta = (_by_id(_rerank(catalogue, profile), "alpha").personalisation_score or 0) * direction
    assert delta > 0


def test_one_negative_event_cannot_eliminate_a_game(catalogue: list[GameResponse]) -> None:
    profile = PersonalisationProfile(feedback_events=(FeedbackEvent("alpha", "not_relevant", NOW),))
    alpha = _by_id(_rerank(catalogue, profile, scores=(0.2, 0.5, 0.5)), "alpha")
    assert 0 < alpha.score < 0.2


def test_recent_feedback_has_more_influence_than_old_feedback(catalogue: list[GameResponse]) -> None:
    recent = PersonalisationProfile(feedback_events=(FeedbackEvent("alpha", "relevant", NOW),))
    old = PersonalisationProfile(feedback_events=(FeedbackEvent("alpha", "relevant", NOW - timedelta(days=180)),))
    recent_delta = _by_id(_rerank(catalogue, recent), "alpha").personalisation_score or 0
    old_delta = _by_id(_rerank(catalogue, old), "alpha").personalisation_score or 0
    assert recent_delta > old_delta > 0


def test_total_personalisation_cap_is_enforced(catalogue: list[GameResponse]) -> None:
    weights = PersonalisationWeights(total_cap=0.01)
    profile = PersonalisationProfile(
        explicit_preferences=ExtractedPreferences(genres=("action",)),
        favourite_game_ids=("alpha",),
        feedback_events=(FeedbackEvent("alpha", "relevant", NOW),),
        recent_search_preferences=ExtractedPreferences(genres=("action",)),
    )
    alpha = _by_id(_rerank(catalogue, profile, weights=weights), "alpha")
    assert alpha.personalisation_score == pytest.approx(1.0)


@pytest.mark.parametrize("base", [0.0, 0.01, 0.99, 1.0])
def test_final_score_stays_inside_zero_to_one_and_percent_bounds(catalogue: list[GameResponse], base: float) -> None:
    profile = PersonalisationProfile(
        explicit_preferences=ExtractedPreferences(genres=("action",)),
        favourite_game_ids=("alpha",),
        feedback_events=(FeedbackEvent("alpha", "relevant", NOW),),
    )
    item = _by_id(_rerank(catalogue, profile, scores=(base, base, base)), "alpha")
    assert 0 <= item.score <= 1
    if item.final_score is not None:
        assert 0 <= item.final_score <= 100


def test_repeated_recent_theme_adds_small_signal(catalogue: list[GameResponse]) -> None:
    profile = PersonalisationProfile(
        recent_search_terms=("strategy",),
        recent_search_preferences=ExtractedPreferences(genres=("strategy",)),
    )
    gamma = _by_id(_rerank(catalogue, profile), "gamma")
    assert gamma.score > 0.5
    assert gamma.personalisation_reasons is not None
    assert "Matches themes from your recent searches" in gamma.personalisation_reasons


def test_empty_recent_history_has_no_signal(catalogue: list[GameResponse]) -> None:
    item = _by_id(_rerank(catalogue, PersonalisationProfile(recent_search_terms=())), "gamma")
    assert item.score == 0.5 and item.final_score is None


def test_incomplete_profile_uses_only_available_category(catalogue: list[GameResponse]) -> None:
    profile = PersonalisationProfile(explicit_preferences=ExtractedPreferences(platforms=("PC",)))
    alpha = _by_id(_rerank(catalogue, profile), "alpha")
    assert alpha.personalisation_signals is not None
    assert set(alpha.personalisation_signals) == {"explicit_preferences"}


def test_overlapping_reasons_are_deduplicated(catalogue: list[GameResponse]) -> None:
    profile = PersonalisationProfile(
        explicit_preferences=ExtractedPreferences(genres=("action",)),
        favourite_game_ids=("alpha",),
    )
    reasons = _by_id(_rerank(catalogue, profile), "alpha").personalisation_reasons
    assert reasons is not None
    assert len(reasons) == len(set(reasons))


def test_no_personalised_claim_when_signal_does_not_change_score(catalogue: list[GameResponse]) -> None:
    profile = PersonalisationProfile(explicit_preferences=ExtractedPreferences(genres=("action",)))
    alpha = _by_id(_rerank(catalogue, profile, scores=(1.0, 1.0, 1.0)), "alpha")
    assert alpha.base_score is None and alpha.personalisation_reasons is None


def test_personalisation_can_change_order_without_replacing_base_ranker(catalogue: list[GameResponse]) -> None:
    profile = PersonalisationProfile(explicit_preferences=ExtractedPreferences(genres=("role-playing",)))
    result = _rerank(catalogue, profile, scores=(0.54, 0.5, 0.4))
    assert result[0].game.id == "beta"
    assert result[0].score_breakdown.final_score == 0.5


def test_score_explanation_fields_use_zero_to_one_hundred_scale(catalogue: list[GameResponse]) -> None:
    profile = PersonalisationProfile(favourite_game_ids=("alpha",))
    alpha = _by_id(_rerank(catalogue, profile), "alpha")
    assert alpha.base_score == 50
    assert alpha.personalisation_score == 2
    assert alpha.final_score == 52


def test_generated_games_are_optional_and_tolerated(catalogue: list[GameResponse]) -> None:
    profile = PersonalisationProfile(generated_game_ids=("future-game",))
    assert profile.is_empty
    assert _by_id(_rerank(catalogue, profile), "alpha").score == 0.5


def test_service_empty_profile_matches_anonymous_ranking(catalogue: list[GameResponse]) -> None:
    service = RecommendationService(catalogue, DeterministicHashEmbeddingService(64))
    request = RecommendationRequest(preference_text="game", limit=3)
    assert service.recommend(request) == service.recommend(request, PersonalisationProfile())


def test_service_personalised_results_retain_base_breakdown(catalogue: list[GameResponse]) -> None:
    service = RecommendationService(catalogue, DeterministicHashEmbeddingService(64))
    request = RecommendationRequest(preference_text="game", limit=3)
    result = service.recommend(
        request, PersonalisationProfile(explicit_preferences=ExtractedPreferences(genres=("action",)))
    )
    assert result
    assert all(0 <= item.score_breakdown.final_score <= 1 for item in result)
    assert any(item.base_score is not None for item in result)
