# Sprint 3 completion report

Verified on 2026-08-10 from `feature/ai-sprint-2`. This report describes the implemented repository and distinguishes automated evidence, browser evidence, and remaining human judgement.

## 1. Executive summary

Sprint 3 is implemented as one FastAPI/SQLAlchemy backend and one React/Vite/TypeScript frontend. It preserves anonymous Sprint 2 discovery and recommendation behavior while adding authenticated profiles, activity, bounded personalisation, three playable Phaser templates, and owner-scoped generated-game persistence and sharing.

The final clean-database check upgraded all Alembic revisions from an empty SQLite database. The complete automated suites pass: 280 backend tests and 36 frontend tests. Ruff lint/format, MyPy, TypeScript, application import, OpenAPI generation, and the production build also pass.

## 2. Completed Sprint 3 phases

- Phase 10 — Authentication and User Profiles: persistent accounts, rotating sessions, profiles, controlled preferences, and protected frontend routes.
- Phase 11 — History, Favourites and Feedback: owner-scoped search history, catalogue favourites, four feedback values, and dashboard activity.
- Phase 12 — Personalised Recommendation Engine: bounded signals from preferences, favourites, feedback, and recurring searches without replacing Sprint 2 ranking.
- Phase 8 — Additional Game Templates: shared Phaser runtime plus Space Shooter, Endless Runner, and Maze Escape.
- Phase 13 — Generated Game Saving and Sharing: versioned owner storage, reopen/update/delete, public slugs, and revocation.
- Phase 15 — Testing and Integration: consistent frontend states, navigation/session fixes, responsive/accessibility polish, regression verification, and documentation synchronization.

## 3. Final implemented architecture

FastAPI owns the HTTP contract, exception envelope, catalogue service, recommendation service, and dependency injection. SQLAlchemy stores accounts and user-owned activity; Alembic owns schema evolution. The catalogue remains an immutable processed JSON dataset so Sprint 3 persistence does not alter Sprint 2 game records.

The AI path normalizes prompts, extracts taxonomy values, retrieves semantic candidates, applies hybrid ranking and explanations, and optionally applies capped personalisation. Generation selects one of exactly three discriminated configuration schemas. React uses one typed API client and auth context. `GameHost`, the template registry, and the shared mount function isolate Phaser lifecycle from React.

## 4. Backend capabilities

- Catalogue list/detail/search and normalized facets.
- Prompt interpretation, semantic retrieval, hybrid ranking, and grounded explanations.
- Registration, login, refresh rotation, logout, current-user lookup, and optional-current-user recommendation access.
- Controlled preferences, search history, favourites, recommendation feedback, and personalised reranking.
- Prompt-to-template generation with schema-bounded settings and warning-preserving fallbacks.
- Generated-game CRUD, sharing, public read-only lookup, configuration revalidation, and version compatibility.
- Standard validation and application-error envelopes across the API.

## 5. Frontend capabilities

The frontend implements registration, login, dashboard, profile, preferences, history, favourites, recommendation controls, game generation, My Games, saved playback, and public shared playback. Protected routes wait for session restoration and preserve the requested URL through login. Public shared pages remain anonymous. Loading, error, and empty states use shared components; navigation is SPA-safe and responsive; controls have labels, focus styles, and readable busy/error states.

## 6. AI and recommendation capabilities

Anonymous requests use the unchanged Sprint 2 route and omit search persistence and personalisation claims. Authenticated empty profiles retain the same effective base ranking. The configured target mix is 80% existing hybrid score, 10% explicit preferences, 4% favourite similarity, 4% feedback, and 2% recurring recent searches. Overlap reduction and a ±20-point total cap keep the prompt dominant. Feedback direction and recency, removed favourites, cold starts, score bounds, and reason deduplication have focused automated coverage.

Generated games are persisted but are not currently a ranking signal. The profile model tolerates that future source without requiring it.

## 7. Supported game templates

The supported list is exactly:

- `space_shooter` — movement, firing, enemies, collisions, score, lives, game over, scaling, and restart.
- `endless_runner` — automatic movement, jump, obstacles, collision, distance score, optional speed scaling, game over, and restart.
- `maze_escape` — deterministic maze, movement, timer, obstacles, exit, win/lose states, difficulty, and restart.

Synonyms, ambiguity, reasonable fallback, unsupported intent, original-prompt preservation, field bounds, and cross-template rejection are automated. Scene-level deterministic logic and shared mount/cleanup/resize behavior are also tested.

## 8. Generated-game persistence and sharing

