"""Persistent account, preference, and refresh-session models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
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
    search_history: Mapped[list[SearchHistory]] = relationship(back_populates="user", cascade="all, delete-orphan")
    favourites: Mapped[list[FavouriteGame]] = relationship(back_populates="user", cascade="all, delete-orphan")
    recommendation_feedback: Mapped[list[RecommendationFeedback]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


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


class SearchHistory(Base):
    __tablename__ = "search_history"
    __table_args__ = (Index("ix_search_history_user_created", "user_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(String(2000), nullable=False)
    extracted_preferences: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    user: Mapped[User] = relationship(back_populates="search_history")
    feedback: Mapped[list[RecommendationFeedback]] = relationship(back_populates="search")


class FavouriteGame(Base):
    __tablename__ = "favourite_games"
    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_favourite_games_user_game"),
        Index("ix_favourite_games_user_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    game_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    user: Mapped[User] = relationship(back_populates="favourites")


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"
    __table_args__ = (
        Index("ix_recommendation_feedback_user_created", "user_id", "created_at"),
        Index("ix_recommendation_feedback_user_game", "user_id", "game_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    game_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    search_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("search_history.id", ondelete="SET NULL"), nullable=True, index=True
    )
    feedback_type: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    user: Mapped[User] = relationship(back_populates="recommendation_feedback")
    search: Mapped[SearchHistory | None] = relationship(back_populates="feedback")
