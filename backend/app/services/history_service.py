"""In-memory ring buffer for recent search activity.

Persisted history would require a database, which is out of scope for
Sprint 2. This service keeps the last N interactions in memory so that the
UI and internal debugging tools can inspect recent traffic without adding
new infrastructure.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any


class HistoryService:
    def __init__(self, *, capacity: int = 100) -> None:
        if capacity < 1:
            raise ValueError("History capacity must be a positive integer.")
        self._entries: deque[dict[str, Any]] = deque(maxlen=capacity)
        self._lock = Lock()

    @property
    def capacity(self) -> int:
        return self._entries.maxlen or 0

    def record(
        self,
        *,
        query: str,
        preferences: dict[str, Any],
        result_count: int,
        processing_time_ms: float,
    ) -> None:
        entry = {
            "query": query,
            "preferences": preferences,
            "result_count": result_count,
            "processing_time_ms": round(processing_time_ms, 3),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._entries.append(entry)

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if limit < 1:
            return []
        with self._lock:
            snapshot = list(self._entries)
        return snapshot[-limit:][::-1]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
