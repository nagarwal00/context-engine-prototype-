# ANTIGRAVITY HANDOFF v2 — Context Intelligence Framework (CIF)

> **This file replaces `ANTIGRAVITY_HANDOFF.md` (v1).** v1 phases may already be partly done. Do **not** redo them blindly: Phase 0 below re-baselines the project and tells you what is really done.
>
> **Read the whole file before changing code.** Work **one step at a time**, in order. After each step run its **Verify** command, send the report in §14, then continue. Never batch steps, never skip steps, never mark a step done unless every acceptance criterion is met.

---

## 0. Mission and context

CIF reconstructs **why** a software project looks the way it does: decision → alternatives → evidence → code change → present implementation. It is a 17-week university software-engineering capstone (course UCS503, four-person team).

The project is already a working prototype (Python standard-library backend, SQLite, a 9-surface web UI, ingestion adapters, a temporal graph, a drift detector, guard rules, a WhyBench evaluation harness). An external review of the current state found that it **passes its own checks** (31/31 unit tests, 21/21 demo checks) but still has:

1. **Security and reliability defects** (§3, Phase 1).
2. **Incomplete features**: the decision lifecycle, evidence engine, drift detector, time-travel, onboarding are only *partial* (§2).
3. **Missing features**: staleness, bus-factor map, privacy-first ingestion, Slack (§2).
4. **A weak evaluation**: on the reported WhyBench test split, CIF's decision recall (30.8%) is below the plain keyword baseline (64.9%) (§Phase 4).

The professor's standing challenge is: *"AI agents and READMEs can already do this."* The project's answer must be **measured, reproducible evidence** plus features that a README or a one-off chat cannot provide: lifecycle history, evidence grading, rejected-idea memory, and drift checks tied to decisions.

---

## 1. Non-negotiable rules

Breaking any rule makes the work wrong, even if the code runs.

1. **Verify before you fix.** Several findings below cite line numbers and behaviours from an external review. Line numbers may have moved. For every finding, first reproduce it (Phase 0), then fix it. If a finding cannot be reproduced, record `NOT REPRODUCED` with proof and do not change code for it.
2. **Never hard-code a metric, score, confidence, percentage, latency, or baseline result.** Every number shown anywhere (API, UI, README, slides) must be computed from data, or shown as `not measured` / `uncalibrated`.
3. **Never tune on a test split that has been seen.** The first WhyBench test split (`test_v1`) was already run and its results were read. It is **burned**: report it as the pre-improvement result and never use it to guide changes. Create a **new frozen test split `test_v2`** (Step 4.9) before improving recall. Tune only on `dev`.
4. **Keep the evidence invariant** (redefined in Step 2.1): a decision claiming `tested`, `accepted`, `rejected` or `superseded` must have at least one evidence event. Never weaken it.
5. **Do not make the existing checks weaker.** `python -m unittest discover -s tests -v` and `python run_demo.py` must pass after every step. You may change a check only to make it stricter or to match an intentional, documented behaviour change.
6. **Standard library only** for backend, tools and tests (Python 3.11 or 3.12). Any extra package is *optional*, must be imported inside `try/except ImportError`, and the system must still work without it.
7. **Windows-safe.** The author runs Windows (`C:\Users\HP\Desktop\SE_project`). Use `pathlib`/`os.path`, open files with `encoding="utf-8"`, never assume a Unix shell inside code, avoid non-cp1252 characters in console output.
8. **No secrets in the repo, logs, DB, or error messages.** Tokens only via environment variables: `GITHUB_TOKEN`, `CIF_LLM_API_KEY`, `CIF_WEBHOOK_SECRET`, `CIF_ADMIN_TOKEN`, `CIF_REVIEWER_TOKEN`.
9. **Back up before any destructive or schema-changing action.** Copy `context_intelligence.db` (and `whybench.db`) to `backups/` first. Migrations must be tested on a **copy** of the real DB before running on the real one.
10. **Smallest change that satisfies the step.** No unrelated refactors, renames, or reformatting.
11. **Tests never touch the real DB and never use the network.** Use `tempfile` and mocks.
12. **If blocked**, write the problem to `BLOCKERS.md` (what you tried, exact error, what you need) and continue with the next *independent* step. Do not guess around a blocker.
13. **Human-required tasks (§12) cannot be faked.** Never fabricate labels, verification flags, screenshots, live-test results or Copilot results. Leave them empty/`not measured` and list them in your report.

---

## 2. Status map (from the external review) and where each item is handled

Legend: **I** = implemented, **P** = partial, **M** = missing. "Handled in" gives the step IDs below.

| Feature | Status | What is needed | Handled in |
|---|---|---|---|
| Decision Lifecycle Engine | P | Transition rules, history, reopening, review workflow, audit view, reconcile state definitions | 2.1–2.5, 2.7 |
| Evidence and Confidence Engine | P | Claim-level evidence, independence, contradiction handling, source trace, abstention, no fake probabilities | 3.1–3.3 |
| Decision–Code Drift Detector | P | Per-decision machine-checkable constraints instead of hard-coded scenarios, negatives, feedback | 3.4, 3.6 |
| Temporal & Counterfactual Explorer | P | "As of" queries, documented-alternative explanations, no speculation | 2.6 |
| Adaptive Developer Onboarding | P | Personalised paths by role/module/files from decision evidence | 5.4 |
| Temporal Context Graph | I | Temporal consistency, traversal and historical-query correctness | 1.5, 2.6 |
| Decision half-life / staleness | M | Assumptions, triggers, freshness status, review reminders | 5.2 |
| Time-travel questions | P | Historical snapshots, not just a timeline | 2.6 |
| Bus-factor map | M | Knowledge concentration per module/decision/contributor | 5.3 |
| Privacy-first ingestion | M | Redaction before persistence, safe logging, local-only mode | 5.1 |
| Rejected-idea guard | P | Match proposals to rejected approaches, retrieve original evidence and reason | 3.5 |
| Evidence-graded decisions | P | Independent corroboration vs repeated copies | 3.1–3.2 |
| Measured benchmark | P | Recall, label validation, fair baselines, reproducible results | Phase 4 |
| Real GitHub integration | P | Install/config, end-to-end webhook validation, CI deployment test | 6.1 |
| Slack integration | M | Only if kept in scope | 5.5 (decision required) |

Security/reliability findings (P0 = fix first):

| ID | Finding | Handled in |
|---|---|---|
| P0-a | SSL verification can be disabled (unverified-context fallback in `backend/ingestion/live_github.py`) | 1.1 |
| P0-b | No authorization on destructive/write endpoints; wildcard CORS (`server.py`, `backend/api.py`) | 1.2 |
| P0-c | Repository text inserted with `innerHTML` (XSS) (`web/app.js`, copy in `docs/app.js`) | 1.3 |
| P1-a | Rejected-idea/drift detection depends on hard-coded keywords and PID/Redis scenarios | 3.4, 3.5 |
| P1-b | Guard-rule failures swallowed silently in `drift_detector.py` | 1.4 |
| P1-c | `TemporalGraph.add_edge()` defaults `valid_from` to a fixed date | 1.5 |
| P1-d | Supersession matching links unrelated decisions by title-word overlap | 1.6 |

Other correctness problems: hard-coded drift confidences (3.4); `state_history` empty in the shipped DB (2.3); benchmark may let one system decision satisfy several labels (4.1); "evidence-link validity" only checks the URL format (4.1, 3.3); confidence and evidence quality conflated (3.2); demo vs deployed product unclear (6.2); DB/Git hygiene (6.3); test gaps (6.7).

---

## 3. Environment checklist (run once)

```text
cd C:\Users\HP\Desktop\SE_project        (or wherever the project is unzipped)
python --version                         # 3.11 or 3.12
python -m unittest discover -s tests -v  # expected: all pass (reported 31/31)
python run_demo.py                       # expected: all pass (reported 21/21)
python server.py                         # starts on 127.0.0.1:8080; then Ctrl+C
python tools/ci_check.py                 # expected: usage error (it needs --base and --head); this is NOT a bug
```

