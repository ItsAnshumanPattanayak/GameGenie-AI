"""Three-template selection, discriminated validation, and generation coverage."""

import pytest
from pydantic import TypeAdapter, ValidationError

from app.ai.game_generator import GameConfigurationGenerator
from app.ai.template_selector import TemplateSelector
from app.schemas.ai import EndlessRunnerConfig, GameConfiguration, MazeEscapeConfig


@pytest.mark.parametrize(
    ("prompt", "template"),
    [
        ("space shooter", "space_shooter"),
        ("alien shooter", "space_shooter"),
        ("spaceship combat", "space_shooter"),
        ("endless runner", "endless_runner"),
        ("endless running", "endless_runner"),
        ("obstacle race", "endless_runner"),
        ("maze escape", "maze_escape"),
        ("escape labyrinth", "maze_escape"),
        ("find the exit", "maze_escape"),
        ("maze", "maze_escape"),
    ],
)
def test_supported_template_synonyms(prompt: str, template: str) -> None:
    selection = TemplateSelector().select(prompt)
    assert selection.supported and selection.template == template
    assert selection.original_prompt == prompt


def test_ambiguous_prompt_uses_deterministic_priority_and_warning() -> None:
    selection = TemplateSelector().select("obstacle race maze escape")
    assert selection.template == "endless_runner"
    assert selection.fallback
    assert [warning.code for warning in selection.warnings] == ["AMBIGUOUS_TEMPLATE"]


def test_reasonable_partial_match_uses_warned_fallback() -> None:
    selection = TemplateSelector().select("jump over obstacle challenge")
    assert selection.template == "endless_runner" and selection.fallback
    assert selection.warnings[0].code == "CLOSEST_TEMPLATE"


@pytest.mark.parametrize("prompt", ["farming simulator", "turn-based card game", "", "shooter"])
def test_unsupported_or_insufficient_prompts_do_not_claim_support(prompt: str) -> None:
    selection = TemplateSelector().select(prompt)
    assert not selection.supported and selection.template is None
    if prompt:
        assert selection.warnings[0].code == "UNSUPPORTED_TEMPLATE"


@pytest.mark.parametrize(
    ("prompt", "field", "expected"),
    [
        ("endless runner", "theme", "city"),
        ("fast runner", "player_speed", 11),
        ("very fast runner", "player_speed", 14),
        ("runner with high jumps", "jump_force", 780),
        ("runner with huge jumps", "jump_force", 900),
        ("runner with low jump", "jump_force", 380),
        ("runner with many obstacles", "obstacle_frequency", 0.8),
        ("runner with few obstacles", "obstacle_frequency", 3.2),
        ("runner that gets faster", "difficulty_scaling", True),
        ("easy endless runner", "difficulty", "easy"),
        ("hard endless runner", "difficulty", "hard"),
        ("cyberpunk endless runner", "theme", "cyberpunk"),
    ],
)
def test_endless_runner_prompt_configuration(prompt: str, field: str, expected: object) -> None:
    result = GameConfigurationGenerator().generate(prompt)
    assert result.success and result.configuration is not None
    assert result.configuration.template == "endless_runner"
    assert getattr(result.configuration, field) == expected


def test_runner_boundaries_are_clamped_and_typed() -> None:
    result = GameConfigurationGenerator().generate(
        "endless runner",
        overrides={"player_speed": 999, "jump_force": 1, "obstacle_frequency": 0},
    )
    assert result.configuration is not None
    assert isinstance(result.configuration, EndlessRunnerConfig)
    assert result.configuration.player_speed == 14
    assert result.configuration.jump_force == 300
    assert result.configuration.obstacle_frequency == 0.6
    assert [warning.code for warning in result.warnings].count("VALUE_CLAMPED") == 3


@pytest.mark.parametrize(
    ("prompt", "field", "expected"),
    [
        ("maze escape", "theme", "mystery"),
        ("large maze", "maze_size", 25),
        ("very large maze", "maze_size", 31),
        ("small maze", "maze_size", 9),
        ("maze with short timer", "time_limit", 45),
        ("maze with very short timer", "time_limit", 25),
        ("maze with long timer", "time_limit", 180),
        ("maze with many obstacles", "obstacle_count", 14),
        ("maze with few obstacles", "obstacle_count", 2),
        ("easy maze escape", "difficulty", "easy"),
        ("hard maze escape", "difficulty", "hard"),
        ("jungle maze escape", "theme", "jungle"),
    ],
)
def test_maze_escape_prompt_configuration(prompt: str, field: str, expected: object) -> None:
    result = GameConfigurationGenerator().generate(prompt)
    assert result.success and result.configuration is not None
    assert result.configuration.template == "maze_escape"
    assert getattr(result.configuration, field) == expected


def test_maze_boundaries_are_clamped_and_even_size_becomes_valid_odd_size() -> None:
    result = GameConfigurationGenerator().generate(
        "maze escape",
        overrides={"maze_size": 20, "time_limit": 1, "obstacle_count": 100},
    )
    assert result.configuration is not None
    assert isinstance(result.configuration, MazeEscapeConfig)
    assert result.configuration.maze_size == 21
    assert result.configuration.time_limit == 20
    assert result.configuration.obstacle_count == 20


@pytest.mark.parametrize(
    "payload",
    [
        {"template": "space_shooter", "title": "X", "theme": "space", "difficulty": "medium", "maze_size": 15},
        {"template": "endless_runner", "title": "X", "theme": "city", "difficulty": "medium", "lives": 3},
        {"template": "maze_escape", "title": "X", "theme": "mystery", "difficulty": "medium", "jump_force": 500},
        {"template": "maze_escape", "title": "X", "theme": "mystery", "difficulty": "medium", "maze_size": 10},
        {"template": "platformer", "title": "X", "theme": "city", "difficulty": "medium"},
    ],
)
def test_discriminated_configuration_rejects_invalid_or_wrong_template_fields(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(GameConfiguration).validate_python(payload)


def test_generator_reports_template_incompatible_override_as_failure() -> None:
    result = GameConfigurationGenerator().generate("space shooter", overrides={"maze_size": 15})
    assert not result.success and result.configuration is None
    assert result.warnings[0].code == "TEMPLATE_INCOMPATIBLE_FIELD"


def test_space_shooter_generation_regression() -> None:
    result = GameConfigurationGenerator().generate(
        "hard cyberpunk space shooter with fast enemies and increasing difficulty"
    )
    assert result.success and result.configuration is not None
    assert result.configuration.template == "space_shooter"
    assert result.configuration.theme == "cyberpunk"
    assert result.configuration.enemy_speed == 6
    assert result.configuration.lives == 2
    assert result.configuration.difficulty_scaling is True
