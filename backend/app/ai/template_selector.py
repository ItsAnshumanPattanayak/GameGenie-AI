"""Extensible, controlled template selection for generated mini-games."""

from __future__ import annotations

from app.ai.prompt_normalizer import PromptNormalizer
from app.schemas.ai import TemplateSelection


class TemplateSelector:
    def __init__(self, normalizer: PromptNormalizer | None = None) -> None:
        self.normalizer = normalizer or PromptNormalizer()

    def select(self, prompt: str | None) -> TemplateSelection:
        text = self.normalizer.normalize(prompt).normalized
        if not text:
            return TemplateSelection(reason="A non-empty prompt is required to select a template.")
        space_signal = any(phrase in text for phrase in ("space", "spaceship", "starship", "galactic"))
        shooter_signal = any(
            phrase in text for phrase in ("first-person shooter", "third-person shooter", "shoot", "combat", "blaster")
        )
        arcade_signal = "arcade" in text
        if space_signal and shooter_signal:
            confidence = 0.98 if arcade_signal else 0.92
            return TemplateSelection(
                template="space_shooter",
                supported=True,
                confidence=confidence,
                reason="The prompt combines space action with shooting or combat.",
            )
        return TemplateSelection(
            supported=False,
            confidence=0.0,
            reason="No implemented template matches this prompt; only space_shooter is currently supported.",
        )
