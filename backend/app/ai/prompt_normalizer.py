"""Unicode-safe, longest-phrase-first prompt normalization."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.ai.taxonomy import SYNONYMS, category_for
from app.schemas.ai import MatchedTerm, NormalizedPrompt

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.IGNORECASE)
_CONTRACTIONS = {"can't": "cannot", "won't": "will not", "don't": "do not", "isn't": "is not", "i'd": "i would"}
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "be",
        "create",
        "for",
        "game",
        "games",
        "give",
        "i",
        "in",
        "is",
        "it",
        "me",
        "of",
        "on",
        "or",
        "please",
        "something",
        "that",
        "the",
        "to",
        "want",
        "with",
    }
)


@dataclass(frozen=True)
class _PhraseMatch:
    start: int
    end: int
    source: str
    canonical: str


class PromptNormalizer:
    """Normalize prompts without replacing aliases inside unrelated words."""

    def __init__(self, aliases: dict[str, str] | None = None) -> None:
        source = aliases or dict(SYNONYMS)
        self._aliases = tuple(sorted(source.items(), key=lambda item: (-len(item[0].split()), -len(item[0]), item[0])))

    @staticmethod
    def _clean(prompt: str | None) -> str:
        if not isinstance(prompt, str):
            return ""
        text = unicodedata.normalize("NFKC", prompt).replace("’", "'").casefold().strip()
        for contraction, expanded in _CONTRACTIONS.items():
            text = re.sub(rf"(?<!\w){re.escape(contraction)}(?!\w)", expanded, text)
        text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
        return re.sub(r"\s+", " ", text).strip()

    def normalize(self, prompt: str | None) -> NormalizedPrompt:
        original = prompt if isinstance(prompt, str) else ""
        cleaned = self._clean(prompt)
        if not cleaned:
            return NormalizedPrompt(original=original, normalized="")

        occupied = [False] * len(cleaned)
        matches: list[_PhraseMatch] = []
        for source, canonical in self._aliases:
            # Spaces in an alias tolerate either whitespace or hyphens, while explicit hyphens remain meaningful.
            expression = re.escape(source).replace(r"\ ", r"[\s-]+")
            for found in re.finditer(rf"(?<!\w){expression}(?!\w)", cleaned, re.IGNORECASE):
                if any(occupied[found.start() : found.end()]):
                    continue
                occupied[found.start() : found.end()] = [True] * (found.end() - found.start())
                matches.append(_PhraseMatch(found.start(), found.end(), found.group(0), canonical))

        matches.sort(key=lambda item: item.start)
        parts: list[str] = []
        cursor = 0
        for match in matches:
            parts.append(cleaned[cursor : match.start])
            parts.append(match.canonical)
            cursor = match.end
        parts.append(cleaned[cursor:])
        normalized = re.sub(r"\s+", " ", "".join(parts)).strip()

        tokens = _TOKEN_RE.findall(normalized)
        deduplicated: list[str] = []
        for token in tokens:
            if not deduplicated or token != deduplicated[-1]:
                deduplicated.append(token)
        normalized = " ".join(deduplicated)

        matched_terms = [
            MatchedTerm(source=match.source, canonical=match.canonical, category=category_for(match.canonical))
            for match in matches
        ]
        recognized = {token.casefold() for match in matches for token in _TOKEN_RE.findall(match.canonical)}
        unmatched = [token for token in deduplicated if token.casefold() not in recognized and token not in _STOPWORDS]
        return NormalizedPrompt(
            original=original,
            normalized=normalized,
            tokens=deduplicated,
            matched_phrases=matched_terms,
            unmatched_tokens=unmatched,
        )


def normalize_prompt(prompt: str | None) -> NormalizedPrompt:
    return PromptNormalizer().normalize(prompt)
