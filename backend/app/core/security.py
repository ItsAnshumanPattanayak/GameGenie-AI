"""Password hashing and signed token primitives."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import Settings
from app.core.exceptions import AppError

TOKEN_ISSUER = "gamegenie-ai"
JWT_ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    try:
        return password_hash.verify(password, encoded)
    except (TypeError, ValueError):
        return False


def _secret(settings: Settings) -> str:
    secret = settings.auth_secret_key.get_secret_value() if settings.auth_secret_key else ""
    if len(secret) < 32:
        raise AppError(
            "AUTH_CONFIGURATION_ERROR",
            "Authentication is unavailable because AUTH_SECRET_KEY is not configured securely.",
            503,
        )
    return secret


def create_token(
    user_id: str,
    token_type: Literal["access", "refresh"],
    settings: Settings,
    *,
    now: datetime | None = None,
) -> tuple[str, str, datetime]:
    issued_at = now or datetime.now(UTC)
    duration = (
        timedelta(minutes=settings.access_token_minutes)
        if token_type == "access"
        else timedelta(days=settings.refresh_token_days)
    )
    expires_at = issued_at + duration
    token_id = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "typ": token_type,
        "jti": token_id,
        "iss": TOKEN_ISSUER,
        "iat": issued_at,
        "exp": expires_at,
    }
    return jwt.encode(payload, _secret(settings), algorithm=JWT_ALGORITHM), token_id, expires_at


def decode_token(token: str, expected_type: Literal["access", "refresh"], settings: Settings) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            _secret(settings),
            algorithms=[JWT_ALGORITHM],
            issuer=TOKEN_ISSUER,
            options={"require": ["sub", "typ", "jti", "iss", "iat", "exp"]},
        )
    except ExpiredSignatureError as exc:
        raise AppError("TOKEN_EXPIRED", "The authentication token has expired.", 401) from exc
    except InvalidTokenError as exc:
        raise AppError("INVALID_TOKEN", "The authentication token is malformed or invalid.", 401) from exc
    if payload.get("typ") != expected_type:
        raise AppError("INVALID_TOKEN", "The authentication token has the wrong type.", 401)
    if not isinstance(payload.get("sub"), str) or not isinstance(payload.get("jti"), str):
        raise AppError("INVALID_TOKEN", "The authentication token is malformed or invalid.", 401)
    return payload


def refresh_session_id(token_id: str) -> str:
    return hashlib.sha256(token_id.encode("utf-8")).hexdigest()
