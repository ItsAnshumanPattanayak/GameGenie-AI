# Sprint 3 baseline

Verified on 2026-08-10 from branch `feature/ai-sprint-2` at commit `649534c`. The tracked worktree was clean before this inspection. This document describes only files and behavior present in this checkout; it does not assume work from the source laptop or other team members exists.

## Existing architecture

- A Python 3.11+ FastAPI application lives under `backend/app`. `app.main:create_app` configures CORS, exception handlers, routes, and a lifespan-managed catalogue/recommendation service.
- Catalogue data is read from `backend/data/processed/games.json` (21 records). Startup rebuilds it from `backend/data/raw/games.json` through the deterministic loader/normalizer/preprocessor if the processed file is absent or invalid.
- `GameService` is an immutable, in-memory catalogue adapter supporting listing, filtering, sorting, pagination, text search, facets, and bulk access for AI scoring.
- Pydantic schemas define the public catalogue, AI, recommendation, generator, pagination, and error contracts.
- AI routes are thin adapters over deterministic, independently testable prompt, recommendation, explanation, and generation modules.
- There is no frontend or persistence/authentication layer in this checkout.

## Feature baseline

| Feature | State | Evidence / boundary |
|---|---|---|
| FastAPI backend | Verified | Application factory, lifespan, middleware, handlers, routes, Swagger, and ReDoc exist. |
| Database layer | Missing | Runtime uses JSON files plus in-memory `GameService`; no database engine/session/repository exists. |
| SQLAlchemy models | Missing | No SQLAlchemy dependency or ORM models. Pydantic API models are not database models. |
| Alembic migrations | Missing | No Alembic dependency, config, or migration tree. |
| Authentication | Missing | No users, credentials, sessions, tokens, auth dependencies, or protected routes. |
| React/Vite frontend | Missing | No frontend directory, `package.json`, Vite config, or JavaScript application. |
| TypeScript | Missing | No TypeScript sources or `tsconfig`. |
| Tailwind | Missing | No Tailwind dependency or configuration. |
| Phaser.js | Missing | Only a Phaser-shaped configuration contract exists; no Phaser runtime/game code. |
| Discovery UI | Missing | Discovery exists only as backend catalogue/search/recommendation APIs. |
| Space Shooter | Partial | Template selection and safe configuration generation exist; playable movement, shooting, enemies, collisions, score, lives UI, game over, and restart do not. |
| Prompt interpretation | Verified | Unicode-safe normalization, taxonomy/aliases, typed extraction, conflicts, hard-filter markers, and confidence scoring. |
| Semantic embeddings | Partial | Sentence Transformer and deterministic hash services, artifact validation, and a build script exist. Production MiniLM model cache and generated embedding artifacts are intentionally absent; local app/test runtime uses hash embeddings. |
| Hybrid recommendation engine | Verified | Vectorized semantic retrieval, active-weight redistribution, hard filters, stable ordering, exclusions, score breakdowns, and bulk catalogue lookup. |
| Explanation engine | Verified | Deterministic explanations are grounded in recorded matched attributes. |
| Template selector | Verified | Controlled selection supports only `space_shooter` and returns typed unsupported results otherwise. |
| Game configuration generator | Verified | Typed defaults, deterministic prompt rules, safe selected-game handoff, override validation/clamping, title sanitization, and warnings. |
| Frontend/backend API client | Missing | No frontend and no generated or handwritten client. |
| Automated backend tests | Verified | 150 tests cover catalogue/data/schema/API and Sprint 2 AI/generator behavior. |
| Frontend tests | Missing | No frontend exists, so no frontend tests were invented or run. |

## Existing backend endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Service, environment, catalogue state, and game count. |
| `GET` | `/api/games` | Paginated catalogue with filters and sorting. |
| `GET` | `/api/games/search` | Deterministic text search plus catalogue filters. |
| `GET` | `/api/games/{game_id}` | Single game or standardized `GAME_NOT_FOUND`. |
| `GET` | `/api/genres` | Genre facet counts. |
| `GET` | `/api/platforms` | Platform facet counts. |
| `POST` | `/api/search/interpret` | Sprint 2 prompt normalization and typed preference extraction. |
| `POST` | `/api/search/recommend` | Hybrid ranked, scored, and explained recommendations. |
| `POST` | `/api/generator/interpret` | Template selection and optional validated game configuration. |

There is a contract conflict at `POST /api/search/interpret`: both `app.api.routes.ai` and the older `app.api.routes.search` register that method/path with different schemas. Runtime routing currently reaches the Sprint 2 handler first, which is why both compatibility and Sprint 2 tests pass, but OpenAPI generation overwrites the operation with the older `query` request/response schema and emits a duplicate-operation warning. Sprint 3 must choose one canonical route/contract (retaining aliases if needed) before generating a frontend client.

## Current AI modules

- `taxonomy.py`: immutable taxonomy and deterministic aliases.
- `prompt_normalizer.py`: Unicode-safe, longest-phrase-first normalization.
- `preference_extractor.py` and `preference_parser.py`: typed extraction plus the compatibility adapter.
- `embedding_service.py`: MiniLM wrapper, deterministic offline embeddings, game text construction, and artifact integrity checks.
- `recommendation_engine.py`: vectorized cosine candidate retrieval.
- `ranking_engine.py`: hybrid scoring, filtering, matching, and stable ordering.
- `explanation_engine.py`: grounded natural-language reasons.
- `recommender.py`: orchestration over catalogue, embeddings, retrieval, ranking, and explanation.

