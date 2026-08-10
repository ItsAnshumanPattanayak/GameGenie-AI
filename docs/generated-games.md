# Generated games: persistence and sharing

Sprint 3 Phase 13 persists validated game configurations for authenticated users and provides revocable public playback links without exposing account details.

## Data model

`GeneratedGame` stores `id`, owner `user_id`, `title`, source `prompt`, `template_type`, JSON `configuration`, `config_version`, optional unique `public_slug`, `is_public`, `created_at`, and `updated_at`. Deleting a user cascades to their generated games. Owner/date, user, template, and public-slug indexes support the primary access paths.

The public API never returns `user_id`, email, prompt, or other private profile data. Creator names are not exposed by the current API design.

## Ownership and sharing

All `/api/generated-games` mutation and owner-read endpoints require an access token and scope database queries to the current user. A cross-user identifier returns the same not-found response as an unknown identifier.

Sharing creates a URL-safe, cryptographically random slug of at least 24 characters. The database enforces uniqueness. Repeated sharing is idempotent while a link remains active. Unsharing clears the slug, so the old public URL immediately becomes unavailable; sharing again creates a new URL.

`GET /api/public/generated-games/{slug}` is anonymous and read-only. It returns only rows where `is_public` is true. Invalid, unknown, private, deleted, and revoked links all return `PUBLIC_GAME_NOT_FOUND` without revealing which case occurred.

## Configuration compatibility

Current saves use configuration version `1.1`. Both storage and loading validate configuration through the existing discriminated `SpaceShooterConfig`, `EndlessRunnerConfig`, or `MazeEscapeConfig` schema.

Legacy `1.0` is explicitly compatible. During normalization, a missing template discriminator may be restored from `template_type`, and safe Pydantic defaults fill newly optional or missing settings. Core values already present are preserved. The response returns normalized version `1.1` and `migrated_from_version: "1.0"` where useful.

Malformed version strings return `INVALID_CONFIG_VERSION`. Versions outside the explicit compatibility set, including unsupported major versions, return `UNSUPPORTED_CONFIG_VERSION`; the service never guesses or silently rewrites their gameplay. Template mismatches and wrong-template fields return readable validation errors.

## Frontend routes

- `/my-games`: authenticated library with loading, empty, error, play, edit, share, unshare, copy-link, and confirmed-delete behavior.
- `/play/saved/:id`: authenticated owner playback through the Phase 8 registry.
- `/generator?saved=:id`: loads saved prompt/settings, permits regeneration, and updates the existing record.
- `/shared/:slug`: anonymous read-only playback with an unavailable state and Create Your Own Game action.

Saved and public players pass validated configuration to the shared `GameHost`, so responsive sizing, registry dispatch, restart behavior, duplicate-instance prevention, and cleanup match newly generated games.

## Current limitations

- Saved records persist configuration, not active play progress, scores, or scene state.
- Public links are bearer-style URLs; anyone possessing an active link can play the game.
- There is no public discovery index, creator attribution, collaboration, or edit access for visitors.
- Version compatibility is deliberately limited to `1.0` and `1.1` until a later migration is explicitly implemented and tested.
