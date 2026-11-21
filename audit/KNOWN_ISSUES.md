# Known Issues — Verified Findings

Audit date: 2026-11-21 · Branch: `audit-and-fixes` · Baseline commit: `a2a1839`

Every finding below was **reproduced** (live HTTP request, browser run, or script) unless
marked *(code review)*.

## Status summary (end of audit)
| Status | IDs |
|---|---|
| **Fixed + regression-tested** | SEC-01..08, SEC-10..12, APP-01, APP-02, INT-01..04, DB-01, DB-02, FE-01, ALG-01..03, ALG-05, AUD-01, TOOL-01, TOOL-02, P3-01, P3-02 |
| Fixed by documentation (behaviour kept on purpose) | SEC-09 (demo repos writable by signed-in users) |
| Partially fixed | ARCH-01 (fabrication removed; static preview keeps simulated review buttons), ARCH-02 (login logic moved out of `server.py`; `api.py` still large), EVAL-02 (CIs reported in `audit/`; old docs not rewritten), DOC-01 |
| Open | ARCH-03 (import cycle), EVAL-01 (precision labels keyed to DB file hash), ALG-04 (conflict vocabulary), FE-02 (three frontend copies — needs your decision), P3-03, P3-04, P3-05, job-runner graph edges (new, P2), `demo_sample_repo` broken submodule (new, P1 — needs your decision) |

Findings added during the fix phase: INT-04 / ALG-05 (local ingest invented metadata; three
different extractors), test-isolation bug (a test wrote to the real `whybench.db`), drift UI
showed an empty decision title, guard-rule endpoints reported success for unknown rules,
dashboard ingest mangled local paths, rate limit too low for normal dashboard use.

Severity: **P0** critical security / data-loss / integrity · **P1** major functionality or
reliability · **P2** moderate · **P3** minor.

---

## P0 — Critical

### SEC-01 · Password-less login lets anyone become any user
- **Where:** `server.py` lines 352–390 (`POST /auth/login`, `/auth/register`, `/api/auth/*`)
- **Problem:** The endpoint accepts only a `username`. If that user exists (including a user
  who signed in with GitHub OAuth) a session for them is issued; otherwise a user is created.
  There is no password, no proof of identity.
- **Reproduce:** `curl -X POST :8080/auth/login -H 'Content-Type: application/json' -d '{"username":"nagarwal00"}'`
- **Expected:** credentials verified, or the route disabled in favour of GitHub OAuth.
- **Actual:** `200 OK`, `Set-Cookie: cif_session=…`, "Successfully signed in as nagarwal00".
- **Fix:** Disable username-only login unless an explicit local-demo flag is set *and* the
  request is from loopback; never allow it to log into an account that has a GitHub identity.
  Real authentication is GitHub OAuth (already implemented correctly in `backend/auth/github_login.py`).

### SEC-02 · Dev mode + missing CSRF check ⇒ any website can wipe the database
- **Where:** `backend/security.py` `is_dev_mode()` / `authenticate_caller()`; `server.py` lines 293–301
- **Problem:** With `CIF_DEV_MODE=1` (set in the shipped `.env`), *every* loopback request is
  treated as admin with no credentials. The CSRF Origin check only runs for cookie-authenticated
  requests, and bodies are parsed as JSON regardless of `Content-Type`. A malicious page can
  therefore send a "simple" `text/plain` POST (no CORS preflight) to `127.0.0.1:8080`.
  The required "confirmation" is just the DB filename, which `/api/diagnostics` discloses publicly.
- **Reproduce:** with dev mode on:
  `curl -X POST :8092/api/clear-db -H 'Origin: https://evil.example' -H 'Content-Type: text/plain' -d '{"confirm":"context_intelligence.db"}'`
- **Actual:** `"status":"success"`; events 9→0, decisions 7→0, guard_rules 10→0.
- **Fix:** Reject every state-changing request whose `Origin` (or `Referer`) is present and not
  same-origin, regardless of auth type; require `Content-Type: application/json` on JSON APIs.