If anything fails, fix the environment first or record it in `BLOCKERS.md`.

---

# PHASES

Order: **0 → 1 → 2 → 3 → 4 → 5 → 6**. Within a phase, keep the order of steps.

---

## PHASE 0 — Re-baseline and audit (no feature work)

### Step 0.1 — Snapshot
- **Do:** Ensure the project is a git repo with a clean commit named `chore: baseline before v2`. Copy `context_intelligence.db` and `whybench.db` to `backups/` (ignored by git). Record `git rev-parse HEAD`.
- **Accept:** backups exist; working tree clean.
- **Verify:** `git status`; both `.db` backups listed.

### Step 0.2 — Audit every finding
- **Do:** Create `STATUS_AUDIT.md`. For **every row** in the two tables in §2 and every item in "Other correctness problems", write: the file and real line numbers you found, a one-line **reproduction** (command, tiny script, or a failing test), and a verdict: `CONFIRMED`, `NOT REPRODUCED`, or `ALREADY FIXED`. Also record real DB counts (`decisions`, `events`, `edges`, `state_history`) for both DBs. Examples of what to reproduce:
  - P0-a: `grep -n "unverified\|CERT_NONE\|check_hostname" backend/ingestion/live_github.py`.
  - P0-b: start the server, `POST /api/clear-db` against a **temp copy** of the DB with no credentials; record the response.
  - P0-c: list every `innerHTML` with an interpolated value in `web/app.js`.
  - P1-b: find the `except Exception:` / `pass` block around guard-rule execution in `drift_detector.py`.
  - P1-c: grep for `2026-01-01T00:00:00Z` in `backend/engine/graph.py` and in stored edges.
  - P1-d: write a 2-decision example with similar titles and show whether they get linked.
  - Benchmark overcounting: show whether one system decision can satisfy two ground-truth items.
- **Accept:** every row has a verdict with evidence. No code changed except `STATUS_AUDIT.md`.
- **Verify:** read the file back; commit it.

### Step 0.3 — Repo hygiene quick fix
- **Do:** Make sure `.gitignore` covers `*.db`, `*.db-journal`, `backups/`, `__pycache__/`, `*.pyc`, `.env`. If `*.db` are tracked, run `git rm --cached` on them (do **not** delete the files). Do not touch the nested git repo inside `demo_sample_repo/` yet (Step 6.3 handles it).
- **Accept:** `git ls-files | findstr /i ".db .pyc"` returns nothing.
- **Verify:** tests and demo still pass.

---

## PHASE 1 — Fix reliability and security (do this first)

### Step 1.1 — Remove the SSL verification fallback (P0-a)
- **Files:** `backend/ingestion/live_github.py` (and any other file that creates an SSL context: `grep -rn "ssl\." backend tools server.py`).
- **Do:**
  1. Delete every unverified context path: `ssl._create_unverified_context`, `CERT_NONE`, `check_hostname = False`, any "retry without verification" logic.
  2. Always use `ssl.create_default_context()`. If env var `CIF_CA_BUNDLE` points to a file, pass it as `cafile=`.
  3. On `ssl.SSLCertVerificationError` (or a `URLError` whose `reason` is one), raise a new `GitHubTLSError` with a clear message: update the OS root certificates or set `CIF_CA_BUNDLE`. The message must never contain the token or request headers.
  4. Do not retry a failed TLS handshake with weaker settings.
- **Accept:** a certificate failure produces `GitHubTLSError` exactly once (no second attempt); the token never appears in the message.
- **Verify:** `tests/test_tls_safety.py`: (a) mock `urllib.request.urlopen` to raise `ssl.SSLCertVerificationError`, assert `GitHubTLSError` and that `urlopen` was called once; (b) a source scan test asserting the banned strings above appear nowhere in `backend/` or `tools/`.

### Step 1.2 — Authorization boundary for the API (P0-b)
- **Files:** `server.py`, `backend/api.py`, new `backend/security.py`.
- **Roles:**
  - `viewer` — no token; allowed: GET endpoints only.
  - `reviewer` — `Authorization: Bearer <CIF_REVIEWER_TOKEN>`; allowed: `/api/review-action`, guard-rule approve/disable, finding feedback.
  - `admin` — `Authorization: Bearer <CIF_ADMIN_TOKEN>`; allowed: everything, including `/api/clear-db`, `/api/reseed`, `/api/ingest-repo`, purge endpoints.
  - `/api/webhook/github` is exempt from tokens because it has its own HMAC check (`X-Hub-Signature-256`, `CIF_WEBHOOK_SECRET`).
- **Do:**
  1. Implement `authorize(headers, required_role) -> (ok, status_code, message)` using `hmac.compare_digest`. If the needed env var is **unset**, that role is disabled (requests get 403), except in dev mode: `CIF_DEV_MODE=1` **and** the client address is `127.0.0.1`.
  2. Build one table in `api.py` mapping every route → required role. A route not in the table is rejected (default deny).
  3. `/api/clear-db` and `/api/reseed` additionally require a body `{"confirm": "<exact db filename>"}`.
  4. CORS: remove the wildcard `Access-Control-Allow-Origin: *`. Default = same-origin only (send no CORS header). Optional allowlist from `CIF_CORS_ORIGINS` (comma-separated); echo the origin only if it is in the list.
  5. Limit request bodies to 1 MB; reject invalid JSON with 400; return JSON errors, never stack traces.
  6. Default bind stays `127.0.0.1`. Binding elsewhere requires `CIF_BIND` **and** at least an admin token set; otherwise refuse to start.
  7. Add `GET /api/auth-status` returning `{ "role_required_for_writes": true, "dev_mode": bool }` so the UI can ask for a token.
  8. UI: add a small "Access token" field (kept in memory, sent as the `Authorization` header on write calls). Show a clear message on 401/403.
- **Accept:** destructive routes fail without a valid token; read routes still work without one; old CORS wildcard is gone.
- **Verify:** `tests/test_api_auth.py` starts the real server on an ephemeral port in a thread against a temp DB, and asserts: no token → 401/403 on every write route; wrong token → 403; correct token → 200; unknown route → denied; oversized body → 413/400; `clear-db` without `confirm` → 400.

### Step 1.3 — Stop HTML injection in the frontend (P0-c)
- **Files:** `web/app.js`, `web/index.html`; then copy to `docs/` (use the generator from Step 6.2 when it exists; until then copy manually and diff).
- **Do:**
  1. Inventory: `grep -n "innerHTML\|insertAdjacentHTML\|outerHTML" web/app.js`. Record the count in the audit.
  2. Add `esc(value)` (escapes `& < > " '`) and `safeUrl(value)` (returns the URL only if its scheme is `http` or `https`, else `#`).
  3. Wrap **every** interpolated dynamic value (titles, rationales, authors, repo names, notes, diff text, error messages, evidence snippets) with `esc(...)`; wrap every `href`/`src` with `safeUrl(esc(...))`.
  4. Replace inline handlers that interpolate data (`onclick="fn('${id}')"`) with `addEventListener` and `data-*` attributes (read via `dataset`).
  5. Prefer `textContent` when no markup is needed.
  6. Add a Content-Security-Policy `<meta>` in `index.html`: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'`. If the UI loads external fonts/scripts, allow only those exact origins and note it.
- **Accept:** a decision whose title is `<img src=x onerror=alert(1)>` and whose rationale contains `"><script>alert(1)</script>` renders as plain text everywhere (timeline, graph labels, explorer, evidence panel, review queue, drift tester, onboarding, metrics) and nothing executes.
- **Verify:** (a) `tests/test_frontend_escape.py` — a static lint that fails if any line assigning `innerHTML` interpolates `${...}` without `esc(`/`safeUrl(` (document that this is a heuristic); (b) manual run: ingest a synthetic event with the payload above into a temp DB, open every UI surface, confirm no alert and correct text. Record the result in `STATUS_AUDIT.md`.

