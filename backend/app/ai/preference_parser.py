"""Preference parsing contracts for future natural-language processing."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ParsedPreferences:
    genres: tuple[str, ...] = field(default_factory=tuple)
    platforms: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    free_text: str = ""


class PreferenceParser(Protocol):
    def parse(self, text: str) -> ParsedPreferences:
        """Convert natural language into normalized catalogue preferences."""
        ...