### SEC-03 · Cross-repository IDOR (read **and** write)
- **Where:** `backend/auth/repo_access.py` `resolve_repo_for_request()` (lines 197–205) and every
  handler that acts on an object ID: `/api/explain`, `/api/evidence`, `/api/review-action`,
  `/api/guard-rules/approve|disable`, `/api/findings/feedback`.
- **Problem:** Authorization is decided from the `repo` parameter **first**; the handler then
  loads/mutates the object named by `decision_id` / `target_id` / `rule_id` / `finding_id`,
  which can belong to a different (private) repository.
- **Reproduce:** planted private decision `dec_secret_01` in repo `victim/private-repo`:
  - `GET /api/evidence?decision_id=dec_secret_01` → 403 (correct)
  - `GET /api/evidence?repo=acme-eng/thermal-control-system&decision_id=dec_secret_01` →
    **200, title leaked, anonymously**
  - `POST /api/review-action {"repo":"acme-eng/thermal-control-system","target_id":"dec_secret_01","action":"reopen",…}`
    as an unrelated user → **success; state changed to `reopened`**
- **Fix:** Resolve the repository from the object ID when one is supplied, and reject the
  request if an explicit `repo` disagrees with the object's real repository.

### SEC-12 · List endpoints without `repo` return every repository's data
- **Where:** `backend/api.py` handlers for `/api/decisions`, `/api/timeline`, `/api/graph`,
  `/api/decision-history` (and `/api/artifacts`).
- **Problem:** With no `repo` parameter, authorization is checked against the *demo* repository
  (`resolve_repo_for_request` default), but the handler then queries **all** rows.
- **Reproduce:** anonymous `GET /api/decisions` → response contains `victim/private-repo` rows
  (also `/api/timeline`, `/api/graph`, `/api/decision-history`).
- **Fix:** When no repo is given, restrict results to the caller's accessible repositories
  (the pattern already used by `/api/review-queue` and `/api/stats`).

### INT-01 · Frontend fabricates "grounded" evidence and silently replaces the backend
- **Where:** `web/app.js` `apiFetch()` (≈ lines 2669–2730) and `clientMockApi()` (≈ 2790–3400)
- **Problem:** (a) On **any** 404/405/5xx or timeout from the real server, `apiFetch` switches the
  whole session to an in-browser mock engine. (b) The mock "ingest" invents commits with fake SHAs
  (`c1a001f01234567890abcdef…`) for unknown repos and canned histories for "breathwise",
  "context-engine" and "hello-world", then derives decisions from them. The UI shows success.
- **Why P0:** It contradicts the project's central claim (*every decision is grounded in real
  evidence*). An examiner who disconnects the network or triggers a 500 sees invented history.
- **Fix:** Live mode must never fall back to mock data. Show an explicit error instead. Static
  (GitHub Pages) mode may only show the pre-built snapshot, clearly labelled, and must never
  synthesize commits.

### APP-01 · Every HTTP `DELETE` crashes (undefined function)
- **Where:** `server.py` line 473 — `enforce_csrf_for_cookie` is called but defined nowhere.
- **Reproduce:** `curl -i -X DELETE :8091/api/repos/1` → empty reply; server log shows `NameError`.
- **Impact:** "Delete repository" in the UI cannot work. Tests did not catch it because they
  call `APIHandler` directly and never exercise `server.py`'s `do_DELETE`.
- **Fix:** Implement the CSRF check; add an HTTP-level test.

---

## P1 — Major

