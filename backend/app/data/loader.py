"""Safe CSV and JSON dataset loading."""

import csv
import json
import logging
from pathlib import Path
from typing import Any

from app.core.exceptions import DatasetMissingError, InvalidDatasetError

logger = logging.getLogger(__name__)


def load_raw_records(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise DatasetMissingError(f"Dataset file does not exist: {path.name}")
    try:
        if path.suffix.casefold() == ".json":
            with path.open(encoding="utf-8-sig") as handle:
                payload = json.load(handle)
            records = payload.get("games") if isinstance(payload, dict) else payload
        elif path.suffix.casefold() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as handle:
                records = list(csv.DictReader(handle))
        else:
            raise InvalidDatasetError("Only JSON and CSV datasets are supported.")
    except (json.JSONDecodeError, UnicodeDecodeError, csv.Error) as exc:
        raise InvalidDatasetError("The dataset could not be parsed.") from exc
    if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
        raise InvalidDatasetError("Dataset root must be a list of objects or a games object.")
    logger.info("Loaded raw dataset path=%s records=%d", path, len(records))
    return records
