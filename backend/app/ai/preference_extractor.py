"""Deterministic extraction, conflict detection, and confidence scoring."""

from __future__ import annotations

import re
from collections import defaultdict

from app.ai.prompt_normalizer import PromptNormalizer
from app.ai.taxonomy import TAXONOMY, category_for
from app.schemas.ai import AIWarning, ExtractedPreferences, MatchedTerm, NormalizedPrompt

_SESSION_RE = re.compile(r"\b(\d{1,3})\s*(minutes?|mins?|hours?|hrs?)\b")
_PLAYER_RE = re.compile(r"\b(?:for\s+)?(\d{1,2})\s*(?:players?|people|friends)\b")
_SHORT_SESSION = re.compile(r"\b(short|quick)\s+(?:game|session|round)\b")
_LONG_SESSION = re.compile(r"\b(long|lengthy)\s+(?:game|session|campaign)\b")


def _ordered_unique(values: list[str], category: str) -> tuple[str, ...]:
    requested = {item.casefold() for item in values}
    return tuple(item for item in TAXONOMY[category] if item.casefold() in requested)


def _warning(code: str, message: str, *fields: str) -> AIWarning:
    return AIWarning(code=code, message=message, fields=list(fields))


class PreferenceExtractor:
    def __init__(self, normalizer: PromptNormalizer | None = None) -> None:
        self.normalizer = normalizer or PromptNormalizer()

    def extract(self, prompt: str | None) -> ExtractedPreferences:
        normalized = self.normalizer.normalize(prompt)
        return self.extract_normalized(normalized)

    def extract_normalized(self, normalized: NormalizedPrompt) -> ExtractedPreferences:
        by_category: dict[str, list[str]] = defaultdict(list)
        terms: list[MatchedTerm] = []
        for match in normalized.matched_phrases:
            match_values = (
                match.canonical.split() if match.canonical == "multiplayer cooperative" else [match.canonical]
            )
            for value in match_values:
                category = category_for(value)
                if category:
                    by_category[category].append(value)
                    terms.append(MatchedTerm(source=match.source, canonical=value, category=category))

        # Scan canonical values as a safety net when normalized data is injected by another integration.
        for category, canonical_values in TAXONOMY.items():
            for value in canonical_values:
                if re.search(rf"(?<!\w){re.escape(value.casefold())}(?!\w)", normalized.normalized.casefold()):
                    by_category[category].append(value)

        text = normalized.normalized
        session_length = self._session_length(text)
        player_count = self._player_count(text)
        warnings = self._conflicts(by_category, text, player_count)
        confidence = self._confidence(normalized, by_category, warnings)
        hard_filters = self._hard_filters(text, by_category)

        return ExtractedPreferences(
            genres=_ordered_unique(by_category["genres"], "genres"),
            platforms=_ordered_unique(by_category["platforms"], "platforms"),
            modes=_ordered_unique(by_category["modes"], "modes"),
            themes=_ordered_unique(by_category["themes"], "themes"),
            moods=_ordered_unique(by_category["moods"], "moods"),
            visual_styles=_ordered_unique(by_category["visual_styles"], "visual_styles"),
            difficulty=self._single_value(by_category["difficulty"], "difficulty"),
            price_type=self._single_value(by_category["price_type"], "price_type"),
            hardware_level=self._single_value(by_category["hardware_level"], "hardware_level"),
            session_length=session_length,
            player_count=player_count,
            hard_filters=hard_filters,
            warnings=tuple(warnings),
            matched_terms=tuple(self._unique_terms(terms)),
            confidence=confidence,
        )

    @staticmethod
    def _hard_filters(text: str, by_category: dict[str, list[str]]) -> tuple[str, ...]:
        filters: list[str] = []
        soft_request = any(phrase in text for phrase in ("prefer", "ideally", "if possible", "nice to have"))
        if by_category["platforms"] and (" for " in f" {text} " or "only" in text):
            filters.append("platform")
        if not soft_request and set(by_category["price_type"]) == {"free"}:
            filters.append("free")
        if not soft_request and "multiplayer" in by_category["modes"]:
            filters.append("multiplayer")
        if not soft_request and "offline" in by_category["modes"]:
            filters.append("offline")
        return tuple(filters)

    @staticmethod
    def _single_value(values: list[str], category: str) -> str | None:
        ordered = _ordered_unique(values, category)
        return ordered[0] if ordered else None

    @staticmethod
    def _unique_terms(terms: list[MatchedTerm]) -> list[MatchedTerm]:
        seen: set[tuple[str, str, str | None]] = set()
        output: list[MatchedTerm] = []
        for term in terms:
            key = (term.source.casefold(), term.canonical, term.category)
            if key not in seen:
                seen.add(key)
                output.append(term)
        return output

    @staticmethod
    def _session_length(text: str) -> int | None:
        match = _SESSION_RE.search(text)
        if match:
            value = int(match.group(1))
            return value * 60 if match.group(2).startswith(("hour", "hr")) else value
        if _SHORT_SESSION.search(text):
            return 20
        if _LONG_SESSION.search(text):
            return 120
        return None

    @staticmethod
    def _player_count(text: str) -> int | None:
        match = _PLAYER_RE.search(text)
        return int(match.group(1)) if match else None

    @staticmethod
    def _conflicts(by_category: dict[str, list[str]], text: str, player_count: int | None) -> list[AIWarning]:
        result: list[AIWarning] = []
        prices = set(by_category["price_type"])
        difficulties = set(by_category["difficulty"])
        modes = set(by_category["modes"])
        hardware = set(by_category["hardware_level"])
        if {"free", "paid"} <= prices:
            result.append(_warning("CONFLICT_PRICE", "Both free and paid pricing were requested.", "price_type"))
        if {"easy", "hard"} <= difficulties:
            result.append(
                _warning("CONFLICT_DIFFICULTY", "Both easy and hard difficulty were requested.", "difficulty")
            )
        if {"online", "offline"} <= modes and ("only" in text or "without internet" in text):
            result.append(
                _warning("CONFLICT_CONNECTIVITY", "Both online-only and offline-only play were requested.", "modes")
            )
        if {"single-player", "multiplayer"} <= modes and "only" in text:
            result.append(
                _warning("CONFLICT_MODE", "Both single-player-only and multiplayer-only were requested.", "modes")
            )
        if {"low-end", "high-end"} <= hardware:
            result.append(
                _warning("CONFLICT_HARDWARE", "Both low-end and high-end hardware were requested.", "hardware_level")
            )
        if player_count == 1 and "multiplayer" in modes:
            result.append(
                _warning(
                    "CONFLICT_PLAYER_COUNT",
                    "One player conflicts with the multiplayer request.",
                    "player_count",
                    "modes",
                )
            )
        return result

    @staticmethod
    def _confidence(
        normalized: NormalizedPrompt, by_category: dict[str, list[str]], warnings: list[AIWarning]
    ) -> float:
        if not normalized.normalized:
            return 0.0
        meaningful = [token for token in normalized.tokens if len(token) > 1]
        recognized_tokens = {
            token.casefold()
            for category_values in by_category.values()
            for value in category_values
            for token in re.findall(r"[\w-]+", value)
        }
        recognized = sum(token.casefold() in recognized_tokens for token in meaningful)
        coverage = sum(bool(values) for values in by_category.values())
        phrase_bonus = min(len(normalized.matched_phrases), 5) / 5
        ratio = recognized / max(len(meaningful), 1)
        score = 0.12 + 0.38 * ratio + 0.34 * min(coverage / 5, 1) + 0.16 * phrase_bonus
        score -= min(len(warnings) * 0.12, 0.36)
        if coverage == 0:
            score = min(score, 0.18)
        elif coverage == 1:
            score = min(score, 0.58)
        return round(max(0.0, min(1.0, score)), 3)


def extract_preferences(prompt: str | None) -> ExtractedPreferences:
    return PreferenceExtractor().extract(prompt)
