"""Deterministic selection across the three supported mini-game templates."""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

from app.ai.prompt_normalizer import PromptNormalizer
from app.schemas.ai import AIWarning, TemplateSelection

TemplateIdentifier: TypeAlias = Literal["space_shooter", "endless_runner", "maze_escape"]
TEMPLATE_PRIORITY: Final[tuple[TemplateIdentifier, ...]] = ("space_shooter", "endless_runner", "maze_escape")
STRONG_SIGNALS: Final = MappingProxyType(
    {
        "space_shooter": (
            "space shooter",
            "alien shooter",
            "spaceship combat",
            "starship combat",
            "galactic combat",
        ),
        "endless_runner": ("endless runner", "endless running", "obstacle race", "running game", "runner"),
        "maze_escape": ("maze escape", "escape labyrinth", "find the exit", "labyrinth", "maze"),
    }
)
WEAK_SIGNALS: Final = MappingProxyType(
    {
        "space_shooter": ("spaceship", "starship", "alien", "shooter", "blaster", "galactic"),
        "endless_runner": ("running", "run", "jump", "obstacle", "platformer"),
        "maze_escape": ("escape", "exit", "puzzle corridors"),
    }
)


class TemplateSelector:
    def __init__(self, normalizer: PromptNormalizer | None = None) -> None:
        self.normalizer = normalizer or PromptNormalizer()

    def select(self, prompt: str | None) -> TemplateSelection:
        original = (prompt or "").strip()
        normalized = self.normalizer.normalize(prompt).normalized
        text = f"{original.casefold()} {normalized.casefold()}".strip()
        if not text:
            return TemplateSelection(
                reason="A non-empty prompt is required to select a template.",
                original_prompt=original,
            )
        scores = {template: self._score(text, template) for template in TEMPLATE_PRIORITY}
        highest = max(scores.values())
        if highest < 2:
            return TemplateSelection(
                supported=False,
                confidence=0.0,
                reason="The requested game type does not reasonably match any implemented template.",
                original_prompt=original,
                warnings=[
                    AIWarning(
                        code="UNSUPPORTED_TEMPLATE",
                        message="Only space_shooter, endless_runner, and maze_escape are currently playable.",
                    )
                ],
            )
        winners = [template for template in TEMPLATE_PRIORITY if scores[template] == highest]
        selected = winners[0]
        ambiguous = len(winners) > 1
        fallback = highest < 4 or ambiguous
        warnings: list[AIWarning] = []
        if ambiguous:
            warnings.append(
                AIWarning(
                    code="AMBIGUOUS_TEMPLATE",
                    message=f"Multiple templates matched; deterministically selected {selected}.",
                )
            )
        elif fallback:
            warnings.append(
                AIWarning(
                    code="CLOSEST_TEMPLATE",
                    message=f"The original request is only partially supported and was adapted to {selected}.",
                )
            )
        confidence = min(0.99, 0.52 + highest * 0.08 - (0.12 if ambiguous else 0.0))
        return TemplateSelection(
            template=selected,
            supported=True,
            fallback=fallback,
            confidence=round(confidence, 2),
            reason=(
                f"Selected {selected} as the deterministic closest playable template."
                if fallback
                else f"The prompt directly matches the {selected} template."
            ),
            original_prompt=original,
            warnings=warnings,
        )

    @staticmethod
    def _score(text: str, template: TemplateIdentifier) -> int:
        strong = 4 if any(_contains(text, phrase) for phrase in STRONG_SIGNALS[template]) else 0
        weak = sum(1 for phrase in WEAK_SIGNALS[template] if _contains(text, phrase))
        return strong + min(weak, 3)


def _contains(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None