| ID | Where | Problem (verified) | Fix |
|---|---|---|---|
| SEC-04 | `server.py` 206–225 | `GET /auth/demo/login` always enabled; logs the caller in as `demo-developer` and redirects to an **unvalidated `next`** → `Location: https://evil.example/phish` (open redirect + login CSRF). | Validate `next` with `validate_next_path`; enable only in explicit local demo mode. |
| SEC-05 | `server.py` 82–94 | Rate-limit key is derived from whatever Bearer/cookie string the client sends. Rotating fake tokens gives a fresh bucket each time (verified: 5/5 requests allowed after the IP was already limited). | Key by IP unless the token maps to a *valid* session. |
| SEC-06 | `server.py` 63 and 568 | `check_bind_safety` defined twice; the second (print-only) overrides the first, so binding `0.0.0.0` without `CIF_ADMIN_TOKEN` is allowed. | Remove the duplicate; keep the enforcing version. |
| SEC-07 | `backend/api.py` 255–278 | `GET /api/github-commits` and `/api/github-tree` are **public**, spend the server's `GITHUB_TOKEN`, and pass an unvalidated `repo` into the GitHub API path. | Require sign-in, validate `owner/repo` format strictly. |
| SEC-08 | `Dockerfile` | `COPY . /app` with no `.dockerignore`: the image would contain `.env` (GitHub OAuth client secret, session secret) and the user/session databases. | Add `.dockerignore`. |
| SEC-09 | `backend/auth/repo_access.py` 79–82 | Docstring says demo repos deny writes to non-admins, but code grants `repo_review` on demo repos to any signed-in user (and sign-in is password-less, SEC-01). | Make the demo write policy explicit and match the docstring. |
| SEC-10 | `backend/api.py` 1871 | `POST /api/jobs/<id>/cancel` — any signed-in user can cancel anyone's ingestion job. | Check job ownership. *(code review)* |
| INT-02 | `backend/ingestion/live_github.py` 363–442; `api.py` 263 | Backend substitutes a hard-coded commit list for any repo named "*breathwise*" when GitHub fails — despite the comment "Never synthesize commits". | Remove; surface the real GitHub error. |
| INT-03 | `web/app.js` 14–41, 2795 | `safeUrl()` rewrites **any** URL containing certain 7-char strings (or "breathwise-innovation-hackathon") to commits in the team's repo; `localStorage` state rewrites SHAs. Citation links are not what the evidence says. | `safeUrl` must only validate the scheme. |
| DB-01 | `backend/db.py` schema | Evidence invariant is enforced only in Python. A raw insert of an `accepted` decision with no evidence succeeds; deleting an event cascades away an accepted decision's only evidence and leaves it `accepted`. | Migration 008: triggers blocking (a) removal of the last evidence row of a grounded decision, (b) moving a decision into a grounded state without evidence; plus an integrity-check view. |
| DB-02 | `live_github.py` 703 `clear_database()` | Wipes **all** repositories for all users. Triggered by `/api/clear-db` and by `ingest-repo` with `clear_existing`. | Admin-only and documented as global; ingest's `clear_existing` should purge only the target repo. |
| APP-02 | `server.py` do_GET/do_POST/do_DELETE | No top-level exception handler: any bug (e.g. `"max_commits":"abc"`) returns an **empty reply** instead of a JSON 500/400. | Wrap dispatch; return `{"status":"error","error_code":"INTERNAL_ERROR","request_id":…}`. |
| FE-01 | `web/login.html`, `dashboard.html`, `index.html`, `landing.js`, `app.js` | "Static mode" is decided by `port !== '8080'` (5 copies). On any other port or behind HTTPS the login page loops (62 `/api/me` calls in 2.5 s → 429) and the dashboard shows canned data. | One detection rule: static only when the build marks it (`window.CIF_STATIC_BUILD`) or on `file:`/`github.io`. |
| ALG-01 | `backend/engine/extractor.py` 63–88, 200–225 | Over-broad keyword triggers (`implement`, `support`, `enable`, `feat:`…), hard-coded confidence 0.90, always `auto_confirmed`. Verified: *"feat: change login button color to blue"* → accepted architectural decision. | Require architectural signal (decision phrasing or architectural vocabulary), lower default confidence, route weak extractions to review. |
| ALG-02 | `extractor.py` 163–170 | Any PR review comment containing "rejects" becomes a **rejected** decision. Verified: "LGTM. The validator correctly rejects empty strings." → rejected decision titled "looks good". | Require rejection *of a proposal* (e.g. "we reject", "rejected because", "not viable"), skip approval comments. |
| AUD-01 | `api.py` review-action / findings feedback | Audit trail stores a role (`"repo_review"`) as the actor, not the user's login. The IDOR in SEC-03 left no trace of who did it. | Record `user.login` from the authenticated session. |
| ARCH-01 | `web/app.js` | A complete second "engine" (mock ingest, decisions, review actions) lives in the presentation tier — business logic duplicated outside Tier 2. | Remove fabricating paths; static snapshot becomes read-only. |

