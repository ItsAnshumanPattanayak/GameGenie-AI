"""Database-backed assembly of the API-neutral personalisation profile."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.personalisation import FeedbackEvent, PersonalisationProfile
from app.ai.preference_extractor import PreferenceExtractor
from app.db.models import FavouriteGame, RecommendationFeedback, SearchHistory, UserPreference
from app.schemas.ai import ExtractedPreferences

_STOP_WORDS = {"and", "for", "game", "games", "with", "that", "the", "some", "want", "play"}


def build_personalisation_profile(
    db: Session,
    user_id: str,
    extractor: PreferenceExtractor,
    *,
    now: datetime | None = None,
    history_limit: int = 10,
    feedback_limit: int = 100,
) -> PersonalisationProfile:
    current_time = now or datetime.now(UTC)
    stored = db.get(UserPreference, user_id)
    explicit = (
        ExtractedPreferences(
            genres=tuple(stored.preferred_genres),
            platforms=tuple(stored.preferred_platforms),
            modes=tuple(stored.preferred_modes),
            moods=tuple(stored.preferred_moods),
            difficulty=stored.preferred_difficulty,
            price_type=stored.price_preference,
            hardware_level=stored.hardware_level,
        )
        if stored
        else ExtractedPreferences()
    )
    favourite_ids = tuple(
        db.scalars(
            select(FavouriteGame.game_id)
            .where(FavouriteGame.user_id == user_id)
            .order_by(FavouriteGame.created_at.desc(), FavouriteGame.id.desc())
        ).all()
    )
    feedback_rows = db.scalars(
        select(RecommendationFeedback)
        .where(RecommendationFeedback.user_id == user_id)
        .order_by(RecommendationFeedback.created_at.desc(), RecommendationFeedback.id.desc())
        .limit(feedback_limit)
    ).all()
    history_rows = db.scalars(
        select(SearchHistory)
        .where(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.created_at.desc(), SearchHistory.id.desc())
        .limit(history_limit)
    ).all()
    recent_history = [row for row in history_rows if _aware(row.created_at) >= current_time - timedelta(days=90)]
    return PersonalisationProfile(
        explicit_preferences=explicit,
        favourite_game_ids=favourite_ids,
        recent_search_terms=_recurring_terms(row.query for row in recent_history),
        positive_feedback_game_ids=tuple(
            dict.fromkeys(row.game_id for row in feedback_rows if row.feedback_type != "not_relevant")
        ),
        negative_feedback_game_ids=tuple(
            dict.fromkeys(row.game_id for row in feedback_rows if row.feedback_type == "not_relevant")
        ),
        recent_search_preferences=_recurring_preferences(recent_history, extractor),
        feedback_events=tuple(
            FeedbackEvent(game_id=row.game_id, feedback_type=row.feedback_type, created_at=row.created_at)
            for row in feedback_rows
        ),
    )


def _recurring_terms(queries: Iterable[str]) -> tuple[str, ...]:
    counts: Counter[str] = Counter()
    for query in queries:
        counts.update(
            {
                token
                for token in re.findall(r"[a-z0-9-]+", query.casefold())
                if len(token) > 2 and token not in _STOP_WORDS
            }
        )
    return tuple(sorted(term for term, count in counts.items() if count >= 2))


def _recurring_preferences(rows: list[SearchHistory], extractor: PreferenceExtractor) -> ExtractedPreferences:
    values: list[ExtractedPreferences] = []
    for row in rows:
        try:
            values.append(ExtractedPreferences.model_validate(row.extracted_preferences))
        except ValidationError:
            values.append(extractor.extract(row.query))

    def recurring_values(category: str) -> tuple[str, ...]:
        counts = Counter(value for preferences in values for value in getattr(preferences, category))
        return tuple(sorted(value for value, count in counts.items() if count >= 2))

    def recurring_scalar(category: str) -> str | None:
        counts = Counter(getattr(preferences, category) for preferences in values if getattr(preferences, category))
        return counts.most_common(1)[0][0] if counts and counts.most_common(1)[0][1] >= 2 else None

    return ExtractedPreferences(
        genres=recurring_values("genres"),
        platforms=recurring_values("platforms"),
        modes=recurring_values("modes"),
        themes=recurring_values("themes"),
        moods=recurring_values("moods"),
        difficulty=recurring_scalar("difficulty"),
        price_type=recurring_scalar("price_type"),
        hardware_level=recurring_scalar("hardware_level"),
    )


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)
