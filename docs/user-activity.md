# User activity

Sprint 3 Phase 11 adds account-owned search history, favourites, and recommendation feedback while keeping every catalogue and AI endpoint usable without an account.

## Persistence

Alembic revision `20260810_02` creates:

- `search_history`, storing the original query, normalized extracted-preference JSON, result count, processing time, and creation time.
- `favourite_games`, storing a user/catalogue-game reference. A unique `(user_id, game_id)` constraint makes repeated adds idempotent.
- `recommendation_feedback`, storing a supported feedback value, catalogue game ID, and optional search-history reference.

User foreign keys cascade on account deletion. Deleting search history never changes the JSON-backed catalogue; feedback search references become null if their history entry is deleted. User/time and frequently queried relationship indexes support profile reads. Catalogue details for favourites are resolved with one bulk catalogue read rather than one lookup per row.

## Recommendation integration

`POST /api/search/recommend` still uses `get_optional_current_user`. Anonymous calls are unchanged and return `search_id: null`. An authenticated successful call persists one history entry and returns its ID in `search_id`; ranking is not personalised in Phase 11.

Feedback values are controlled: `relevant`, `not_relevant`, `interested`, and `already_played`. A feedback game must exist in the current catalogue. When `search_id` is supplied, that search must belong to the caller. The current history record stores aggregate results, not individual result IDs, so Phase 11 does not prove that a feedback game appeared in that particular result set.

## Ownership and UI

All activity routes require a Bearer access token and scope reads/deletes to the current user. Cross-user IDs are returned as not found, avoiding disclosure. Duplicate favourite requests return the existing row with `created: false`.

The protected React routes `/dashboard`, `/history`, and `/favourites` provide loading, empty, and error states. History supports repeat search and deletion. Favourites support catalogue/generator links and optimistic removal with rollback. Recommendation cards optimistically add/remove favourites and roll back with a readable error if the request fails; they also submit all four feedback types.

Activity is an input foundation for Phase 12. It is not yet used to change recommendation scores, and generated-game/play-session dashboard sections remain integration placeholders.