Legacy protocol/export modules (`similarity.py` and `explanations.py`) remain compatibility surfaces and should not be replaced merely for modernization.

## Current game-generation modules

- `template_selector.py` selects only the supported `space_shooter` template.
- `game_generator.py` turns prompt plus optional selected catalogue game into a validated `GameConfiguration`.
- `schemas/ai.py` constrains the executable-facing configuration and forbids extra fields.
- This layer generates data only. No browser renderer, Phaser scene, assets, or playable Space Shooter is present.

## Frontend state

No frontend implementation exists in this repository. Sprint 3 should create it as a distinct application rather than mixing UI concerns into the backend. Recommended baseline: React + Vite + TypeScript, Tailwind for the existing design direction, a typed API client after the interpret-route conflict is fixed, and Phaser isolated behind a game component/scene boundary. Add the frontend's own lint, type-check, unit/component test, and production-build scripts at scaffold time. Configure the backend CORS origin for Vite (the current default is `http://localhost:3000`, while the chosen frontend port may differ).

## Database state

There is no database. The checked-in raw/processed JSON catalogue and in-memory `GameService` are the source of runtime data. There are no SQLAlchemy models, sessions, repositories, migrations, user/search-history tables, or seed migration. Any Sprint 3 persistence adapter should preserve the existing bulk catalogue boundary used by `RecommendationService` and avoid N+1 record loading.

## Test and verification state

The transferred ignored `.venv` referenced a missing Anaconda installation on the old laptop. It was rebuilt locally with Python 3.12.13 and `requirements-dev.txt` was installed successfully. The environment is ignored and is not a tracked repository change.

- `python -m pip check`: passed; no broken requirements.
- `python -c "from app.main import app"`: passed.
- `pytest`: 150 passed, with one dependency deprecation warning from FastAPI/Starlette's current `TestClient` import concerning future `httpx2` usage.
- `ruff check .`: passed.
- `ruff format --check .`: passed (55 files already formatted).
- `mypy app tests`: passed (53 source files, no issues).
- Frontend install, tests, type-check, lint, and production build: not applicable because no frontend/package manifest exists.

The older Sprint 2 progress document reports 142 tests; the current checkout collects 150, so that count is historical rather than a failure.

## Missing Sprint 3 foundations and dependencies

- Persistence design, database driver, SQLAlchemy, Alembic, environment configuration, models, repositories, migrations, and seed/import strategy.
- Authentication design and its chosen password/token/session dependencies, user models, API contracts, authorization dependencies, and tests.
- Complete frontend toolchain: package manager lockfile, React, Vite, TypeScript, Tailwind, routing/state choices as needed, API client, test runner/DOM utilities, and lint/build configuration.
- Phaser dependency, scene lifecycle, assets, gameplay implementation, React integration, cleanup/restart behavior, and gameplay tests.
- Deployment provisioning for the MiniLM model/cache and the three generated embedding artifacts (`game_embeddings.npy`, `game_ids.json`, `metadata.json`), or an explicit decision to keep deterministic embeddings outside tests.
- Reproducible dependency locking. Python dependencies currently use bounded ranges but there is no resolved lockfile.

Do not add all possible libraries up front. Select database/auth/frontend packages when their Sprint 3 design is agreed, then record and lock only those used.

## Known blockers

1. Duplicate `/api/search/interpret` registration makes generated OpenAPI disagree with runtime behavior and blocks a trustworthy generated frontend client.
2. No database/authentication foundation exists for features that require users, persistence, or history.
3. No frontend exists, so discovery UI and playable Phaser integration cannot yet be verified.
4. Production embedding artifacts/model cache are absent and must be built or provisioned for production semantic quality.
5. The 21-game sample has documented metadata/relevance gaps, especially shooter, educational, family-friendly, difficulty, and hardware coverage.

## Recommended Sprint 3 dependency order

1. Make `/api/search/interpret` a single canonical OpenAPI contract while retaining intentional backward-compatible input aliases.
2. Define persistence and authentication requirements, entities, API ownership, environment variables, and threat boundaries.
3. Add the database driver, SQLAlchemy session/repository layer, models, Alembic baseline migration, and deterministic catalogue import; preserve the AI bulk-catalogue interface.
4. Add authentication dependencies, models/routes/dependencies, migrations, and backend tests.
5. Scaffold React/Vite/TypeScript with a lockfile and CI-equivalent lint, type-check, test, and build commands; align CORS and environment-based API URLs.
6. Implement the typed API client and discovery UI against the verified catalogue, interpretation, and recommendation contracts.
7. Add Tailwind/design primitives, then accessible loading, empty, error, filtering, recommendation, and explanation states.
8. Add Phaser and implement the Space Shooter as a consumer of the existing safe configuration schema; keep scene lifecycle isolated from React.
9. Add frontend component/gameplay and cross-layer integration tests, then production builds and deployment configuration.
10. Provision production embeddings, enrich/evaluate catalogue metadata, run end-to-end acceptance/security/performance checks, and only then treat the repository as ready for Sprint 3 Phase 10 integration/release work.

## Readiness decision

The backend and Sprint 2 AI baseline are healthy and ready to be extended. The repository as a whole is **not yet ready for Sprint 3 Phase 10** because the canonical API contract, database/authentication foundations, frontend/API client, playable Phaser game, and production embedding provisioning are still missing. Follow the dependency order above rather than replacing the verified Sprint 2 systems.
