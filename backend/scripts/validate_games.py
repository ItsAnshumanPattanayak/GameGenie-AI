"""Data quality validator for the raw and processed games datasets.

Run: python scripts/validate_games.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.schemas.game import GameResponse  # noqa: E402


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _validate_raw(path: Path) -> tuple[int, int, list[str]]:
    if not path.is_file():
        return 0, 0, [f"Raw dataset not found: {path}"]

    payload = _load_json(path)
    records = payload.get("games", [])

    valid = 0
    errors: list[str] = []
    for index, record in enumerate(records):
        title = record.get("title") or record.get("name") or record.get("game_name")
        if not title:
            errors.append(f"[raw #{index}] missing title/name field")
            continue
        valid += 1
    return valid, len(records), errors


def _validate_processed(path: Path) -> tuple[int, int, list[str]]:
    if not path.is_file():
        return 0, 0, [f"Processed dataset not found: {path}"]

    payload = _load_json(path)
    records = payload if isinstance(payload, list) else payload.get("games", [])

    valid = 0
    errors: list[str] = []
    for index, record in enumerate(records):
        try:
            GameResponse.model_validate(record)
            valid += 1
        except (ValueError, TypeError) as exc:
            errors.append(f"[processed #{index}] {type(exc).__name__}: {exc}")
    return valid, len(records), errors


def main() -> int:
    settings = get_settings()
    print("GameGenie AI — Dataset Validator")
    print("=" * 60)

    raw_valid, raw_total, raw_errors = _validate_raw(settings.raw_data_path)
    print(f"\nRaw dataset ({settings.raw_data_path.name}):")
    print(f"  Valid rows: {raw_valid} / {raw_total}")
    for issue in raw_errors[:10]:
        print(f"  ! {issue}")

    processed_valid, processed_total, processed_errors = _validate_processed(settings.processed_data_path)
    print(f"\nProcessed dataset ({settings.processed_data_path.name}):")
    print(f"  Valid rows: {processed_valid} / {processed_total}")
    for issue in processed_errors[:10]:
        print(f"  ! {issue}")

    print("\n" + "=" * 60)
    if raw_errors or processed_errors:
        print("Validation completed with warnings.")
        return 1
    print("Validation completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