### Step 1.4 — No more silent detector failures (P1-b)
- **Files:** `backend/engine/drift_detector.py`, `backend/api.py`, `tools/ci_check.py`, webhook handler, `web/app.js`.
- **Do:**
  1. Change `analyze_diff_for_drift` to return a report object/dict: `{ "status": "complete" | "incomplete", "findings": [...], "errors": [ { "stage", "rule_id", "error_type", "message" } ] }`. Remove the broad `except Exception: pass`.
  2. Each rule evaluates inside its own `try/except`; on failure append a **sanitised** error (rule id + exception class + short message, no diff content, no params dump) and continue with other rules; mark status `incomplete`.
  3. Log errors with the standard `logging` module (never `print` secrets).
  4. API returns the full report. UI shows a visible warning "Check incomplete: N rule(s) could not run" and distinguishes it from "No violations found".
  5. `tools/ci_check.py` exit codes: `0` = complete and clean, `1` = violations, `2` = incomplete.
  6. Update every caller (`api.py`, webhook, `run_demo.py`, tests).
- **Accept:** a deliberately broken rule (malformed `params_json`) yields `status: "incomplete"` plus an error entry; healthy rules still report.
- **Verify:** `tests/test_drift_errors.py` for: broken rule → incomplete; clean diff + all rules ok → complete with empty findings; CI exit codes 0/1/2.

### Step 1.5 — Correct temporal defaults (P1-c)
- **Files:** `backend/engine/graph.py` and every caller of `add_edge`.
- **Do:**
  1. Remove the fixed default timestamp. `add_edge(..., valid_from)` is **required**; callers pass the real event/decision timestamp.
  2. Validate: ISO-8601 parse; if `valid_to` is set it must be `>= valid_from`, else raise `ValueError`.
  3. Write `tools/repair_edge_validity.py` (**dry-run by default**, `--apply` to write): finds stored edges whose `valid_from` equals the old placeholder and sets it to the earliest relevant timestamp (decision `made_at` or its earliest evidence event). Print a before/after report; back up first.
- **Accept:** no edge can be created without a real start; invalid ranges are rejected; repair tool reports counts.
- **Verify:** `tests/test_graph_temporal.py`: missing `valid_from` raises; `valid_to < valid_from` raises; an edge created from an event at 2025-06-01 has `valid_from` 2025-06-01.

### Step 1.6 — Evidence-based supersession (P1-d)
- **Files:** `backend/engine/reconciliation.py` (`detect_supersessions`), review-queue code in `api.py`.
- **Do:**
  1. Candidate priority: (1) **explicit reference** (decision id, ADR number, `#PR/issue` number, "supersedes ADR-0003"); (2) **shared affected entity** (≥ 1 common entity) **and** the new decision is later in time **and** a replacement cue ("supersedes", "replaces", "instead of", "migrate from"); (3) title-word overlap may be used **only to break ties among candidates that already share an entity**, after removing a stop list of common/generic words (put the list in one constant).
  2. If more than one candidate qualifies, or the only match is word overlap, do **not** auto-link. Create a review-queue item of type `supersession_candidate` listing the candidates and why each matched.
  3. Keep the symmetrical `supersedes`/`superseded_by` fields and edge validity consistent (transition via the lifecycle engine once Phase 2 exists).
- **Accept:** unrelated decisions with similar titles never link; explicit references link; ambiguous cases go to review.
- **Verify:** `tests/test_supersession.py` with: (a) two unrelated decisions sharing a generic word; (b) explicit reference; (c) entity match + cue; (d) two equally plausible candidates → review item, no auto-link.

### Phase 1 exit check
All of: tests + demo pass; no unverified SSL anywhere; write routes protected; XSS payload inert; detector failures visible; no placeholder edge dates; supersession no longer word-overlap-only. Commit tag `phase1-done`.

---

## PHASE 2 — Complete the decision history

### Step 2.0 — Migration framework
- **Files:** new `backend/migrations/`, `backend/db.py`.
- **Do:** Add a `schema_migrations(version INTEGER PRIMARY KEY, name TEXT, applied_at TEXT)` table. Each migration is a numbered Python module with `upgrade(conn)`; the runner applies pending ones in order inside one transaction each, and is called from `Database._init_schema()`. A fresh DB gets all migrations; an existing DB gets only the pending ones. `tools/migrate_db.py --db PATH [--dry-run]` runs it manually.
- **Accept:** running twice is a no-op; a failed migration rolls back and leaves the DB unchanged.
- **Verify:** `tests/test_migrations.py` on a temp DB and on a **copy** of `backups/context_intelligence.pre_v2.db` (skip with a clear message if that file is absent).

### Step 2.1 — Reconcile state definitions (migration 001)
**Problem:** the requested lifecycle uses `tested`, `reopened` (and "uncertain"), but the schema `CHECK` currently allows only `proposed, accepted, rejected, superseded, unresolved`. Also, *lifecycle state* (what the team decided) is different from *evidence quality* (how well it is supported).
- **Do (design — implement exactly):**
  - Lifecycle `state` ∈ `proposed | tested | accepted | rejected | superseded | reopened`.
  - New column `evidence_assessment` ∈ `strong | moderate | weak | insufficient | contradicted` (default `insufficient`). "Uncertain" is **not** a lifecycle state; it is `insufficient`/`contradicted` here.
  - New column `freshness` ∈ `fresh | stale | under_review | revalidated` (default `fresh`) — used in Step 5.2.
  - Legacy `unresolved` → migrated to `state='proposed'`, `evidence_assessment='insufficient'`.
  - **Evidence invariant (new wording):** states `tested`, `accepted`, `rejected`, `superseded` require ≥ 1 evidence event. `proposed` and `reopened` may have none, but then `evidence_assessment` must be `insufficient`.
- **Do (SQLite):** a `CHECK` cannot be altered in place, so rebuild the table inside one transaction: `PRAGMA foreign_keys=OFF; BEGIN; CREATE TABLE decisions_new (...new CHECKs...); INSERT INTO decisions_new SELECT ... (mapping unresolved → proposed); DROP TABLE decisions; ALTER TABLE decisions_new RENAME TO decisions;` recreate every index/trigger/foreign key that referenced the old table; `COMMIT; PRAGMA foreign_keys=ON; PRAGMA foreign_key_check;` (must return no rows). First read the current DDL with `SELECT sql FROM sqlite_master WHERE name='decisions'` and preserve all columns and defaults.
- **Update everywhere:** `models.py` (validation), `db.save_decision`, `api.py`, extractor outputs, `run_demo.py`, tests, UI state badges and filters.
- **Accept:** migration runs on a fresh DB and on a copy of the real DB with zero data loss (row counts equal; `foreign_key_check` empty); no code still references `unresolved` except the migration mapping and a compatibility alias.
- **Verify:** `tests/test_state_model.py` (every allowed state saves; an illegal state is rejected; invariant enforced) plus the migration test on the DB copy.

### Step 2.2 — Lifecycle engine
- **Files:** new `backend/engine/lifecycle.py`.
- **Allowed transitions (data-driven dictionary; do not scatter `if` checks):**

| From | To |
|---|---|
| proposed | tested, accepted, rejected |
| tested | accepted, rejected |
| accepted | superseded, reopened |
| rejected | reopened |
| reopened | tested, accepted, rejected |
| superseded | *(none — terminal)* |

