"""Deployment configuration and database-engine safety checks."""

from typing import Any, cast

import pytest
from pydantic import ValidationError
from sqlalchemy import Engine
from sqlalchemy.engine import URL

from app.core.config import Settings
from app.db import session as db_session

PRODUCTION_SECRET = "deployment-test-secret-that-is-long-enough"


def test_blank_database_url_preserves_local_sqlite_default() -> None:
    settings = Settings(database_url="")

    assert settings.database_url == "sqlite:///data/gamegenie.db"


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://"])
def test_postgresql_urls_use_psycopg_three(scheme: str) -> None:
    settings = Settings(database_url=f"{scheme}user:password@database.example/gamegenie?sslmode=require")

    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.database_url.endswith("?sslmode=require")


def test_production_requires_secure_complete_configuration() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production")
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            database_url="postgresql://user:password@database.example/gamegenie",
            auth_secret_key=PRODUCTION_SECRET,
            allowed_origins="https://gamegenie.example",
            debug=True,
        )


def test_production_accepts_neon_style_configuration() -> None:
    settings = Settings(
        app_env="prod",
        database_url="postgresql://user:password@database.example/gamegenie?sslmode=require",
        auth_secret_key=PRODUCTION_SECRET,
        allowed_origins="https://gamegenie.example,http://localhost:5173",
    )

    assert settings.app_env == "production"
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.allowed_origins == ["https://gamegenie.example", "http://localhost:5173"]


def test_credentialed_cors_rejects_wildcard() -> None:
    with pytest.raises(ValidationError):
        Settings(allowed_origins="*")
    with pytest.raises(ValidationError):
        Settings(allowed_origins="https://gamegenie.example/dashboard")


def test_postgresql_engine_has_no_sqlite_options(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_create_engine(url: URL, **options: object) -> Engine:
        captured["url"] = url
        captured["options"] = options
        return cast(Engine, object())

    monkeypatch.setattr(db_session, "create_engine", fake_create_engine)

    db_session.build_engine("postgresql+psycopg://user:password@database.example/gamegenie")

    assert cast(URL, captured["url"]).get_backend_name() == "postgresql"
    assert captured["options"] == {"pool_pre_ping": True}
