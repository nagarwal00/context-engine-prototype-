# ANTIGRAVITY HANDOFF v3 — GitHub Login, Automatic Repo Ingestion, Chrome Extension (then VS Code)

> **This is an ADDENDUM to `ANTIGRAVITY_HANDOFF_V2.md`.** It adds Phases 7, 8 and 9. All V2 rules (§1), the reporting format (§14) and the pitfalls (§13) still apply unless this file explicitly changes them (see §1 here).
> **Work one step at a time, in order.** After each step run its **Verify** command and send the §14 report from V2. Never skip steps or mark one done unless every acceptance criterion is met.

---

## 0. What we are building

Today a user must hand the system a GitHub token to add a repository. The new product flow is:

1. The user opens the CIF web page (or the Chrome extension) and clicks **Sign in with GitHub**.
2. They install the **CIF GitHub App** on the repositories they choose (GitHub shows its own consent screen).
3. They click **Add repository**. CIF **automatically fetches the whole repository history** (commits, pull requests, issues, comments, reviews, docs/ADRs, code snapshot) in a background job with visible progress. **No token is ever typed or pasted.**
4. In Chrome, while browsing GitHub, the **extension** shows decision history, drift warnings and rejected-idea warnings directly on pull-request, issue and file pages.
5. Later, a **VS Code extension** reuses the same backend API (Phase 9).

The backend stays the single source of truth. Extensions are thin clients.

### Prerequisites (do not start Phase 7 until these V2 items are done)

| V2 step | Why it is required first |
|---|---|
| 1.1 SSL fix, 1.2 API authorization, 1.3 XSS fix | Login and extensions expose the API publicly |
| 2.0 migration framework | This addendum adds many tables |
| 5.1 privacy sanitizer | Private-repo content must be redacted **before** it is stored |
| 6.1 GitHub App docs/webhook | The same GitHub App is reused for login, ingestion and webhooks |

If any prerequisite is incomplete, report `blocked on V2 <step>` and finish that step first.

---

## 1. Rule changes and additions (override V2 only where stated)

**R1 — Optional dependency exception (changes V2 rule 6 in one place only).** The backend stays standard-library only, **except** one optional package, `cryptography`, used for exactly two features: (a) signing the GitHub App JSON Web Token (RS256) to mint **installation tokens** (webhook PR comments, background re-sync), and (b) encrypting stored GitHub refresh tokens at rest. Import it inside `try/except ImportError`. Without it: login, repo adding, ingestion with the signed-in user's token, and all read features still work; the two gated features report `unavailable: install cryptography`.

**R2 — Identity replaces pasted tokens.** The V2 `reviewer` token role is replaced by GitHub identity (§Phase 7). The `admin` token (`CIF_ADMIN_TOKEN`) stays for operations only (`clear-db`, `reseed`, `purge`). The UI "Access token" field from V2 Step 1.2 moves into a collapsed **Admin** section.

**R3 — Per-repository isolation is mandatory.** A signed-in user may only read or change data of repositories they can access on GitHub. Private-repo data must **never** be returned to anyone else. Deny by default.

**R4 — GitHub tokens are secrets.** Never log them, never put them in URLs, never send them to the browser or extension, never store them unencrypted on disk. The browser/extension only ever holds a **CIF session token**, which grants access to CIF only.

**R5 — No remote code in the extension.** No `eval`, no inline scripts, no remotely hosted JS, all untrusted text rendered with `textContent`.

**R6 — Honesty about coverage.** If ingestion hits a cap (commits, PRs, size), the UI must say "partial: X of Y" and store a `partial` flag. Never label a capped import "whole repository".

**R7 — Human-required tasks (§12 here) cannot be faked.** Registering the GitHub App, creating secrets, choosing hosting, and loading the extension in a real browser are human actions.

---

## 2. Key design decisions (already made — do not re-decide)

