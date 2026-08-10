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

## User activity endpoints

All activity endpoints require `Authorization: Bearer <access_token>` and only return or mutate the current user's records.

- `GET /api/history/searches` lists recent searches; `GET /api/history/searches/{id}` returns one owned entry.
- `DELETE /api/history/searches/{id}` removes one owned entry; `DELETE /api/history/searches` clears the caller's history.
- `GET /api/favourites` returns favourite rows with embedded catalogue game data.
- `POST /api/favourites/{game_id}` adds a valid catalogue game idempotently; `created` distinguishes a new row from an existing favourite.
- `DELETE /api/favourites/{game_id}` removes the caller's favourite.
- `POST /api/feedback` accepts `game_id`, optional `search_id`, and `feedback_type` (`relevant`, `not_relevant`, `interested`, or `already_played`).
- `GET /api/feedback` lists the caller's feedback.

Unknown catalogue IDs use `GAME_NOT_FOUND` (404). Unknown or cross-user history IDs use `SEARCH_HISTORY_NOT_FOUND` (404). Invalid feedback types use the standard validation response.

Existing semantic, component, and legacy recommendation `score` values remain JSON numbers on a 0–1 scale. Optional Phase 12 explanatory scores use the documented 0–100 percentage-point scale. Existing catalogue routes and fields are unchanged.

## `POST /api/search/interpret`

Request: `{ "prompt": "A free multiplayer shooter for low-end PC" }`. Null and empty prompts are accepted for controlled zero-confidence interpretation.

Response contains `success`, a `prompt` object (`original`, `normalized`, `tokens`, `matched_phrases`, `unmatched_tokens`), and `preferences`. Preferences contain `genres`, `platforms`, `modes`, `themes`, `moods`, `visual_styles`, `difficulty`, `price_type`, `hardware_level`, `session_length` in minutes, `player_count`, `hard_filters`, structured `warnings`, `matched_terms`, and `confidence`. Tuple-backed immutable fields serialize as JSON arrays.

## `POST /api/search/recommend`

Request accepts either `preference_text` (the existing field) or backward-compatible input alias `prompt`, plus `limit` (1–50, default 10) and `excluded_game_ids`.

Response contains `success`, `normalized_prompt`, `preferences`, `items`, and `search_id`. Each item retains the existing `game`, `score`, and `explanation` fields and adds `score_breakdown` plus `matched_attributes`. The breakdown includes `semantic_score`, `genre_score`, `platform_score`, `mode_score`, `theme_score`, `mood_score`, `price_score`, `difficulty_score`, `hardware_score`, and its original 0–1 `final_score`.

When an authenticated profile actually changes an item score, that item also includes `base_score` (0–100), signed `personalisation_score` (percentage-point adjustment), `final_score` (0–100), `personalisation_reasons`, and a `personalisation_signals` contribution map. These optional fields are omitted when no signal changes the score. The top-level percent-scale `final_score` is distinct from the preserved hybrid `score_breakdown.final_score`.

Anonymous requests return `search_id: null`, do not persist activity, and retain the Sprint 2 ranking exactly. Authenticated successful requests build the Phase 12 profile before the current query is recorded, apply bounded reranking when signals exist, persist the query, and return the created history ID. A new authenticated user with an empty profile receives the anonymous item ranking.

## `POST /api/generator/interpret`

Request: `{ "prompt": "...", "selected_game_id": null, "overrides": {} }`. `prompt` may be null and is limited to 2,000 characters; `selected_game_id` is optional; `overrides` is an object.

Response contains `success`, `selection`, optional `configuration`, and top-level structured `warnings`. `selection` contains `template`, `supported`, `fallback`, `confidence`, `reason`, `original_prompt`, and its own `warnings`. The only non-null template values are `space_shooter`, `endless_runner`, and `maze_escape`.

`configuration` is discriminated by `template`:

- `space_shooter`: shared `title`, `theme`, and `difficulty`, plus `player_speed`, `enemy_speed`, `enemy_spawn_interval`, `lives`, and `difficulty_scaling`.
- `endless_runner`: shared fields plus `player_speed`, `jump_force`, `obstacle_frequency`, and `difficulty_scaling`.
- `maze_escape`: shared fields plus `maze_size`, `time_limit`, and `obstacle_count`.

Template schemas forbid extra fields. A known field belonging to a different template returns HTTP 200 with `success: false`, no configuration, and `TEMPLATE_INCOMPATIBLE_FIELD`. Numeric overrides may be clamped with `VALUE_CLAMPED`; malformed or unknown overrides return structured warnings.

An unrelated prompt returns HTTP 200 with `success: false`, `UNSUPPORTED_TEMPLATE`, and no configuration. A reasonable partial or ambiguous match may return a deterministic supported configuration with `fallback: true` and `CLOSEST_TEMPLATE` or `AMBIGUOUS_TEMPLATE`. In every case, `original_prompt` preserves the source intent. Malformed request schemas use the standard 422 error envelope. Unknown selected game IDs use the existing game-not-found error.

## Generated-game endpoints

Owner endpoints require `Authorization: Bearer <access_token>`:

- `POST /api/generated-games` creates a private saved game.
- `GET /api/generated-games` lists only the current user's games.
- `GET /api/generated-games/{id}` returns one owner-scoped game.
- `PUT /api/generated-games/{id}` updates supplied title, prompt, template, configuration, or version fields after validating the complete resulting configuration.
- `DELETE /api/generated-games/{id}` deletes one owner-scoped game.
- `POST /api/generated-games/{id}/share` creates or returns the active public slug.
- `POST /api/generated-games/{id}/unshare` revokes the public link and clears its slug.

Create accepts `title`, `prompt`, `template_type`, `configuration`, and optional `config_version` (default `1.1`). Responses contain `id`, the create fields, normalized `config_version`, optional `migrated_from_version`, `public_slug`, `is_public`, `created_at`, and `updated_at`. Configuration is validated both before storage and each time it is returned.

`GET /api/public/generated-games/{slug}` requires no authentication and returns a read-only public representation containing title, template, validated configuration, version/migration information, slug, and timestamps. It excludes owner ID, creator account details, and prompt. Private, revoked, malformed, and unknown slugs use the same `PUBLIC_GAME_NOT_FOUND` response.

Compatible configuration versions are `1.0` and `1.1`; responses normalize compatible legacy data to `1.1` and may report `migrated_from_version: "1.0"`. Malformed versions use `INVALID_CONFIG_VERSION`; unsupported versions use `UNSUPPORTED_CONFIG_VERSION`; mismatched templates use `TEMPLATE_CONFIGURATION_MISMATCH`; invalid or wrong-template fields use `INVALID_GAME_CONFIGURATION`.

## Errors and ownership

Account and activity persistence are separate from catalogue persistence. Authentication and activity migrations leave the JSON-backed `GameService` and anonymous AI APIs unchanged. `POST /api/search/interpret` now has one registered operation; backward-compatible `query` input remains an alias of canonical `prompt` input.

If the recommendation index cannot initialize, the endpoint returns `AI_SERVICE_UNAVAILABLE` with HTTP 503. Catalogue access remains behind the backend-owned `GameService`; activity rows store stable catalogue IDs and favourite responses use its immutable bulk view.
