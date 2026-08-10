# Authentication

Sprint 3 Phase 10 adds persistent accounts and revocable sessions without changing anonymous catalogue, interpretation, recommendation, or generator access.

## Storage and migration

SQLAlchemy 2 models live in `backend/app/db/models.py`. Alembic revision `20260810_01` creates `users`, `user_preferences`, and `refresh_sessions`. The refresh table stores SHA-256 identifiers for JWT IDs rather than raw refresh tokens.

Apply migrations from `backend`:

```powershell
python -m alembic upgrade head
```

The local default is `sqlite:///data/gamegenie.db`. Set `DATABASE_URL` and install the maintained driver for the chosen deployment database.

## Security configuration

Set `AUTH_SECRET_KEY` to an unpredictable value of at least 32 characters. It has no source-code default; authentication endpoints return `AUTH_CONFIGURATION_ERROR` until configured. `ACCESS_TOKEN_MINUTES` defaults to 15 and `REFRESH_TOKEN_DAYS` to 30.

Passwords must be 10–128 characters with uppercase, lowercase, and numeric characters. `pwdlib`'s recommended Argon2 implementation hashes them. Passwords and hashes never appear in public schemas. Emails are syntactically validated, trimmed, and case-folded; a unique database index is the final duplicate guard.

## Session flow

Registration and login return a short-lived Bearer access token plus a refresh token. Both require issuer, subject, type, ID, issue-time, and expiry claims. Refresh tokens also require an active server-side session.

`POST /api/auth/refresh` rotates the refresh token and revokes the old session. `POST /api/auth/logout` revokes the supplied refresh session. Malformed, expired, wrong-type, unknown-user, revoked, and inactive-user tokens use the standard API error envelope.

The frontend keeps access tokens in React state and the refresh token in local storage for session restoration. A production deployment with stricter XSS/session requirements should move refresh transport to Secure, HttpOnly, SameSite cookies and add CSRF handling.

`get_current_user` protects account and activity endpoints. `get_optional_current_user` accepts no token for public endpoints but validates a supplied token. Recommendations use the optional dependency: anonymous calls retain the Sprint 2 ranking, while authenticated calls assemble the bounded Phase 12 profile and record Phase 11 search history.
