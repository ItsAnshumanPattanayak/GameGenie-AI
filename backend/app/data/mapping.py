"""Central mapping from common raw fields to canonical game fields."""

from typing import Any

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "title": ("name", "game_name"),
    "description": ("summary",),
    "genres": ("genre",),
    "platforms": ("platform",),
    "rating": ("score",),
    "release_date": ("released", "release"),
    "developer": ("company",),
}


def map_raw_record(record: dict[str, Any]) -> dict[str, Any]:
    """Copy a raw record while filling absent canonical fields from aliases."""
    mapped = dict(record)
    for canonical, aliases in FIELD_ALIASES.items():
        if canonical in mapped and mapped[canonical] not in (None, ""):
            continue
        for alias in aliases:
            if alias in record and record[alias] not in (None, ""):
                mapped[canonical] = record[alias]
                break
    return {
        key: value
        for key, value in mapped.items()
        if key not in {a for aliases in FIELD_ALIASES.values() for a in aliases}
    }
