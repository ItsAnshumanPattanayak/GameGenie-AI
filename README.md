# GameGenie AI

GameGenie AI provides the FastAPI/catalogue and Sprint 2 AI foundation plus Sprint 3 persistent accounts, controlled user preferences, and a React/Vite/TypeScript account frontend. Anonymous prompt interpretation, recommendation, and game configuration remain available.

## Backend setup

Python 3.11 or newer is supported.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env  # required for auth; .env is ignored
python -m alembic upgrade head
```

Settings use environment variables. Dataset paths must be relative to `backend` and are prevented from escaping it. `ALLOWED_ORIGINS` is a comma-separated list. Authentication requires an unpredictable `AUTH_SECRET_KEY` of at least 32 characters. SQLite is the local database default; override `DATABASE_URL` for deployment.

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
- `POST /api/search/interpret` — normalize a prompt and extract typed preferences, warnings, and confidence.
- `POST /api/search/recommend` — return filtered, ranked, scored, and explained catalogue matches.
- `POST /api/generator/interpret` — select the supported template and return a validated game configuration.

- `POST /api/auth/register`, `/login`, `/refresh`, and `/logout` — persistent account sessions.
- `GET /api/auth/me` — current authenticated user.
- `GET` and `PUT /api/preferences` — controlled profile preferences aligned with the AI taxonomy.

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

## Frontend setup

```powershell
cd frontend
pnpm install
pnpm dev
```

The frontend reads `VITE_API_URL` (default `http://127.0.0.1:8000`) and provides `/register`, `/login`, `/profile`, and `/preferences`. `/dashboard`, `/history`, `/favourites`, and `/my-games` are protected; the last three are intentional placeholders.

```powershell
cd frontend
pnpm test
pnpm build
```

Build production embedding artifacts after the public model is available locally:

```powershell
cd backend
python -m scripts.build_embeddings --batch-size 32
```

AI documentation:

- [Architecture and taxonomy](docs/ai-architecture.md)
- [Recommendation engine](docs/recommendation-engine.md)
- [Game-generation AI](docs/game-generation-ai.md)
- [API contract](docs/api-contract.md)
- [Recommendation evaluation](docs/recommendation-evaluation.md)
- [Sprint 2 AI progress](docs/sprint-2-ai-progress.md)
- [Authentication](docs/authentication.md)
- [User preferences](docs/user-preferences.md)
