"""Preference parsing: contract plus a concrete catalogue-vocabulary implementation."""

from __future__ import annotations

import re
from collections.abc import Iterable
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


_WORD_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

# Query phrases that imply a catalogue tag/genre/platform even though the
# word itself never appears verbatim in the vocabulary.
_SYNONYMS: dict[str, tuple[str, ...]] = {
    "relaxing": ("relaxing", "cozy", "chill"),
    "chill": ("relaxing", "cozy"),
    "scary": ("horror",),
    "spooky": ("horror",),
    "pc": ("pc",),
    "computer": ("pc",),
    "phone": ("mobile", "ios", "android"),
    "co-op": ("co-op", "coop"),
    "coop": ("co-op",),
    "multiplayer": ("multiplayer",),
    "singleplayer": ("single-player", "single player"),
    "solo": ("single-player", "single player"),
}


class KeywordPreferenceParser:
    """Matches free-text queries against a known catalogue vocabulary.

    Deterministic and dependency-free by design: it is seeded from the
    genres/platforms/tags that actually exist in the catalogue, so it never
    "discovers" a preference the dataset can't act on. This keeps Phase 3
    testable without a live model call, and gives Phase 4's semantic search
    a clean, normalized set of preferences to score against.
    """

    def __init__(
        self, *, known_genres: Iterable[str], known_platforms: Iterable[str], known_tags: Iterable[str]
    ) -> None:
        self._genres = {value.casefold(): value for value in known_genres}
        self._platforms = {value.casefold(): value for value in known_platforms}
        self._tags = {value.casefold(): value for value in known_tags}

    def parse(self, text: str) -> ParsedPreferences:
        normalized = " ".join(text.casefold().split())
        tokens = set(_WORD_PATTERN.findall(normalized))
        expanded = set(tokens)
        for token in tokens:
            expanded.update(_SYNONYMS.get(token, ()))

        genres = self._match(expanded, normalized, self._genres)
        platforms = self._match(expanded, normalized, self._platforms)
        tags = self._match(expanded, normalized, self._tags)

        return ParsedPreferences(
            genres=tuple(sorted(genres)),
            platforms=tuple(sorted(platforms)),
            tags=tuple(sorted(tags)),
            free_text=normalized,
        )

    @staticmethod
    def _match(tokens: set[str], normalized_text: str, vocabulary: dict[str, str]) -> set[str]:
        matched: set[str] = set()
        for key, original in vocabulary.items():
            if key in tokens or f" {key} " in f" {normalized_text} ":
                matched.add(original)
        return matched
