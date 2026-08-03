# GameGenie AI — API Contract

Base URL: `http://localhost:8000`

Every successful response wraps data in `{"success": true, ...}`.
Every error uses the shape:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": null
  }
}
```

---

## Health

### GET /health

Returns application and catalogue status.

Response:
```json
{
  "status": "healthy",
  "service": "GameGenie AI Backend",
  "version": "1.0.0",
  "environment": "development",
  "catalogue_initialized": true,
  "game_count": 21
}
```

---

## Games Catalogue

### GET /api/games

Paginated + filtered list.

Query parameters:
- `page` (int, default 1)
- `page_size` (int, default 20, max 100)
- `genre`, `platform`, `tag`, `developer`, `publisher` (str)
- `release_year` (int)
- `min_rating` (float 0-5)
- `multiplayer`, `single_player` (bool)
- `price_category` (`free` | `budget` | `mid-range` | `premium` | `unknown`)
- `sort_by` (`title` | `release_year` | `rating` | `popularity` | `price`)
- `sort_direction` (`asc` | `desc`)

### GET /api/games/{game_id}

Single game or `404 GAME_NOT_FOUND`.

### GET /api/games/search?q=...

Title/tag/genre search with pagination. Query `q` must be non-empty.

### GET /api/genres

Facet list of genres with counts.

### GET /api/platforms

Facet list of platforms with counts.

---

## Search — Phase 3

### POST /api/search/interpret

Extracts genres, platforms, tags, and free_text from a natural-language prompt using deterministic keyword matching.

Request:
```json
{ "query": "a relaxing farming game" }
```

Response:
```json
{
  "success": true,
  "query": "a relaxing farming game",
  "preferences": {
    "genres": [],
    "platforms": [],
    "tags": ["relaxing", "farming"],
    "free_text": "a relaxing farming game"
  }
}
```

---

## Recommendations — Phase 5

> **Note:** Two recommendation implementations coexist:
> - `POST /api/search/recommend` — AI-powered engine using semantic embeddings (accepts `preference_text` field)
> - `POST /api/v2/recommend` — Rule-based hybrid ranking (accepts `query` field)
>
> The frontend may use either. The v2 endpoint is deterministic and dependency-free;
> the AI endpoint provides richer semantic matching.

### POST /api/search/recommend

AI-powered semantic recommendations. See `docs/recommendation-engine.md` for scoring model details.

Request:
```json
{
  "preference_text": "a cozy puzzle game on PC",
  "limit": 10,
  "excluded_game_ids": []
}
```

Response includes `items` (with per-item scores and explanations), the normalized prompt, and extracted preferences.

### POST /api/v2/recommend

Rule-based hybrid ranking. Deterministic and dependency-free.

Weights:
- Genre overlap: 40%
- Tag overlap: 25%
- Platform overlap: 20%
- Rating (normalised 0-5 → 0-1): 15%

Request:
```json
{
  "query": "a cozy puzzle game on PC",
  "limit": 10,
  "filters": {
    "platforms": ["PC"],
    "genres": ["Puzzle"],
    "tags": ["cozy"],
    "price_category": "budget",
    "min_rating": 4.0
  }
}
```

Validation:
- `query` — 3 to 500 characters (whitespace-stripped)
- `limit` — 1 to 20
- Hard filters (platform, genre, tag, price_category, min_rating) applied before ranking

---

## Game Generator — Phase 9

> **Note:** Two generator implementations coexist:
> - `POST /api/generator/interpret` — AI-driven configuration builder (accepts `prompt` field)
> - `POST /api/v2/generator/interpret` — Rule-based deterministic interpreter (accepts `query` + `template` fields)

### POST /api/generator/interpret

AI-driven template selection and configuration. See `docs/game-generation-ai.md`.

Request:
```json
{
  "prompt": "a hard cyberpunk shooter with fast enemies",
  "selected_game_id": null,
  "overrides": {}
}
```

Response includes `selection` (template + confidence), `configuration`, and any `warnings`.

### POST /api/v2/generator/interpret

Rule-based interpreter that maps prompt keywords to `SpaceShooterConfig` fields. Deterministic.

Request:
```json
{
  "query": "a hard cyberpunk shooter with fast enemies",
  "template": "space_shooter"
}
```

Response:
```json
{
  "success": true,
  "query": "a hard cyberpunk shooter with fast enemies",
  "template": "space_shooter",
  "configuration": {
    "template": "space_shooter",
    "title": "Neon Strike",
    "theme": "cyberpunk",
    "difficulty": "hard",
    "player_speed": 8,
    "enemy_speed": 7,
    "enemy_spawn_interval": 1.0,
    "lives": 2,
    "difficulty_scaling": true
  },
  "warnings": []
}
```

Supported templates:
- `space_shooter`

Value ranges (all enforced by Pydantic):
- `player_speed` — 3 to 10
- `enemy_speed` — 1 to 8
- `enemy_spawn_interval` — 0.5 to 5.0 seconds
- `lives` — 1 to 5

Keyword detection:

| Category | Keywords |
|----------|----------|
| Hard difficulty | hard, difficult, challenging, brutal, extreme, punishing |
| Easy difficulty | easy, casual, relaxing, beginner, gentle, chill |
| Fast pace | fast, quick, rapid, speedy, swift |
| Slow pace | slow, steady, calm |
| Dense spawning | many enemies, waves, swarm, hordes, endless |
| Difficulty scaling | scaling, increasing, gets harder, escalating, progressive |

Theme detection: cyberpunk, neon, alien, asteroid, retro, pixel, steampunk, fantasy (defaults to `space`).

---

## Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `VALIDATION_ERROR` | 422 | Request body failed Pydantic validation |
| `INVALID_QUERY` | 400 | Query string was empty or whitespace-only |
| `INVALID_PAGE_SIZE` | 422 | Page size exceeded configured max |
| `GAME_NOT_FOUND` | 404 | No game with the given ID |
| `NOT_FOUND` | 404 | Route does not exist |
| `UNSUPPORTED_TEMPLATE` | 422 | Generator template not recognised |
| `DATASET_MISSING` | 503 | Games dataset file not found |
| `INVALID_DATASET` | 503 | Games dataset is malformed |
| `CATALOGUE_INITIALIZATION_FAILED` | 503 | Startup could not load the catalogue |
| `AI_SERVICE_UNAVAILABLE` | 503 | Recommendation service not initialised |
| `HISTORY_UNAVAILABLE` | 503 | History service not initialised |
| `GENERATOR_UNAVAILABLE` | 503 | Generator service not initialised |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