- **Do:** implement `transition(db, decision_id, to_state, actor, reason, at=None, evidence_event_ids=None)`:
  1. Validate against the table; raise `InvalidTransition` otherwise (API maps it to HTTP 409).
  2. Require non-empty `actor` and `reason`.
  3. If `to_state` is one of `tested/accepted/rejected/superseded`, require evidence (existing or supplied).
  4. In **one DB transaction**: update `decisions.state`, insert a `state_history` row (`decision_id, from_state, to_state, changed_at, changed_by, notes` — inspect the real column names in `_init_schema`), and for `superseded` set `superseded_by_decision_id` plus close the edge validity (`valid_to`).
  5. Never allow a silent overwrite: any code that changes state must go through this function.
  6. Creation at ingestion is a special case: record a first history row with `from_state = NULL`.
- **Accept:** invalid transitions are impossible through any path; every change leaves a history row.
- **Verify:** `tests/test_lifecycle.py`: every legal transition passes; every illegal pair (use itertools over all pairs) raises; history rows have actor/reason/time; `superseded` is terminal; `rejected → reopened → accepted` works.

### Step 2.3 — Record history everywhere and backfill
- **Do:**
  1. Find every state mutation: `grep -rn "UPDATE decisions\|\.state *=\|state=" backend server.py tools`. Route all of them through `lifecycle.transition` (review actions, reconciliation, extractor re-runs, supersession).
  2. Write a migration (002) or tool `tools/backfill_state_history.py` that creates one history row per existing decision with `notes="reconstructed from current state at backfill"` and `changed_by="system:backfill"`, using the decision's `made_at`. Mark these rows so the UI can show "reconstructed" rather than "observed".
- **Accept:** on a freshly seeded DB, `SELECT COUNT(*) FROM state_history` ≥ number of decisions, and after a review action the count increases. The previously-empty `state_history` of the shipped DB is populated after migration.
- **Verify:** `tests/test_history_recorded.py` (fresh DB + one review action) and a before/after count printout from the backfill tool on the DB copy.

### Step 2.4 — Review workflow for lifecycle
- **Do:** Extend `/api/review-action` so `confirm/reject/merge/correct` call the lifecycle engine, plus new actions `reopen` and `mark_tested`, each requiring `reason`. Require the `reviewer` role (Step 1.2). Record the reviewer identity (token role + optional display name) as `actor`.
- **Accept:** each action produces a history row with the reason; invalid actions return 409 with a readable message.
- **Verify:** extend `tests/test_api_auth.py` or add `tests/test_review_actions.py`.

### Step 2.5 — Lifecycle UI and audit view
- **Do:** Add `GET /api/decision-history?decision_id=...` returning transitions (who, what, when, why, `reconstructed` flag) and the supersession chain (previous/next decisions). In the Decision Explorer add a "Lifecycle" tab: a vertical timeline of transitions, the supersession chain, and an "Audit log" table (all decisions, filterable by actor/date). All dynamic text goes through `esc()`.
- **Accept:** for a seeded superseded decision the UI shows `proposed → accepted → superseded` with actors and reasons.
- **Verify:** manual walkthrough + an API test for the endpoint.

### Step 2.6 — Historical "as of" queries and counterfactual explorer
- **Files:** `backend/engine/graph.py`, `backend/api.py`, new `backend/engine/as_of.py`, UI.
- **Do:** implement `as_of(db, repo, cutoff)` returning what the team believed at `cutoff`:
  - Decisions with `made_at <= cutoff`, each with its **state as of cutoff** reconstructed from `state_history` (latest row with `changed_at <= cutoff`). Never use the current state.
  - Edges valid at the cutoff: `valid_from <= cutoff` and (`valid_to IS NULL` or `valid_to > cutoff`).
  - Evidence events with `timestamp <= cutoff` only; evidence that appeared later is listed separately as "later evidence".
  - Alternatives already rejected by the cutoff (their rejection evidence dated `<= cutoff`).
  - A "changed afterwards" list: later transitions, supersessions, new decisions on the same entities.
  - Endpoint `GET /api/as-of?repo=...&date=YYYY-MM-DD[&artifact=...]`. UI: a date picker plus text box ("What did the team believe on 2026-03-01, and why?").
- **Counterfactual rules:** show only **documented** alternatives with their recorded rejection reasons. Label this section "Documented alternatives". If an alternative was never tried, state "no recorded outcome — consequences of the untried alternative are unknown." The explanation generator must never write speculative outcomes.
- **Accept:** a query for 1 March never shows a decision made on 15 March as active; a supersession dated 10 March is shown as `accepted` on 5 March and `superseded` on 12 March.
- **Verify:** `tests/test_as_of.py` with fixtures covering: before any decision (empty result), between made_at and supersession, after supersession, evidence appearing after the cutoff, a decision with only reconstructed history (flag it).

### Step 2.7 — Fresh-database lifecycle proof
- **Do:** Write `tools/verify_lifecycle_fresh_db.py`: create a temp DB, seed, ingest a small fixture, run a scripted sequence (create → test → accept → supersede → reopen-attempt-on-superseded must fail), print the audit log, exit non-zero on any deviation.
- **Accept:** script passes on a clean checkout.
- **Verify:** run it; add it to the test suite via `subprocess`.

### Phase 2 exit check
Fresh DB records history; all state changes pass the lifecycle engine; migrations tested on the DB copy; as-of queries correct on boundary dates. Tag `phase2-done`.

---
## PHASE 3 — Strengthen evidence and rejection memory (main novelty)

### Step 3.1 — Claim-level evidence and independence (migration 003)
- **Do:** Add tables (additive migration):
  - `decision_claims(claim_id TEXT PRIMARY KEY, decision_id TEXT NOT NULL, claim_type TEXT NOT NULL, text TEXT NOT NULL)` where `claim_type` ∈ `rationale | alternative_rejected | outcome | constraint`.
  - `claim_evidence(claim_id TEXT, event_id TEXT, relation TEXT NOT NULL, passage_text TEXT, passage_start INTEGER, passage_end INTEGER, source_group TEXT NOT NULL, PRIMARY KEY (claim_id, event_id))` where `relation` ∈ `direct | indirect | contradicting`.
