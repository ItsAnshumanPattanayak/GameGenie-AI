"""Preference parser protocols and backward-compatible adapters."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Protocol

from app.ai.preference_extractor import PreferenceExtractor
from app.schemas.ai import ExtractedPreferences

ParsedPreferences = ExtractedPreferences


class PreferenceParser(Protocol):
    def parse(self, text: str) -> ParsedPreferences: ...


class RuleBasedPreferenceParser:
    """Primary deterministic parser backed by the Sprint 2 extractor."""

    def __init__(self) -> None:
        self._extractor = PreferenceExtractor()

    def parse(self, text: str) -> ParsedPreferences:
        return self._extractor.extract(text)


class KeywordPreferenceParser(RuleBasedPreferenceParser):
    """Compatibility adapter for main-branch catalogue-vocabulary callers.

    The Sprint 2 extractor remains authoritative. Known catalogue values are
    only overlaid when they occur verbatim, preserving older search contracts
    without reintroducing a second synonym or interpretation system.
    """

    def __init__(
        self,
        *,
        known_genres: Iterable[str] = (),
        known_platforms: Iterable[str] = (),
        known_tags: Iterable[str] = (),
    ) -> None:
        super().__init__()
        self._known_genres = tuple(known_genres)
        self._known_platforms = tuple(known_platforms)
        self._known_tags = tuple(known_tags)

    def parse(self, text: str) -> ParsedPreferences:
        parsed = super().parse(text)
        normalized = parsed.free_text
        return parsed.model_copy(
            update={
                "genres": self._merge(parsed.genres, self._matches(normalized, self._known_genres)),
                "platforms": self._merge(parsed.platforms, self._matches(normalized, self._known_platforms)),
                "tags": self._merge(parsed.tags, self._matches(normalized, self._known_tags)),
            }
        )

    @staticmethod
    def _matches(text: str, vocabulary: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            value for value in vocabulary if re.search(rf"(?<!\w){re.escape(value.casefold())}(?!\w)", text.casefold())
        )

    @staticmethod
    def _merge(current: tuple[str, ...], additions: tuple[str, ...]) -> tuple[str, ...]:
        seen: set[str] = set()
        merged: list[str] = []
        for value in (*current, *additions):
            key = value.casefold()
            if key not in seen:
                seen.add(key)
                merged.append(value)
        return tuple(merged)
