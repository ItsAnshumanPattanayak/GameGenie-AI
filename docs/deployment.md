# Free deployment: Render and Neon

GameGenie deploys from GitHub `main` as a Render Python Web Service and a Render Static Site, with account and generated-game data stored in Neon PostgreSQL. Render's filesystem is ephemeral and must not be used for persistent user data. The tracked catalogue files are read-only application assets; PostgreSQL is the production system of record.

The repository-level `render.yaml` is the canonical service configuration. It contains no credentials or fixed deployment hostnames.

## Before deployment

1. Merge the verified deployment changes into `main`. Render cannot deploy uncommitted local work.
2. Create or sign in to Render, Neon, and the GitHub account that can read `ItsAnshumanPattanayak/GameGenie-AI`.
3. In Neon, create a Free project and database in a region close to the Render service. In Neon's **Connect** dialog, disable the connection-pooling toggle and copy the direct connection string because the same URL runs Alembic schema migrations. Treat it as a secret; never paste it into source, an issue, or chat.
4. Use a TLS-enabled Neon URL of this shape:

   ```text
   postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require
   ```

   The backend normalizes `postgres://` and `postgresql://` URLs to SQLAlchemy's Psycopg 3 dialect. Percent-encoded credentials are supported by both the application and Alembic. Keep any additional TLS or channel-binding parameters Neon supplies.

5. Generate an unpredictable authentication secret of at least 32 characters in a trusted local terminal. Keep the output private. For example:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

## Create the Render services

In Render, select **New > Blueprint**, connect the GitHub repository, select branch `main`, and use the root `render.yaml`. The Blueprint declares:

| Setting | Backend | Frontend |
| --- | --- | --- |
| Type/runtime | Web Service / Python | Static Site |
| Plan | Free | Free static site |
| Root directory | `backend` | `frontend` |
| Build | `pip install -r requirements.txt && alembic upgrade head` | `pnpm install --frozen-lockfile && pnpm build` |
| Start | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | Not applicable |
| Publish directory | Not applicable | `dist` |
| Health check | `/health` | Not applicable |

Render prompts for every value marked `sync: false`. Enter:

### Backend environment

```env
DATABASE_URL=<SECRET NEON CONNECTION STRING>
AUTH_SECRET_KEY=<SECRET RANDOM VALUE, AT LEAST 32 CHARACTERS>
ALLOWED_ORIGINS=https://<ACTUAL-FRONTEND-SERVICE>.onrender.com
```

`APP_ENV=production` and `DEBUG=false` are non-secret values already declared in the Blueprint. Production startup rejects SQLite, a missing or short auth secret, debug mode, wildcard CORS, and an origin list without an HTTPS frontend.

### Frontend environment

```env
VITE_API_URL=https://<ACTUAL-BACKEND-SERVICE>.onrender.com
```

Do not include a trailing slash in either deployed URL. Vite embeds `VITE_API_URL` at build time, so changing it requires a new frontend deploy.

If Render has not shown both assigned hostnames when it asks for variables, create the two services from the same repository manually with the settings in the table. Deploy the backend only after `DATABASE_URL`, `AUTH_SECRET_KEY`, and the actual frontend origin are set. Do not invent or commit a temporary hostname.

## Database migrations

The backend build runs `alembic upgrade head` after installing dependencies. Render serializes deploys for one service, and this command runs once per backend build—not once per Uvicorn worker startup. A failed migration fails the new deploy while the last successful deploy remains active.

All current migrations (`20260810_01`, `20260810_02`, and `20260810_03`) use portable SQLAlchemy types and explicit indexes, uniqueness, foreign keys, and delete behavior. JSON configuration maps to PostgreSQL JSON, generated-game public slugs remain unique, and user-owned rows cascade on account deletion.

Before introducing a destructive or long-running future migration, revise the migration plan. Paid Render services can move migrations to a pre-deploy command. Free services do not provide shell access or pre-deploy commands, so the build step is the reproducible free-tier option.

To verify the current migration from a trusted machine without exposing the URL in a tracked file, set `DATABASE_URL` only in that process environment, change to `backend`, and run:

```powershell
python -m alembic upgrade head
python -m alembic current
```

## SPA routing and CORS finalization

The Blueprint defines a Render static-site rewrite from `/*` to `/index.html`. Existing assets still win over the wildcard, while direct visits or refreshes on React routes such as `/dashboard`, `/play/saved/:id`, and `/shared/:slug` reach the client router.