| Decision | Choice | Reason |
|---|---|---|
| GitHub integration type | **GitHub App** (not a plain OAuth App) | Per-repository install consent, fine-grained permissions, multiple callback URLs, expiring user tokens, same App also serves webhooks |
| Who talks to GitHub | **Backend only** | The backend holds the client secret; browser/extension never sees GitHub tokens |
| Login flow | **Authorization-code web flow** handled by the backend | Standard; works for web page and (via redirect) for the extension |
| Extension login | `chrome.identity.launchWebAuthFlow` against the backend, returning a **one-time code** exchanged for a CIF session token | Keeps tokens out of URLs and out of GitHub's reach |
| Fetching the repo | **GitHub REST API** (no `git clone`) | No git binary needed; no token inside clone URLs/logs |
| Background work | In-process worker threads + `ingest_jobs` table | Stdlib-only; resumable |
| Extension UI placement | **Floating Shadow-DOM widget** (not injected into GitHub's DOM tree) | GitHub's markup changes often; this is robust |
| Chrome first, VS Code later | Yes | Faster to build and demo |
| GitHub Pages demo | Stays a **static simulation**; it cannot do login | Login needs a live HTTPS backend |

GitHub App user-to-server tokens expire after 8 hours and come with a refresh token (GitHub's documented default for new apps), so design for refresh.

---

# PHASE 7 — Backend: GitHub login, repo access, automatic ingestion

### Step 7.1 — Register the GitHub App (HUMAN) and add configuration
- **Human (H-A):** create a GitHub App with: *Homepage URL* = `CIF_BASE_URL`; *Callback URLs* = `${CIF_BASE_URL}/auth/github/callback` (plus `http://127.0.0.1:8080/auth/github/callback` for development); *Setup URL* = `${CIF_BASE_URL}/repos?installed=1`; **Expire user authorization tokens = on**; *Webhook* URL = `${CIF_BASE_URL}/api/webhook/github` with a secret; **Repository permissions:** Contents → Read, Metadata → Read, Issues → Read, Pull requests → Read & write (write only for PR comments); **Account permissions:** none (do not request e-mail); **Subscribe to events:** Pull request, Push, Issues, Issue comment, Pull request review, Installation, Installation repositories. Generate and download a private key (only needed for Rule R1 features).
- **Do (code):** create `backend/config.py` reading these environment variables once, validating them, and exposing safe getters (never printing secrets): `CIF_BASE_URL`, `CIF_SESSION_SECRET`, `GITHUB_APP_SLUG`, `GITHUB_APP_ID`, `GITHUB_APP_CLIENT_ID`, `GITHUB_APP_CLIENT_SECRET`, `GITHUB_APP_PRIVATE_KEY_PATH` (optional), `CIF_TOKEN_ENC_KEY` (optional), `CIF_EXTENSION_IDS` (comma-separated), `CIF_MAX_COMMITS` (default 5000), `CIF_MAX_PRS` (default 1500), `CIF_MAX_ISSUES` (default 1500), `CIF_MAX_TARBALL_MB` (default 100). Add `.env.example` with placeholders only and `GET /api/auth-config` (public) returning only `{ "login_enabled": bool, "app_slug": "..." }`.
- **Accept:** with no GitHub variables set, the server starts and login is reported disabled (the rest of the app keeps working). No secret appears in logs.
- **Verify:** `tests/test_config.py` (missing vars → disabled; secrets never in `repr`/log output).

### Step 7.2 — Tables for users, sessions, repos and jobs (migration)
- **Do:** numbered migration adding (inspect existing schema first; reuse names where they exist):
  - `users(user_id INTEGER PRIMARY KEY, github_id INTEGER UNIQUE NOT NULL, login TEXT NOT NULL, avatar_url TEXT, created_at TEXT, last_login_at TEXT)`
  - `sessions(session_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, client TEXT NOT NULL, created_at TEXT, expires_at TEXT, last_seen_at TEXT)` — store only the SHA-256 of the session token.
  - `oauth_states(state_hash TEXT PRIMARY KEY, created_at TEXT, next_path TEXT, client TEXT, ext_id TEXT)` — single use, 10-minute lifetime.
  - `ext_codes(code_hash TEXT PRIMARY KEY, session_hash TEXT, created_at TEXT)` — single use, 60-second lifetime.
  - `repos(repo_full_name TEXT PRIMARY KEY, github_repo_id INTEGER, visibility TEXT NOT NULL, added_by_user_id INTEGER, added_at TEXT, last_synced_at TEXT, partial INTEGER DEFAULT 0, stats_json TEXT)` where `visibility` ∈ `demo | public | private`.
  - `repo_access(user_id INTEGER, repo_full_name TEXT, level TEXT, verified_at TEXT, PRIMARY KEY (user_id, repo_full_name))`
  - `ingest_jobs(job_id TEXT PRIMARY KEY, repo_full_name TEXT, requested_by INTEGER, status TEXT, phase TEXT, progress_json TEXT, error_code TEXT, cursor_json TEXT, created_at TEXT, started_at TEXT, finished_at TEXT)` with `status` ∈ `queued | running | needs_relogin | failed | partial | done | cancelled`.
  - `user_tokens(user_id INTEGER PRIMARY KEY, token_cipher BLOB, refresh_cipher BLOB, expires_at TEXT)` — **only written if R1 encryption is available** (see 7.3).
- **Repo attribution (important):** make sure **every** existing data table (`events, entities, decisions, edges, claims, …`) can be tied to a repository (`repo_full_name` column, indexed, backfilled; seeded demo repos become `visibility='demo'`). Add the column additively and verify with `PRAGMA foreign_key_check`.
- **Accept:** migration works on a fresh DB and on a **copy** of the real DB without data loss.
- **Verify:** `tests/test_migration_auth_tables.py`.

### Step 7.3 — Login (web flow), sessions and token handling
- **Files:** new `backend/auth/github_login.py`, `backend/auth/sessions.py`; routes in `api.py`/`server.py`.
- **Routes (all outside the V2 token table; default-deny still applies to everything else):**
  - `GET /auth/github/login?next=/repos` (also `client=extension&ext_id=<id>`)
  - `GET /auth/github/callback?code=...&state=...`
  - `POST /auth/extension/exchange` body `{ "code": "..." }`
  - `POST /auth/logout`
  - `GET /api/me` → `{ "login", "avatar_url", "csrf" }` or 401
- **Do:**
  1. `login`: create a random `state` (32 bytes, urlsafe), store only its hash in `oauth_states` with `next_path` (validated: must start with `/` and not `//`; reject anything else), `client`, `ext_id` (must be in `CIF_EXTENSION_IDS` for `client=extension`). Redirect (302) to `https://github.com/login/oauth/authorize` with `client_id`, `redirect_uri=${CIF_BASE_URL}/auth/github/callback`, `state`. A GitHub App takes its permissions from the App settings; do not add scope parameters. **PKCE:** check GitHub's *current* documentation for GitHub Apps; if `code_challenge`/`code_verifier` is supported add it; `state` is mandatory regardless.
  2. `callback`: fail closed on any problem. Look up and **delete** the state (single use, ≤ 10 minutes old). POST to `https://github.com/login/oauth/access_token` with `Accept: application/json` using `urllib` and the secure SSL context from V2 Step 1.1 (never log the body). Handle GitHub's `error`/`error_description` responses. You receive an access token, a refresh token and `expires_in`. Call `GET https://api.github.com/user` for `id`, `login`, `avatar_url`; upsert `users`.
  3. **Create a CIF session:** random 32-byte token; store only its SHA-256 in `sessions` (7-day expiry, 24-hour idle timeout, sliding `last_seen_at`).
     - **Web client:** set cookie `cif_session` with `HttpOnly; SameSite=Lax; Path=/; Max-Age=...` and `Secure` whenever `CIF_BASE_URL` is `https`. Then redirect to the validated `next_path`.
     - **Extension client:** create a one-time code (random, hash stored in `ext_codes`, 60-second life) bound to the session and redirect to `https://<ext_id>.chromiumapp.org/cb?code=<one-time-code>`. `POST /auth/extension/exchange` swaps the code for the session token **once** and deletes it. Never put the session token itself in a URL.
  4. **GitHub tokens:** if R1 encryption is available and `CIF_TOKEN_ENC_KEY` is set, store the encrypted user token and refresh token in `user_tokens`. Otherwise keep them **only in memory** (a dict keyed by `user_id`, guarded by a lock) so jobs that outlive the token fail with `needs_relogin` and the user simply signs in again. Refresh automatically on a 401 or near expiry via `POST https://github.com/login/oauth/access_token` with `grant_type=refresh_token`; on refresh failure mark `needs_relogin`.
  5. **CSRF:** requests authenticated by **cookie** that change state (POST/PUT/DELETE) must carry an `Origin` header equal to `CIF_BASE_URL` (else 403). Requests authenticated by `Authorization: Bearer <session token>` (extension) are exempt.
  6. `logout` deletes the session row and clears the cookie; `/api/me` updates `last_seen_at`.
- **Accept:** a full login works against the real GitHub App; a reused or expired `state` is rejected; `next=//evil.example` is rejected; an unlisted `ext_id` is rejected; a one-time code cannot be used twice or after 60 seconds.
- **Verify:** `tests/test_auth_flow.py` using a **mocked** HTTP layer for GitHub (no network): happy path, wrong/missing/reused/expired state, bad `next`, bad `ext_id`, code reuse, code expiry, cookie flags, CSRF Origin check, session expiry. Then a **manual** live login (H-B).

### Step 7.4 — Identity-based authorization and repo scoping
- **Do:**
  1. Extend the V2 route table: each route declares a requirement: `public` (health, auth-config, static UI), `user` (any signed-in user), `repo_read`, `repo_review`, or `admin` (admin token). Default deny remains.
  2. `authorize_repo(user, repo_full_name, need)`:
     - `demo` repos: readable by everyone (anonymous included) so the professor demo works; no writes.
     - Otherwise require a row in `repo_access` verified within the TTL (**15 minutes** for private repos, 1 hour for public). If stale, re-verify with `GET /repos/{owner}/{repo}` using the user's token; 200 → grant, 404/403 → deny and delete the row; no usable token → deny with `needs_relogin`.
     - `repo_review` (approve rules, confirm/reject decisions, finding feedback): requires verified GitHub `permissions.push` (or higher) if the `permissions` object is present in the response **for this token type — verify this against the live API**; if it is absent, fall back to: the user who added the repo, plus users that user adds to a small `repo_reviewers` table (create it, with `POST /api/repos/{r}/reviewers` owner-only).
  3. **Every** data endpoint takes a required `repo` parameter (or resolves it from an entity/decision id) and calls `authorize_repo`. List endpoints (`/api/repos`) return only repositories the caller may access. Cross-repo joins must filter by repo **inside SQL**, not after fetching.
  4. Keep the V2 admin token for `clear-db`, `reseed`, `purge`, and global maintenance.
  5. Remove the V2 `reviewer` token path (R2) and update tests.
- **Accept:** user A cannot read user B's private repo data by any endpoint, id guess, or parameter tampering; anonymous users see only demo repos.
- **Verify:** `tests/test_repo_isolation.py` — build two users and a private repo for each; for **every GET and POST route** assert cross-user access returns 403/404 and leaks no data; test ID-guessing on decisions/events/evidence.

### Step 7.5 — Add-repository flow (installation discovery)
- **Do:**
  - `GET /api/github/repos` (user): using the user's token call `GET /user/installations`, then `GET /user/installations/{installation_id}/repositories` (paginate) and return `{ "repos": [ { "full_name", "private", "added": bool, "status" } ], "install_url": "https://github.com/apps/<slug>/installations/new" }`.
  - `POST /api/repos` body `{ "repo": "owner/name" }` (user): verify access (7.4) and that the App is installed on it; create/update `repos`; create an `ingest_jobs` row; return `{ "job_id" }`. If the App is not installed on that repo, return `409 { "error": "app_not_installed", "install_url": ... }`.
  - `GET /api/repos/status?repo=owner/name` (user): `{ "added": bool, "partial": bool, "last_synced_at", "active_job": ... }`.
  - **No tokens in any request body.** If a caller sends a field named like `token`/`access_token`, reject with 400.
- **Accept:** a user can see exactly the repos they have installed the App on and add one with a single call.
- **Verify:** `tests/test_add_repo.py` with mocked GitHub responses (not installed → 409 with `install_url`; installed → job created; duplicate add → reuses/refreshes).

### Step 7.6 — Automatic whole-repo ingestion job
- **Files:** new `backend/ingestion/job_runner.py`, `backend/ingestion/github_client.py` (hardened client reused by `live_github.py`).
- **Hardened client rules (must all hold):**
  1. Uses the secure SSL context (V2 Step 1.1); header `Authorization: Bearer <token>`; `Accept: application/vnd.github+json`; `X-GitHub-Api-Version` pinned in one constant.
  2. **Redirects:** disable automatic redirects for authenticated requests (Python's `urllib` forwards the `Authorization` header on redirect). Follow redirects manually and **strip `Authorization` when the host changes** (e.g. tarball downloads redirect to another GitHub host).
  3. Paginate with `per_page=100` and the `Link` header; never assume page counts.
  4. Respect `X-RateLimit-Remaining`/`X-RateLimit-Reset` and `Retry-After`; on rate-limit or secondary-limit responses back off (exponential, capped) and continue; update progress with "waiting for rate limit".
  5. Use `ETag`/`If-None-Match` for re-syncs; a 304 counts as "unchanged".
  6. Timeouts (30 s), retries (3) with backoff on 5xx; **never** retry TLS errors with weaker settings.
  7. Tokens only in memory; error messages scrubbed with the V2 sanitizer patterns.
- **Job phases (record `phase` and `progress_json` after every page; make each phase resumable using `cursor_json`):**
  1. `metadata` — repo info, default branch, visibility, languages.
  2. `docs` — README, `docs/`, ADR/decision folders (`docs/adr`, `adr`, `docs/decisions`, `decisions`, `rfcs`), `CONTRIBUTING`, `CHANGELOG`. Use the git trees API (`recursive=1`; if the response says `truncated`, walk subtrees) and fetch blobs ≤ 1 MB.
  3. `code` — snapshot of the default branch via the tarball endpoint, limited by `CIF_MAX_TARBALL_MB`; if larger, take only source files up to a total cap and set `partial=1`. Feed the existing function-level (AST) entity extraction; for languages without an extractor create file-level entities.
  4. `commits` — paginate up to `CIF_MAX_COMMITS`; fetch per-commit file lists **only** for commits that pass the decision-candidate filter (keeps API calls bounded).
  5. `pull_requests` — list up to `CIF_MAX_PRS`; for each: reviews, review comments, issue comments; file lists for candidate PRs.
  6. `issues` — up to `CIF_MAX_ISSUES`, plus comments; skip PR entries returned by the issues endpoint.
  7. `analyze` — run the existing pipeline (sanitizer → events → entities → extraction → evidence assessment → graph → review queue).
  8. `finalize` — update `repos.stats_json`, `last_synced_at`, `partial`.
- **Cross-cutting rules:**
  - **Sanitizer first:** every item passes the V2 Step 5.1 sanitizer **before** it is written or cached. Never persist raw API responses.
  - **Idempotent:** deterministic IDs and upserts; re-running a job never duplicates data.
  - **Concurrency:** at most 2 jobs run at once; at most 1 per repository (a second request attaches to the running job).
  - **Restarts:** on startup mark leftover `running` jobs as `failed(restart)`; a new request resumes from `cursor_json`.
  - **Tokens:** if the token is missing/expired and cannot be refreshed, set `needs_relogin` (not `failed`) and keep the cursor.
  - **Cancel:** `POST /api/jobs/{id}/cancel` stops at the next page boundary.
  - **Progress:** `GET /api/jobs/{id}` → `{ status, phase, progress: { phase_done, counts, capped: [...], waiting_for_rate_limit }, error_code }` with no sensitive details.
  - **Coverage honesty (R6):** when any cap triggers, status becomes `partial` and the numbers shown are "ingested X of Y".
- **Accept:** adding a medium public repository completes with real counts; killing the server mid-job and restarting resumes from the cursor without duplicates; a capped import is labelled partial.
- **Verify:** `tests/test_job_runner.py` with a fake GitHub server (a local `http.server` fixture serving canned paginated JSON, rate-limit headers, a redirect that changes host, and a 304) covering: pagination, rate limiting, redirect header stripping, resume after interruption, idempotent re-run, cap → `partial`, `needs_relogin`, cancellation, sanitizer applied (a canned comment containing a synthetic secret built at runtime must not reach the DB).

### Step 7.7 — Webhook live-sync (incremental updates)
- **Do:** extend the V2 webhook (`/api/webhook/github`, HMAC-validated, token-exempt) for `push`, `pull_request`, `issues`, `issue_comment`, `pull_request_review`, `installation`, `installation_repositories`. Each event triggers a small **incremental** job for that repo (fetch only the changed item(s)). Installation events create/remove access links; `installation` `deleted` and repositories removed → mark the repo `removed` and stop syncing. Fetching with installation tokens requires R1 (JWT); without R1, the webhook records the event and a **user-initiated "Re-sync"** button performs the update with the user's token.
- **Accept:** a new PR comment appears in CIF after the webhook; removing the App from a repo stops syncing.
- **Verify:** `tests/test_webhook_sync.py` with signed fixtures; R1-gated paths skipped with a clear message when `cryptography` is absent.

### Step 7.8 — Consent, deletion and retention
- **Do:** Before the first add, the UI shows what CIF reads (commits, PRs, issues, comments, docs, code), where it is stored, that secrets are redacted before storage, and how to delete. Add `DELETE /api/repos/{owner}/{repo}` (the person who added it, or an admin) that deletes **all** rows for the repo (events, entities, decisions, edges, claims, history, jobs, access rows, cached files) and reports row counts. Update `PRIVACY.md` accordingly.
- **Accept:** after deletion, a raw-byte scan of the DB file finds none of the repo's text (use the V2 Step 5.1 scan helper).
- **Verify:** `tests/test_repo_delete.py`.

### Step 7.9 — Web login page and repository manager
- **Do:** `web/login.html` (a single clear **Sign in with GitHub** button, short privacy note, link to the demo repos), a **Repositories** screen (list from `/api/github/repos`, **Add** buttons, a progress bar driven by `/api/jobs/{id}` polling every 2 seconds, status chips: `partial`, `needs re-login`, `failed` with a readable reason, **Re-sync**, **Delete data**), a repo selector in the header of the existing dashboard, and a user menu (avatar, login, **Sign out**). All dynamic text goes through the V2 `esc()` helper. The static GitHub Pages build shows "Login is available on the live server" instead of the button.
- **Accept:** a first-time user goes login → install App → add repo → watch progress → open the dashboard, entering no tokens.
- **Verify:** manual walk-through with screenshots saved to `docs/integration_evidence/login/` (H-B).

### Phase 7 exit check
Tests pass; isolation test green; a real user logged in, added a repository, and the whole history was fetched with visible progress and honest coverage. Tag `phase7-done`.

---

# PHASE 8 — Chrome extension (Manifest V3)

### Step 8.0 — API contract for extensions (backend)
Add or confirm exactly these routes (all under `/api`, Bearer-authenticated, repo-scoped):

| Route | Purpose |
|---|---|
| `GET /api/me` | Who is signed in |
| `GET /api/repos/status?repo=owner/name` | Is it added, partial, active job |
| `POST /api/repos` | Add the repo (7.5) |
| `GET /api/jobs/{id}` | Ingestion progress |
| `GET /api/pr-analysis?repo=&number=` | Drift + rejected-idea findings and related decisions for a PR (fetches the diff with the user's token; **cache by head SHA**) |
| `GET /api/file-context?repo=&path=&ref=` | Decisions, rejected alternatives and staleness affecting a file/entity |
| `POST /api/findings/feedback` | confirm / dismiss / reopen (V2 Step 3.6) |

Responses must contain **only** JSON, stable field names, and a `schema_version`. Return `{ "status": "not_added" }` or `{ "status": "needs_relogin" }` as normal JSON states, not stack traces.
- **Accept/Verify:** `tests/test_extension_api.py` (contract shape, isolation, caching by head SHA, no GitHub token ever present in any response).

### Step 8.1 — Project skeleton and manifest
- **Layout:**
```text
extension/
  manifest.json
  src/service_worker.js        (all network + auth; no DOM)
  src/content/github.js        (page detection + floating widget)
  src/content/widget.css
  src/popup/popup.html, popup.js
  src/options/options.html, options.js
  src/lib/api.js, src/lib/github_url.js, src/lib/messages.js, src/lib/render.js
  icons/ (16, 32, 48, 128)
  tests/ (node --test, pure functions only)
  README.md
```
- **`manifest.json` rules:** `manifest_version: 3`; `permissions`: only `identity`, `storage`, `alarms`; `host_permissions`: only `https://github.com/*` and the CIF backend origin(s) (`http://127.0.0.1:8080/*` for development and the production origin); **no** `<all_urls>`, no `tabs`, no `scripting` unless a step proves it is needed; `content_scripts` matching only `https://github.com/*/*` with `run_at: document_idle`; `background.service_worker`; `action` with the popup; a `key` field so the extension ID is stable in development (H-C records the ID in `CIF_EXTENSION_IDS`). Default CSP is kept (do not weaken it).
- **Accept:** loads as an unpacked extension in Chrome without warnings.
- **Verify:** load it (H-C); `chrome://extensions` shows no errors.

### Step 8.2 — Authentication in the extension
- **Do:** in the service worker: `signIn()` calls `chrome.identity.launchWebAuthFlow({ url: BACKEND + "/auth/github/login?client=extension&ext_id=" + chrome.runtime.id, interactive: true })`, reads `code` from the returned `https://<id>.chromiumapp.org/cb?code=...`, POSTs it to `/auth/extension/exchange`, and stores `{ token, expires_at }` in `chrome.storage.local` (never in page-accessible storage). `signOut()` calls `/auth/logout` and clears storage. Every API call adds `Authorization: Bearer <token>`; on 401 the extension shows "Sign in again". The token is never sent to content scripts — content scripts ask the service worker for data via messages.
- **Accept:** one click signs in through GitHub; signing out removes the token; an expired token leads to a clear sign-in prompt.
- **Verify:** manual (H-C) plus unit tests of the token-expiry logic (`node --test`).

### Step 8.3 — Popup (status and quick actions)
- **Do:** states: **Signed out** (button), **Signed in, not on GitHub** (list of the user's added repos + link to the dashboard), **On a GitHub repo page** (`parseGithubUrl(location)` → owner/repo): *Not added* → **Add this repository** (if the App is not installed show **Install CIF on GitHub**), *Importing* → progress bar (poll via `chrome.alarms` every 5 s because the service worker may be suspended; never `setInterval`), *Ready* → **Open dashboard** and counts, *Partial* → badge "partial import". All text via `textContent`.
- **Accept:** a user can add and monitor a repository from the popup with no token entry.
- **Verify:** manual E2E on a small public repo with the App installed.

### Step 8.4 — Pull-request panel (headline feature)
- **Do:** on `https://github.com/<owner>/<repo>/pull/<n>[/...]` the content script asks the service worker for `/api/pr-analysis`, then shows a **floating Shadow-DOM widget** (bottom-right button with a count badge; expands to a side drawer). Contents:
  - **Rejected-idea warnings** (advisory): matched decision, original discussion link(s), recorded rejection reason, current state, changed-circumstances hints.
  - **Drift findings** (`potential_violation`): file, line, offending line, rule, linked decision and evidence passages, `signal_strength` shown as "heuristic".
  - **Related decisions** touching the changed files.
  - **Detector status:** "Check incomplete" banner when `status != complete` (V2 Step 1.4).
  - **Buttons:** Confirm, Dismiss (with reason), Reopen decision → `POST /api/findings/feedback`.
  - Never says "blocked"; wording is "possible", "please review".
- **Accept:** on a PR that re-adds a previously rejected library the widget shows the original URL and reason; on a clean PR it shows "No findings" (and not an error).
- **Verify:** manual on two prepared PRs (one violating, one clean) + screenshots in `docs/integration_evidence/extension/`; unit tests for `render.js` helpers with hostile strings (`<img onerror>` must appear as text).

### Step 8.5 — File and issue context
- **Do:** on `/blob/<ref>/<path>` pages the widget lists decisions affecting that file (and the function under the cursor line if the URL has `#L<n>` and an AST entity exists), rejected alternatives, and `stale`/`under_review` badges. On `/issues/<n>` pages show related decisions and past rejected ideas matching the issue text. Same widget, same security rules.
- **Accept:** opening a file with recorded decisions shows them within 2 seconds on a warm cache.
- **Verify:** manual + `test_extension_api.py` cases for `file-context`.

### Step 8.6 — Robustness against GitHub's single-page navigation
- **Do:** GitHub swaps pages without a full reload. In the content script: listen for `turbo:render`, `turbo:load`, `popstate`, and fall back to a debounced `MutationObserver` on `document.body`; compute the page "kind" and key (`owner/repo`, `pull/n`, `blob/ref/path`) with `parseGithubUrl`; **idempotent injection** (a single host element marked with a `data-cif` attribute; remove/update on navigation; cancel in-flight requests when the key changes). Do not depend on GitHub's CSS class names.
- **Accept:** navigating between pull requests without reload updates the widget exactly once, with no duplicates and no stale data.
- **Verify:** manual navigation script (PR → PR → files tab → repo home) plus `node --test` for `parseGithubUrl` with ≥ 15 URL variants (including `/files`, `/commits`, `/pull/12#discussion_r1`, enterprise-like lookalike hosts that must be **rejected**).

### Step 8.7 — Security hardening for the extension
- **Do:** (1) the service worker accepts messages only from its own content scripts/popup (`sender.id === chrome.runtime.id`) and validates message shape and an allow-list of message types; (2) API base URL is fixed in `config.js`, overridable only on the options page to an **allow-listed** origin; (3) no `innerHTML`/`outerHTML`/`insertAdjacentHTML` anywhere (add a lint test that greps for them); (4) all links built from backend data pass `safeUrl` (http/https only) and use `rel="noopener noreferrer"`; (5) no logging of tokens or response bodies; (6) a privacy section in the extension README: what is sent (repo name, PR number, file path), to whom, and that nothing leaves to third parties.
- **Accept:** lint test passes; a hostile backend response cannot execute script in the extension or page.
- **Verify:** `extension/tests/test_security.js` (lint + render with hostile payloads).

### Step 8.8 — Packaging and documentation
- **Do:** `tools/build_extension.py` creates `dist/cif-extension.zip` (excluding tests and docs) and prints the manifest version; `extension/README.md` covers install-unpacked steps, how to set `CIF_BASE_URL`/`CIF_EXTENSION_IDS`, the sign-in flow, and a manual QA checklist. A public store listing is **out of scope** unless the team asks (it requires a privacy policy and review).
- **Accept:** a teammate installs from the README alone and completes sign-in → add repo → see a PR panel.
- **Verify:** that walk-through (H-C) with a screen recording or screenshots.

### Phase 8 exit check
Extension works end-to-end on a real repo; hostile-text tests pass; no GitHub token reaches the browser. Tag `phase8-done`.

---

# PHASE 9 — VS Code extension (start only after Phase 8 is done and demonstrated)

Outline only — do **not** build until the team confirms.
- **Reuse** the Step 8.0 API. **Auth:** open the backend login URL with `vscode.env.openExternal`, register a `vscode.window.registerUriHandler`, receive `vscode://<publisher>.<name>/auth?code=...` (one-time code, same exchange endpoint, new `client=vscode` handled and allow-listed like `ext_id`), store the session token in `context.secrets` (VS Code SecretStorage). Do not use VS Code's built-in GitHub session for backend access: that token belongs to a different app.
- **Features:** CodeLens or hover on functions showing decision + rejected alternatives (via `/api/file-context`), a Decisions tree view for the open workspace repo (detected from `git remote`), diagnostics for guard-rule violations on save (advisory severity), and a command **"CIF: Add this repository"**.
- **Rules:** same security rules as Phase 8; no network calls to GitHub from the extension; message and response validation; unit tests with `@vscode/test-electron` only if the team accepts that dev dependency (extension code may use Node tooling; the backend stays Python/stdlib).

---

## 12. Human tasks for this addendum (never fake them)

| # | Task | Needed for |
|---|---|---|
| H-A | Register the GitHub App (settings in Step 7.1), create the client secret, webhook secret and private key | 7.1 onward |
| H-B | Run a real login → install App → add repository → dashboard walk-through; save screenshots | 7.3, 7.9 |
| H-C | Load the unpacked extension in Chrome, record the extension ID into `CIF_EXTENSION_IDS`, run the sign-in/PR-panel walk-through | Phase 8 |
| H-D | Choose and set up public HTTPS hosting for the backend (needed for GitHub callbacks and webhooks beyond localhost); set the environment variables there | 7.1, 7.7 |
| H-E | Prepare two demo PRs on a test repo (one reintroducing a rejected approach, one clean) | 8.4 |
| H-F | Confirm whether the VS Code extension should be started | Phase 9 |

If a human task is missing when needed, report `blocked on H-<letter>` and continue with the next independent step.

---

## 13. Pitfalls specific to this addendum

- **Redirect header leak:** `urllib` forwards `Authorization` on redirects. Disable auto-redirect and strip the header when the host changes (Step 7.6).
- **Open redirect:** validate `next` and the extension redirect target against strict allow-lists.
- **State and codes are single-use:** delete on first use; compare hashes in constant time.
- **8-hour user tokens:** always handle refresh and `needs_relogin`; do not treat it as a generic failure.
- **GitHub trees can be truncated:** check the `truncated` flag and walk subtrees.
- **Issues endpoint includes PRs:** filter them out to avoid double counting.
- **Rate limits:** a large repo can take minutes; show progress and never block the web server thread (jobs run in worker threads with their own DB connections).
- **MV3 service workers are suspended:** keep no state in globals; use `chrome.storage` and `chrome.alarms`.
- **Extension ID changes break login:** keep the manifest `key` and the `CIF_EXTENSION_IDS` list in sync.
- **GitHub changes its markup:** use the floating widget, not DOM insertion into GitHub's layout.
- **Isolation bugs hide in joins:** filter by repository inside every SQL query and test with two users.
- **Static demo ≠ live product:** the GitHub Pages build cannot log in; label it a simulation (V2 Step 6.2).
- **Private data on a shared server:** the sanitizer, the deletion endpoint and the consent text are part of the feature, not extras.

---

## 15. Definition of done (addendum)

- [ ] A new user signs in with GitHub, installs the App, adds a repository with one click, and the whole history is fetched automatically with live progress — **no token is ever typed**.
- [ ] Cap/partial coverage is shown honestly; jobs are resumable and idempotent; rate limits are respected.
- [ ] Per-repository isolation is proven by a two-user test across every route; anonymous users see only demo repos.
- [ ] GitHub tokens never reach the browser, extension, logs, URLs or unencrypted disk; sessions are hashed at rest; CSRF and open-redirect protections tested.
- [ ] The Chrome extension signs in, adds repos, shows rejected-idea and drift findings on PR pages and decision context on file/issue pages, survives GitHub's SPA navigation, and passes the hostile-text and no-`innerHTML` tests.
- [ ] User data can be deleted completely, verified by a raw-byte scan.
- [ ] Docs (`PRIVACY.md`, `GITHUB_APP_SETUP.md`, `extension/README.md`, `DEPLOYMENT.md`) match what was actually built and tested; anything verified only with mocks says so.
- [ ] VS Code extension: not started unless H-F confirms.

---

## 16. Start here

1. Confirm the V2 prerequisites in §0. Report any that are not finished.
2. Do **Step 7.1** (the human registers the GitHub App; you add the configuration code and tests).
3. Continue in order. Do not start Phase 8 until the Phase 7 exit check passes. Do not start Phase 9 without H-F.