- **Source independence (`source_group`) — implement as a pure function `independence_key(event)`:**
  - Same issue/PR **thread** (the issue/PR itself, its comments, its review comments) → one group, key like `thread:<repo>#<number>`.
  - A commit and the PR that contains it → same group (key by PR number when known, else `commit:<sha>`).
  - An ADR/doc file → one group per file path (`doc:<repo>:<path>`); different revisions of the same file are the same group.
  - A copy/quote of the same text in another place (identical normalised body, or body containing > 80% of another event's tokens) → same group as the original.
  - Different authors alone do **not** make two sources independent; different underlying threads/documents do.
  - Slack (Step 5.5): one group per thread.
- **Passage extraction:** for each claim and evidence event, pick the best-matching sentence by content-word overlap and store the text and character offsets. If overlap is below the threshold, do not store a direct relation.
- **Accept:** 5 comments in one PR thread count as **1** independent source; an ADR plus a separate PR discussion count as **2**.
- **Verify:** `tests/test_independence.py` with duplicate-copy, same-thread, ADR+PR, and commit+PR cases.

### Step 3.2 — Evidence assessment and abstention
- **Do:** `backend/engine/evidence.py` → `assess(decision)` returns `{ label, direct_support, indirect_support, contradicting, missing_corroboration, independent_sources }` using this **documented deterministic rule** (write it in `METRICS.md` and in code comments; state that thresholds are design choices, not statistics):
  - `contradicted`: at least one `contradicting` relation from a source not already superseded by later evidence.
  - `strong`: ≥ 2 independent source groups, at least one `direct`.
  - `moderate`: 1 `direct` group plus ≥ 1 other group (any relation), **or** 2 independent `indirect` groups.
  - `weak`: exactly 1 source group.
  - `insufficient`: no evidence, or only one `indirect` group.
  - "Missing corroboration" is generated from the rule (e.g. "no independent source besides the ADR", "no outcome/test evidence linked"); "conflicting evidence" lists contradicting items and any later decision/supersession on the same entity.
- Store the label in `decisions.evidence_assessment`; recompute whenever evidence or relations change.
- **Confidence vs evidence:** keep the legacy `confidence` field but rename its UI label to **"Heuristic score (uncalibrated)"** until Step 4.7 demonstrates calibration. Show the evidence label as the primary indicator. Never show a numeric probability that has not been validated.
- **Review routing:** labels `weak`, `insufficient`, `contradicted` create review-queue items with the reason.
- **Abstention:** `/api/explain` and the answer generator return `{ "status": "insufficient_evidence", "message": "..." }` when the label is `insufficient` and no stronger source exists. The LLM path must also abstain (grounding validator from v1 stays).
- **Accept:** a decision with a single copied source cannot be labelled `strong`; a contradicted decision cannot be shown with high certainty.
- **Verify:** `tests/test_assessment.py` covering each label boundary, copy vs independent sources, abstention, and review routing.

### Step 3.3 — Evidence-aware explanation output
- **Do:** Change the explanation payload (and UI evidence panel) to this structure, per decision:
  - `decision`, `lifecycle_state`, `needs_review` (bool), `evidence_assessment.label`.
  - `direct_support[]`, `indirect_support[]`, `missing_corroboration[]`, `conflicting_evidence[]`.
  - Per evidence item: source link, **relevant passage**, author, date, relation to the decision, source group.
  - Sentence-level support check (reuse the "claim support rate" from `METRICS.md`).
  - Remove the legacy "evidence-link validity = URL starts with http" as a quality claim. If you keep it, name it `url_format_ok` and never present it as correctness.
- **Accept:** every statement in an answer links to a passage; unsupported sentences are removed or flagged.
- **Verify:** extend `tests/test_explanation.py` (create it if absent): output structure, passage presence, flagged unsupported sentence.

### Step 3.4 — Decision-specific constraints and a general drift detector (P1-a)
- **Files:** `backend/engine/drift_detector.py`, `backend/engine/guard_rules.py`, new table `decision_constraints` (or reuse `guard_rules` with the extra columns below).
- **Do:**
  1. Data model: each **accepted** decision may have constraints `{ polarity: "must" | "must_not", rule_type, params, applies_to: [entity ids or path globs], source: "human" | "proposed" }`. Each **rejected alternative** may have a **detection signature**: forbidden imports/dependencies, regex patterns, config values, and affected entities. Reuse the four existing guard-rule types (`forbid_import`, `require_import`, `forbid_pattern`, `config_value`); add `applies_to` and `polarity`. Only human-approved (`active`) constraints are enforced.
  2. **Delete the hard-coded PID/Redis/keyword scenario branches** from the detector. Move those scenarios into test fixtures as ordinary constraint definitions + example diffs.
  3. Detector flow: parse the diff → find touched files/entities → fetch only the decisions/constraints whose `applies_to` overlaps → evaluate each rule against **added lines** (and removed lines for `require_*`).
  4. Each finding contains: `finding_id`, `status: "potential_violation"`, `rule_id`, `decision_id`, file, line numbers, the exact offending line/hunk, the decision's evidence passages with URLs, `signal_strength` (see below), and `reviewed: false`.
  5. **No hard-coded confidences.** Replace literals such as 0.92/0.94 with `signal_strength` ∈ `high | medium | low` derived from how many independent signals matched (entity overlap, rule match, text/signature match). Add `"calibrated": false` and label the UI "Heuristic signal (uncalibrated)".
  6. Status stays `potential_violation` until a human confirms.
- **Accept:** a violation is found through constraints, not keyword scenarios; clean changes (including ones that merely *mention* a forbidden term in a comment, a docstring, or a removed line) produce no finding.
- **Verify:** `tests/test_drift_rules.py` with ≥ 6 positive and ≥ 10 negative diffs (negatives must include near-misses), plus a grep test asserting no domain keywords (`redis`, `pid`, `hysteresis`) remain in `drift_detector.py`. Re-run the labelled `drift_cases.json` and record precision/recall.

### Step 3.5 — Rejected-idea guard (headline novelty)
- **Files:** new `backend/engine/rejected_idea_guard.py`; hook into the webhook/CI path and the UI "Live CI Drift Tester".
- **Workflow (implement exactly):**
  1. **Input:** a PR or proposal (title, body, diff, touched files).
  2. **Extract the design approach:** deterministic first — added imports/dependencies, config keys, identifier names, entities touched, noun phrases from title/body. Optional LLM summary (only if `llm_client.available()`; must pass the grounding rules; never required).
  3. **Retrieve candidates:** all `rejected` decisions and all rejected alternatives whose affected entities/paths overlap the proposal, plus those with a detection signature.
  4. **Compare on substance** using several signals, not shared words alone: (a) entity/path overlap; (b) signature/guard-rule match; (c) dependency/library match; (d) text similarity (implement token TF-IDF cosine with stdlib; optionally an LLM judge). Combine into explicit tiers: `strong` (≥ 2 independent signals incl. a structural one), `possible` (1 structural or high text similarity), otherwise no finding. Document the tiers.
  5. **Output** for a match: the original discussion link(s) and passages, the recorded **rejection reason**, who/when, the current state of that decision (it may already be `reopened` or `superseded`), and **changed-circumstances hints**: time since the decision, dependency versions changed since (use the requirements/config parser already in `entity_res.py`), later related decisions, and any assumptions marked stale (Step 5.2).
  6. **Never auto-block.** The finding is advisory (`advisory: true`); the PR comment says "Possible reintroduction of a previously rejected approach — please review", never "blocked".
  7. **Developer actions:** `confirm`, `dismiss` (with reason), `reopen decision` (calls the lifecycle engine: `rejected → reopened` with the PR as evidence). Store in `finding_feedback`; a dismissed finding for the same PR+decision is not repeated.
- **Accept:** a PR that re-adds a library rejected in an earlier discussion triggers an advisory finding with the original URL and reason; a PR that adds an unrelated library with a similar name does not; a `reopened` decision changes the message.
- **Verify:** `tests/test_rejected_idea_guard.py`: ≥ 5 true matches (including a paraphrased proposal with different terminology matched by structural signals), ≥ 8 non-matches (including keyword-only coincidences), reopen flow, dismiss persistence, and "never blocks" assertion (CI exit code stays 0 for advisory-only findings unless `--strict`).

### Step 3.6 — Developer feedback loop and review routing
- **Do:** Table `finding_feedback(feedback_id, finding_id, finding_type, action, reason, actor, created_at)` and `POST /api/findings/feedback` (reviewer role). Ambiguous findings (`possible` tier, supersession candidates, `weak` evidence) go to the review queue with the reason. Show feedback counts in the metrics page as *measured data*; use them later as extra labelled examples for precision (never as test data).
- **Accept:** confirm/dismiss persists and changes subsequent output.
- **Verify:** `tests/test_feedback.py`.

### Phase 3 exit check
Constraints replace hard-coded scenarios; evidence is claim-level with independence; rejected-idea guard works end-to-end on fixtures with negatives; nothing shows an uncalibrated number as a probability. Tag `phase3-done`.

---

## PHASE 4 — Prove it works (evaluation)

**Why this phase matters most for grading.** The reported WhyBench test split shows CIF decision recall 30.8% versus 64.9% for the keyword baseline, with 100% state accuracy on only 8 matched decisions and 100% refusal accuracy on 11 negative cases (figures from the existing `evaluation_results.md`). Small matched subsets do not offset low recall. The goal is to **find out why** recall is low, fix real causes on `dev`, and report honestly on a **new frozen** test split.

### Step 4.1 — Audit the matching protocol
- **Files:** `backend/evaluation/benchmark.py`, `ground_truth.py`, `tools/run_whybench.py`, `METRICS.md`.
- **Do:**
  1. Define and implement **one-to-one matching**: build the bipartite graph of (ground-truth item, system decision) pairs that share ≥ 1 expected evidence event id; assign greedily by descending overlap count with each system decision used at most once (or use an optimal assignment and say so). Unmatched system decisions count against precision.
  2. Report both strict (one-to-one) and lenient (many-to-one) recall and show the difference, to expose any previous overcounting.
  3. Replace the weak "evidence-link validity" with: `url_format_ok` (format only), `event_exists` (the cited event is in the DB), and `claim_supported` (sentence support from Step 3.3). Never describe the first as accuracy.
  4. Keep the matching code in one function with unit tests (§4.10).
- **Accept:** a test shows that one system decision cannot satisfy two labels in strict mode.
- **Verify:** `tests/test_benchmark.py` additions (below).

### Step 4.2 — Compare equivalent tasks only
- **Do:** Split the benchmark into two clearly defined tasks and document, for each: the input, what each system/baseline receives, what counts as correct, and how refusal is scored (put it in `METRICS.md`).
  - **Task 1 — Evidence retrieval** ("find the sources that explain X"): comparable across CIF and the keyword/BM25-style baselines (top-k event hit rate).
  - **Task 2 — Decision reconstruction** (state, rationale, rejected alternatives, supersession): the keyword baseline can only be scored on locating evidence, so mark non-applicable cells `n/a` instead of `0`.
  - Refusal (`no recorded decision`) scored for every system that can abstain; a baseline that always returns top-k never abstains and gets `n/a` or an explicit "always answers" note.
- **Accept:** the results table no longer compares unlike tasks directly.
- **Verify:** read the generated `evaluation_results.md` and confirm each column states its task.

### Step 4.3 — Failure analysis tool
- **Do:** `tools/analyze_failures.py --split dev` classifies every **missed** ground-truth item into exactly one category (check in this order): (1) `not_ingested` — expected evidence event absent from the DB; (2) `no_candidate` — event present, no decision extracted from its bundle; (3) `filtered` — candidate produced but removed by a noise/quality filter; (4) `wrong_evidence` — a decision exists but cites different events; (5) `wrong_state` — found but state differs. Also list wrongly-extracted system decisions (false positives) with a short reason. Output a table of counts and per-item detail (JSON + Markdown).
- **Accept:** a count per category and per repository, with item lists.
- **Verify:** run on `dev`; spot-check 5 items by hand and record that the category is right.

### Step 4.4 — Improve recall from the analysis (dev only)
- **Do:** Work through categories in order of count, one change per commit, and re-run `dev` after each change, logging precision, recall, F1 in `docs_changelog.md`. Typical fixes: ingest gaps (missing PR review comments, ADR folders not scanned, pagination); lower extraction thresholds but send low-confidence candidates to review instead of dropping them; use event-level retrieval (BM25/TF-IDF) as a *candidate generator* feeding the structured extractor; improve entity matching; fix state classification cues. Do not special-case ground-truth titles.
- **Guards:** do **not** open `test_v1` or `test_v2` results while tuning; report the precision/recall trade-off (curve over a threshold sweep), not a single lucky point.
- **Accept:** dev recall improves or the failure analysis explains, with numbers, why it cannot; precision does not collapse (state the measured precision).
- **Verify:** `dev` runs before/after in the changelog; unit tests still pass.

### Step 4.5 — Human-labelled precision
- **Do:** `tools/make_precision_sample.py` samples up to 40 system decisions per repository (seed 1234) from a **named, hashed DB snapshot** and writes a label template. The label file must record `dataset_version`, `db_snapshot_sha256`, `repo`, and `decision_id` per row, and `correct: null` until a human fills it in. The benchmark refuses to use labels whose snapshot hash does not match the DB being evaluated (prevents stale-ID labels).
- **Human task:** see §12.
- **Accept:** precision reports `not measured` until labels exist and match.
- **Verify:** unit test: wrong snapshot hash → precision `not measured` with a clear reason.

### Step 4.6 — Representative negative cases
- **Do:** Extend the ground truth with negatives of two kinds: (a) questions whose honest answer is "no recorded decision"; (b) **discussions that mention a technology without making a decision** (e.g. "should we maybe look at X sometime", release notes listing a dependency, a bot comment). Label them `expected_state: "none"`. Count a false decision on a negative as a false positive.
- **Accept:** ≥ 15 negatives per repository in `dev` and `test_v2`, at least half of type (b).
- **Verify:** `tools/validate_whybench.py` checks the mix.

### Step 4.7 — Confidence quality and calibration
- **Do:** For decisions with labels (Step 4.5) compute accuracy by heuristic-score bucket (e.g. 5 equal-width bins) and by `evidence_assessment` label; report whether higher scores are really more accurate. Compute a reliability table and Expected Calibration Error **only if** there are ≥ 100 labelled predictions; otherwise print `not enough labels for calibration`. If the score is not shown to be calibrated, keep the "uncalibrated" label in the UI.
- **Accept:** a computed table in `evaluation_results.md`, or an explicit `not measured`.
- **Verify:** unit test with a toy labelled set where the expected ECE is known.

### Step 4.8 — Per-repository and reproducible reporting
- **Do:** Every run of `tools/run_whybench.py` writes a **manifest** `results/<run_id>/manifest.json` containing: dataset version and file hashes (questions, labels, drift/conflict cases), the DB snapshot hash, `git rev-parse HEAD`, a clean/dirty flag, Python version, all config/env flags that affect behaviour (extractor mode, model name if used, thresholds — never keys), random seeds, the full per-item predictions, and the computed metrics, **per repository and overall** (never only the aggregate). `evaluation_results.md` is generated from the latest manifests, not hand-edited.
- **Accept:** re-running with the same manifest values reproduces identical metrics.
- **Verify:** run twice on `dev`, diff the metrics JSON (must be identical).

### Step 4.9 — New frozen test split `test_v2` (needs a human)
- **Do:** Add a third real repository and/or new unseen questions per repository, labelled **before** looking at any system output, split off as `test_v2`. Freeze it: store its SHA-256 in `whybench/FROZEN.md`; the runner refuses to modify it and refuses to run it unless `--final` is given, and refuses a second run without `--force`. Report `test_v1` as "pre-improvement baseline" and `test_v2` as the headline result.
- **Accept:** frozen hash recorded; ≥ 20 verified questions per repository in `test_v2`.
- **Verify:** `tools/validate_whybench.py`.

### Step 4.10 — Expand the test suite for evaluation
- **Do:** Extend `tests/test_benchmark.py` for: one-to-one vs many-to-one matching; missing labels; duplicate matches; contradictory evidence; empty datasets; negatives; reproducibility (same inputs → same metrics); snapshot-hash mismatch; strict test-split protection.
- **Verify:** `python -m unittest discover -s tests -v`.

### Phase 4 exit check
Honest matching; failure analysis done; tuned only on `dev`; precision from human labels; per-repo, reproducible reports; `test_v2` run once at the end (Step 6.7). Tag `phase4-done`.

---

## PHASE 5 — Distinctive extensions (only after Phases 1–4 are dependable)

### Step 5.1 — Privacy-first ingestion (do this before Slack)
- **Files:** new `backend/ingestion/sanitizer.py`; hook **before** `upsert_event` for every adapter.
- **Do:**
  1. `sanitize_event(event) -> event` redacts in `title`, `body`, `source_url` (query parameters), `author` display text where configured, and **every** value in `raw_metadata`. Replacement tokens: `[REDACTED:<type>]`.
  2. Detect at least: GitHub tokens (`ghp_`, `gho_`, `ghs_`, `github_pat_`), AWS access keys (`AKIA…`) and secret-key assignments, Slack tokens (`xox…`), Google API keys, private-key blocks (`-----BEGIN … PRIVATE KEY-----`), JWTs, `Authorization: Bearer …`, and `password|passwd|secret|token|api_key` assignments with a value. Optional PII (off by default, on with `CIF_REDACT_PII=1`): e-mail addresses and phone numbers.
  3. Redact **before** hashing/IDs are derived from content, before graph/extractor/LLM processing, and before anything is logged. Add a logging filter that scrubs the same patterns from log records and exception messages.
  4. **Local-only mode** `CIF_LOCAL_ONLY=1`: disable the LLM client and any network ingestion; the system must still run on local folders/exports.
  5. Retention/deletion: `POST /api/purge-repo` (admin) deletes all events, entities, decisions, edges, claims, history for a repository; document it in `PRIVACY.md` together with what is stored, what is redacted, and what is never sent to an LLM.
- **Tests (important):** build synthetic secrets **at runtime** by string concatenation so no realistic secret appears in the repo (avoids false alarms from secret scanners). Assert: after ingesting events containing each secret type, a full-table scan of the SQLite file (`strings`-style read of the raw bytes) finds none of them; logs and API error messages contain none; the LLM client is never called in local-only mode.
- **Accept:** secrets never reach persistence.
- **Verify:** `tests/test_sanitizer.py`, `tests/test_local_only.py`.

### Step 5.2 — Decision half-life / staleness
- **Do:**
  1. Table `decision_assumptions(assumption_id, decision_id, text, watch_type, watch_params_json, status, last_checked_at)`; `watch_type` ∈ `dependency_version | config_value | file_exists | infrastructure_note | manual`. Assumptions come from the extractor (explicit statements like "assuming traffic below…", "because library X 1.x…") or from humans.
  2. **Never** expire decisions by age alone. Staleness is triggered only by events affecting an assumption: a dependency upgrade (diff of parsed requirements/lockfiles between snapshots), a changed config value, a deleted/renamed watched file, a manual flag.
  3. Freshness: `fresh → stale → under_review → revalidated` stored in `decisions.freshness` (separate from lifecycle state). Recompute when relevant events are ingested. A stale decision creates a review-queue item whose message names the **triggering change**, with its source link.
  4. Review reminder = review-queue entry + a "stale for N days" counter; no timers or e-mail.
- **Accept:** a version bump that breaks an assumption marks the decision stale; a bump that does not, leaves it fresh; revalidating records history.
- **Verify:** `tests/test_staleness.py` for both directions and for the review item content.

### Step 5.3 — Bus-factor / knowledge-concentration map
- **Do:** `backend/engine/bus_factor.py`. For each module (top-level package/dir, or an entity grouping) compute and show: number of **important decisions** (state `accepted/rejected/superseded` with evidence label ≥ `moderate`, or touching ≥ N entities); contributors per decision using a **weighted knowledge score** — decision author and substantive discussion authors (comments above a minimum length), reviewers who commented on the decision's PR, and ADR authors count; **raw commit count does not**; the share of important decisions supported by exactly one contributor; documentation coverage (decision has an ADR/doc source); and a ranked list of modules by concentration, each with a "missing documentation / onboarding material" hint. Add `GET /api/bus-factor` and a UI table/heat map.
- **Accept:** a module whose important decisions all come from one person ranks above a module with distributed knowledge, even if the second has far more commits.
- **Verify:** `tests/test_bus_factor.py` with a fixture containing a prolific-committer/low-knowledge case and a quiet-architect case.

### Step 5.4 — Adaptive developer onboarding
- **Do:** Replace the fixed walkthrough in `web/app.js` with a request-driven path: `GET /api/onboarding?repo=...&role=...&module=...&files=a,b` (or POST). Algorithm: resolve the modules/files/functions → entities; fetch decision chains via the graph; rank by (active/accepted first, evidence label, recency, number of rejected alternatives = "pitfalls"); produce an ordered **learning path** (overview of the module → key active decisions → important commits/discussions → rejected alternatives and known pitfalls → open/stale items). UI form asks for role, module/task, optional files. Add a checklist so the developer can mark items read.
- **Measurement:** `evaluation/onboarding_tasks.json` defines, per task, the decisions a developer must find; report onboarding recall (path contains them) and compare against plain search for the same task, computed by code.
- **Demo requirement:** two personas on the same repo (e.g. authentication vs payments or the two pilot modules) must receive **materially different** paths; add a test that the two paths share fewer than 50% of items.
- **Accept:** no prewritten example content remains in the onboarding surface.
- **Verify:** `tests/test_onboarding.py`.

### Step 5.5 — Slack ingestion (**DECISION REQUIRED from the team first**)
- **Do only if the team confirms Slack stays in scope.** Implement an **offline export adapter** (Slack workspace export folders: `users.json`, `channels.json`, per-channel `YYYY-MM-DD.json` files with `user`, `ts`, `text`, `thread_ts`). Map messages to `Event(source_type="slack_message")`, resolve users through `users.json` and the identity resolver, group messages by thread (`independence_key` = thread), and run the sanitizer (Step 5.1) **before** persistence. A live Slack API connector is out of scope unless the team provides credentials and approval.
- **If Slack is dropped:** write the decision in `LIMITATIONS.md` and remove Slack from README, slides and the pipeline description.
- **Accept:** a fixture export yields events, threads and a decision with correct independence grouping; no secrets persisted.
- **Verify:** `tests/test_slack_adapter.py`.

### Phase 5 exit check
Privacy pipeline proven by raw-byte scan; staleness, bus-factor and onboarding all driven by data and tested. Tag `phase5-done`.

---

## PHASE 6 — Release-quality integration

### Step 6.1 — Real GitHub App / webhook / CI test (needs a human)
- **Do (code):** make sure the webhook path covers: signature validation, `pull_request` actions, diff fetch, drift + rejected-idea analysis, PR comment, optional commit status. Provide `GITHUB_APP_SETUP.md` (App permissions: Pull requests read/write, Contents read, Issues read; subscribe to *Pull request*; secret stored in `CIF_WEBHOOK_SECRET`; a tunnel for local testing) and the `cif-check.yml` workflow using `tools/ci_check.py --base ... --head ...` with exit codes 0/1/2 (Step 1.4).
- **Do (human):** create the App, install it on a test repository, open a PR that violates an approved rule and one that is clean, and save evidence (screenshots of the delivery log and PR comment) in `docs/integration_evidence/`.
- **Rule:** mocked tests prove only code paths. Until the human live test exists, README must say *"webhook/CI verified with mocks only"*.
- **Accept:** documented live run, or the honest "mocks only" statement.
- **Verify:** `tests/test_webhook.py` (mocks) plus the evidence folder.

### Step 6.2 — Separate live and simulated frontends
- **Do:** Create `tools/build_static.py` (the missing generator): run the real API handler in-process against a chosen DB, collect every GET response the UI uses into `web/static_data.js` (same keys `app.js` reads from `window.__CIF_STATIC_DATA__`), deterministic ordering, include the generation date and DB snapshot hash, then copy `web/*` to `docs/` so the two cannot drift. UI badge: **"Live engine"** when API calls succeed, **"Static snapshot — simulated"** otherwise. In static mode every write action (review, drift test, ingest) is clearly labelled *simulated* and does not claim to have changed data. The deployment workflow must run `build_static.py` and fail if `docs/` differs from `web/`.
- **Accept:** `diff -r web docs` is empty after the tool; the badge is correct in both modes; the static page states its snapshot date.
- **Verify:** run the tool twice (identical output); manual check in both modes. Test the **deployed** build separately from the local one.

### Step 6.3 — Database and repository hygiene
- **Do:**
  1. Scan **both git histories** (project and the nested repo in `demo_sample_repo/`) for secrets: write `tools/scan_secrets.py` reusing the sanitizer patterns, scanning every revision (`git rev-list --all` + `git grep` or `git log -p`), and every text column of both `.db` files. Report findings in `SECURITY_SCAN.md`; if a real credential is found, **stop and tell the human** — it must be revoked, not just deleted.
  2. Inspect DB contents for private discussion text or personal data (imported repos may contain names/e-mails).
  3. Nested repo: first check how `run_demo.py`/`git_adapter.py` use `demo_sample_repo/.git`. Replace the nested `.git` with a generator `tools/make_demo_repo.py` that builds it deterministically in a temp/ignored folder, so the distributable has no nested repo. Verify the demo still passes.
  4. `tools/package_release.py` builds a ZIP excluding `.git`, `*.db`, `backups/`, `__pycache__/`, `.env`; synthetic fixtures are shipped as files, not as live DBs. Keep synthetic and imported data in separate DB files with clear names.
  5. DB init docs: `python tools/init_db.py [--seed]` + migration instructions in README.
- **Accept:** release ZIP contains no DB, no history, no secrets; scan report written.
- **Verify:** unzip the package into a temp folder and run the tests there.

### Step 6.4 — Docs that match reality
- **Do:** Update `readme.md`, `task.md`, `explanation.md`, `DEPLOYMENT.md`; create `LIMITATIONS.md`, `PRIVACY.md`, `EVALUATION.md` (methodology, splits, baselines, how to reproduce). No hard-coded numbers: point to generated `evaluation_results.md`. State plainly: pilot repos are synthetic; benchmark size; heuristic scores are uncalibrated unless Step 4.7 shows otherwise; webhook live-tested or mocks-only; Pages site is a snapshot.
- **Accept:** `grep -rn "92.6\|98.4\|94.1\|91.2" *.md` finds nothing stale.
- **Verify:** read each file top to bottom once.

### Step 6.5 — Test gaps from the review
- **Do:** add tests for each item (create the file if missing): historical queries before/after a supersession (`test_as_of.py`); two unrelated decisions with similar titles (`test_supersession.py`); duplicated vs independent evidence (`test_independence.py`); malicious HTML in titles/discussions (`test_frontend_escape.py` + manual); SSL failure (`test_tls_safety.py`); failed guard-rule execution (`test_drift_errors.py`); unauthorized destructive API calls (`test_api_auth.py`); clean changes that resemble violations (`test_drift_rules.py`). Mark which tests are **unit** and which are **integration** (see 6.6).
- **Verify:** `python -m unittest discover -s tests -v`; list the test counts in the report.

### Step 6.6 — End-to-end integration test (no network)
- **Do:** `tests/test_integration_pipeline.py`: from a **local fixture** (a small git repo + exported issues/PRs/ADRs JSON) run ingestion → sanitizer → extraction → evidence assessment → graph → review queue → as-of query → drift/rejected-idea check, using a temp DB. Assert the specific decision, its evidence passages and independence groups, the graph edges with correct `valid_from`, the review-queue entry for a weak decision, and the correct as-of result on two dates.
- **Accept:** one test proves the whole chain on a realistic fixture.
- **Verify:** run it alone and in the full suite.

### Step 6.7 — Final run, clean clone and release
- **Do:** (1) Run `tools/run_whybench.py --split test_v2 --final` **once**; commit the manifest and the generated report; do not change code afterwards to improve it. (2) `tools/clean_clone_check.py`: `git clone` the repo to a temp folder, run migrations on a fresh DB, run the full test suite and `run_demo.py` there, and report. (3) Rehearse the demo script (update README section "Demo walkthrough" with the **measured** numbers, the rejected-idea-guard scenario, time-travel, and a 3-line answer to "why not just a README or an AI agent?" based on baseline results).
- **Accept:** clean clone passes; final numbers in the UI equal the manifest.
- **Verify:** compare Metrics page values to `manifest.json`.

---

## 12. Tasks only humans can do (never fake them)

| # | Task | Needed for |
|---|---|---|
| H1 | Verify each benchmark question against its public source URL and set `"verified": true` | 4.9, 2 repos |
| H2 | Fill `correct: true/false` in the precision label files | 4.5, 4.7 |
| H3 | Decide whether Slack stays in scope | 5.5 |
| H4 | Create/install the GitHub App on a test repo, open a violating and a clean PR, save screenshots | 6.1 |
| H5 | Run the Copilot (or other assistant) baseline by hand and fill `manual_copilot_results.csv` | 4.2 |
| H6 | Choose the third benchmark repository and approve `test_v2` before it is frozen | 4.9 |
| H7 | Revoke any credential found by `scan_secrets.py` | 6.3 |
| H8 | Provide `CIF_LLM_API_KEY`/`CIF_LLM_MODEL` if an LLM comparison is wanted | 3.2, 4.2 |

If a human task is missing when you need it, report `blocked on H#` and continue with the next independent step.

---

## 13. Pitfalls — read before coding

- **SQLite + threads:** `ThreadingHTTPServer` serves requests on different threads. Use a new connection per request; keep `sqlite3.Row` as the row factory (existing code uses `row["col"]`).
- **Schema changes:** only through numbered migrations; test on a copy; the `decisions` rebuild (Step 2.1) must preserve indexes and foreign keys and end with `PRAGMA foreign_key_check` returning nothing.
- **Timestamps:** parse ISO-8601 to timezone-aware datetimes before comparing; never compare raw strings from different sources.
- **Deterministic IDs:** keep decision/event IDs derived from stable inputs so re-ingestion upserts instead of duplicating. Compute them **after** sanitisation only if the ID inputs do not include secret-bearing text.
- **Windows console:** keep the UTF-8 `reconfigure` guard; avoid exotic characters in `print`.
- **GitHub API limits:** use a token, cache raw exports to disk, never call the API in tests.
- **Destructive endpoints:** `/api/reseed`, `/api/clear-db`, `/api/purge-repo` must never be called by tests or tools against the real DB path.
- **Paths in tools:** compute the project root from `__file__`; add it to `sys.path`; do not rely on the current working directory.
- **Frontend copy:** `docs/` is generated from `web/`; edit `web/` only.
- **LLM output is untrusted:** always run the grounding validator; never write LLM text to the DB without it; never put keys in logs.
- **Heuristic ≠ probability:** do not label any heuristic number as "confidence" or "probability" in UI or docs unless calibration (4.7) supports it.
- **Do not tune on burned data:** `test_v1` is burned; `test_v2` is touched once.

---

## 14. Reporting format (after every step)

```text
STEP: <number and name>
STATUS: done | partial | blocked
FILES CHANGED: <list>
VERIFY COMMAND(S): <exactly what you ran>
RESULT: <real output summary, real numbers only>
ACCEPTANCE CRITERIA MET: yes | no (list any not met)
HUMAN TASKS NEEDED: <H# list or none>
NEXT: <next step number>
```

If `STATUS` is `blocked`, also append an entry to `BLOCKERS.md`. At the end of each phase, also report: test count, demo checks, and the git tag.

---

## 15. Definition of done

- [ ] Tests and `run_demo.py` pass in a **clean clone**; CI is green.
- [ ] P0-a/b/c and P1-a..d each have a regression test and a closed audit entry.
- [ ] `decisions` use the reconciled lifecycle; every change has an audit row; as-of queries are correct on boundary dates.
- [ ] Evidence is claim-level with independence; assessment labels are rule-based; the system abstains when evidence is insufficient.
- [ ] Drift detection runs from decision constraints; the rejected-idea guard returns original evidence and reason, is advisory, and is feedback-driven.
- [ ] Evaluation: one-to-one matching, fair task definitions, failure analysis, human precision labels, per-repo and reproducible manifests, a frozen `test_v2` run exactly once, and the pre-improvement `test_v1` figures reported honestly.
- [ ] Privacy pipeline proven by raw-byte scan; staleness, bus-factor and onboarding implemented and tested; Slack implemented or explicitly removed from scope.
- [ ] Live GitHub test documented, or README states "mocks only".
- [ ] UI clearly shows Live engine vs Static snapshot (simulated).
- [ ] Release ZIP has no DBs, no git history, no secrets; docs match reality; no hard-coded metrics anywhere.

---

## 16. Start here

1. Run the environment checklist (§3).
2. Do **Phase 0** completely and send the first report.
3. Begin **Step 1.1**. Do not start Phase 2 until the Phase 1 exit check passes.