The two deployed URLs must point at each other:

```text
frontend VITE_API_URL  = https://<actual-backend>.onrender.com
backend ALLOWED_ORIGINS = https://<actual-frontend>.onrender.com
```

To retain local access in the same backend deployment, use a comma-separated explicit list:

```env
ALLOWED_ORIGINS=https://<actual-frontend>.onrender.com,http://localhost:5173,http://127.0.0.1:5173
```

Never use `*`: the API allows credentialed requests and authorization headers. After changing `ALLOWED_ORIGINS`, redeploy the backend. After changing `VITE_API_URL`, redeploy the frontend.

## Verification

After both deploys complete:

1. Open `https://<backend>.onrender.com/health`; expect HTTP 200 and `status: healthy` after startup.
2. Open `https://<backend>.onrender.com/docs`; confirm Swagger loads without exposing configuration values.
3. Open the frontend and directly refresh `/login`, `/dashboard`, and `/shared/<valid-slug>`; none should return a Render 404.
4. Register and log in, then exercise preferences, recommendations, history, favourites, feedback, all three generators, save/reopen, share, anonymous playback, and unshare.
5. Inspect the browser console and Network panel for unexpected 4xx/5xx responses, CORS errors, mixed content, or `localhost` requests.

The health endpoint checks application/catalogue availability and does not connect to an embedding model. A first request to a sleeping Free web service can take about a minute. The catalogue and deterministic recommendation index initialize once during application startup; the optional Sentence Transformer implementation remains lazy and is not initialized by health checks.

## Redeployment from `main`

Teammates should run the repository's backend and frontend quality checks, merge through the normal review process, and push the approved commit to `main`. Both services have commit-triggered auto-deploys. Watch the backend migration/build and health check before accepting the frontend deployment as complete. A Render restart alone does not pick up a new commit or newly changed environment variables; trigger a deploy after configuration changes.

## Secret and database rotation

To rotate `AUTH_SECRET_KEY`, generate a new value, replace it in the Render backend environment, and deploy. Existing access and refresh tokens become invalid; users must sign in again. Do not retain the old value in source or logs.

To replace or rotate `DATABASE_URL`:

1. Create the new Neon database/role and migrate or restore the required data.
2. Run `alembic upgrade head` against the new database.
3. Replace `DATABASE_URL` in the Render backend environment and deploy.
4. Verify `/health`, authentication, and saved data before revoking the old Neon credential.
5. Revoke the old role or password in Neon after the cutover succeeds.

Changing `DATABASE_URL` without copying existing data creates an empty GameGenie account database. Never place either old or new URLs in `.env.example` or Git.

## Troubleshooting

- **Backend fails during settings load:** confirm `APP_ENV=production`, a PostgreSQL `DATABASE_URL`, a 32+ character `AUTH_SECRET_KEY`, `DEBUG=false`, and at least one exact HTTPS origin.
- **Psycopg connection failure:** recopy the Neon URL, retain its TLS query parameters, ensure special characters are percent-encoded, and confirm the Neon project is active.
- **Migration fails through a pooler hostname:** select Neon's direct/unpooled connection string; session-dependent schema migrations should not use the pooled endpoint.
- **Migration build failure:** inspect only the exception type/message in Render logs; do not copy a credential-bearing URL into support channels. Run the same revision against a disposable PostgreSQL database if diagnosis is needed.
- **CORS error:** compare the browser's exact frontend origin (scheme and hostname) with `ALLOWED_ORIGINS`; paths and trailing slashes do not belong in origins.
- **Frontend calls localhost:** set `VITE_API_URL` on the Static Site and redeploy because Vite values are build-time values.
- **Route refresh returns 404:** confirm the Static Site rewrite is `/*` to `/index.html` with action **Rewrite**, as declared in `render.yaml`.
- **First request is slow:** wait through the Free-service cold start and retry `/health`; distinguish the spin-up delay from a sustained 5xx response.
- **Data disappears after restart:** production is using SQLite or writing files. Set the Neon `DATABASE_URL`; Render's Free filesystem is ephemeral.

Free hosting is appropriate for an MVP, demo, or hobby workload. It has cold starts, finite monthly resources, no free shell access, and no persistent local disk. Monitor Neon and Render free-tier limits before treating the deployment as durable production infrastructure.
