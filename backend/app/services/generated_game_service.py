"""Configuration compatibility and response helpers for saved generated games."""

from dataclasses import dataclass
from typing import Any

from pydantic import TypeAdapter, ValidationError

from app.core.exceptions import AppError
from app.db.models import GeneratedGame
from app.schemas.ai import GameConfiguration
from app.schemas.generated_games import (
    CURRENT_CONFIG_VERSION,
    GeneratedGameResponse,
    PublicGeneratedGameResponse,
)

CONFIGURATION_ADAPTER: TypeAdapter[GameConfiguration] = TypeAdapter(GameConfiguration)
COMPATIBLE_CONFIG_VERSIONS = frozenset({"1.0", CURRENT_CONFIG_VERSION})


@dataclass(frozen=True)
class CompatibleConfiguration:
    configuration: GameConfiguration
    config_version: str
    migrated_from_version: str | None


def validate_configuration(
    configuration: dict[str, Any] | dict[str, object],
    template_type: str,
    config_version: str,
) -> CompatibleConfiguration:
    if not isinstance(configuration, dict):
        raise AppError("INVALID_GAME_CONFIGURATION", "The saved game configuration must be an object.", 422)
    if config_version not in COMPATIBLE_CONFIG_VERSIONS:
        if not _looks_like_version(config_version):
            raise AppError("INVALID_CONFIG_VERSION", "The configuration version is malformed.", 422)
        raise AppError(
            "UNSUPPORTED_CONFIG_VERSION",
            f"Configuration version {config_version} is not supported. Supported versions are 1.0 and 1.1.",
            422,
        )
    if template_type not in {"space_shooter", "endless_runner", "maze_escape"}:
        raise AppError("INVALID_TEMPLATE_TYPE", "The generated-game template is not supported.", 422)
    candidate = dict(configuration)
    if config_version == "1.0" and "template" not in candidate:
        candidate["template"] = template_type
    if candidate.get("template") != template_type:
        raise AppError(
            "TEMPLATE_CONFIGURATION_MISMATCH",
            "The configuration template does not match template_type.",
            422,
        )
    try:
        validated = CONFIGURATION_ADAPTER.validate_python(candidate)
    except ValidationError as exc:
        fields = ", ".join(".".join(map(str, error["loc"])) for error in exc.errors())
        message = "The saved game configuration is invalid."
        if fields:
            message = f"The saved game configuration is invalid for {template_type}: {fields}."
        raise AppError("INVALID_GAME_CONFIGURATION", message, 422) from exc
    migrated_from = config_version if config_version != CURRENT_CONFIG_VERSION else None
    return CompatibleConfiguration(validated, CURRENT_CONFIG_VERSION, migrated_from)


def generated_game_response(row: GeneratedGame, migrated_from: str | None = None) -> GeneratedGameResponse:
    compatible = validate_configuration(row.configuration, row.template_type, row.config_version)
    return GeneratedGameResponse(
        id=row.id,
        title=row.title,
        prompt=row.prompt,
        template_type=row.template_type,
        configuration=compatible.configuration,
        config_version=compatible.config_version,
        migrated_from_version=migrated_from or compatible.migrated_from_version,
        public_slug=row.public_slug,
        is_public=row.is_public,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def public_generated_game_response(row: GeneratedGame) -> PublicGeneratedGameResponse:
    compatible = validate_configuration(row.configuration, row.template_type, row.config_version)
    if row.public_slug is None:
        raise AppError("PUBLIC_GAME_NOT_FOUND", "The shared game is unavailable.", 404)
    return PublicGeneratedGameResponse(
        title=row.title,
        template_type=row.template_type,
        configuration=compatible.configuration,
        config_version=compatible.config_version,
        migrated_from_version=compatible.migrated_from_version,
        public_slug=row.public_slug,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _looks_like_version(value: str) -> bool:
    parts = value.split(".")
    return len(parts) == 2 and all(part.isdigit() for part in parts)
