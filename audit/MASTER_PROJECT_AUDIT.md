# CIF — Master Project Audit

Date: 2026-11-21 · Auditor role: senior engineer / QA / security reviewer
Scope: full repository from `SE_project.zip`, Git HEAD `a2a1839`, work on branch `audit-and-fixes`.

## 1. Verdict in one paragraph
The project is **much more real than a typical student project**: it starts from a clean clone,
368 automated tests pass, the GitHub OAuth flow and webhook verification are built correctly,
and the headline benchmark numbers reproduce exactly. However, it had **five critical defects**
an examiner could find in minutes: anyone could log in as anyone (no password), any website
could wipe the database when dev mode is on, a user could read or change another user's
private repository data by adding `repo=<demo repo>` to a request, the frontend silently
invented commit history when the backend failed, and every `DELETE` request crashed.
None of these were caught because the tests call the business layer directly and never go
through the HTTP server.

## 2. How the system actually works (beginner version)
Think of CIF as three stacked boxes:

1. **Presentation tier — `web/`**: HTML pages and one big JavaScript file (`app.js`). It draws
   the dashboard and calls the backend with `fetch('/api/...')`.
2. **Application tier — `server.py` + `backend/`**: `server.py` receives each HTTP request,
   checks rate limits, CSRF and permissions, then hands it to `backend/api.py`, which calls the
   "engine" modules (extraction, conflict detection, drift detection, explanations).
3. **Data tier — SQLite via `backend/db.py`**: every table (events, decisions, evidence links,
   entities, edges, users, sessions…) and all SQL live here.

The *intelligence* is in `backend/engine/`: it reads **events** (commits, PRs, issues, ADRs),
decides which ones represent **architectural decisions**, links each decision to the events that
prove it (**evidence**), connects decisions to code (**entities**) in a **graph**, tracks each
decision's **lifecycle** (proposed → accepted → superseded…), and checks new code diffs against
accepted decisions (**drift**). The central promise: *no decision without evidence.*

## 3. Ten most important problems (all reproduced)
| # | ID | Sev | Problem |
|---|---|---|---|
| 1 | SEC-01 | P0 | Password-less login — become any user by typing their name |
| 2 | SEC-02 | P0 | Dev mode: any website can wipe the DB via a cross-site POST |
| 3 | SEC-03 | P0 | Cross-repo IDOR: read/modify private decisions via `repo=<demo>` |
| 4 | INT-01 | P0 | Frontend fabricates commits/decisions when the backend errors |
| 5 | APP-01 | P0 | Every `DELETE` crashes (`NameError`) |
| 6 | SEC-04 | P1 | Demo login: open redirect + forced login |
| 7 | INT-02/03 | P1 | Hard-coded "breathwise" commits; citation URLs rewritten to the team's repo |
| 8 | DB-01 | P1 | Evidence invariant not enforced by the database |
| 9 | FE-01 | P1 | Frontend only works live on port 8080 |
| 10 | ALG-01/02 | P1 | Extractor turns UI tweaks and "LGTM" comments into architectural decisions |

Full list with reproduction steps: [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) (5 P0, 18 P1, 11 P2, 5 P3).

## 4. Correction plan (priority order)
1. **Security P0s**: disable password-less login outside explicit local demo; same-origin check on
   every state-changing request; object-based repo resolution (fix IDOR); fix `DELETE`.
2. **Integrity**: remove all fabricated-data paths (backend + frontend), stop URL rewriting,
   never fall back to mock data in live mode.
3. **Reliability**: global JSON error handler, rate-limit key fix, bind-safety, `.dockerignore`.
4. **Data layer**: migration 008 with triggers enforcing the evidence invariant.
5. **Frontend**: single live/static detection, honest error states.
6. **Algorithms**: tighten extractor triggers and rejection detection; fix ADR status parsing.
7. **Tooling/docs**: CRLF-safe freeze hash, `node --check`, consolidated reports.

## 5. How fixes are verified
- **HTTP-level regression tests** (new `tests/test_http_security.py`) that start the real
  `server.py` on a random port and send real requests — the layer the old tests skipped.
- Re-run full suite + `run_demo.py` + benchmark reproduction after every group of fixes.
- Playwright browser run of the main workflow (login → dashboard → decision → evidence →
  drift check → logout), checking console errors and network calls.
- DB checksum comparison to prove tests do not touch real databases.

## 6. Safety measures taken
- Original DBs copied with SHA-256 to `../db_backups_original/` before anything ran.
- All work on a local branch `audit-and-fixes`; nothing pushed.
- Benchmark/tools executed in a scratch clone. (One accidental run of `run_holdout.py` in the
  real tree regenerated a byte-identical file — no change.)
- Frozen datasets were not modified.
