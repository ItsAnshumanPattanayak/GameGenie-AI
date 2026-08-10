"""Owner-scoped generated-game persistence and anonymous public playback."""

import secrets

from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies import CurrentUserDep, DbDep
from app.core.exceptions import AppError
from app.db.models import GeneratedGame
from app.schemas.generated_games import (
    CURRENT_CONFIG_VERSION,
    GeneratedGameCreate,
    GeneratedGameDeleteResponse,
    GeneratedGameEnvelope,
    GeneratedGameListResponse,
    GeneratedGameUpdate,
    PublicGeneratedGameEnvelope,
)
from app.services.generated_game_service import (
    generated_game_response,
    public_generated_game_response,
    validate_configuration,
)

router = APIRouter(tags=["generated games"])


def _owned_game(db: DbDep, user_id: str, game_id: str) -> GeneratedGame:
    row = db.scalar(select(GeneratedGame).where(GeneratedGame.id == game_id, GeneratedGame.user_id == user_id))
    if row is None:
        raise AppError("GENERATED_GAME_NOT_FOUND", "The generated game was not found.", 404)
    return row


@router.post("/generated-games", response_model=GeneratedGameEnvelope, status_code=201)
def create_generated_game(payload: GeneratedGameCreate, user: CurrentUserDep, db: DbDep) -> GeneratedGameEnvelope:
    compatible = validate_configuration(payload.configuration, payload.template_type, payload.config_version)
    row = GeneratedGame(
        user_id=user.id,
        title=payload.title,
        prompt=payload.prompt,
        template_type=payload.template_type,
        configuration=compatible.configuration.model_dump(mode="json"),
        config_version=CURRENT_CONFIG_VERSION,
        is_public=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return GeneratedGameEnvelope(item=generated_game_response(row, compatible.migrated_from_version))


@router.get("/generated-games", response_model=GeneratedGameListResponse)
def list_generated_games(user: CurrentUserDep, db: DbDep) -> GeneratedGameListResponse:
    rows = db.scalars(
        select(GeneratedGame)
        .where(GeneratedGame.user_id == user.id)
        .order_by(GeneratedGame.created_at.desc(), GeneratedGame.id.desc())
    ).all()
    return GeneratedGameListResponse(items=[generated_game_response(row) for row in rows])


@router.get("/generated-games/{game_id}", response_model=GeneratedGameEnvelope)
def get_generated_game(game_id: str, user: CurrentUserDep, db: DbDep) -> GeneratedGameEnvelope:
    return GeneratedGameEnvelope(item=generated_game_response(_owned_game(db, user.id, game_id)))


@router.put("/generated-games/{game_id}", response_model=GeneratedGameEnvelope)
def update_generated_game(
    game_id: str, payload: GeneratedGameUpdate, user: CurrentUserDep, db: DbDep
) -> GeneratedGameEnvelope:
    row = _owned_game(db, user.id, game_id)
    values = payload.model_dump(exclude_unset=True)
    template_type = str(values.get("template_type", row.template_type))
    configuration = values.get("configuration", row.configuration)
    config_version = str(values.get("config_version", row.config_version))
    if not isinstance(configuration, dict):
        raise AppError("INVALID_GAME_CONFIGURATION", "The saved game configuration must be an object.", 422)
    compatible = validate_configuration(configuration, template_type, config_version)
    if "title" in values:
        row.title = str(values["title"])
    if "prompt" in values:
        row.prompt = str(values["prompt"])
    row.template_type = template_type
    row.configuration = compatible.configuration.model_dump(mode="json")
    row.config_version = CURRENT_CONFIG_VERSION
    db.commit()
    db.refresh(row)
    return GeneratedGameEnvelope(item=generated_game_response(row, compatible.migrated_from_version))


@router.delete("/generated-games/{game_id}", response_model=GeneratedGameDeleteResponse)
def delete_generated_game(game_id: str, user: CurrentUserDep, db: DbDep) -> GeneratedGameDeleteResponse:
    row = _owned_game(db, user.id, game_id)
    db.delete(row)
    db.commit()
    return GeneratedGameDeleteResponse(deleted_id=game_id)


@router.post("/generated-games/{game_id}/share", response_model=GeneratedGameEnvelope)
def share_generated_game(game_id: str, user: CurrentUserDep, db: DbDep) -> GeneratedGameEnvelope:
    row = _owned_game(db, user.id, game_id)
    generated_game_response(row)
    if not row.is_public or row.public_slug is None:
        row.public_slug = _unique_slug(db)
        row.is_public = True
        db.commit()
        db.refresh(row)
    return GeneratedGameEnvelope(item=generated_game_response(row))


@router.post("/generated-games/{game_id}/unshare", response_model=GeneratedGameEnvelope)
def unshare_generated_game(game_id: str, user: CurrentUserDep, db: DbDep) -> GeneratedGameEnvelope:
    row = _owned_game(db, user.id, game_id)
    generated_game_response(row)
    row.is_public = False
    row.public_slug = None
    db.commit()
    db.refresh(row)
    return GeneratedGameEnvelope(item=generated_game_response(row))


@router.get("/public/generated-games/{slug}", response_model=PublicGeneratedGameEnvelope)
def get_public_generated_game(slug: str, db: DbDep) -> PublicGeneratedGameEnvelope:
    if len(slug) < 24 or len(slug) > 64:
        raise AppError("PUBLIC_GAME_NOT_FOUND", "The shared game is unavailable.", 404)
    row = db.scalar(select(GeneratedGame).where(GeneratedGame.public_slug == slug, GeneratedGame.is_public.is_(True)))
    if row is None:
        raise AppError("PUBLIC_GAME_NOT_FOUND", "The shared game is unavailable.", 404)
    return PublicGeneratedGameEnvelope(item=public_generated_game_response(row))


def _unique_slug(db: DbDep) -> str:
    for _ in range(5):
        slug = secrets.token_urlsafe(24)
        if db.scalar(select(GeneratedGame.id).where(GeneratedGame.public_slug == slug)) is None:
            return slug
    raise AppError("SHARE_LINK_UNAVAILABLE", "A unique share link could not be created. Please try again.", 503)
