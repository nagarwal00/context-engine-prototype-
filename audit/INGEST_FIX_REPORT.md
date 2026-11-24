# Fix Report — `/api/ingest-repo` (2026-11-24)

## 1. Root cause
Two separate things appeared together in the browser:
1. **`Endpoint not found: GET /api/ingest-repo`** — the route exists and the dashboard calls it
   correctly with **POST**. Opening the URL in the address bar (or clicking `api/ingest-repo:1` in the
   console) sends **GET**. The router answered 404 for any method mismatch.
2. **`400 Bad Request` on the dashboard's POST** — the request was well-formed. The backend turned every
   ingestion failure into HTTP 400: GitHub rate limit, repository not found, private repository,
   network failure, empty repository. Most likely cause on a normal PC: GitHub's limit of
   **60 unauthenticated requests per hour** — one ingestion could make ~50 requests (file tree fetched
   twice with up to 3 branch guesses each, 15 commit details, 25 file downloads, 5 ADRs), so the second
   attempt within an hour was refused. The real reason was in the response body; the status hid it.

Found while tracing (same function): the GitHub path still invented data — a decision titled
"Initial Architecture for {repo}" when nothing was found, files `src/main.py`/`README.md` when the tree
was unavailable, the first repository file attached to commits without file details, the first 5 files
attached to every issue/PR, ADR author `lead-architect` dated 2026-01-15 — and used a substring keyword
extractor instead of the benchmarked `DecisionExtractor`. A mid-run rate limit silently produced
incomplete data reported as complete. The dashboard printed invented progress steps on a timer.

## 2. Files changed
| File | Change |
|---|---|
| `backend/ingestion/live_github.py` | `GitHubIngestError` (status + error code), rate-limit detection from GitHub headers, request budget with *partial* warnings, tree fetched once from the default branch, ADR metadata from git history, `DecisionExtractor`, no invented data, optional `CIF_GITHUB_API_BASE` |
| `backend/api.py` | `/api/ingest-repo` returns real status codes + `error_code`; router returns **405** (not 404) for a wrong method |
| `server.py` | 405 responses carry `Allow:` header |
| `web/app.js`, `docs/app.js` | Ingest dialog: honest elapsed-time progress, exact error with HTTP status/code, rate-limit message, warnings; banner accepts a message |
| `tests/test_ingest_repo_endpoint.py` | 14 tests (12 fail on the old code) |
| `.env.example` | documents `CIF_GITHUB_API_BASE` |

## 3. Endpoint contract
`POST /api/ingest-repo`, `Content-Type: application/json`, admin (or dev mode on localhost).
```json
{"repo": "owner/name | https://github.com/owner/name | local folder path",
 "token": null, "clear_existing": false, "max_commits": 25, "max_issues": 15}
```
| Situation | HTTP | `error_code` |
|---|---|---|
| Success | 200 | — (`data.partial`, `data.warnings`, `data.github_requests`) |
| Missing / invalid input, bad local path | 400 | `INVALID_REQUEST`, `INVALID_REPOSITORY`, `LOCAL_PATH_NOT_FOUND` |
| Token rejected | 400 | `INVALID_GITHUB_TOKEN` |
| GitHub refused access | 403 | `GITHUB_ACCESS_DENIED` |
| Not found / private without token | 404 | `REPOSITORY_NOT_FOUND` |
| Wrong HTTP method | 405 | `METHOD_NOT_ALLOWED` (+ `Allow: POST`) |
| Empty repository | 422 | `EMPTY_REPOSITORY` |
| GitHub rate limit | 429 | `GITHUB_RATE_LIMIT` — "GitHub API rate limit exceeded. Please try again later." (+ `retry_after` ≤ 3600) |
| GitHub server error / TLS | 502 | `GITHUB_ERROR`, `GITHUB_TLS_ERROR` |
| GitHub unreachable | 503 | `GITHUB_UNREACHABLE` |
| Unexpected processing failure | 500 | `INGESTION_FAILED` (details only in server log) |
| Backend down (browser) | — | `BACKEND_UNREACHABLE` |

## 4. Verification
- Unit/integration: real pipeline against a local server that answers like the GitHub REST API
  (JSON, status codes, rate-limit headers). Success, idempotent re-ingest, partial budget, and all
  error cases. **This simulates GitHub; it does not prove github.com itself works.**
- Browser (Playwright, real `server.py`): valid repo with double-click → exactly 1 POST, success, repo
  listed; 404, 429 (banner, button locked), invalid/empty input blocked before sending, backend down →
  clear message; 0 GET requests, 0 JS errors, 0 server tracebacks.
- Real repository data: local-folder ingestion of a git clone of `npryce/adr-tools` (earlier audit).
- Full suite: 449 run, OK, 2 skipped; 0 unclosed SQLite connections.

## 5. Not verifiable here
This environment's network proxy blocks GitHub's REST API, so ingestion from **github.com** must be
confirmed on your PC (steps in the chat reply / below):
```powershell
$env:CIF_DEV_MODE="1"; python server.py
```
Dashboard → Workspace → Connect & Ingest → `https://github.com/octocat/Hello-World` → expect
"Context Extraction Complete!". With a Personal Access Token in the dialog the 60/hour limit becomes 5,000/hour.
