"""Account registration, session, and current-user endpoints."""

from fastapi import APIRouter, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUserDep, DbDep
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.db.models import User, UserPreference
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    UserEnvelope,
)
from app.services.auth_service import authenticate_user, issue_tokens, revoke_refresh_token, rotate_refresh_token

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest, request: Request, db: DbDep) -> AuthResponse:
    if db.scalar(select(User.id).where(User.email == str(payload.email))):
        raise AppError("EMAIL_ALREADY_REGISTERED", "An account with this email already exists.", 409)
    user = User(name=payload.name, email=str(payload.email), password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.flush()
        db.add(UserPreference(user_id=user.id))
        tokens = issue_tokens(db, user, request.app.state.settings)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError("EMAIL_ALREADY_REGISTERED", "An account with this email already exists.", 409) from exc
    db.refresh(user)
    return AuthResponse(user=user, tokens=tokens)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, db: DbDep) -> AuthResponse:
    user = authenticate_user(db, str(payload.email), payload.password)
    tokens = issue_tokens(db, user, request.app.state.settings)
    db.commit()
    return AuthResponse(user=user, tokens=tokens)


@router.post("/refresh", response_model=AuthResponse)
def refresh(payload: RefreshRequest, request: Request, db: DbDep) -> AuthResponse:
    user, tokens = rotate_refresh_token(db, payload.refresh_token, request.app.state.settings)
    return AuthResponse(user=user, tokens=tokens)


@router.post("/logout", response_model=LogoutResponse)
def logout(payload: LogoutRequest, request: Request, db: DbDep) -> LogoutResponse:
    revoke_refresh_token(db, payload.refresh_token, request.app.state.settings)
    return LogoutResponse()


@router.get("/me", response_model=UserEnvelope)
def me(user: CurrentUserDep) -> UserEnvelope:
    return UserEnvelope(user=user)