## P2 — Moderate

| ID | Where | Problem | Fix |
|---|---|---|---|
| SEC-11 | `api.py` 218–252 | `/api/diagnostics` is public and discloses the absolute DB path and user/session counts. | Public response: status only; details for admin. |
| ARCH-02 | `server.py`, `backend/api.py` | `server.py` (HTTP layer) contains raw SQL and login business logic; `api.py` is a 2,442-line class depending on 24 modules. | Move auth logic into `backend/auth/`; split later. |
| ARCH-03 | `backend/db.py` ↔ `engine/lifecycle.py` | Circular import: data layer imports business logic. | Document; break later (lazy import is already used). |
| TOOL-01 | `tools/validate_whybench.py` | Freeze hash was recorded on a Windows CRLF checkout; on Linux/CI the (unchanged) file fails validation. **Content verified identical** after newline normalisation. | Hash newline-normalised bytes. |
| TOOL-02 | `tools/check_js.py` | Naive brace counter reports "depth 1" on valid JS (template literals). `node --check` passes all 19 JS files. | Use `node --check` when available. |
| EVAL-01 | `backend/evaluation/benchmark.py` | Precision is "not measured" because labels are keyed to the SQLite **file** hash, which differs on every rebuild. | Key labels to a content hash of decisions. |
| EVAL-02 | docs | Headline (reproduced exactly): strict recall **80.8 % (21/26)**, state accuracy 100 % (21/21), refusal accuracy **64.4 % (29/45)**. N=26 is small (Wilson 95 % CI ≈ 62–92 %). Several docs still quote pilot/self-test "100 %" figures. | Report CIs; label self-tests as such. |
| ALG-03 | `ingestion/adr_adapter.py` 64–71 | ADR status uses substring tests in order accept→reject→supersede: "Not accepted" ⇒ accepted; "Superseded (previously accepted)" ⇒ accepted. | Check negation and supersession first. |
| ALG-04 | `engine/conflict_pairs.json` | Only 7 generic pairs; 2 "demo" pairs tuned to the seed repos; `rest` matches ordinary English. | Document limits; use `rest api`/`restful`. |
| FE-02 | `web/`, `docs/`, `new_frontend/` | Three copies of the frontend (identical except `static_data.js`). Edits must be made 3×. `web/` is authoritative (served by `server.py`); `docs/` is the Pages build output. | Keep `web/` as source, generate `docs/`; mark `new_frontend/` as obsolete. |
| DOC-01 | repo root | ~40 overlapping report files with contradictory figures (352 vs 368 tests, "100 %" claims). | Consolidate under `audit/`; annotate superseded reports. |

## P3 — Minor

| ID | Where | Problem |
|---|---|---|
| P3-01 | `server.py` 125 & 544 | `end_headers` defined twice; the no-cache version is dead code. |
| P3-02 | `server.py` 326–330 | Malformed JSON on `/auth/*` silently becomes `{}`. |
| P3-03 | `web/app.js` | 401/403 shown with blocking `alert()`. |
| P3-04 | `api.py` `/api/file-context` | Distinguishes "not added" from "access denied", leaking existence of private repos. |
| P3-05 | repo | `__pycache__/`, `scratch/`, `dist/`, `logs/` shipped in the zip (git-ignored, so not in Git). |

## Verified **not** to be problems
- No secrets in Git history (searched all 150 commits for the `.env` values); `.env` is git-ignored.
- No tokens, session cookies or OAuth codes in `logs/`.
- GitHub OAuth: hashed single-use state with 10-min TTL, validated `next`, hashed session tokens.
- Webhook: HMAC-SHA256 with constant-time compare; fails closed without a secret.
- SQL: parameterised queries throughout the reviewed paths.
- Frozen WhyBench and hold-out datasets: content unchanged (holdout hashes match exactly; WhyBench matches after newline normalisation).
- Unit tests do not mutate the databases (checksums identical before/after).
