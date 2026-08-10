"""Persistent account, preference, and refresh-session models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    preferences: Mapped[UserPreference] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    refresh_sessions: Mapped[list[RefreshSession]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    preferred_genres: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    preferred_platforms: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    preferred_modes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    preferred_moods: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    preferred_difficulty: Mapped[str | None] = mapped_column(String(20))
    price_preference: Mapped[str | None] = mapped_column(String(20))
    hardware_level: Mapped[str | None] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    user: Mapped[User] = relationship(back_populates="preferences")


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    user: Mapped[User] = relationship(back_populates="refresh_sessions")
