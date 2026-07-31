# AI API contract

All scores are JSON numbers on a 0–1 scale. Existing catalogue routes and fields are unchanged.

## `POST /api/search/interpret`

Request: `{ "prompt": "A free multiplayer shooter for low-end PC" }`. Null and empty prompts are accepted for controlled zero-confidence interpretation.

Response contains `success`, a `prompt` object (`original`, `normalized`, `tokens`, `matched_phrases`, `unmatched_tokens`), and `preferences`. Preferences contain `genres`, `platforms`, `modes`, `themes`, `moods`, `visual_styles`, `difficulty`, `price_type`, `hardware_level`, `session_length` in minutes, `player_count`, `hard_filters`, structured `warnings`, `matched_terms`, and `confidence`. Tuple-backed immutable fields serialize as JSON arrays.

## `POST /api/search/recommend`

Request accepts either `preference_text` (the existing field) or backward-compatible input alias `prompt`, plus `limit` (1–50, default 10) and `excluded_game_ids`.

Response contains `success`, `normalized_prompt`, `preferences`, and `items`. Each item retains the existing `game`, `score`, and `explanation` fields and adds `score_breakdown` plus `matched_attributes`. The breakdown includes `semantic_score`, `genre_score`, `platform_score`, `mode_score`, `theme_score`, `mood_score`, `price_score`, `difficulty_score`, `hardware_score`, and `final_score`.

## `POST /api/generator/interpret`

Request: `{ "prompt": "...", "selected_game_id": null, "overrides": {} }`. Response contains `success`, `selection` (`template`, `supported`, `confidence`, `reason`), optional `configuration`, and structured warnings. Unsupported prompts return HTTP 200 with `success: false` and no configuration; malformed schemas use the standard 422 error envelope. Unknown selected game IDs use the existing game-not-found error.

## Errors and ownership

If the recommendation index cannot initialize, the endpoint returns `AI_SERVICE_UNAVAILABLE` with HTTP 503. Catalogue persistence remains behind the backend-owned `GameService`; the AI integration only calls its immutable bulk view and does not add migrations, history persistence, or database infrastructure.

