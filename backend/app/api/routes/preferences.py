"""Authenticated controlled user-preference endpoints."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUserDep, DbDep
from app.core.exceptions import AppError
from app.db.models import UserPreference
from app.schemas.preferences import PreferenceEnvelope, PreferenceUpdate, UserPreferenceResponse

router = APIRouter(prefix="/preferences", tags=["preferences"])


def _response(preferences: UserPreference) -> PreferenceEnvelope:
    return PreferenceEnvelope(preferences=UserPreferenceResponse.model_validate(preferences, from_attributes=True))


@router.get("", response_model=PreferenceEnvelope)
def get_preferences(user: CurrentUserDep, db: DbDep) -> PreferenceEnvelope:
    preferences = db.get(UserPreference, user.id)
    if preferences is None:
        raise AppError("PREFERENCES_NOT_FOUND", "User preferences are unavailable.", 404)
    return _response(preferences)


@router.put("", response_model=PreferenceEnvelope)
def update_preferences(payload: PreferenceUpdate, user: CurrentUserDep, db: DbDep) -> PreferenceEnvelope:
    preferences = db.get(UserPreference, user.id)
    if preferences is None:
        preferences = UserPreference(user_id=user.id)
        db.add(preferences)
    for field, value in payload.model_dump().items():
        setattr(preferences, field, value)
    db.commit()
    db.refresh(preferences)
    return _response(preferences)
