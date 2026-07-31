"""Backward-compatible preference parser facade."""

from typing import Protocol

from app.ai.preference_extractor import PreferenceExtractor
from app.schemas.ai import ExtractedPreferences

ParsedPreferences = ExtractedPreferences


class PreferenceParser(Protocol):
    def parse(self, text: str) -> ParsedPreferences: ...


class RuleBasedPreferenceParser:
    def __init__(self) -> None:
        self._extractor = PreferenceExtractor()

    def parse(self, text: str) -> ParsedPreferences:
        return self._extractor.extract(text)
