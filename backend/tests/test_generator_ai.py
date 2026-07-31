"""Template selection and prompt-to-configuration coverage (15+ cases)."""

import pytest

from app.ai.game_generator import GameConfigurationGenerator
from app.ai.template_selector import TemplateSelector
from app.schemas.game import GameResponse


@pytest.mark.parametrize(
    ("prompt", "supported"),
    [
        ("space shooter", True),
        ("cyberpunk space shooter", True),
        ("arcade spaceship combat", True),
        ("shooter", False),
        ("farming game", False),
        ("racing request", False),
        ("", False),
    ],
)
def test_template_selection(prompt: str, supported: bool) -> None:
    selection = TemplateSelector().select(prompt)
    assert selection.supported is supported
    assert (selection.template == "space_shooter") is supported


@pytest.mark.parametrize(
    ("prompt", "field", "expected"),
    [
        ("space shooter", "difficulty", "medium"),
        ("cyberpunk space shooter", "theme", "cyberpunk"),
        ("easy space shooter", "lives", 5),
        ("hard space shooter", "lives", 2),
        ("space shooter fast player", "player_speed", 8),
        ("space shooter very fast player", "player_speed", 10),
        ("space shooter very fast enemies", "enemy_speed", 7),
        ("space shooter many enemies", "enemy_spawn_interval", 1.0),
        ("space shooter few enemies", "enemy_spawn_interval", 4.0),
        ("space shooter increasing difficulty", "difficulty_scaling", True),
    ],
)
def test_prompt_configuration(prompt: str, field: str, expected: object) -> None:
    result = GameConfigurationGenerator().generate(prompt)
    assert result.success and result.configuration is not None
    assert getattr(result.configuration, field) == expected


def test_override_clamping_and_title_sanitizing() -> None:
    result = GameConfigurationGenerator().generate(
        "space shooter", overrides={"player_speed": 99, "enemy_spawn_interval": 0, "title": "<Bad>; Strike"}
    )
    assert result.configuration is not None
    assert result.configuration.player_speed == 10 and result.configuration.enemy_spawn_interval == 0.5
    assert result.configuration.title == "Bad Strike"
    assert {warning.code for warning in result.warnings} == {"VALUE_CLAMPED", "TITLE_SANITIZED"}


def test_invalid_override_is_controlled() -> None:
    result = GameConfigurationGenerator().generate(
        "space shooter", overrides={"enemy_speed": "quick", "difficulty": "impossible", "script": "alert(1)"}
    )
    assert result.success and result.configuration is not None
    assert len(result.warnings) == 3


def test_recommendation_handoff_and_serialization() -> None:
    game = GameResponse(
        id="iron", title="Iron Comet", description="Spaceship combat", genres=["Action"], tags=["space", "cyberpunk"]
    )
    result = GameConfigurationGenerator().generate("fast enemies", selected_game=game)
    assert result.success and result.configuration is not None
    assert result.configuration.theme == "cyberpunk" and result.configuration.enemy_speed == 6
    assert result.model_dump(mode="json")["configuration"]["template"] == "space_shooter"


def test_deterministic_repeated_generation() -> None:
    generator = GameConfigurationGenerator()
    prompt = "Create a difficult cyberpunk space shooter with fast enemies and increasing difficulty"
    first = generator.generate(prompt)
    assert first == generator.generate(prompt)
    assert first.configuration is not None
    assert first.configuration.difficulty == "hard"
    assert first.configuration.enemy_speed >= 6 and first.configuration.difficulty_scaling
    assert 3 <= first.configuration.player_speed <= 10
    assert 1 <= first.configuration.enemy_speed <= 8
