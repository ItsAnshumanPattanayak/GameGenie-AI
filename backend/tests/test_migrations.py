"""Alembic migration smoke test."""

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from app.core.config import get_settings


def test_auth_migration_upgrades_empty_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database_path = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    get_settings.cache_clear()
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    tables = set(inspect(create_engine(f"sqlite:///{database_path.as_posix()}")).get_table_names())
    assert {"alembic_version", "users", "user_preferences", "refresh_sessions"} <= tables
    get_settings.cache_clear()
