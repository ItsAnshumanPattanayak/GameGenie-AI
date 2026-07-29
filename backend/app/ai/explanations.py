"""Explanation generation contract for recommendation results."""

from typing import Protocol

from app.ai.preference_parser import ParsedPreferences
from app.schemas.game import GameResponse


class ExplanationGenerator(Protocol):
    def explain(self, game: GameResponse, preferences: ParsedPreferences) -> str:
        """Explain the strongest matching attributes in plain language."""
        ...
