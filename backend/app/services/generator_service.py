"""Prompt-to-configuration service for the Phase 9 game generator.

Deterministic rule-based interpreter used as a stable baseline while the
Phase 9 AI configuration builder is in development. Once the AI module lands
under ``app.ai.game_config_builder``, this service will delegate to it and
keep the current keyword rules as a fallback.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.generator import Difficulty, SpaceShooterConfig, Template

_HARD_KEYWORDS = ("hard", "difficult", "challenging", "brutal", "extreme", "punishing")
_EASY_KEYWORDS = ("easy", "casual", "relaxing", "beginner", "gentle", "chill")
_FAST_KEYWORDS = ("fast", "quick", "rapid", "speedy", "swift")
_SLOW_KEYWORDS = ("slow", "steady", "calm")
_DENSE_KEYWORDS = ("many enemies", "waves", "swarm", "lots of", "hordes", "endless")
_SCALING_KEYWORDS = ("scaling", "increasing", "gets harder", "escalating", "progressive")

_THEMES: dict[str, tuple[str, str]] = {
    "cyberpunk": ("cyberpunk", "Neon Strike"),
    "neon": ("cyberpunk", "Neon Strike"),
    "alien": ("alien", "Alien Assault"),
    "asteroid": ("asteroid", "Asteroid Field"),
    "retro": ("retro", "Retro Blaster"),
    "pixel": ("retro", "Retro Blaster"),
    "steampunk": ("steampunk", "Brass Voyager"),
    "fantasy": ("fantasy", "Astral Wizards"),
}

_DEFAULT_THEME = ("space", "Space Defender")

_WORD_SPLIT = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class _Interpretation:
    difficulty: Difficulty
    theme: str
    title: str
    player_speed: int
    enemy_speed: int
    enemy_spawn_interval: float
    lives: int
    difficulty_scaling: bool
    warnings: tuple[str, ...]


class GeneratorService:
    """Interprets natural-language prompts into typed template configurations."""

    def __init__(self, *, supported_templates: tuple[Template, ...] = ("space_shooter",)) -> None:
        self._supported = supported_templates

    @property
    def supported_templates(self) -> tuple[Template, ...]:
        return self._supported

    def build_space_shooter(self, query: str) -> tuple[SpaceShooterConfig, list[str]]:
        interpretation = self._interpret(query)
        config = SpaceShooterConfig(
            template="space_shooter",
            title=interpretation.title,
            theme=interpretation.theme,
            difficulty=interpretation.difficulty,
            player_speed=interpretation.player_speed,
            enemy_speed=interpretation.enemy_speed,
            enemy_spawn_interval=interpretation.enemy_spawn_interval,
            lives=interpretation.lives,
            difficulty_scaling=interpretation.difficulty_scaling,
        )
        return config, list(interpretation.warnings)

    def _interpret(self, query: str) -> _Interpretation:
        normalized = " ".join(query.casefold().split())
        tokens = set(filter(None, _WORD_SPLIT.split(normalized)))
        warnings: list[str] = []

        difficulty, lives, enemy_speed, spawn_interval, difficulty_scaling = self._difficulty(tokens)

        player_speed = 6
        if any(word in tokens for word in _FAST_KEYWORDS):
            player_speed = min(player_speed + 2, 10)
            enemy_speed = min(enemy_speed + 1, 8)
        if any(word in tokens for word in _SLOW_KEYWORDS):
            player_speed = max(player_speed - 1, 3)
            enemy_speed = max(enemy_speed - 1, 1)

        if any(phrase in normalized for phrase in _DENSE_KEYWORDS):
            spawn_interval = max(round(spawn_interval - 0.5, 2), 0.5)

        if any(phrase in normalized for phrase in _SCALING_KEYWORDS):
            difficulty_scaling = True

        theme, title = self._theme(tokens, normalized)

        if not tokens:
            warnings.append("Prompt was too short; defaults were applied.")

        return _Interpretation(
            difficulty=difficulty,
            theme=theme,
            title=title,
            player_speed=player_speed,
            enemy_speed=enemy_speed,
            enemy_spawn_interval=spawn_interval,
            lives=lives,
            difficulty_scaling=difficulty_scaling,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _difficulty(tokens: set[str]) -> tuple[Difficulty, int, int, float, bool]:
        if any(word in tokens for word in _HARD_KEYWORDS):
            return "hard", 2, 6, 1.0, True
        if any(word in tokens for word in _EASY_KEYWORDS):
            return "easy", 5, 2, 3.0, False
        return "medium", 3, 3, 2.0, False

    @staticmethod
    def _theme(tokens: set[str], normalized: str) -> tuple[str, str]:
        for keyword, mapping in _THEMES.items():
            if keyword in tokens or keyword in normalized:
                return mapping
        return _DEFAULT_THEME
