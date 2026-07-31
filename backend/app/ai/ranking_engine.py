"""Hybrid recommendation ranking with active-category weight redistribution."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from app.ai.embedding_service import build_game_text
from app.ai.preference_extractor import PreferenceExtractor
from app.ai.similarity import overlap_score
from app.schemas.ai import ExtractedPreferences, ScoreBreakdown, SemanticCandidate
from app.schemas.game import GameResponse

BASE_WEIGHTS: Final = MappingProxyType(
    {
        "semantic": 0.50,
        "genre": 0.15,
        "platform": 0.10,
        "mode": 0.08,
        "theme": 0.035,
        "mood": 0.035,
        "price": 0.04,
        "difficulty": 0.03,
        "hardware": 0.03,
    }
)


@dataclass(frozen=True)
class RankedGame:
    game: GameResponse
    breakdown: ScoreBreakdown
    matched_attributes: tuple[str, ...]


def active_weights(preferences: ExtractedPreferences) -> dict[str, float]:
    """Proportionally scale only active weights so they sum to one."""
    active = {
        "semantic": True,
        "genre": bool(preferences.genres),
        "platform": bool(preferences.platforms),
        "mode": bool(preferences.modes),
        "theme": bool(preferences.themes),
        "mood": bool(preferences.moods),
        "price": preferences.price_type is not None,
        "difficulty": preferences.difficulty is not None,
        "hardware": preferences.hardware_level is not None,
    }
    total = sum(weight for name, weight in BASE_WEIGHTS.items() if active[name])
    return {name: (weight / total if active[name] else 0.0) for name, weight in BASE_WEIGHTS.items()}


class HybridRankingEngine:
    def __init__(self, extractor: PreferenceExtractor | None = None) -> None:
        self.extractor = extractor or PreferenceExtractor()

    def rank(
        self,
        candidates: list[SemanticCandidate],
        games_by_id: dict[str, GameResponse],
        preferences: ExtractedPreferences,
        *,
        limit: int = 10,
    ) -> list[RankedGame]:
        weights = active_weights(preferences)
        ranked: list[RankedGame] = []
        for candidate in candidates:
            game = games_by_id.get(candidate.game_id)
            if game is None or not self.passes_hard_filters(game, preferences):
                continue
            profile = self._profile(game)
            scores = self._component_scores(candidate.semantic_score, game, profile, preferences)
            final = sum(scores[name] * weights[name] for name in weights)
            breakdown = ScoreBreakdown(
                semantic_score=scores["semantic"],
                genre_score=scores["genre"],
                platform_score=scores["platform"],
                mode_score=scores["mode"],
                theme_score=scores["theme"],
                mood_score=scores["mood"],
                price_score=scores["price"],
                difficulty_score=scores["difficulty"],
                hardware_score=scores["hardware"],
                final_score=round(max(0.0, min(1.0, final)), 6),
            )
            ranked.append(
                RankedGame(game=game, breakdown=breakdown, matched_attributes=self._matches(game, profile, preferences))
            )
        ranked.sort(key=lambda item: (-item.breakdown.final_score, item.game.normalized_title, item.game.id))
        return ranked[:limit]

    @staticmethod
    def passes_hard_filters(game: GameResponse, preferences: ExtractedPreferences) -> bool:
        filters = set(preferences.hard_filters)
        platforms = {platform.casefold() for platform in game.platforms}
        if "platform" in filters and not any(
            requested.casefold() == "playstation"
            and any(value.startswith("playstation") for value in platforms)
            or requested.casefold() == "xbox"
            and any(value.startswith("xbox") for value in platforms)
            or requested.casefold() in platforms
            for requested in preferences.platforms
        ):
            return False
        if "free" in filters and game.price_category != "free":
            return False
        if "multiplayer" in filters and game.multiplayer is not True:
            return False
        return not ("offline" in filters and game.online_multiplayer is not False)

    def _profile(self, game: GameResponse) -> ExtractedPreferences:
        profile = self.extractor.extract(build_game_text(game))
        modes = list(profile.modes)
        if game.single_player and "single-player" not in modes:
            modes.append("single-player")
        if game.multiplayer and "multiplayer" not in modes:
            modes.append("multiplayer")
        if game.online_multiplayer and "online" not in modes:
            modes.append("online")
        if not game.online_multiplayer and "offline" not in modes:
            modes.append("offline")
        return profile.model_copy(update={"modes": tuple(modes)})

    @staticmethod
    def _component_scores(
        semantic: float, game: GameResponse, profile: ExtractedPreferences, requested: ExtractedPreferences
    ) -> dict[str, float]:
        price = 1.0 if requested.price_type and _price_type(game) == requested.price_type else 0.0
        difficulty = 1.0 if requested.difficulty and profile.difficulty == requested.difficulty else 0.0
        hardware = 1.0 if requested.hardware_level and profile.hardware_level == requested.hardware_level else 0.0
        return {
            "semantic": semantic,
            "genre": overlap_score(set(requested.genres), set(profile.genres)),
            "platform": _platform_overlap(set(requested.platforms), set(game.platforms)),
            "mode": overlap_score(set(requested.modes), set(profile.modes)),
            "theme": overlap_score(set(requested.themes), set(profile.themes)),
            "mood": overlap_score(set(requested.moods), set(profile.moods)),
            "price": price,
            "difficulty": difficulty,
            "hardware": hardware,
        }

    @staticmethod
    def _matches(game: GameResponse, profile: ExtractedPreferences, requested: ExtractedPreferences) -> tuple[str, ...]:
        result: list[str] = []
        pairs = (
            ("genre", requested.genres, profile.genres),
            ("platform", requested.platforms, tuple(game.platforms)),
            ("mode", requested.modes, profile.modes),
            ("theme", requested.themes, profile.themes),
            ("mood", requested.moods, profile.moods),
        )
        for label, wanted, available in pairs:
            available_folded = {item.casefold() for item in available}
            for item in wanted:
                if item.casefold() in available_folded or (
                    label == "platform"
                    and item in {"PlayStation", "Xbox"}
                    and any(value.casefold().startswith(item.casefold()) for value in available)
                ):
                    result.append(f"{label}:{item}")
        if requested.price_type and _price_type(game) == requested.price_type:
            result.append(f"price:{requested.price_type}")
        if requested.difficulty and profile.difficulty == requested.difficulty:
            result.append(f"difficulty:{requested.difficulty}")
        if requested.hardware_level and profile.hardware_level == requested.hardware_level:
            result.append(f"hardware:{requested.hardware_level}")
        return tuple(result)


def _price_type(game: GameResponse) -> str:
    return "free" if game.price_category == "free" else "paid"


def _platform_overlap(requested: set[str], available: set[str]) -> float:
    if not requested:
        return 0.0
    folded = {value.casefold() for value in available}
    matches = 0
    for value in requested:
        key = value.casefold()
        if key in folded or key in {"playstation", "xbox"} and any(item.startswith(key) for item in folded):
            matches += 1
    return matches / len(requested)
