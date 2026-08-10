"""Bounded, explainable reranking over the existing hybrid recommendation score."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Final

from app.ai.ranking_engine import _platform_overlap, _price_type
from app.ai.similarity import overlap_score
from app.schemas.ai import ExtractedPreferences
from app.schemas.game import GameResponse
from app.schemas.recommendation import RecommendationItem

DEFAULT_BASE_WEIGHT: Final = 0.80
DEFAULT_EXPLICIT_WEIGHT: Final = 0.10
DEFAULT_FAVOURITE_WEIGHT: Final = 0.04
DEFAULT_FEEDBACK_WEIGHT: Final = 0.04
DEFAULT_RECENT_SEARCH_WEIGHT: Final = 0.02
DEFAULT_TOTAL_CAP: Final = 0.20
DEFAULT_PROMPT_OVERLAP_FACTOR: Final = 0.25


@dataclass(frozen=True)
class PersonalisationWeights:
    base: float = DEFAULT_BASE_WEIGHT
    explicit: float = DEFAULT_EXPLICIT_WEIGHT
    favourite: float = DEFAULT_FAVOURITE_WEIGHT
    feedback: float = DEFAULT_FEEDBACK_WEIGHT
    recent_search: float = DEFAULT_RECENT_SEARCH_WEIGHT
    total_cap: float = DEFAULT_TOTAL_CAP
    prompt_overlap_factor: float = DEFAULT_PROMPT_OVERLAP_FACTOR

    def __post_init__(self) -> None:
        values = (self.base, self.explicit, self.favourite, self.feedback, self.recent_search)
        if any(value < 0 or value > 1 for value in values):
            raise ValueError("personalisation weights must be between zero and one")
        if abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("personalisation weights must sum to one")
        if not 0 <= self.total_cap <= 1 or not 0 <= self.prompt_overlap_factor <= 1:
            raise ValueError("personalisation controls must be between zero and one")


@dataclass(frozen=True)
class FeedbackEvent:
    game_id: str
    feedback_type: str
    created_at: datetime


@dataclass(frozen=True)
class PersonalisationProfile:
    explicit_preferences: ExtractedPreferences = field(default_factory=ExtractedPreferences)
    favourite_game_ids: tuple[str, ...] = ()
    recent_search_terms: tuple[str, ...] = ()
    positive_feedback_game_ids: tuple[str, ...] = ()
    negative_feedback_game_ids: tuple[str, ...] = ()
    recent_search_preferences: ExtractedPreferences = field(default_factory=ExtractedPreferences)
    feedback_events: tuple[FeedbackEvent, ...] = ()
    generated_game_ids: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not (
            _has_preferences(self.explicit_preferences)
            or self.favourite_game_ids
            or self.feedback_events
            or _has_preferences(self.recent_search_preferences)
        )


class PersonalisedRankingEngine:
    """Apply small profile-derived deltas while keeping the base rank dominant."""

    def __init__(self, weights: PersonalisationWeights | None = None) -> None:
        self.weights = weights or PersonalisationWeights()

    def rerank(
        self,
        items: list[RecommendationItem],
        profile: PersonalisationProfile,
        prompt: ExtractedPreferences,
        games_by_id: dict[str, GameResponse],
        game_profiles: dict[str, ExtractedPreferences],
        *,
        limit: int,
        now: datetime | None = None,
    ) -> list[RecommendationItem]:
        if profile.is_empty:
            return items[:limit]
        current_time = now or datetime.now(UTC)
        output = [self._score(item, profile, prompt, games_by_id, game_profiles, current_time) for item in items]
        output.sort(key=lambda item: (-item.score, item.game.normalized_title, item.game.id))
        return output[:limit]

    def _score(
        self,
        item: RecommendationItem,
        profile: PersonalisationProfile,
        prompt: ExtractedPreferences,
        games_by_id: dict[str, GameResponse],
        game_profiles: dict[str, ExtractedPreferences],
        now: datetime,
    ) -> RecommendationItem:
        base = item.score
        reasons: list[str] = []
        contributions: dict[str, float] = {}

        explicit = self._explicit_signal(item.game, game_profiles[item.game.id], profile.explicit_preferences, prompt)
        if explicit is not None:
            score, factor, explicit_reasons = explicit
            contributions["explicit_preferences"] = self.weights.explicit * factor * (score - base)
            reasons.extend(explicit_reasons)

        if profile.favourite_game_ids:
            similarity = self._reference_similarity(item.game, profile.favourite_game_ids, games_by_id, game_profiles)
            contributions["favourites"] = self.weights.favourite * (similarity - base)
            if similarity > base and similarity >= 0.35:
                reasons.append("Similar to games in your favourites")

        if profile.feedback_events:
            feedback = self._feedback_signal(item.game, profile.feedback_events, games_by_id, game_profiles, now)
            feedback_target = max(0.0, min(1.0, base + feedback))
            contributions["feedback"] = self.weights.feedback * (feedback_target - base)
            if feedback > 0.05:
                reasons.append("Reflects games you marked as relevant or interesting")
            elif feedback < -0.05:
                reasons.append("Adjusted away from games you marked not relevant")

        if _has_preferences(profile.recent_search_preferences):
            recent_score = self._preference_match(
                item.game, game_profiles[item.game.id], profile.recent_search_preferences
            )
            contributions["recent_searches"] = self.weights.recent_search * (recent_score - base)
            if recent_score > base and recent_score >= 0.4:
                reasons.append("Matches themes from your recent searches")

        raw_delta = sum(contributions.values())
        delta = max(-self.weights.total_cap, min(self.weights.total_cap, raw_delta))
        final = max(0.0, min(1.0, base + delta))
        if abs(final - base) < 0.0000005:
            return item
        return item.model_copy(
            update={
                "score": round(final, 6),
                "base_score": round(base * 100, 3),
                "personalisation_score": round((final - base) * 100, 3),
                "final_score": round(final * 100, 3),
                "personalisation_reasons": list(dict.fromkeys(reasons)),
                "personalisation_signals": {name: round(value * 100, 3) for name, value in contributions.items()},
            }
        )

    def _explicit_signal(
        self,
        game: GameResponse,
        game_profile: ExtractedPreferences,
        stored: ExtractedPreferences,
        prompt: ExtractedPreferences,
    ) -> tuple[float, float, list[str]] | None:
        categories: list[tuple[str, float, bool, str | None]] = []
        if stored.genres:
            score = overlap_score(set(stored.genres), set(game_profile.genres))
            matched = next((value for value in stored.genres if value in game_profile.genres), None)
            categories.append(
                ("genres", score, bool(prompt.genres), f"Matches your preferred {matched} genre" if matched else None)
            )
        if stored.platforms:
            score = _platform_overlap(set(stored.platforms), set(game.platforms))
            matched = next(
                (value for value in stored.platforms if _platform_overlap({value}, set(game.platforms))), None
            )
            categories.append(
                (
                    "platforms",
                    score,
                    bool(prompt.platforms),
                    f"Matches your preferred {matched} platform" if matched else None,
                )
            )
        if stored.modes:
            score = overlap_score(set(stored.modes), set(game_profile.modes))
            matched = next((value for value in stored.modes if value in game_profile.modes), None)
            categories.append(
                ("modes", score, bool(prompt.modes), f"Supports your preferred {matched} mode" if matched else None)
            )
        if stored.moods:
            score = overlap_score(set(stored.moods), set(game_profile.moods))
            matched = next((value for value in stored.moods if value in game_profile.moods), None)
            categories.append(
                ("moods", score, bool(prompt.moods), f"Matches your preferred {matched} mood" if matched else None)
            )
        scalar_pairs = (
            ("difficulty", stored.difficulty, game_profile.difficulty, prompt.difficulty, "difficulty"),
            ("price", stored.price_type, _price_type(game), prompt.price_type, "price preference"),
            ("hardware", stored.hardware_level, game_profile.hardware_level, prompt.hardware_level, "hardware level"),
        )
        for category, wanted, available, prompt_value, label in scalar_pairs:
            if wanted:
                match = float(wanted == available)
                categories.append(
                    (category, match, prompt_value is not None, f"Matches your preferred {label}" if match else None)
                )
        if not categories:
            return None
        category_weights = [self.weights.prompt_overlap_factor if overlap else 1.0 for _, _, overlap, _ in categories]
        factor = sum(category_weights) / len(categories)
        weighted_score = sum(
            score * weight for (_, score, _, _), weight in zip(categories, category_weights, strict=True)
        )
        weighted_score /= sum(category_weights)
        reasons = [reason for (_, score, _, reason) in categories if reason and score > 0]
        return weighted_score, factor, reasons

    @staticmethod
    def _preference_match(
        game: GameResponse, game_profile: ExtractedPreferences, preferences: ExtractedPreferences
    ) -> float:
        scores: list[float] = []
        if preferences.genres:
            scores.append(overlap_score(set(preferences.genres), set(game_profile.genres)))
        if preferences.platforms:
            scores.append(_platform_overlap(set(preferences.platforms), set(game.platforms)))
        if preferences.modes:
            scores.append(overlap_score(set(preferences.modes), set(game_profile.modes)))
        if preferences.themes:
            scores.append(overlap_score(set(preferences.themes), set(game_profile.themes)))
        if preferences.moods:
            scores.append(overlap_score(set(preferences.moods), set(game_profile.moods)))
        if preferences.difficulty:
            scores.append(float(preferences.difficulty == game_profile.difficulty))
        if preferences.price_type:
            scores.append(float(preferences.price_type == _price_type(game)))
        if preferences.hardware_level:
            scores.append(float(preferences.hardware_level == game_profile.hardware_level))
        return sum(scores) / len(scores) if scores else 0.0

    def _reference_similarity(
        self,
        candidate: GameResponse,
        reference_ids: tuple[str, ...],
        games_by_id: dict[str, GameResponse],
        game_profiles: dict[str, ExtractedPreferences],
    ) -> float:
        similarities = [
            self._game_similarity(candidate, games_by_id[game_id], game_profiles[candidate.id], game_profiles[game_id])
            for game_id in reference_ids
            if game_id in games_by_id
        ]
        return sum(sorted(similarities, reverse=True)[:3]) / min(len(similarities), 3) if similarities else 0.0

    @staticmethod
    def _game_similarity(
        candidate: GameResponse,
        reference: GameResponse,
        candidate_profile: ExtractedPreferences,
        reference_profile: ExtractedPreferences,
    ) -> float:
        if candidate.id == reference.id:
            return 1.0
        scores = [
            _symmetric_overlap(candidate_profile.genres, reference_profile.genres),
            _symmetric_overlap(candidate.platforms, reference.platforms),
            _symmetric_overlap(candidate_profile.modes, reference_profile.modes),
            _symmetric_overlap(candidate.tags, reference.tags),
            _symmetric_overlap(candidate_profile.themes, reference_profile.themes),
            _symmetric_overlap(candidate_profile.moods, reference_profile.moods),
        ]
        active = [score for score in scores if score is not None]
        return sum(active) / len(active) if active else 0.0

    def _feedback_signal(
        self,
        candidate: GameResponse,
        events: tuple[FeedbackEvent, ...],
        games_by_id: dict[str, GameResponse],
        game_profiles: dict[str, ExtractedPreferences],
        now: datetime,
    ) -> float:
        values = {"relevant": 1.0, "interested": 0.8, "already_played": 0.2, "not_relevant": -0.7}
        weighted = 0.0
        denominator = 0.0
        for event in events:
            reference = games_by_id.get(event.game_id)
            value = values.get(event.feedback_type)
            if reference is None or value is None:
                continue
            age = max(0.0, (_aware(now) - _aware(event.created_at)).total_seconds() / 86400)
            recency = 0.5 ** (age / 90.0)
            similarity = self._game_similarity(
                candidate, reference, game_profiles[candidate.id], game_profiles[reference.id]
            )
            strength = 1.0 if candidate.id == reference.id else similarity * 0.6
            weighted += value * strength * recency
            denominator += abs(value)
        return max(-1.0, min(1.0, weighted / denominator)) if denominator else 0.0


def _has_preferences(preferences: ExtractedPreferences) -> bool:
    return bool(
        preferences.genres
        or preferences.platforms
        or preferences.modes
        or preferences.themes
        or preferences.moods
        or preferences.difficulty
        or preferences.price_type
        or preferences.hardware_level
    )


def _symmetric_overlap(left: tuple[str, ...] | list[str], right: tuple[str, ...] | list[str]) -> float | None:
    left_set = {value.casefold() for value in left}
    right_set = {value.casefold() for value in right}
    if not left_set or not right_set:
        return None
    return len(left_set & right_set) / len(left_set | right_set)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)
