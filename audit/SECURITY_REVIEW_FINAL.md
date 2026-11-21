# Security Review — Final (2026-11-21)

Scope: `server.py`, `backend/` (auth, security, api, ingestion), `web/`, configuration, Docker.
Method: code review, live exploitation against a local server, regression tests.

## Fixed (each was reproduced before fixing and has a regression test)
| ID | Exploit scenario (before) | Impact | Fix |
|---|---|---|---|
| SEC-01 | `POST /auth/login {"username":"<anyone>"}` → session for that account | Full account takeover, incl. GitHub-OAuth users | Real password verification (PBKDF2-SHA256), OAuth accounts cannot use passwords |
| SEC-02 | Victim with dev mode on visits any website → page sends `text/plain` POST to `127.0.0.1:8080/api/clear-db` | All decision data deleted; also arbitrary local-folder ingest | Same-origin check on all state-changing requests, JSON content type required, Host check in dev mode |
| SEC-03 | `GET /api/evidence?repo=<demo>&decision_id=<private>` (anonymous) → private decision; same for `review-action` writes | Cross-tenant read and write | Repo resolved from the object; mismatch → 404 |
| SEC-12 | Anonymous `GET /api/decisions` → every repository's decisions | Cross-tenant read | Scope to accessible repos |
| SEC-04 | `/auth/demo/login?next=https://evil/` | Open redirect + login CSRF (phishing aid) | Validated `next`; switch to disable |
| SEC-05 | Random `Authorization: Bearer <x>` per request | Rate limit bypass (brute force) | Bucket by IP unless the token is a valid session |
| SEC-06 | `CIF_BIND=0.0.0.0` with dev mode | Network-wide admin | Refused at start-up |
| SEC-07 | Anonymous `/api/github-commits?repo=../…` | Spends server GitHub token; API path manipulation | Sign-in + strict slug validation |
| SEC-08 | `docker build` | `.env` OAuth secret + user DB inside image | `.dockerignore` |
| SEC-10 | Any user cancels any ingestion job | Denial of service between users | Ownership check |
| SEC-11 | Anonymous `/api/diagnostics` | DB path, user/session counts | Admin-only details |
| AUD-01 | Client sets `"actor"` in body | Forged audit trail | Actor from verified session |
| APP-02 | Any exception | Empty reply; frontend then faked data | JSON 500, traceback only in logs |

## Verified secure (no change needed)
- GitHub OAuth: 32-byte state, stored hashed, single use, 10-minute TTL; `next` validated.
- Session tokens: random 32 bytes, stored as SHA-256, HttpOnly, SameSite=Lax, Secure on HTTPS, 7-day expiry.
- GitHub user tokens: Fernet-encrypted at rest when `CIF_TOKEN_ENC_KEY` is set, otherwise memory only.
- Webhook: HMAC-SHA256, constant-time compare, fails closed when no secret is configured.
- SQL: parameterised queries in all reviewed paths (only fixed table names are interpolated).
- XSS: a scan of all 159 template-literal interpolations in `web/app.js` found no data field
  (title, label, rationale, message, author, url…) reaching `innerHTML` without `esc()`; the
  remaining ones go to `textContent`, `setAttribute`, `alert` or are numbers/constants.
  `tests/test_frontend_escape.py` also passes. CSP `default-src 'self'`. (Heuristic scan, not a proof.)
- TLS verification is never disabled (custom CA only via `CIF_CA_BUNDLE`).
- Secrets: none in Git history (all 150 commits searched); none in `logs/`; `.env` is git-ignored.

## Residual risks (not fixed)
| Risk | Severity | Notes / recommendation |
|---|---|---|
| `.env` in the shared ZIP contains a real GitHub OAuth client secret and session secret | **Action for you** | The ZIP left your machine; **rotate the OAuth client secret** in GitHub settings and generate a new `CIF_SESSION_SECRET`. I did not print, copy or transmit the values. |
| CSP allows `'unsafe-inline'` scripts | P2 | Inline `onclick` handlers throughout the HTML; removing needs a frontend refactor. |
| Dev mode makes every local process an admin | P2 | By design for local demos; never enable on shared machines. `.env.example` still defaults to `CIF_DEV_MODE=1`. |
| No account lockout / password reset | P3 | Rate limit (10 auth attempts/min/IP) is the only brute-force control. |
| Demo repositories can be modified by any signed-in user | P3 | Documented; restore with `/api/reseed`. |
| In-memory rate limiter | P3 | Resets on restart; per-process only. |
| `/api/file-context` reveals whether a private repo is registered | P3 | "not added" vs "access denied". |
