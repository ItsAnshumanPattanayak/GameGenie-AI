"""Transactional authentication and refresh-session operations."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.security import create_token, decode_token, refresh_session_id, verify_password
from app.db.models import RefreshSession, User
from app.schemas.auth import AuthTokens


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "The email or password is incorrect.", 401)
    if not user.is_active:
        raise AppError("USER_INACTIVE", "This account is inactive.", 403)
    return user


def issue_tokens(db: Session, user: User, settings: Settings) -> AuthTokens:
    access, _, _ = create_token(user.id, "access", settings)
    refresh, refresh_id, refresh_expiry = create_token(user.id, "refresh", settings)
    db.add(
        RefreshSession(
            id=refresh_session_id(refresh_id),
            user_id=user.id,
            expires_at=refresh_expiry,
        )
    )
    return AuthTokens(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_minutes * 60,
    )


def rotate_refresh_token(db: Session, token: str, settings: Settings) -> tuple[User, AuthTokens]:
    payload = decode_token(token, "refresh", settings)
    session = db.get(RefreshSession, refresh_session_id(payload["jti"]))
    now = datetime.now(UTC)
    if session is None or session.revoked_at is not None or _as_utc(session.expires_at) <= now:
        raise AppError("INVALID_TOKEN", "The refresh token is invalid or has been revoked.", 401)
    user = db.get(User, payload["sub"])
    if user is None or user.id != session.user_id:
        raise AppError("INVALID_TOKEN", "The refresh token is invalid.", 401)
    if not user.is_active:
        raise AppError("USER_INACTIVE", "This account is inactive.", 403)
    session.revoked_at = now
    tokens = issue_tokens(db, user, settings)
    db.commit()
    return user, tokens


def revoke_refresh_token(db: Session, token: str, settings: Settings) -> None:
    payload = decode_token(token, "refresh", settings)
    session = db.get(RefreshSession, refresh_session_id(payload["jti"]))
    if session is None or session.user_id != payload["sub"]:
        raise AppError("INVALID_TOKEN", "The refresh token is invalid.", 401)
    if session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        db.commit()


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)
