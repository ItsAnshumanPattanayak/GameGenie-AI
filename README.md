# GameGenie AI

GameGenie AI currently provides the Phase 1 FastAPI foundation and Phase 2 local catalogue pipeline. The repository is the `GameGenie-AI` child within the parent project folder; all commands below start at this repository root.

## Backend setup

Python 3.11 or newer is supported.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env  # optional; .env is ignored
```

Settings use environment variables. Dataset paths must be relative to `backend` and are prevented from escaping it. `ALLOWED_ORIGINS` is a comma-separated list. Safe defaults work without an `.env` file.

## Run and inspect

```powershell
cd backend
python -m app.data.preprocessing
python -m uvicorn app.main:app --reload
```

Open Swagger at `http://127.0.0.1:8000/docs` or ReDoc at `http://127.0.0.1:8000/redoc`.

The API includes:

- `GET /health` — service and catalogue status.
- `GET /api/games` — paginated catalogue with sorting and filters.
- `GET /api/games/search?q=star` — deterministic ranked text search with filters.
- `GET /api/games/{game_id}` — one game or a standardized 404.
- `GET /api/genres` and `GET /api/platforms` — normalized facets with counts.

Examples:

```text
/api/games?genre=RPG&platform=PC&min_rating=4&sort_by=rating&sort_direction=desc
/api/games?multiplayer=true&page=1&page_size=10
/api/games/search?q=space&platform=PC
```

## Dataset pipeline

`backend/data/raw/games.json` is a small, original CC0 development sample with varied records and deliberate duplicate/malformed cases. The loader accepts UTF-8 JSON (`[...]` or `{ "games": [...] }`) and CSV. Preprocessing centralizes aliases, normalizes text/lists/genres/platforms/booleans/dates/ratings/prices, skips unusable rows, merges carefully matched duplicates, creates deterministic IDs, sorts deterministically, and atomically writes `backend/data/processed/games.json`.

At startup, the app loads a valid processed catalogue once. If it is absent or invalid, raw data is preprocessed. Catalogue state lives on the FastAPI application for dependency injection and can be replaced by a database service later.

Validation strategy: missing titles are skipped; malformed optional values become null; known rating scales can be converted to 0–5; unknown/out-of-range ratings and negative prices become null; invalid years/dates are preserved as unknown; malformed list values become empty lists. Every skipped/duplicate record is counted.

## Quality checks

```powershell
cd backend
pytest
ruff check .
ruff format --check .
mypy app tests
```

The `app.ai` package defines typed contracts for preference parsing, similarity, orchestration, and explanations. The full TF-IDF/cosine-similarity recommendation engine and public recommendation endpoints intentionally remain Phase 3 work.

