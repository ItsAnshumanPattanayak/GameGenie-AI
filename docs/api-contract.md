# AI API contract

## Authentication endpoints

- `POST /api/auth/register` accepts `name`, `email`, and `password`; returns HTTP 201 with public `user` and `tokens` objects.
- `POST /api/auth/login` accepts `email` and `password`; returns the same session response.
- `POST /api/auth/refresh` accepts `refresh_token`, rotates it, and returns a new session.
- `POST /api/auth/logout` accepts `refresh_token` and revokes its server-side session.
- `GET /api/auth/me` requires `Authorization: Bearer <access_token>` and returns the public user.

Token responses contain `access_token`, `refresh_token`, `token_type: "bearer"`, and access-token `expires_in` seconds. Public users never expose `password_hash`.

Expected auth errors include `EMAIL_ALREADY_REGISTERED` (409), `INVALID_CREDENTIALS` (401), `AUTHENTICATION_REQUIRED` (401), `INVALID_TOKEN` (401), `TOKEN_EXPIRED` (401), `USER_INACTIVE` (403), and `AUTH_CONFIGURATION_ERROR` (503). Schema validation uses `VALIDATION_ERROR` (422).

## Preference endpoints

- `GET /api/preferences` returns the authenticated user's controlled preference object.
- `PUT /api/preferences` replaces controlled fields and returns their normalized stored representation.

Unknown taxonomy values use the standard 422 envelope. See [user-preferences.md](user-preferences.md).

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

Account persistence is separate from catalogue persistence. Authentication adds user/preference/refresh-session migrations but leaves the JSON-backed `GameService` and anonymous AI APIs unchanged. `POST /api/search/interpret` now has one registered operation; backward-compatible `query` input remains an alias of canonical `prompt` input.

If the recommendation index cannot initialize, the endpoint returns `AI_SERVICE_UNAVAILABLE` with HTTP 503. Catalogue persistence remains behind the backend-owned `GameService`; the AI integration only calls its immutable bulk view and does not add migrations, history persistence, or database infrastructure.
