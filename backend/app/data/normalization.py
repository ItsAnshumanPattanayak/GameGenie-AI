"""Reusable normalization helpers for heterogeneous game data."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

NULL_VALUES = {"", "null", "none", "n/a", "na", "unknown", "-"}
GENRES = {
    "role playing": "RPG",
    "role-playing": "RPG",
    "roleplaying": "RPG",
    "rpg": "RPG",
    "fps": "First-Person Shooter",
}
PLATFORMS = {
    "pc": "PC",
    "windows": "PC",
    "windows pc": "PC",
    "mac": "macOS",
    "macos": "macOS",
    "ios": "iOS",
    "android": "Android",
    "linux": "Linux",
    "switch": "Nintendo Switch",
    "nintendo switch": "Nintendo Switch",
    "ps4": "PlayStation 4",
    "ps5": "PlayStation 5",
    "playstation 4": "PlayStation 4",
    "playstation 5": "PlayStation 5",
    "xbox one": "Xbox One",
    "xbox series x": "Xbox Series X|S",
    "xbox series s": "Xbox Series X|S",
    "xbox series x/s": "Xbox Series X|S",
}


def normalize_text(value: Any) -> str | None:
    if value is None or not isinstance(value, (str, int, float)):
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return None if text.casefold() in NULL_VALUES else text


def normalize_title(value: Any) -> tuple[str | None, str]:
    display = normalize_text(value)
    if display is None:
        normalized = ""
    else:
        separated = re.sub(r"[^\w\s]", " ", display)
        normalized = re.sub(
            r"[^a-z0-9]+", " ", unicodedata.normalize("NFKD", separated).encode("ascii", "ignore").decode().casefold()
        ).strip()
    return display, normalized


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize_title(value)[1]).strip("-")


def parse_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("["):
            try:
                value = json.loads(text.replace("'", '"'))
            except (json.JSONDecodeError, TypeError):
                value = re.split(r"[,;|]", text.strip("[]"))
        else:
            value = re.split(r"[,;|]", text)
    if not isinstance(value, (list, tuple, set)):
        return []
    output: list[str] = []
    seen: set[str] = set()
    for item in value:
        normalized_item = normalize_text(item)
        if normalized_item and normalized_item.casefold() not in seen:
            seen.add(normalized_item.casefold())
            output.append(normalized_item)
    return output


def normalize_genres(value: Any) -> list[str]:
    return _normalized_list(value, GENRES)


def normalize_platforms(value: Any) -> list[str]:
    return _normalized_list(value, PLATFORMS)


def _normalized_list(value: Any, aliases: dict[str, str]) -> list[str]:
    output: list[str] = []
    for item in parse_list(value):
        canonical = aliases.get(item.casefold(), item)
        if canonical.casefold() not in {existing.casefold() for existing in output}:
            output.append(canonical)
    return output


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    text = normalize_text(value)
    if text is None:
        return None
    if text.casefold() in {"true", "yes", "y", "1", "multiplayer", "single-player", "single player"}:
        return True
    if text.casefold() in {"false", "no", "n", "0"}:
        return False
    return None


def parse_rating(value: Any, scale: float | None = None) -> float | None:
    if normalize_text(value) is None:
        return None
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return None
    if scale is not None and scale != 5:
        rating = rating * 5 / scale
    return round(rating, 2) if 0 <= rating <= 5 else None


def parse_date(value: Any) -> date | None:
    text = normalize_text(value)
    if text is None:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def parse_price(value: Any) -> Decimal | None:
    text = normalize_text(value)
    if text is None:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", text)
    try:
        price = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None
    return price if price >= 0 else None


def price_category(price: Decimal | None) -> str:
    if price is None:
        return "unknown"
    if price == 0:
        return "free"
    if price < 15:
        return "budget"
    if price < 40:
        return "mid-range"
    return "premium"
