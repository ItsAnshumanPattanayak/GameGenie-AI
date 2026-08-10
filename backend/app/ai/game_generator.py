"""Deterministic prompt-to-configuration generation for three playable templates."""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from pydantic import TypeAdapter, ValidationError

from app.ai.prompt_normalizer import PromptNormalizer
from app.ai.template_selector import TemplateSelector
from app.schemas.ai import AIWarning, GameConfiguration, GeneratorResponse
from app.schemas.game import GameResponse

DEFAULT_CONFIGS: Final = MappingProxyType(
    {
        "space_shooter": {
            "template": "space_shooter",
            "title": "Star Defender",
            "theme": "space",
            "difficulty": "medium",
            "player_speed": 7,
            "enemy_speed": 4,
            "enemy_spawn_interval": 2.0,
            "lives": 3,
            "difficulty_scaling": False,
        },
        "endless_runner": {
            "template": "endless_runner",
            "title": "Neon Dash",
            "theme": "city",
            "difficulty": "medium",
            "player_speed": 7,
            "jump_force": 550,
            "obstacle_frequency": 2.0,
            "difficulty_scaling": False,
        },
        "maze_escape": {
            "template": "maze_escape",
            "title": "Maze Escape",
            "theme": "mystery",
            "difficulty": "medium",
            "maze_size": 15,
            "time_limit": 90,
            "obstacle_count": 5,
        },
    }
)
NUMERIC_LIMITS: Final = MappingProxyType(
    {
        "space_shooter": {
            "player_speed": (3.0, 10.0, True),
            "enemy_speed": (1.0, 8.0, True),
            "enemy_spawn_interval": (0.5, 5.0, False),
            "lives": (1.0, 5.0, True),
        },
        "endless_runner": {
            "player_speed": (4.0, 14.0, True),
            "jump_force": (300.0, 900.0, True),
            "obstacle_frequency": (0.6, 4.0, False),
        },
        "maze_escape": {
            "maze_size": (7.0, 31.0, True),
            "time_limit": (20.0, 300.0, True),
            "obstacle_count": (0.0, 20.0, True),
        },
    }
)
CONFIG_ADAPTER: Final[TypeAdapter[GameConfiguration]] = TypeAdapter(GameConfiguration)


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
        if not selection.supported or selection.template is None:
            return GeneratorResponse(success=False, selection=selection, warnings=list(selection.warnings))

        template = selection.template
        text = self.normalizer.normalize(combined).normalized
        values = dict(DEFAULT_CONFIGS[template])
        self._apply_prompt_rules(template, text, values)
        warnings, incompatible = self._apply_overrides(template, values, overrides or {})
        warnings = [*selection.warnings, *warnings]
        if incompatible:
            return GeneratorResponse(success=False, selection=selection, warnings=warnings)
        try:
            configuration = CONFIG_ADAPTER.validate_python(values)
        except ValidationError as exc:
            return GeneratorResponse(
                success=False,
                selection=selection,
                warnings=[*warnings, AIWarning(code="INVALID_CONFIGURATION", message=str(exc))],
            )
        return GeneratorResponse(success=True, selection=selection, configuration=configuration, warnings=warnings)

    def _apply_prompt_rules(self, template: str, text: str, values: dict[str, object]) -> None:
        self._apply_theme(text, values)
        if template == "space_shooter":
            self._space_rules(text, values)
        elif template == "endless_runner":
            self._runner_rules(text, values)
        else:
            self._maze_rules(text, values)

    @staticmethod
    def _apply_theme(text: str, values: dict[str, object]) -> None:
        themes = (
            ("cyberpunk", "cyberpunk"),
            ("futuristic", "futuristic"),
            ("fantasy", "fantasy"),
            ("jungle", "jungle"),
            ("desert", "desert"),
            ("neon", "neon"),
        )
        for phrase, theme in themes:
            if phrase in text:
                values["theme"] = theme
                if values["template"] == "space_shooter":
                    values["title"] = f"{theme.title()} Strike"
                elif values["template"] == "endless_runner":
                    values["title"] = f"{theme.title()} Dash"
                else:
                    values["title"] = f"{theme.title()} Labyrinth"
                break

    @staticmethod
    def _space_rules(text: str, values: dict[str, object]) -> None:
        if re.search(r"\beasy\b", text):
            values.update(difficulty="easy", lives=5, enemy_speed=2, enemy_spawn_interval=3.0)
        elif re.search(r"\b(hard|difficult)\b", text):
            values.update(difficulty="hard", lives=2, enemy_speed=6, enemy_spawn_interval=1.25)
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
        if _scaling_requested(text):
            values["difficulty_scaling"] = True

    @staticmethod
    def _runner_rules(text: str, values: dict[str, object]) -> None:
        if re.search(r"\beasy\b", text):
            values.update(difficulty="easy", player_speed=6, jump_force=650, obstacle_frequency=2.8)
        elif re.search(r"\b(hard|difficult)\b", text):
            values.update(difficulty="hard", player_speed=10, obstacle_frequency=1.1, difficulty_scaling=True)
        if "very fast runner" in text:
            values["player_speed"] = 14
        elif "fast runner" in text or "speedy runner" in text:
            values["player_speed"] = 11
        if "very high jump" in text or "huge jumps" in text:
            values["jump_force"] = 900
        elif "high jump" in text or "high jumps" in text:
            values["jump_force"] = 780
        elif "low jump" in text:
            values["jump_force"] = 380
        if "many obstacles" in text or "lots of obstacles" in text:
            values["obstacle_frequency"] = 0.8
        elif "few obstacles" in text:
            values["obstacle_frequency"] = 3.2
        if _scaling_requested(text) or "gets faster" in text:
            values["difficulty_scaling"] = True

    @staticmethod
    def _maze_rules(text: str, values: dict[str, object]) -> None:
        if re.search(r"\beasy\b", text):
            values.update(difficulty="easy", maze_size=9, time_limit=150, obstacle_count=2)
        elif re.search(r"\b(hard|difficult)\b", text):
            values.update(difficulty="hard", maze_size=25, time_limit=45, obstacle_count=14)
        if "very large maze" in text or "huge maze" in text:
            values["maze_size"] = 31
        elif "large maze" in text or "big maze" in text:
            values["maze_size"] = 25
        elif "small maze" in text:
            values["maze_size"] = 9
        if "very short timer" in text:
            values["time_limit"] = 25
        elif "short timer" in text or "quick timer" in text:
            values["time_limit"] = 45
        elif "long timer" in text:
            values["time_limit"] = 180
        if "many obstacles" in text or "lots of obstacles" in text:
            values["obstacle_count"] = 14
        elif "few obstacles" in text:
            values["obstacle_count"] = 2

    @staticmethod
    def _apply_overrides(
        template: str, values: dict[str, object], overrides: Mapping[str, object]
    ) -> tuple[list[AIWarning], bool]:
        warnings: list[AIWarning] = []
        allowed = set(DEFAULT_CONFIGS[template]) - {"template"}
        all_known = set().union(*(set(config) for config in DEFAULT_CONFIGS.values())) - {"template"}
        incompatible = False
        for field, raw_value in overrides.items():
            if field not in allowed:
                if field in all_known:
                    incompatible = True
                    warnings.append(
                        AIWarning(
                            code="TEMPLATE_INCOMPATIBLE_FIELD",
                            message=f"'{field}' is not valid for the {template} template.",
                            fields=[field],
                        )
                    )
                else:
                    warnings.append(
                        AIWarning(
                            code="UNKNOWN_OVERRIDE",
                            message=f"Unsupported override '{field}' was ignored.",
                            fields=[field],
                        )
                    )
                continue
            limits = NUMERIC_LIMITS[template]
            if field in limits:
                try:
                    number = float(raw_value)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    warnings.append(
                        AIWarning(
                            code="INVALID_OVERRIDE", message=f"Invalid value for '{field}' was ignored.", fields=[field]
                        )
                    )
                    continue
                minimum, maximum, integer = limits[field]
                clamped = min(max(number, minimum), maximum)
                if field == "maze_size":
                    clamped = int(clamped) | 1
                    clamped = min(clamped, int(maximum))
                if clamped != number:
                    warnings.append(
                        AIWarning(
                            code="VALUE_CLAMPED",
                            message=f"'{field}' was clamped to its supported range.",
                            fields=[field],
                        )
                    )
                values[field] = int(clamped) if integer else clamped
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
        return warnings, incompatible

    @staticmethod
    def _handoff_text(game: GameResponse | None) -> str:
        if game is None:
            return ""
        return " ".join([game.title, *(game.genres or []), *(game.tags or []), game.description or ""])


def _scaling_requested(text: str) -> bool:
    return any(
        phrase in text for phrase in ("gets harder", "increasing difficulty", "difficulty scaling", "gets faster")
    )
