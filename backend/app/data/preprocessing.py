"""Deterministic raw-to-processed catalogue pipeline."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.core.config import get_settings
from app.core.exceptions import InvalidDatasetError
from app.data.loader import load_raw_records
from app.data.mapping import map_raw_record
from app.data.normalization import (
    normalize_genres,
    normalize_platforms,
    normalize_text,
    normalize_title,
    parse_bool,
    parse_date,
    parse_list,
    parse_price,
    parse_rating,
    price_category,
    slugify,
)
from app.schemas.game import GameResponse

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    input_records: int = 0
    output_records: int = 0
    skipped_records: int = 0
    repaired_records: int = 0
    duplicate_records: int = 0


def stable_game_id(record: dict[str, Any]) -> str:
    """Return a source ID when present, otherwise a stable content-derived ID."""
    existing = normalize_text(record.get("id"))
    if existing:
        return existing
    source, source_id = normalize_text(record.get("source")), normalize_text(record.get("source_id"))
    if source and source_id:
        return f"{slugify(source)}-{slugify(source_id)}"
    parts = [
        record.get("normalized_title"),
        record.get("release_year"),
        record.get("developer"),
        record.get("publisher"),
    ]
    digest = hashlib.sha256("|".join(str(item or "").casefold() for item in parts).encode()).hexdigest()[:16]
    return f"gg-{digest}"


def clean_record(raw: dict[str, Any]) -> GameResponse | None:
    """Map, normalize, and validate one record; return None when unusable."""
    data = map_raw_record(raw)
    title, normalized_title = normalize_title(data.get("title"))
    if not title:
        logger.warning("Skipping dataset record with missing title")
        return None
    released = parse_date(data.get("release_date"))
    year_value = data.get("release_year")
    release_year: int | None = released.year if released else None
    if isinstance(year_value, (str, int, float)) and year_value != "":
        with suppress(TypeError, ValueError):
            release_year = int(year_value)
    if release_year is not None and not 1950 <= release_year <= 2100:
        release_year = released.year if released and 1950 <= released.year <= 2100 else None
    rating = parse_rating(data.get("rating"), data.get("rating_scale"))
    price = parse_price(data.get("price"))
    payload: dict[str, Any] = {
        "title": title,
        "normalized_title": normalized_title,
        "slug": normalize_text(data.get("slug")) or slugify(title),
        "description": normalize_text(data.get("description")),
        "short_description": normalize_text(data.get("short_description")),
        "genres": normalize_genres(data.get("genres")),
        "platforms": normalize_platforms(data.get("platforms")),
        "developer": normalize_text(data.get("developer")),
        "publisher": normalize_text(data.get("publisher")),
        "release_date": released,
        "release_year": release_year,
        "rating": rating,
        "rating_count": _nonnegative_int(data.get("rating_count")),
        "popularity": _nonnegative_float(data.get("popularity")),
        "tags": parse_list(data.get("tags")),
        "multiplayer": parse_bool(data.get("multiplayer")),
        "online_multiplayer": parse_bool(data.get("online_multiplayer")),
        "single_player": parse_bool(data.get("single_player")),
        "age_rating": normalize_text(data.get("age_rating")),
        "price": price,
        "currency": _currency(data.get("currency")),
        "price_category": price_category(price),
        "image_url": normalize_text(data.get("image_url")),
        "website_url": normalize_text(data.get("website_url")),
        "minimum_requirements": normalize_text(data.get("minimum_requirements")),
        "recommended_requirements": normalize_text(data.get("recommended_requirements")),
        "source": normalize_text(data.get("source")),
        "source_id": normalize_text(data.get("source_id")),
    }
    payload["id"] = stable_game_id({**data, **payload})
    try:
        return GameResponse.model_validate(payload)
    except ValidationError as exc:
        logger.warning("Skipping invalid record title=%r errors=%s", title, exc.error_count())
        return None


def _nonnegative_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _nonnegative_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _currency(value: Any) -> str | None:
    text = normalize_text(value)
    return text.upper() if text and len(text) == 3 else None


def _duplicate_key(game: GameResponse) -> tuple[str, int | None, str, str]:
    return (
        game.normalized_title,
        game.release_year,
        (game.developer or "").casefold(),
        (game.publisher or "").casefold(),
    )


def _completeness(game: GameResponse) -> int:
    return sum(value not in (None, "", [], {}) for value in game.model_dump().values())


def merge_games(left: GameResponse, right: GameResponse) -> GameResponse:
    """Keep the more complete duplicate and merge its list fields deterministically."""
    primary, other = (left, right) if _completeness(left) >= _completeness(right) else (right, left)
    data = primary.model_dump()
    for field in ("genres", "platforms", "tags"):
        data[field] = list(dict.fromkeys([*getattr(primary, field), *getattr(other, field)]))
    for field, value in other.model_dump().items():
        if data.get(field) in (None, "", [], {}):
            data[field] = value
    return GameResponse.model_validate(data)


def preprocess_records(records: list[dict[str, Any]]) -> tuple[list[GameResponse], ProcessingStats]:
    stats = ProcessingStats(input_records=len(records))
    unique: dict[tuple[str, int | None, str, str], GameResponse] = {}
    source_keys: dict[tuple[str, str], tuple[str, int | None, str, str]] = {}
    for raw in records:
        game = clean_record(raw)
        if game is None:
            stats.skipped_records += 1
            continue
        if _was_repaired(raw, game):
            stats.repaired_records += 1
        key = _duplicate_key(game)
        source_key = ((game.source or "").casefold(), (game.source_id or "").casefold())
        existing_key = source_keys.get(source_key) if all(source_key) else None
        target_key = existing_key or key
        if target_key in unique:
            unique[target_key] = merge_games(unique[target_key], game)
            stats.duplicate_records += 1
            logger.info("Merged duplicate dataset record title=%s", game.title)
        else:
            unique[key] = game
            if all(source_key):
                source_keys[source_key] = key
    games = sorted(unique.values(), key=lambda item: (item.normalized_title, item.id))
    stats.output_records = len(games)
    return games, stats


def _was_repaired(raw: dict[str, Any], game: GameResponse) -> bool:
    """Identify accepted rows that required normalization or alias mapping."""
    raw_title = raw.get("title")
    aliases = ("name", "game_name", "summary", "genre", "platform", "score", "released", "release", "company")
    return (
        raw_title is None
        or (isinstance(raw_title, str) and raw_title != game.title)
        or any(alias in raw for alias in aliases)
    )


def write_processed(games: list[GameResponse], output_path: Path, stats: ProcessingStats) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    payload = {
        "metadata": {"schema_version": 1, "statistics": asdict(stats)},
        "games": [game.model_dump(mode="json", exclude_none=True) for game in games],
    }
    try:
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, output_path)
    finally:
        if temporary.exists():
            temporary.unlink()


def run_preprocessing(raw_path: Path, output_path: Path) -> tuple[list[GameResponse], ProcessingStats]:
    records = load_raw_records(raw_path)
    games, stats = preprocess_records(records)
    if not games:
        raise InvalidDatasetError("No valid games remained after preprocessing.")
    write_processed(games, output_path, stats)
    logger.info(
        "Preprocessing complete input=%d output=%d skipped=%d duplicates=%d",
        stats.input_records,
        stats.output_records,
        stats.skipped_records,
        stats.duplicate_records,
    )
    return games, stats


def main() -> None:
    settings = get_settings()
    games, stats = run_preprocessing(settings.raw_data_path, settings.processed_data_path)
    print(f"Processed {stats.input_records} records into {len(games)} games at {settings.processed_data_path}")


if __name__ == "__main__":
    main()