`GeneratedGame` stores the owner, title, source prompt, template discriminator, validated JSON configuration, version, optional public slug, visibility, and timestamps. Owner-scoped queries conceal cross-user IDs. Public responses exclude owner details and prompt. Slugs are cryptographically random and unique; unsharing clears the slug and revokes the old URL.

Version `1.1` is current. Version `1.0` is explicitly compatible, preserves supplied core gameplay values, fills safe defaults, and reports `migrated_from_version`. Malformed, unsupported, mismatched, and wrong-template data fail readably.

## 9. Final automated test totals

- Backend: 280 passed.
- Frontend: 36 passed.

The backend total includes authentication/security, two-user ownership, anonymous recommendations, activity, personalisation, template generation, validation, migrations, and generated-game compatibility. The frontend total includes auth state, protected routes, preferences, activity controls, optimistic rollback, all three saved-player dispatches, public pages, registry dispatch, cleanup, resize, and duplicate-instance prevention.

## 10. Lint, format, type, and build results

- Ruff lint: passed.
- Ruff formatting check: passed (82 files formatted).
- MyPy: passed for `app` and `tests` (76 source files).
- TypeScript project check: passed.
- Vite production build: passed.
- Frontend lint: no lint script or configuration exists, so no frontend lint result is claimed.
- Application import and OpenAPI generation: passed; 25 paths, 33 operations, and no duplicate operation IDs.
- Alembic: one head, `20260810_03`; clean upgrade passed.

## 11. Browser and manual verification

The Phase 8 release smoke check launched all three templates in a browser, switched templates, maintained one canvas, resized, navigated away/back, and exercised an Endless Runner restart. Phase 15A browser checks covered registration, login, logout, session restoration on refresh, protected redirects, authenticated route navigation, the anonymous shared route, and tablet/mobile overflow and navigation behavior.

The final in-app browser environment freezes a JavaScript prototype that Phaser 3.90 expects to extend, so Phaser cannot initialize inside that instrumented browser. This is a verification-environment limitation rather than a failure reproduced in the normal browser smoke check. Keyboard feel, complete collision pacing, and every win/lose path remain human gameplay checks.

## 12. Security and ownership results

Passwords use the maintained Argon2 implementation from `pwdlib`; plaintext and hashes are absent from response schemas. Emails are normalized and uniquely indexed. JWTs require issuer, subject, type, ID, issued-at, and expiry claims. Refresh sessions store a SHA-256 identifier, rotate on refresh, and revoke on logout. Missing, malformed, expired, wrong-type, revoked, inactive-user, and insecure-secret cases are covered.

User-owned database queries scope preferences, history, favourites, feedback, and generated games to the current user. Cross-user history and generated-game access use concealment/not-found behavior. Share and unshare are owner-only. No real `.env`, secret, or local database is tracked; environment examples contain placeholders.

## 13. Anonymous Sprint 2 regression result

Passed. Catalogue discovery, interpretation, recommendation, explanations, and configuration generation remain public. Anonymous recommendation uses the non-profile ranker, returns `search_id: null`, creates no history, and omits personalisation fields. Empty authenticated profiles produce the same effective item ranking.

## 14. Known limitations

- The development catalogue and deterministic fallback embeddings are intentionally small; production relevance needs a larger labelled dataset and offline metrics.
- Phaser uses programmatic assets and compact mechanics; audio, a production asset pipeline, and broader cross-browser gameplay judgement are outside Sprint 3.
- Play progress, scores, and active scene state are not persisted.
- Public links are bearer-style URLs and there is no public discovery index or collaboration model.
- Refresh tokens currently use browser local storage; production hardening should use Secure, HttpOnly, SameSite cookies with CSRF controls.
- The lazy Phaser production chunk is large and produces a non-failing Vite warning.

## 15. Deferred post-MVP features

Production catalogue ingestion, trained/hosted embeddings, richer evaluation datasets, play-progress persistence, continue-playing state, audio/art pipelines, public discovery, collaboration, creator attribution, analytics, end-to-end browser CI, and cookie-based refresh transport are deferred.

## 16. Final Sprint 3 status

Sprint 3 is complete against the implemented scope. All required backend contracts and frontend routes are present, migrations build cleanly, current automated verification is green, and previous normal-browser gameplay smoke testing covers the three supported templates.

## 17. Hackathon MVP readiness

The Hackathon MVP is ready for final demonstration with a local `.env`, migrated database, and both servers running. A presenter should perform one final human check of keyboard focus and game input on the actual demo browser and hardware before the live session.
