"""Sprint 3 authentication, session, preference, and anonymous-AI tests."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.core.security import create_token, verify_password
from app.db.base import Base
from app.db.models import User
from app.main import create_app
from app.schemas.preferences import PreferenceUpdate

TEST_SECRET = "test-only-secret-key-with-at-least-thirty-two-characters"
PASSWORD = "StrongPass123"


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    application = create_app(Settings(database_url="sqlite://", auth_secret_key=TEST_SECRET))
    Base.metadata.create_all(application.state.db_engine)
    with TestClient(application) as client:
        yield client


def register(client: TestClient, *, email: str = "player@example.com") -> dict[str, object]:
    response = client.post(
        "/api/auth/register",
        json={"name": "Player One", "email": email, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()


def bearer(data: dict[str, object]) -> dict[str, str]:
    tokens = data["tokens"]
    assert isinstance(tokens, dict)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_successful_registration_hashes_password_and_hides_hash(auth_client: TestClient) -> None:
    data = register(auth_client, email="  PLAYER@Example.COM ")
    assert data["user"]["email"] == "player@example.com"  # type: ignore[index]
    assert "password_hash" not in data["user"]  # type: ignore[operator]
    application = cast(FastAPI, auth_client.app)
    with application.state.db_session_factory() as db:
        user = db.scalar(select(User).where(User.email == "player@example.com"))
        assert user is not None
        assert user.password_hash != PASSWORD
        assert verify_password(PASSWORD, user.password_hash)


def test_duplicate_email_is_rejected_case_insensitively(auth_client: TestClient) -> None:
    register(auth_client, email="player@example.com")
    response = auth_client.post(
        "/api/auth/register",
        json={"name": "Other Player", "email": "PLAYER@example.com", "password": PASSWORD},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("not-an-email", PASSWORD),
        ("player@example.com", "short"),
        ("player@example.com", "alllowercase123"),
        ("player@example.com", "NOLOWERCASE123"),
        ("player@example.com", "NoNumberPassword"),
    ],
)
def test_invalid_registration_input(auth_client: TestClient, email: str, password: str) -> None:
    response = auth_client.post("/api/auth/register", json={"name": "Player One", "email": email, "password": password})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_correct_login_wrong_password_and_me(auth_client: TestClient) -> None:
    registered = register(auth_client)
    wrong = auth_client.post("/api/auth/login", json={"email": "player@example.com", "password": "WrongPass123"})
    assert wrong.status_code == 401
    assert wrong.json()["error"]["code"] == "INVALID_CREDENTIALS"

    login = auth_client.post("/api/auth/login", json={"email": "PLAYER@example.com", "password": PASSWORD})
    assert login.status_code == 200
    me = auth_client.get("/api/auth/me", headers=bearer(login.json()))
    assert me.status_code == 200
    assert me.json()["user"]["id"] == registered["user"]["id"]  # type: ignore[index]


def test_missing_malformed_and_expired_access_tokens(auth_client: TestClient) -> None:
    missing = auth_client.get("/api/auth/me")
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    malformed = auth_client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert malformed.status_code == 401
    assert malformed.json()["error"]["code"] == "INVALID_TOKEN"

    data = register(auth_client)
    settings = cast(FastAPI, auth_client.app).state.settings
    expired, _, _ = create_token(
        data["user"]["id"],  # type: ignore[index]
        "access",
        settings,
        now=datetime.now(UTC) - timedelta(days=1),
    )
    response = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_refresh_rotation_and_logout_revocation(auth_client: TestClient) -> None:
    data = register(auth_client)
    tokens = data["tokens"]
    assert isinstance(tokens, dict)
    old_refresh = tokens["refresh_token"]
    refreshed = auth_client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    assert refreshed.json()["tokens"]["refresh_token"] != old_refresh

    replay = auth_client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401
    new_refresh = refreshed.json()["tokens"]["refresh_token"]
    assert auth_client.post("/api/auth/logout", json={"refresh_token": new_refresh}).status_code == 200
    assert auth_client.post("/api/auth/refresh", json={"refresh_token": new_refresh}).status_code == 401


def test_preference_retrieval_update_and_ai_normalization(auth_client: TestClient) -> None:
    data = register(auth_client)
    headers = bearer(data)
    initial = auth_client.get("/api/preferences", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["preferences"]["preferred_genres"] == []

    values = {
        "preferred_genres": ["strategy", "action", "strategy"],
        "preferred_platforms": ["PC", "Nintendo Switch"],
        "preferred_modes": ["single-player", "offline"],
        "preferred_moods": ["relaxing"],
        "preferred_difficulty": "medium",
        "price_preference": "paid",
        "hardware_level": "mid-range",
    }
    updated = auth_client.put("/api/preferences", headers=headers, json=values)
    assert updated.status_code == 200
    preferences = updated.json()["preferences"]
    assert preferences["preferred_genres"] == ["action", "strategy"]
    normalized = PreferenceUpdate.model_validate(values).to_ai_preferences()
    assert normalized.genres == ("action", "strategy")
    assert normalized.price_type == "paid"


def test_invalid_preference_vocabulary_is_rejected(auth_client: TestClient) -> None:
    data = register(auth_client)
    response = auth_client.put(
        "/api/preferences",
        headers=bearer(data),
        json={"preferred_genres": ["not-a-real-genre"]},
    )
    assert response.status_code == 422


def test_anonymous_and_authenticated_recommendations_remain_public(auth_client: TestClient) -> None:
    anonymous = auth_client.post("/api/search/recommend", json={"prompt": "relaxing puzzle", "limit": 3})
    assert anonymous.status_code == 200
    data = register(auth_client)
    authenticated = auth_client.post(
        "/api/search/recommend",
        headers=bearer(data),
        json={"prompt": "relaxing puzzle", "limit": 3},
    )
    assert authenticated.status_code == 200
    assert authenticated.json() == anonymous.json()
