"""Deterministic prompt-to-Phaser configuration generation."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Final

from pydantic import ValidationError

from app.ai.prompt_normalizer import PromptNormalizer
from app.ai.template_selector import TemplateSelector
from app.schemas.ai import AIWarning, GameConfiguration, GeneratorResponse
from app.schemas.game import GameResponse

DEFAULT_CONFIG: Final = {
    "template": "space_shooter",
    "title": "Star Defender",
    "theme": "space",
    "difficulty": "medium",
    "player_speed": 7,
    "enemy_speed": 4,
    "enemy_spawn_interval": 2.0,
    "lives": 3,
    "difficulty_scaling": False,
}
_LIMITS: Final = {
    "player_speed": (3.0, 10.0),
    "enemy_speed": (1.0, 8.0),
    "enemy_spawn_interval": (0.5, 5.0),
    "lives": (1.0, 5.0),
}


class GameConfigurationGenerator:
    def __init__(self, normalizer: PromptNormalizer | None = None, selector: TemplateSelector | None = None) -> None:
        self.normalizer = normalizer or PromptNormalizer()
        self.selector = selector or TemplateSelector(self.normalizer)

    def generate(
        self,
        prompt: str | None,
        *,
        selected_game: GameResponse | None = None,
        overrides: Mapping[str, object] | None = None,
    ) -> GeneratorResponse:
        handoff = self._handoff_text(selected_game)
        combined = " ".join(part for part in (prompt or "", handoff) if part).strip()
        selection = self.selector.select(combined)
        if not selection.supported:
            return GeneratorResponse(success=False, selection=selection)

        text = self.normalizer.normalize(combined).normalized
        values = dict(DEFAULT_CONFIG)
        self._apply_prompt_rules(text, values)
        warnings = self._apply_overrides(values, overrides or {})
        try:
            configuration = GameConfiguration.model_validate(values)
        except ValidationError as exc:
            return GeneratorResponse(
                success=False,
                selection=selection,
                warnings=[AIWarning(code="INVALID_CONFIGURATION", message=str(exc))],
            )
        return GeneratorResponse(success=True, selection=selection, configuration=configuration, warnings=warnings)

    @staticmethod
    def _apply_prompt_rules(text: str, values: dict[str, object]) -> None:
        if "cyberpunk" in text:
            values.update(theme="cyberpunk", title="Cyber Strike")
        elif "futuristic" in text:
            values.update(theme="futuristic", title="Future Strike")
        if "very fast player" in text:
            values["player_speed"] = 10
        elif "fast player" in text:
            values["player_speed"] = 8
        if "very fast enemies" in text:
            values["enemy_speed"] = 7
        elif "fast enemies" in text:
            values["enemy_speed"] = 6
        if "many enemies" in text or "lots of enemies" in text:
            values["enemy_spawn_interval"] = 1.0
        elif "few enemies" in text:
            values["enemy_spawn_interval"] = 4.0
        if re.search(r"\beasy\b", text):
            values.update(difficulty="easy", lives=5, enemy_speed=2, enemy_spawn_interval=3.0)
        elif re.search(r"\b(hard|difficult)\b", text):
            existing_speed = values["enemy_speed"]
            enemy_speed = int(existing_speed) if isinstance(existing_speed, (int, float, str)) else 4
            values.update(
                difficulty="hard",
                lives=2,
                enemy_speed=max(enemy_speed, 6),
                enemy_spawn_interval=1.25,
            )
        if any(phrase in text for phrase in ("gets harder", "increasing difficulty", "difficulty scaling")):
            values["difficulty_scaling"] = True

    @staticmethod
    def _apply_overrides(values: dict[str, object], overrides: Mapping[str, object]) -> list[AIWarning]:
        warnings: list[AIWarning] = []
        allowed = set(DEFAULT_CONFIG) - {"template"}
        for field, raw_value in overrides.items():
            if field not in allowed:
                warnings.append(
                    AIWarning(
                        code="UNKNOWN_OVERRIDE", message=f"Unsupported override '{field}' was ignored.", fields=[field]
                    )
                )
                continue
            if field in _LIMITS:
                try:
                    number = float(raw_value)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    warnings.append(
                        AIWarning(
                            code="INVALID_OVERRIDE", message=f"Invalid value for '{field}' was ignored.", fields=[field]
                        )
                    )
                    continue
                minimum, maximum = _LIMITS[field]
                clamped = min(max(number, minimum), maximum)
                if clamped != number:
                    warnings.append(
                        AIWarning(
                            code="VALUE_CLAMPED",
                            message=f"'{field}' was clamped to the supported range {minimum:g}-{maximum:g}.",
                            fields=[field],
                        )
                    )
                values[field] = clamped if field == "enemy_spawn_interval" else int(clamped)
            elif field == "title":
                safe = re.sub(r"[^A-Za-z0-9 '&-]", "", str(raw_value))[:60].strip()
                if not safe:
                    warnings.append(
                        AIWarning(code="INVALID_TITLE", message="Unsafe or empty title was ignored.", fields=[field])
                    )
                else:
                    if safe != str(raw_value):
                        warnings.append(
                            AIWarning(code="TITLE_SANITIZED", message="The title was sanitized.", fields=[field])
                        )
                    values[field] = safe
            elif field == "difficulty" and raw_value not in {"easy", "medium", "hard"}:
                warnings.append(
                    AIWarning(code="INVALID_OVERRIDE", message="Unsupported difficulty was ignored.", fields=[field])
                )
            else:
                values[field] = raw_value
        return warnings

    @staticmethod
    def _handoff_text(game: GameResponse | None) -> str:
        if game is None:
            return ""
        return " ".join([game.title, *(game.genres or []), *(game.tags or []), game.description or ""])
