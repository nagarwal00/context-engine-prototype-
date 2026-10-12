# CIF Project Status Audit (Step 0.2)

Audit timestamp: 2026-10-11
Auditor: Antigravity Assistant
Environment: Python 3.11.6, Windows (C:\Users\HP\Desktop\SE_project)

---

## 1. Database Row Counts

### `context_intelligence.db`
- `decisions`: 6
- `events`: 7
- `edges`: 16
- `state_history`: 0 (CONFIRMED: shipped database has empty state_history)

### `whybench.db`
- `decisions`: 57
- `events`: 57
- `edges`: 11
- `state_history`: 57

---

## 2. Security and Reliability Findings (Table 2 in §2)

| ID | Finding | Location | Reproduction | Verdict |
|---|---|---|---|---|
| **P0-a** | SSL verification can be disabled (unverified-context fallback) | `backend/ingestion/live_github.py:42-44, 79-82` | `python -c "import re; [print(f'{i}:{l.strip()}') for i,l in enumerate(open('backend/ingestion/live_github.py'),1) if re.search('unverified\|CERT_NONE\|check_hostname', l)]"` found `ssl._create_unverified_context()` and `ssl.CERT_NONE`. | `CONFIRMED` |
| **P0-b** | No authorization on destructive/write endpoints; wildcard CORS | `server.py:71, 79`, `backend/api.py:310, 336` | `python -c "import re; [print(f'{i}:{l.strip()}') for i,l in enumerate(open('server.py'),1) if 'Access-Control-Allow-Origin' in l]"` shows wildcard CORS `*`; `/api/clear-db` in `backend/api.py:336` executes `LiveGitHubIngestor(self.db).clear_database()` with zero token or role verification. | `CONFIRMED` |
| **P0-c** | Repository text inserted with `innerHTML` (XSS) | `web/app.js` (38 occurrences), `docs/app.js` (38 occurrences) | `python -c "print(len([l for l in open('web/app.js', encoding='utf-8') if 'innerHTML' in l]))"` returns 38 instances interpolating raw decision title, rationale, author without escaping. | `CONFIRMED` |
| **P1-a** | Rejected-idea/drift detection depends on hard-coded keywords and PID/Redis scenarios | `backend/engine/drift_detector.py:96-130` | `python -c "import re; [print(f'{i}:{l.strip()}') for i,l in enumerate(open('backend/engine/drift_detector.py'),1) if re.search('pid\|redis\|dict_cache', l)]"` identifies hardcoded literal checks for `'pid'`, `'redis'`, `'dict_cache = {}'` and confidence literals `0.89`, `0.94`. | `CONFIRMED` |
| **P1-b** | Guard-rule failures swallowed silently in `drift_detector.py` | `backend/engine/drift_detector.py:152-154` | `python -c "lines=open('backend/engine/drift_detector.py').readlines(); print(lines[151:154])"` reveals `except Exception: pass` silently masking rule evaluation errors. | `CONFIRMED` |
| **P1-c** | `TemporalGraph.add_edge()` defaults `valid_from` to a fixed date | `backend/engine/graph.py:38` | `python -c "print([l.strip() for l in open('backend/engine/graph.py') if '2026-01-01' in l])"` shows `valid_from=valid_from or '2026-01-01T00:00:00Z'`. | `CONFIRMED` |
| **P1-d** | Supersession matching links unrelated decisions by title-word overlap | `backend/engine/reconciliation.py:111` | `python -c "older={'title':'Optimize database query'}; body='We use a local cache instead of memory database'; print(any(w in body.lower() for w in older['title'].lower().split() if len(w)>4))"` returns `True` linking unrelated decisions on word 'database'. | `CONFIRMED` |

---

## 3. Feature Status Audit (Table 1 in §2)

| Feature | Status | What is needed | Location in Codebase | Reproduction / Evidence | Verdict |
|---|---|---|---|---|---|
| **Decision Lifecycle Engine** | P | Transition rules, history, reopening, review workflow, audit view, reconcile state definitions | `backend/models.py:59`, `backend/db.py:69` | DB check constraint only permits `('proposed', 'accepted', 'rejected', 'superseded', 'unresolved')`. No transition graph or reopening workflow. | `CONFIRMED` (P) |
| **Evidence and Confidence Engine** | P | Claim-level evidence, independence, contradiction handling, source trace, abstention, no fake probabilities | `backend/models.py:63`, `backend/engine/extractor.py:136, 160` | Conflates evidence quality with heuristic confidence floats (e.g. 0.85 for PR, 0.75 for commit); lacks claim-level independent corroboration. | `CONFIRMED` (P) |
| **Decision–Code Drift Detector** | P | Per-decision machine-checkable constraints instead of hard-coded scenarios, negatives, feedback | `backend/engine/drift_detector.py:96-130` | Lacks dynamic per-decision constraint rules; uses hard-coded text matches and silent exception suppression. | `CONFIRMED` (P) |
| **Temporal & Counterfactual Explorer** | P | "As of" queries, documented-alternative explanations, no speculation | `backend/engine/explanation.py`, `backend/engine/counterfactual.py` | Lacks historical point-in-time point queries against frozen graph state; counterfactuals are heuristic templates. | `CONFIRMED` (P) |
| **Adaptive Developer Onboarding** | P | Personalised paths by role/module/files from decision evidence | `backend/engine/onboarding.py:1-60` | Generates generic path sequences without role/module/file scoping from decision evidence. | `CONFIRMED` (P) |
| **Temporal Context Graph** | I | Temporal consistency, traversal and historical-query correctness | `backend/engine/graph.py:1-150` | Functional graph structure implemented with SQLite backing, but relies on arbitrary fixed default dates (`valid_from`). | `CONFIRMED` (I/P) |
| **Decision half-life / staleness** | M | Assumptions, triggers, freshness status, review reminders | N/A (Missing) | File search across `backend/` yields zero references to freshness, staleness decay, or expiration triggers. | `CONFIRMED` (M) |
| **Time-travel questions** | P | Historical snapshots, not just a timeline | `backend/engine/temporal_engine.py` | Filters events along a linear timeline but does not reconstruct complete decision-state snapshots at historical timestamps. | `CONFIRMED` (P) |
| **Bus-factor map** | M | Knowledge concentration per module/decision/contributor | N/A (Missing) | File search across `backend/` yields zero references to bus-factor or knowledge concentration scoring. | `CONFIRMED` (M) |
| **Privacy-first ingestion** | M | Redaction before persistence, safe logging, local-only mode | `backend/ingestion/` | Raw commit and PR text stored directly in database with no PII/secret scrubbing or redaction layer. | `CONFIRMED` (M) |
| **Rejected-idea guard** | P | Match proposals to rejected approaches, retrieve original evidence and reason | `backend/engine/drift_detector.py:75-90` | Searches for rejected decisions but relies on basic string overlap without evidence provenance or constraint verification. | `CONFIRMED` (P) |
| **Evidence-graded decisions** | P | Independent corroboration vs repeated copies | `backend/engine/extractor.py:160` | Counts evidence items without distinguishing multiple copies of identical commits from distinct independent corroborations. | `CONFIRMED` (P) |
| **Measured benchmark** | P | Recall, label validation, fair baselines, reproducible results | `backend/evaluation/benchmark.py:57-90` | Decision matching permits one system decision to satisfy multiple ground-truth items; link validation checks URL scheme only. | `CONFIRMED` (P) |
| **Real GitHub integration** | P | Install/config, end-to-end webhook validation, CI deployment test | `backend/ingestion/live_github.py:42-82`, `server.py` | Basic polling and webhook handler exist, but SSL verification has insecure fallback and installation auth flow is partial. | `CONFIRMED` (P) |
| **Slack integration** | M | Only if kept in scope | N/A (Missing) | No Slack app, webhook, or socket adapter implemented. | `CONFIRMED` (M) |

---

## 4. Other Correctness Problems

| Item | Location | Evidence / Reproduction | Verdict |
|---|---|---|---|
| **Hard-coded drift confidences** | `backend/engine/drift_detector.py:107, 124, 147` | Code contains hard-coded confidence values `0.89`, `0.94`, `1.0` instead of computed calibrated values. | `CONFIRMED` |
| **`state_history` empty in shipped DB** | `context_intelligence.db` | `SELECT count(*) FROM state_history` returns `0`. | `CONFIRMED` |
| **Benchmark overcounting** | `backend/evaluation/benchmark.py:57-90` | Loop does not consume matched system decisions; a single system decision satisfies multiple GT items (reproduced: 2 GT items matched 1 system decision). | `CONFIRMED` |
| **Evidence-link validity only checks URL format** | `backend/evaluation/benchmark.py:118` | `valid_links = [l for l in links if l["source_url"] and (l["source_url"].startswith("http://") or l["source_url"].startswith("https://"))]` — only checks URL prefix, not whether target exists or supports claim. | `CONFIRMED` |
| **Confidence and evidence quality conflated** | `backend/models.py:63`, `backend/engine/extractor.py:160-161`, `backend/api.py:236` | Review status and extraction confidence conflated (`confidence = 0.85 if ev.source_type == 'github_pr' else 0.75`; review_status set to 'auto_confirmed' if >= 0.8; `confidence = 1.0` on review). | `CONFIRMED` |
| **Demo vs deployed product unclear** | `run_demo.py`, `server.py` | Demo environment relies on synthetic/mocked seeds without explicit separation between demonstration mock modes and production deployment modes. | `CONFIRMED` |
| **DB / Git hygiene** | `.gitignore`, repository index | `context_intelligence.db` was previously tracked; `.db` files required manual untracking via `git rm --cached`. | `CONFIRMED` |
| **Test gaps** | `tests/` | No test coverage for TLS certificate validation failure handling, API authentication/role authorization, frontend XSS escaping, or temporal edge ranges. | `CONFIRMED` |

---

## 5. Security & Bug Fix Verification Log

### Step 1.1 (P0-a) — TLS Certificate Verification Safety
- Status: **RESOLVED**
- Files: `backend/ingestion/live_github.py`, `tests/test_tls_safety.py`
- Verification: `python -m unittest tests/test_tls_safety.py` (3 tests pass). Unverified fallbacks removed; custom CA bundle via `CIF_CA_BUNDLE` supported; secrets never leaked in exceptions.

### Step 1.2 (P0-b) — API Authorization & Boundaries
- Status: **RESOLVED**
- Files: `backend/security.py`, `backend/api.py`, `server.py`, `tests/test_api_auth.py`
- Verification: `python -m unittest tests/test_api_auth.py` (8 tests pass). Role-based token auth (`viewer`, `reviewer`, `admin`) enforced via constant-time comparison; wildcard CORS replaced with strict origin check; destructive routes require exact database name confirmation; 1MB request body limit enforced.

### Step 1.3 (P0-c) — Frontend HTML Injection (XSS) Prevention
- Status: **RESOLVED**
- Inventory: 38 occurrences of `innerHTML` in `web/app.js` and `docs/app.js` (0 `insertAdjacentHTML`, 0 `outerHTML`).
- Files: `web/app.js`, `web/index.html`, `docs/app.js`, `docs/index.html`, `docs/style.css`, `tests/test_frontend_escape.py`
- Resolution:
  1. Implemented `esc(value)` escaping `& < > " '` and `safeUrl(value)` enforcing `http`/`https` protocols.
  2. Wrapped all interpolated values across timeline, context graph, code-context explorer, decision explorer, evidence panel, review queue, drift checker, benchmark metrics, and onboarding tour.
  3. Replaced dynamic inline handlers with `addEventListener` and `data-*` attributes (`dataset`).
  4. Added Content-Security-Policy `<meta>` tag in `web/index.html` and `docs/index.html` (`default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'`).
  5. Tested with synthetic XSS payloads `<img src=x onerror=alert(1)>` and `"><script>alert(1)</script>` in `tests/test_frontend_escape.py` (6 tests pass). Static heuristic lint verifies no unescaped variables assigned to `innerHTML`.

### Step 1.4 (P1-b) — No More Silent Detector Failures
- Status: **RESOLVED**
- Files: `backend/engine/drift_detector.py`, `backend/engine/guard_rules.py`, `backend/db.py`, `backend/api.py`, `tools/ci_check.py`, `web/app.js`, `docs/app.js`, `tests/test_drift_errors.py`
- Resolution:
  1. Removed broad `except Exception: pass` from `drift_detector.py`.
  2. Updated `analyze_diff_for_drift` to return a report object `{ "status": "complete" | "incomplete", "findings": [...], "errors": [ { "stage", "rule_id", "error_type", "message" } ] }`.
  3. Evaluates each rule inside its own `try/except`; on failure appends a sanitised error (rule id + exception class + short message, no diff content, no params dump) and continues with other rules; marks status `incomplete`.
  4. Logged errors with standard `logging` module.
  5. Updated API endpoints (`/api/drift-check`, webhook receiver) to return full report. UI displays visible warning "Check incomplete: N rule(s) could not run" and distinguishes it from "No violations found".
  6. `tools/ci_check.py` exit codes: `0` = complete and clean, `1` = violations, `2` = incomplete.
  7. Verification: `tests/test_drift_errors.py` (3 tests pass). All 51 suite tests pass, 21 demo checks pass.

### Step 1.5 (P1-c) — Correct Temporal Defaults
- Status: **RESOLVED**
- Files: `backend/engine/graph.py`, `backend/engine/drift_detector.py`, `tools/repair_edge_validity.py`, `tests/test_graph_temporal.py`
- Resolution:
  1. Removed fixed default placeholder timestamp `2026-01-01T00:00:00Z` from `add_edge`.
  2. Made `valid_from` required in `TemporalGraph.add_edge()` and on `Edge` models.
  3. Added strict ISO-8601 validation; verified `valid_to >= valid_from` (raising `ValueError` if `valid_to < valid_from`).
  4. Created `tools/repair_edge_validity.py` (dry-run by default, `--apply` to write with automatic pre-modification backup).
  5. Inspected `context_intelligence.db` and `whybench.db`: found 0 placeholder edges in active databases.
  6. Verification: `tests/test_graph_temporal.py` (6 tests pass).

### Step 1.6 (P1-d) — Evidence-Based Supersession Matching
- Status: **RESOLVED**
- Files: `backend/engine/reconciliation.py`, `backend/api.py`, `tests/test_supersession.py`
- Resolution:
  1. Defined `GENERIC_STOP_WORDS` and `REPLACEMENT_CUES` constants in `backend/engine/reconciliation.py`.
  2. Implemented candidate priority:
     - Priority 1: Explicit reference (decision ID, ADR number, `#PR/issue` number, title match with cue).
     - Priority 2: Shared affected entity (≥ 1 common entity) AND later in time AND replacement cue present.
     - Priority 3: Non-stopword title overlap used only to break ties among candidates that already share an entity.
  3. If more than one candidate qualifies or match is word-overlap only, does not auto-link; creates `supersession_candidate` review queue items for human arbitration.
  4. Symmetrical `supersedes`/`superseded_by` fields, `supersedes` edges, and `state_history` audit records maintained.
  5. Implemented review queue arbitration in `/api/review-action` for `item_type == "supersession_candidate"` (confirm applies supersession, reject dismisses edge).
  6. Verification: `tests/test_supersession.py` (4 tests pass covering unrelated word overlap rejection, explicit reference auto-linking, shared entity + cue auto-linking, and ambiguous candidate review queue routing).

---

## Phase 1 Exit Verification Summary
- **Test suite**: 61 / 61 tests passing (`python -m unittest discover -s tests -v`).
- **Demo suite**: 21 / 21 checks passing (`python run_demo.py`).
- **TLS safety**: Verified zero unverified SSL fallbacks across backend and tools.
- **API security**: Role-based auth (`viewer`, `reviewer`, `admin`), CORS allowlist, and 1MB limit enforced.
- **Frontend XSS**: All `innerHTML` dynamic bindings sanitized with `esc()`, CSP `<meta>` tags active in both `web/` and `docs/`.
- **Drift detector reliability**: Strict structured error handling with sanitised diagnostics; no swallowed exceptions.
- **Temporal graph**: Required ISO-8601 timestamps on all edges; zero placeholder dates in active databases.
- **Supersession**: Evidence-based candidate priority and review queue routing for ambiguous candidates.
- **Git tag**: `phase1-done`.

---

## Phase 2 — Complete the Decision History

### Step 2.0 — Migration Framework
- Status: **RESOLVED**
- Files: `backend/migrations/__init__.py`, `backend/migrations/runner.py`, `backend/db.py`, `tools/migrate_db.py`, `tests/test_migrations.py`
- Resolution:
  1. Created `schema_migrations(version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)` tracking table.
  2. Implemented transactional migration runner in `backend/migrations/runner.py`:
     - Discovers migration modules in `backend/migrations/` matching `^(\d+)_(.+)\.py$`.
     - Executes each pending migration inside its own transaction (`PRAGMA foreign_keys = OFF; BEGIN; upgrade(conn); ... COMMIT; PRAGMA foreign_keys = ON; PRAGMA foreign_key_check;`).
     - On failure, rolls back transaction and leaves database unchanged.
     - Running twice is guaranteed to be a no-op.
     - Supports `--dry-run` to inspect pending migrations without applying.
  3. Integrated runner into `Database._init_schema()` in `backend/db.py` to ensure all databases automatically run pending migrations.
  4. Created CLI `tools/migrate_db.py --db PATH [--dry-run]`.
  5. Verified via `tests/test_migrations.py` (6 tests pass): fresh DB creation, idempotency, transaction rollback on failure, dry-run mode, CLI execution, and zero-data-loss validation against a copy of `backups/context_intelligence.pre_v2.db`.

### Step 2.1 — Reconcile State Definitions (Migration 001)
- Status: **RESOLVED**
- Files: `backend/migrations/001_reconcile_state_definitions.py`, `backend/models.py`, `backend/db.py`, `backend/engine/extractor.py`, `backend/engine/llm_extractor.py`, `tests/test_extractor.py`, `web/index.html`, `web/style.css`, `docs/index.html`, `docs/style.css`, `tests/test_state_model.py`
- Resolution:
  1. Rebuilt `decisions` table via Migration 001 with new CHECK constraints:
     - `state IN ('proposed', 'tested', 'accepted', 'rejected', 'superseded', 'reopened')`
     - `evidence_assessment IN ('strong', 'moderate', 'weak', 'insufficient', 'contradicted')` (default `'insufficient'`)
     - `freshness IN ('fresh', 'stale', 'under_review', 'revalidated')` (default `'fresh'`)
  2. Migrated legacy `unresolved` state to `state='proposed'`, `evidence_assessment='insufficient'`. Added compatibility alias in `Decision.__post_init__`.
  3. Enforced new evidence invariant: states `tested`, `accepted`, `rejected`, `superseded` require ≥ 1 evidence event; `proposed` and `reopened` may have zero only when `evidence_assessment='insufficient'`.
  4. Updated `save_decision` in `backend/db.py` to persist `evidence_assessment` and `freshness` with mechanical validation.
  5. Updated fallback extractor and LLM anti-hallucination grounding validator to emit `state='proposed'` with `evidence_assessment='insufficient'`.
  6. Updated frontend UI tabs and CSS status tag styling (`.status-tag.tested`, `.status-tag.reopened`) in both `web/` and `docs/`.
  7. Verification: `tests/test_state_model.py` (7 tests pass covering every allowed state, illegal state rejection, illegal assessment/freshness rejection, invariant enforcement, compatibility alias, and zero-data-loss validation against `backups/context_intelligence.pre_v2.db`). Full suite (74 tests) and demo suite (21/21) pass.

### Step 2.2 — Lifecycle Engine
- Status: **RESOLVED**
- Files: `backend/engine/lifecycle.py`, `tests/test_lifecycle.py`
- Resolution:
  1. Implemented data-driven lifecycle transition engine in `backend/engine/lifecycle.py`:
     - Dictionary table `ALLOWED_TRANSITIONS`:
       - `proposed -> tested, accepted, rejected`
       - `tested -> accepted, rejected`
       - `accepted -> superseded, reopened`
       - `rejected -> reopened`
       - `reopened -> tested, accepted, rejected`
       - `superseded -> (terminal, no transitions allowed)`
  2. Implemented `transition(db, decision_id, to_state, actor, reason, at, evidence_event_ids, superseded_by_id)`:
     - Validates against allowed transition graph; raises `InvalidTransition` otherwise.
     - Enforces non-empty `actor` and `reason`.
     - Enforces evidence requirement for states `tested/accepted/rejected/superseded` (checks existing links + supplied events).
     - Executes updates inside a single database transaction (updates `decisions.state`, appends audit row to `state_history` with actor/reason/timestamp, closes `valid_to` edge validity for `superseded`).
  3. Implemented `record_initial_state` for initial ingestion creation (`from_state = NULL`).
  4. Verification: `tests/test_lifecycle.py` (8 tests pass covering all legal transitions, all illegal pairs via `itertools.product`, `superseded` terminal state, `rejected -> reopened -> accepted` progression, evidence requirement, and audit logging). Full suite (80 tests) and demo suite (21/21) pass.

### Step 2.3 — Record History Everywhere and Backfill
- Status: **RESOLVED**
- Files: `backend/migrations/002_backfill_state_history.py`, `tools/backfill_state_history.py`, `backend/db.py`, `backend/engine/lifecycle.py`, `backend/engine/reconciliation.py`, `backend/seed_data.py`, `backend/api.py`, `tests/test_history_recorded.py`
- Resolution:
  1. Found and routed all direct decision state mutations through `lifecycle.transition`:
     - In `backend/db.py`: `save_decision` validates state changes against `ALLOWED_TRANSITIONS` (raises `InvalidTransition`), records initial history for new decisions (`from_state = NULL`), and records transition history with actor, reason, and timestamp.
     - In `backend/engine/reconciliation.py`: supersession links route through `lifecycle.transition(conn, older_id, 'superseded', ...)`.
     - In `backend/seed_data.py`: `dec_cache_local_lru_proposed` undergoes explicit lifecycle progression `proposed -> accepted -> superseded` via `lifecycle.transition`.
     - In `backend/api.py`: review queue triage and decision corrections route state changes through `lifecycle.transition`.
  2. Implemented Migration 002 (`backend/migrations/002_backfill_state_history.py`):
     - Adds `from_state TEXT` and `reconstructed INTEGER DEFAULT 0` columns to `state_history` if missing.
     - Backfills one audit record per decision lacking history with `notes="reconstructed from current state at backfill"`, `changed_by="system:backfill"`, `changed_at=decision.made_at`, `from_state=NULL`, and `reconstructed=1`.
     - Applied Migration 002 to active `context_intelligence.db`, populating previously empty `state_history` (0 -> 6 records).
  3. Created CLI tool `tools/backfill_state_history.py` supporting `--db PATH` and `--dry-run` with before/after count reporting.
  4. Created `tests/test_history_recorded.py`:
     - Verifies fresh seeded DB has `SELECT COUNT(*) FROM state_history >= COUNT(*) FROM decisions`.
     - Verifies review action increases history count.
     - Verifies backfill tool on legacy DB copy (`backups/context_intelligence.pre_v2.db`).
     - Verifies `save_decision` lifecycle transition enforcement and initial audit recording.
     - Verifies migration 002 idempotency.
  5. Verification: All 5 tests in `test_history_recorded.py` pass; full test suite (85 tests) and demo checks (21/21) pass.

### Step 2.4 — Review Workflow for Lifecycle
- Status: **RESOLVED**
- Files: `backend/api.py`, `backend/security.py`, `server.py`, `tests/test_review_actions.py`
- Resolution:
  1. Extended `/api/review-action` with full lifecycle transition integration:
     - Supported actions: `confirm`, `reject`, `merge`, `correct`, `reopen`, `mark_tested`.
     - `mark_tested` advances proposed decision to `tested` via `lifecycle.transition`.
     - `confirm` advances proposed/tested decision to `accepted` via `lifecycle.transition`, updates `review_status = 'human_confirmed'`, and sets `confidence = 1.0`. If already accepted, records a review triage history entry.
     - `reject` advances proposed/tested decision to `rejected` via `lifecycle.transition`, updating `review_status = 'human_rejected'`.
     - `reopen` advances rejected or accepted decision to `reopened` via `lifecycle.transition`.
     - `merge` merges target decision into `into_decision_id`, superseding it via `lifecycle.transition`.
     - `correct` allows human correction of state, title, and rationale with audit history logging.
  2. Implemented reviewer identity resolution:
     - Added `get_authenticated_role(headers, client_ip)` in `backend/security.py` returning `admin`, `reviewer`, or `viewer`.
     - Formats actor as `token_role:display_name` (e.g., `reviewer:Alice`) when display name or reviewer name is supplied.
  3. Enforced reason requirements:
     - `reopen` and `mark_tested` strictly require a non-empty reason; missing returns HTTP 400.
     - Invalid lifecycle transitions (e.g. attempting to reopen a terminal superseded decision or illegal state jumps) raise `InvalidTransition` and return HTTP 409 with readable message.
  4. Created `tests/test_review_actions.py` (10 tests covering all 6 actions, history row generation, reason requirement, 409 on invalid transitions, merge supersession, and reviewer identity resolution).
  5. Verification: All 10 tests in `test_review_actions.py` pass; full test discovery suite (95 tests) and demo checks (21/21) pass.

### Step 2.5 — Lifecycle UI and Audit View
- Status: **RESOLVED**
- Files: `backend/api.py`, `web/index.html`, `web/app.js`, `web/style.css`, `docs/index.html`, `docs/app.js`, `docs/style.css`, `tests/test_decision_history_api.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Added `GET /api/decision-history` route with `viewer` authorization:
     - With `decision_id`: retrieves decision metadata, full chronological state `transitions` (with `from_state`, `to_state`, `changed_at`, `changed_by`, `notes`, `reconstructed` boolean), and `supersession_chain` (preceding ancestors, current node, succeeding descendants). Returns HTTP 404 if decision is not found.
     - Without `decision_id`: retrieves global `audit_log` across all decisions, supporting query parameters `actor` (case-insensitive substring filter) and `date` (ISO date prefix filter), with total record counts and provenance flags.
  2. Implemented Lifecycle & Audit UI in Decision Explorer:
     - Added "Lifecycle & Audit" facet tab toggle and direct "Lifecycle ↻" inspection buttons on decision cards.
     - Added Decision History inspector dropdown (`#lifecycle-decision-select`) and decision summary card.
     - Implemented vertical **Transition Timeline** displaying each state mutation, state change pills (`from_state` → `to_state`), timestamp, actor, notes, and `Reconstructed`/`Observed` provenance badge.
     - Implemented **Supersession Chain** panel visualizing preceding decisions (`supersedes`), current decision, and succeeding decisions (`superseded_by`) with interactive navigation.
     - Implemented filterable **Global Audit Log** table supporting live actor search and date filtering.
     - Protected all dynamic text rendering with `esc()` and URL schemes with `safeUrl()`, verified clean by `tests/test_frontend_escape.py`. Synchronized all updates from `web/` to `docs/`.
  3. Acceptance verification: For seeded superseded decision `dec_cache_local_lru_proposed`, endpoint and UI demonstrate full chronological sequence: `proposed → accepted → superseded` with actors `marcus_vance` and `priya_patel`, recorded rationales, and supersession pointer to `dec_cache_redis_accepted`.
  4. Created `tests/test_decision_history_api.py` (6 tests covering seeded superseded decision history, supersession chain traversal, 404 on nonexistent decision, global audit log, actor filtering, and date filtering).
  5. Verification: All 6 tests in `test_decision_history_api.py` pass; full test discovery suite (101 tests) and demo runner (21/21 checks) pass.

### Step 2.6 — Historical "As Of" Queries and Counterfactual Explorer
- Status: **RESOLVED**
- Files: `backend/engine/as_of.py`, `backend/engine/graph.py`, `backend/api.py`, `web/index.html`, `web/app.js`, `web/style.css`, `docs/index.html`, `docs/app.js`, `docs/style.css`, `tests/test_as_of.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Implemented historical belief engine `as_of(db, repo, cutoff, artifact)` in `backend/engine/as_of.py`:
     - Timezone-aware cutoff parsing supporting ISO-8601 timestamps and date strings (`YYYY-MM-DD` normalized to end-of-day UTC).
     - Decisions filtered by `made_at <= cutoff` with state as of cutoff reconstructed strictly from `state_history` (latest transition `<= cutoff`, never current state). Flagged `has_reconstructed_history_only` if all history prior to cutoff is backfilled/reconstructed.
     - Graph edges filtered by `valid_from <= cutoff` and (`valid_to IS NULL` or `valid_to > cutoff`).
     - Evidence partitioned into `evidence` (`timestamp <= cutoff`) and `later_evidence` (`timestamp > cutoff`).
     - Non-speculative counterfactual rules: documented alternatives show recorded reasons; untried alternatives state `"no recorded outcome — consequences of the untried alternative are unknown."`.
     - `changed_afterwards` lists subsequent state transitions, supersessions, and new decisions on the same entities.
     - Optional `artifact` parameter filters decisions and entity associations.
  2. Implemented `get_edges_as_of(cutoff)` in `TemporalGraph` (`backend/engine/graph.py`).
  3. Added `GET /api/as-of` endpoint with `ROLE_VIEWER` authorization in `backend/api.py`.
  4. Implemented interactive UI in `web/index.html`, `web/app.js`, `web/style.css` (mirrored to `docs/`):
     - Added Historical "As Of" Query card with date picker, artifact filter, quick prompt chips, grounded belief banner, and 3-column breakdown.
  5. Created `tests/test_as_of.py` (9 tests covering empty before decision, query on 1 March never showing 15 March, supersession on 5 March vs 12 March, later evidence segregation, reconstructed history flag, counterfactual rules, edge validity ranges, API error handling, and artifact filtering).
  6. Verification: 9/9 tests in `test_as_of.py` pass; full suite (110 tests) and demo runner (21/21 checks) pass.

### Step 2.7 — Fresh-Database Lifecycle Proof
- Status: **RESOLVED**
- Files: `tools/verify_lifecycle_fresh_db.py`, `tests/test_lifecycle.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Created standalone CLI proof script `tools/verify_lifecycle_fresh_db.py`:
     - Creates isolated temp DB and initializes schema with migrations 001 and 002 applied.
     - Seeds baseline demo repositories.
     - Ingests test entities and evidence events.
     - Executes strict scripted progression:
       * create -> proposed (recorded in state_history as initial state)
       * proposed -> tested with evidence (automated load testing in CI)
       * tested -> accepted (architectural sign-off)
       * accepted -> superseded (by streaming pipeline decision with pointer)
       * attempted reopening of superseded decision strictly rejected (raises `InvalidTransition`).
     - Prints structured audit log containing all 4 transition records with actors, notes, and timestamps.
     - Exits non-zero on any deviation from expected states or invariant checks.
  2. Added subprocess verification test `test_fresh_db_lifecycle_proof_script` in `tests/test_lifecycle.py`.
  3. Verification: `tools/verify_lifecycle_fresh_db.py` executes with exit code 0; test suite (111 tests) and demo checks (21/21) pass.

---

## Phase 2 Exit Check
- Fresh DB records history: **PASS** (proven via migration 002, `test_history_recorded.py`, and `tools/verify_lifecycle_fresh_db.py`).
- All state changes pass lifecycle engine: **PASS** (proven via `backend/engine/lifecycle.py`, `ALLOWED_TRANSITIONS`, `InvalidTransition` enforcement in `backend/db.py` and `/api/review-action`).
- Migrations tested on DB copy: **PASS** (proven via migration tests against `backups/context_intelligence.pre_v2.db`).
- As-of queries correct on boundary dates: **PASS** (proven via `backend/engine/as_of.py` and `tests/test_as_of.py`).
- Git Tag: `phase2-done`

---

## PHASE 3 — Strengthen Evidence and Rejection Memory

### Step 3.1 — Claim-Level Evidence and Independence
- Status: **RESOLVED**
- Files: `backend/migrations/003_claim_evidence_independence.py`, `backend/models.py`, `backend/engine/independence.py`, `backend/db.py`, `tests/test_independence.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Additive Database Migration (`003_claim_evidence_independence.py`):
     - Created `decision_claims` table with `claim_id TEXT PRIMARY KEY`, `decision_id TEXT NOT NULL`, `claim_type TEXT NOT NULL CHECK (claim_type IN ('rationale', 'alternative_rejected', 'outcome', 'constraint'))`, and `text TEXT NOT NULL`, cascading on decision deletion.
     - Created `claim_evidence` table with `(claim_id, event_id)` composite primary key, `relation TEXT NOT NULL CHECK (relation IN ('direct', 'indirect', 'contradicting'))`, `passage_text TEXT`, `passage_start INTEGER`, `passage_end INTEGER`, and `source_group TEXT NOT NULL`.
     - Built indexes on `decision_claims(decision_id)`, `claim_evidence(event_id)`, and `claim_evidence(source_group)`.
     - Includes automatic backfill of claims and claim evidence for existing decisions during migration upgrade.
  2. Data Models (`backend/models.py`):
     - Added `DecisionClaim` and `ClaimEvidence` dataclasses with `validate()` methods asserting allowed claim types (`ALLOWED_CLAIM_TYPES`) and relations (`ALLOWED_CLAIM_RELATIONS`).
  3. Source Independence Engine (`backend/engine/independence.py`):
     - Implemented pure function `independence_key(event, all_events=None) -> str`:
       * Same issue/PR thread (issue, PR, review comments, issue comments) -> `thread:<repo>#<number>`
       * Commit and the PR containing it -> `thread:<repo>#<number>` (else `commit:<sha>`)
       * ADR/doc file -> `doc:<repo>:<path>` (revisions map to same group)
       * Slack -> `slack:<repo>:<channel>#<thread_ts>`
       * Duplicate copy/quote (identical normalized body or >80% token overlap with an existing event) -> maps to original event's source group
       * Author identity does not split source groups; different threads/documents do.
     - Implemented `extract_best_passage(claim_text, event_text, threshold=0.25)`:
       * Extracts candidate sentences with exact character offsets (`event_text[start:end] == passage_text`).
       * Content-word overlap scoring excluding English stopwords.
       * If score >= threshold: checks for contradiction cues ("rejected", "bottlenecks", "failed", etc.); returns exact passage text, offsets, and `direct` or `contradicting` relation.
       * If score < threshold: returns `(None, None, None, 'indirect')`.
     - Implemented claim extraction (`extract_claims_from_decision`) and independent source counting (`calculate_independent_sources`, `get_independent_source_count`).
  4. Database Layer Integration (`backend/db.py`):
     - Added `save_claim`, `get_claims_for_decision`, `save_claim_evidence`, `get_claim_evidence`, and `get_all_claim_evidence_for_decision`.
     - Hooked automatic claim and evidence synchronization into `save_decision`.
  5. Acceptance & Verification:
     - Verified: 5 comments in one PR thread count as **1** independent source (`thread:acme/backend#42`).
     - Verified: ADR plus a separate PR discussion count as **2** independent sources.
     - Verified: Commit belonging to a PR plus the PR count as **1** independent source.
     - Verified: Duplicate copy (>80% token overlap) maps to original event's group (**1** independent source).
     - Verified: Passage extraction exact character offsets equality and contradiction cue detection.
     - Verified: Schema migration 003 applied cleanly to active `context_intelligence.db`.
     - Verified: `tests/test_independence.py` (9 tests pass); full test discovery suite (120 tests pass); demo runner (21/21 checks pass).

### Step 3.2 — Evidence Assessment and Abstention
- Status: **RESOLVED**
- Files: `backend/engine/evidence.py`, `backend/engine/explanation.py`, `backend/api.py`, `backend/db.py`, `backend/evaluation/METRICS.md`, `METRICS.md`, `web/app.js`, `docs/app.js`, `tests/test_assessment.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Evidence Assessment Engine (`backend/engine/evidence.py`):
     - Implemented deterministic assessment function `assess(decision, db=None, all_events=None, claim_evidences=None)`:
       * `contradicted`: at least one `contradicting` relation from an active source (not superseded).
       * `strong`: $\ge 2$ independent source groups with direct support ($\ge 2$ direct groups).
       * `moderate`: 1 direct group plus $\ge 1$ other group (any relation, e.g. 1 direct + 1 indirect), OR $\ge 2$ independent indirect groups.
       * `weak`: exactly 1 source group (e.g. 1 direct source without independent corroboration, or a single thread with multiple comments/copies).
       * `insufficient`: no evidence, or only 1 indirect group.
     - Generated human-readable `missing_corroboration` notes (e.g. "no independent source besides the ADR", "no outcome/test evidence linked", "no direct passage evidence supporting claims").
     - Generated structured `conflicting_evidence` listing contradicting passages and related decisions on the same entities.
     - Documented the rule and explicit design choice statement in code comments, `backend/evaluation/METRICS.md`, and root `METRICS.md`.
  2. Database Layer Integration (`backend/db.py`):
     - Automatically recomputes assessment and persists label in `decisions.evidence_assessment` inside `_sync_decision_claims`.
     - Added `recompute_evidence_assessment(decision_id)` method.
  3. Review Routing (`backend/api.py`):
     - Route `/api/review-queue` automatically includes decisions with `evidence_assessment IN ('weak', 'insufficient', 'contradicted')` and `review_status NOT IN ('human_rejected', 'human_confirmed')` with descriptive queue reasons.
  4. Abstention (`backend/engine/explanation.py` & `backend/api.py`):
     - `/api/explain` and `ExplanationGenerator.explain_artifact` / `explain_decision` return `{ "status": "insufficient_evidence", "message": "..." }` when the governing decision has `evidence_assessment == "insufficient"` and no stronger source exists.
  5. UI Confidence Label Calibration Renaming (`web/app.js`, `docs/app.js`):
     - Display `evidence_assessment` as primary status indicator pill.
     - Renamed legacy confidence badge to **"Heuristic score (uncalibrated): X%"** across Decision Explorer cards and Lifecycle inspector summary card.
  6. Acceptance & Verification:
     - Verified: a decision with a single copied source (>80% token overlap) collapses to 1 source group and is labelled `weak`, NEVER `strong`.
     - Verified: contradicted decision is assessed as `contradicted`.
     - Verified: abstention triggers on insufficient evidence for artifact and decision explanations.
     - Verified: review queue routes `weak`, `insufficient`, and `contradicted` items.
     - Verified: `tests/test_assessment.py` (10 tests pass); full test discovery suite (130 tests pass); demo runner (21/21 checks pass).

### Step 3.3 — Evidence-Aware Explanation Output
- Status: **RESOLVED**
- Files: `backend/engine/explanation.py`, `backend/api.py`, `web/app.js`, `docs/app.js`, `web/static_data.js`, `docs/static_data.js`, `tests/test_explanation.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Explanation Payload Structure (`backend/engine/explanation.py`):
     - Implemented `build_decision_evidence_block(db, dec)` returning:
       * `decision`: `{ decision_id, title, rationale, made_by, made_at, repo }`
       * `lifecycle_state`: current decision state string
       * `needs_review`: boolean flag derived from `pending_review` status, low extraction confidence, or assessment in `('weak', 'insufficient', 'contradicted')`
       * `evidence_assessment`: `{ label: assess_label }`
       * `direct_support`: list of direct evidence items with passage extractions
       * `indirect_support`: list of indirect evidence items
       * `missing_corroboration`: list of corroboration gaps
       * `conflicting_evidence`: list of conflicting evidence items
     - Per evidence item fields:
       * `source_link`: source URL string
       * `url_format_ok`: boolean format check (starts with http/https), decoupled from evidentiary correctness
       * `relevant_passage`: exact passage text quote from source event
       * `author`: event author identity
       * `date`: ISO timestamp
       * `relation`: `direct` or `indirect`
       * `source_group`: canonical independence group key
  2. Sentence-Level Support Check (`backend/engine/explanation.py`):
     - Implemented `verify_sentence_support(text, evidence_items)`:
       * Splits explanation text into distinct sentences.
       * Tokenizes content words (length > 3, stop-words removed) per `METRICS.md` Section 6.
       * Compares sentence content tokens against evidence passages and event titles.
       * Sentence is marked supported if $\ge 50\%$ content words appear in evidence.
       * Flags unsupported sentences (`flagged_unsupported: True`) and returns `(statements, unsupported_sentences, claim_support_rate)`.
  3. API Endpoints (`backend/api.py`):
     - `/api/explain`: returns Step 3.3 payload including sentence support verification, statements, unsupported sentences, claim support rate, and abstention on insufficient evidence.
     - `/api/evidence`: updated to return `lifecycle_state`, `needs_review`, `evidence_assessment`, `direct_support`, `indirect_support`, `missing_corroboration`, and `conflicting_evidence` alongside raw events.
  4. Frontend Evidence Panel & Explanation View (`web/app.js`, `docs/app.js`):
     - Evidence panel renders decision context, lifecycle state badge, evidence assessment pill, needs-review alert, direct support cards with highlighted relevant passage blockquotes, indirect support cards, and warnings for missing corroboration or conflicting evidence.
     - Explanation view renders sentence support rate and flags unsupported sentences if any.
     - Renamed legacy "Evidence Link Validity" metric label to **"URL Format OK (Format Only)"** with tooltip clarifying format check only.
     - Regenerated static snapshot via `tools/build_static.py`.
  5. Acceptance & Verification:
     - Verified: every statement links to a passage; unsupported sentences are flagged with `flagged_unsupported: True` and collected in `unsupported_sentences`.
     - Verified: `tests/test_explanation.py` (8 tests pass); full test discovery suite (138 tests pass); demo runner (21/21 checks pass).

### Step 3.4 (P1-a) — Decision-Specific Constraints & General Drift Detector
- Status: **RESOLVED**
- Files: `backend/migrations/004_decision_constraints.py`, `backend/models.py`, `backend/db.py`, `backend/engine/drift_detector.py`, `backend/engine/guard_rules.py`, `backend/seed_data.py`, `tests/test_guard_rules.py`, `tests/test_drift_rules.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Additive Migration 004 & Data Model:
     - Created `backend/migrations/004_decision_constraints.py` adding `polarity` (`must` | `must_not`), `applies_to` (JSON array of entity IDs or path globs), and `source` (`human` | `proposed`) to `guard_rules`.
     - Created `decision_constraints` view referencing `guard_rules` with alias `DecisionConstraint = GuardRule`.
     - Backfilled `polarity`, `applies_to`, and `source` from rule params.
     - Added `get_decision_evidence_passages` to `backend/db.py`.
  2. Pure Constraint-Driven Evaluation (0 Domain Keywords):
     - Completely removed hard-coded scenario branches (`redis`, `pid`, `hysteresis`) from `backend/engine/drift_detector.py`. Grep test asserts 0 domain keywords remain in source code.
     - Implemented `parse_diff` with hunk headers, line numbers, added/removed line separation, and comment classification (`is_pure_comment`, `is_historical`).
     - Query touched entities and active human-approved constraints overlapping touched entities/paths.
     - Evaluated active rules against added lines (and removed lines for `require_*`), properly handling historical notes (`is_historical` e.g. decommissioned/deprecated notes) as clean changes.
  3. Structured Findings with Passages and Signal Strength:
     - Findings emitted with `status: "potential_violation"`, `rule_id`, `decision_id`, `file`, `line_number`, `offending_line`, `violating_diff_snippet`, `evidence_passages` (with URLs), `signal_strength` (`high` | `medium` | `low`), `confidence: 0.0`, `calibrated: false`, `reviewed: false`, and `drift_type: "drift"`.
  4. Benchmark & Fixture Validation:
     - Seeded active pilot constraints and test fixtures.
     - `drift_cases.json` 20-case suite re-evaluated: **100.0% precision, 100.0% recall** (10 True Positives, 10 True Negatives, 0 False Positives, 0 False Negatives).
     - Verified: `tests/test_drift_rules.py` (4 tests pass covering grep keyword check, 7 positive diffs, 11 negative diffs with near-misses, and full `drift_cases.json` suite); full test discovery suite (142 tests pass); demo runner (21/21 checks pass).

### Step 3.5 — Rejected-Idea Guard (Headline Novelty)
- Status: **RESOLVED**
- Files: `backend/migrations/005_finding_feedback.py`, `backend/db.py`, `backend/engine/rejected_idea_guard.py`, `backend/api.py`, `tools/ci_check.py`, `tests/test_rejected_idea_guard.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Additive Migration 005 & Data Model:
     - Created `backend/migrations/005_finding_feedback.py` implementing `finding_feedback` table:
       `feedback_id`, `finding_id`, `finding_type`, `action`, `reason`, `actor`, `pr_id`, `decision_id`, `created_at`.
     - Added helper methods in `backend/db.py`: `record_finding_feedback`, `is_finding_dismissed`, `get_finding_feedback`, `get_decision`, `get_all_decisions`.
  2. Rejected-Idea Guard Engine (`backend/engine/rejected_idea_guard.py`):
     - Design extraction: deterministic parser extracting added imports/dependencies, function calls/definitions, variable assignments, config keys, and tokens from proposal text and diffs. Filters out historical decommissioning documentation comments (`decommissioned`, `deprecated`, `replaced by`, `superseded`) from active code analysis.
     - Candidate retrieval: retrieves all rejected decisions and rejected alternatives, including candidate rationale and evidence passages.
     - Substance comparison on 4 signals:
       * (a) Entity / path overlap: resolves entity IDs to canonical file paths via database `entities` table.
       * (b) Signature / guard-rule match: checks active decision constraints (`forbid_import`, `forbid_pattern`) and concept signatures across code lines and identifiers.
       * (c) Dependency / library match: compares proposal added imports against candidate rejection rationale and library references.
       * (d) Text similarity: pure Python standard library TF-IDF cosine similarity (`compute_tfidf_cosine`).
     - Explicit Tiers:
       * `strong`: $\ge 2$ independent signals including a structural/substance match (e.g. entity overlap + code signature match).
       * `possible`: 1 structural code signature / dependency match, or high text similarity ($\ge 0.55$), or entity overlap with moderate text similarity ($\ge 0.20$).
       * No finding for keyword coincidence alone or file touch without substance.
     - Advisory findings (`advisory: true`): never auto-blocks. Generates PR review notice ("Possible reintroduction of a previously rejected approach — please review").
     - Changed-circumstances hints: time elapsed since decision, later related decisions modifying overlapping components, and reopened status reminders.
     - Developer feedback loop: `confirm`, `dismiss` (persists for PR + decision, suppressing duplicate alerts on subsequent runs), and `reopen_decision` (transitions decision `rejected -> reopened` via reconciled lifecycle engine with PR evidence).
  3. Integration:
     - `tools/ci_check.py`: integrated rejected-idea guard check; default invocation exits code 0 on advisory findings; `--strict` flag blocks with exit code 1 if advisories are present.
     - `backend/api.py`: hooked guard into `/api/drift-check`, `handle_webhook` (posts advisory comments to PRs), and `POST /api/findings/feedback`.
  4. Acceptance & Verification:
     - Verified: `tests/test_rejected_idea_guard.py` (6 tests pass covering $\ge 5$ true matches including paraphrased proposal, $\ge 8$ non-matches, reopen flow changing advisory message, dismiss persistence, never blocks assertion, and CI check `--strict` flag).
     - Full test discovery suite: **148 tests passing** (0 failures, 0 errors).
     - Demo runner: **21/21 checks passing**.


### Step 3.6 (P1-g) — Developer Feedback Loop & Review Routing
- Status: **RESOLVED**
- Files: `backend/db.py`, `backend/engine/rejected_idea_guard.py`, `backend/api.py`, `backend/evaluation/benchmark.py`, `web/app.js`, `docs/app.js`, `tests/test_feedback.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Feedback Persistence & Measured Feedback Counts (`backend/db.py`, `backend/api.py`):
     - Implemented `ambiguous_findings` table tracking ambiguous findings (`finding_id`, `source`, `item_type`, `decision_id`, `pr_id`, `tier`, `queue_reason`, `status`, `actor`, `created_at`, `resolved_at`).
     - Added `get_finding_feedback_counts()` returning distinct counts for `confirm`, `dismiss`, `reopen`, and `total`.
     - Added `record_ambiguous_finding()`, `resolve_ambiguous_finding()`, and `get_pending_ambiguous_findings()`.
     - Added `GET /api/findings/feedback` returning measured feedback history and aggregate action counts (authenticated viewer/reviewer).
     - Connected measured feedback counts into `GET /api/stats` and `GET /api/benchmark`.
  2. Review Routing for Ambiguous Findings (`backend/api.py`, `backend/engine/rejected_idea_guard.py`):
     - Updated `evaluate_proposal` in `RejectedIdeaGuard` to automatically route `tier == "possible"` findings to `ambiguous_findings` with explicit `queue_reason` ("Ambiguous finding ('possible' tier) requires reviewer triage").
     - Updated `GET /api/review-queue` to combine:
       * `decision` items requiring review (`needs_review == 1` or evidence assessment in `weak`, `insufficient`, `contradicted`).
       * `supersession_candidate` edges with explicit ambiguous candidate reasons.
       * `possible_rejected_idea` findings awaiting reviewer triage.
     - Updated `POST /api/review-action` and `POST /api/findings/feedback` to support resolving ambiguous findings, transitioning their status and updating the review queue dynamically.
  3. UI Integration (`web/app.js`, `docs/app.js`):
     - Added Developer Feedback panel card displaying measured feedback counts (Total feedback, Confirmed, Dismissed, Reopened) under benchmark metrics.
     - Regenerated static bundle with `tools/build_static.py`.
  4. Acceptance & Verification:
     - Auth boundary: `POST /api/findings/feedback` requires reviewer role (viewer returns 403, unauthenticated returns 401).
     - Action persistence: `confirm` and `dismiss` persist to SQLite; dismissing suppresses subsequent checks on the same PR + decision while remaining active on other PRs.
     - Decision reopen: transitions `rejected -> reopened`, logs state history, and changes subsequent advisory behavior.
     - Review queue: all ambiguous categories (`possible` tier, supersession candidates, weak/insufficient evidence) routed with human-readable reasons; resolution purges item from pending queue.
     - Measured data: feedback counts verified non-zero and consistent across `/api/findings/feedback`, `/api/stats`, and `/api/benchmark`.
     - Verified: `tests/test_feedback.py` (6 tests pass). Full test discovery suite: **154 tests passing**. Demo runner: **21/21 checks passing**.
     - Tagged `phase3-done`.


### Step 4.1 — Audit the Matching Protocol
- Status: **RESOLVED**
- Files: `backend/evaluation/benchmark.py`, `backend/evaluation/ground_truth.py`, `tools/run_whybench.py`, `METRICS.md`, `tests/test_benchmark.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Strict One-to-One Bipartite Matching (`backend/evaluation/benchmark.py`):
     - Implemented `compute_decision_matching(gt_dataset, system_decisions, decision_to_evidence)`:
       * Builds candidate bipartite edges between GT items and system decisions sharing $\ge 1$ evidence event ID.
       * Greedily assigns candidate edges in descending order of shared evidence overlap count (secondary tie-breaker: state match).
       * Enforces strict mutual exclusion: each GT item is matched at most once, and each system decision is matched at most once.
       * Unmatched system decisions count against precision and are tracked in `unmatched_system_ids` and `unmatched_system_decisions`.
  2. Lenient Matching Comparison & Overcounting Exposure:
     - Simultaneously computes lenient (many-to-one) matching where a single system decision can satisfy multiple GT items.
     - Reports `decision_recall_strict`, `decision_recall_lenient`, and `recall_difference` to expose previous overcounting gaps.
  3. Evidence Integrity Metrics:
     - Replaced weak legacy "evidence-link validity" with three explicit checks:
       * `url_format_ok`: percentage of links where `source_url` starts with `http://` or `https://` (format check only, never described as correctness or accuracy).
       * `event_exists`: percentage of decision evidence links whose `event_id` exists in the database `events` table.
       * `claim_supported`: sentence-level support verification rate (anti-hallucination).
       * Retained `evidence_link_accuracy` as alias pointing to `url_format_ok` for backward compatibility.
  4. WhyBench Evaluation Protocol Alignment (`tools/run_whybench.py`):
     - Integrated `compute_decision_matching` for standard questions.
     - Reports both strict and lenient decision recall and state accuracy.
  5. Acceptance & Verification:
     - Added 4 unit tests to `tests/test_benchmark.py`:
       * `test_one_to_one_matching_cannot_satisfy_two_labels_in_strict_mode`: Proves that 1 system decision cannot satisfy 2 labels in strict mode (strict recall = 50.0%, lenient recall = 100.0%, overcounting gap = +50.0%).
       * `test_greedy_descending_overlap_bipartite_assignment`: Proves optimal greedy assignment by descending overlap.
       * `test_unmatched_system_decisions_tracked`: Proves unlinked decisions count against precision.
       * `test_evidence_link_replacement_metrics`: Proves `url_format_ok`, `event_exists`, `claim_supported`.
     - Full test discovery suite: **158 tests passing** (0 failures, 0 errors).
     - Demo runner: **21/21 checks passing**.


### Step 4.2 — Compare Equivalent Tasks Only
- Status: **RESOLVED**
- Files: `backend/evaluation/baselines.py`, `tools/run_whybench.py`, `evaluation_results.md`, `METRICS.md`, `tests/test_benchmark.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Formal Split Benchmark Task Definitions (`METRICS.md` Section 10):
     - **Task 1 — Evidence Retrieval** ("Find the sources that explain X"):
       * Input: Natural language query string + repository identifier.
       * Systems evaluated: Comparable across CIF and search baselines (Baseline A: Keyword/BM25 token overlap, Baseline B: Documentation/ADR search).
       * Metric: Top-$k$ ($k=5$) evidence event hit rate.
       * Refusal: Unconditional top-$k$ search baselines have no abstention mechanism and are scored `n/a (always answers)` rather than a false 0.0%. CIF can abstain.
     - **Task 2 — Decision Reconstruction** (Lifecycle State, Rationale, Alternatives, Supersession):
       * Input: Full raw repository event history and git diffs.
       * Systems evaluated: CIF (reconciled lifecycle state machine, structured candidate extraction, context graph) vs Baselines C & D (LLM / Copilot) when configured.
       * Metrics: Strict one-to-one decision recall, decision state accuracy, grounded rationale & alternatives, and refusal accuracy.
       * Non-reconstructing baselines (A & B) cannot extract decisions, states, or alternatives, and are explicitly marked `n/a` across all Task 2 columns rather than misleadingly scored as 0.0%.
  2. Baseline Evaluator Separation (`backend/evaluation/baselines.py`):
     - Updated `run_baseline_keyword` and `run_baseline_docs_only` to compute `task_1_hit_rate` (measured) while marking `task_2_decision_recall`, `task_2_state_accuracy` as `n/a`, and `task_2_refusal_accuracy` as `n/a (always answers)`.
  3. WhyBench Runner Reporting (`tools/run_whybench.py`):
     - Added CIF Task 1 hit rate calculation.
     - Structured summary JSON and terminal output to report Task 1 (Evidence Retrieval) and Task 2 (Decision Reconstruction) in distinct tables.
  4. Evaluation Results Documentation (`evaluation_results.md` Section 1.1):
     - Split final test split results into separate tables for Task 1 and Task 2.
     - Documented honest task analysis explaining why unlike tasks were previously conflated and why the two tasks are now separated.
  5. Acceptance & Verification:
     - Added `test_task_split_equivalent_tasks_reporting` to `tests/test_benchmark.py`: validates that Baseline A and B measure Task 1 hit rate while marking Task 2 metrics as `n/a` and refusal as `n/a (always answers)`.
     - `tests/test_benchmark.py`: **9/9 tests passing**. Full test discovery suite: **159 tests passing**. Demo runner: **21/21 checks passing**.


### Step 4.3 — Failure Analysis Tool
- Status: **RESOLVED**
- Files: `tools/analyze_failures.py`, `tests/test_failure_analysis.py`, `docs/dev_failure_analysis.md`, `results/dev_failure_analysis.json`, `STATUS_AUDIT.md`
- Resolution:
  1. Failure Classifier (`tools/analyze_failures.py`):
     - Implemented strict priority ordering classifier for missed ground-truth items:
       (1) `not_ingested`: Expected evidence event ID(s) absent from DB `events` table.
       (2) `filtered`: Event present in DB, but removed by noise or trivial pre-filter (`is_decision_candidate`).
       (3) `wrong_evidence`: Decision exists in repository for overlapping topic/entity, but cites different evidence event IDs.
       (4) `no_candidate`: Event present in DB, but extractor produced 0 candidate decisions from its bundle.
       (5) `wrong_state`: Found candidate sharing evidence, but system state differs from expected state.
  2. False Positive Accounting:
     - Tracks unlinked decisions in the database and decisions extracted for negative refusal cases (`expected_state == 'unresolved'`).
  3. Reporting & Diagnostics:
     - Outputs executive summary table, per-repository breakdown, itemized failure reasons, and false positive decisions in both JSON (`results/dev_failure_analysis.json`) and Markdown (`docs/dev_failure_analysis.md`).
     - Dev split execution results: 18 standard questions, 10 true positives (strict 1-to-1), 8 missed items:
       * `not_ingested`: 0
       * `no_candidate`: 3 (WB_PAY_03, WB_CH_06, WB_CLI_04)
       * `filtered`: 0
       * `wrong_evidence`: 5 (WB_PAY_02, WB_PAY_05, WB_CH_02, WB_CH_04, WB_CLI_02)
       * `wrong_state`: 0
  4. Acceptance & Verification:
     - Unit test suite: `tests/test_failure_analysis.py` (2 tests pass).
     - Spot-checked 5 missed items by hand, confirming exact categorization matching empirical DB state.
     - Full test discovery suite: **161 tests passing**. Demo runner: **21/21 checks passing**.


### Step 4.4 — Improve Recall from Analysis (Dev Split Only)
- Status: **RESOLVED**
- Files: `backend/engine/extractor.py`, `tools/sweep_thresholds.py`, `docs_changelog.md`, `tests/test_extractor.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Failure Category Remediation:
     - Prioritized error categories by count from Step 4.3: `wrong_evidence` (5 misses) and `no_candidate` (3 misses).
     - **Source Types**: Expanded `backend/engine/extractor.py` to support `git_commit` and `github_issue` in addition to `github_pr`, `pr_review_comment`, and `adr`.
     - **Rejection Cue Detection & Classification**: Introduced `REJECTION_PATTERNS` (`reject`, `rejected`, `must reject`, `cannot use`, `not viable`, `abandoned`). Rejection comments now extract decisions with `state="rejected"`, recording rejected proposals in `alternatives_considered` with `confidence=0.85` (`WB_PAY_03`, `WB_CH_02`, `WB_CLI_02`).
     - **Affirmative Architectural Intent Markers**: Broadened action cues (`implement`, `adopt`, `migrat*`, `switch to`, `enable`, `introduce`, `support`, `isolate`, `batch`, `pinning`, `feat:`, `refactor:`).
     - **Parent Event ID Grounding**: PR decisions closing issues now propagate `[ev.event_id] + list(ev.parent_event_ids)` into `evidence_event_ids`, grounding the decision across the PR and closed issue (`WB_PAY_02`, `WB_CH_06`, `WB_CLI_04`).
     - **Noise Filtering & False Positive Elimination**: Removed arbitrary fallback placeholder decision that generated empty citations (`evidence_event_ids=[]`), dropping false positives from 47 down to 22.
  2. Empirical Impact on Dev Split:
     - Strict Decision Recall: increased from 55.6% (10/18) to **100.0% (18/18)**.
     - Strict State Accuracy: maintained at **100.0% (18/18)**.
     - Task 1 Evidence Hit Rate: increased from 55.6% to **100.0% (18/18)**.
     - Refusal Accuracy: maintained at **100.0% (6/6)**.
     - Missed Questions: reduced from 8 to **0**.
  3. Threshold Sweep & Precision/Recall Curve:
     - Implemented `tools/sweep_thresholds.py` measuring precision, recall, and F1 across $\theta \in [0.50, 0.95]$:
       * $\theta \ge 0.50 - 0.85$: Recall = 100.0%, Precision = 46.2%, F1 = 63.2%.
       * $\theta \ge 0.90$: Recall = 55.6%, Precision = 62.5%, F1 = 58.8%.
       * $\theta \ge 0.95$: Recall = 50.0%, Precision = 60.0%, F1 = 54.5%.
  4. Acceptance & Verification:
     - Added 3 unit tests in `tests/test_extractor.py`:
       * `test_extractor_rejection_cues_from_pr_review`: Validates review rejection extraction with state="rejected".
       * `test_extractor_pr_and_commit_with_parent_events`: Validates PR and commit extraction with parent event grounding.
       * `test_extractor_filters_trivial_events`: Validates that non-decision events return empty extraction and do not invent dummy decisions.
     - Full test discovery suite: **164 tests passing** (0 failures, 0 errors).
     - Demo runner: **21/21 checks passing**.


### Step 4.5 — Human-Labelled Precision & Snapshot Hash Protection
- Status: **RESOLVED**
- Files: `tools/make_precision_sample.py`, `backend/evaluation/benchmark.py`, `tools/run_whybench.py`, `backend/evaluation/precision_labels.json`, `tests/test_precision_sampling.py`, `STATUS_AUDIT.md`
- Resolution:
  1. Hashed Snapshot Sampling (`tools/make_precision_sample.py`):
     - Implemented `make_precision_sample` sampling up to 40 decisions per repository (fixed random seed 1234) from a named SQLite snapshot.
     - Computes cryptographic SHA-256 hash of the snapshot database (`compute_db_sha256`).
     - Emits `precision_labels.json` template with required metadata per row:
       * `dataset_version`: string (e.g., `whybench_v1`)
       * `db_snapshot_sha256`: 64-character SHA-256 hex string
       * `repo`: repository name
       * `decision_id`: system decision identifier
       * `title`, `state`, `confidence`, `rationale`
       * `correct`: `null` (strictly preserved until human fills in `true` or `false`)
       * `note`: annotator comment field
  2. Snapshot Hash Invariant Enforcement (`backend/evaluation/benchmark.py` & `tools/run_whybench.py`):
     - Implemented `evaluate_precision_labels(db_path, labels_file_or_dir)`:
       * Computes runtime SHA-256 hash of the database currently evaluated.
       * Compares against the label file's `db_snapshot_sha256` (both file-level and per-row).
       * **Refuses to use labels** if the snapshot hash does not match, returning `"not measured"` with explicit reason citing the mismatch (`snapshot hash mismatch: labels generated from ..., current DB hash is ...`). This mechanically prevents stale-ID label errors.
       * If all rows have `correct: null`, returns `"not measured"` with reason `"awaiting human labels (H2: all items have correct=null)"`.
       * If valid human labels are present with matching hash, computes exact percentage: $\frac{\sum \text{correct == True}}{\text{total filled labels}}$.
  3. WhyBench Runner Integration:
     - `tools/run_whybench.py` evaluates and displays human precision under Task 2 metrics, reporting `"not measured"` with the reason string.
  4. Acceptance & Verification:
     - Added 5 unit tests in `tests/test_precision_sampling.py`:
       * `test_make_precision_sample_schema_and_per_row_metadata`: Verifies all required fields and correct=null per row.
       * `test_snapshot_hash_mismatch_refuses_labels_with_clear_reason`: Verifies refused evaluation on wrong hash.
       * `test_unfilled_labels_reports_not_measured_awaiting_human`: Verifies 'not measured' when awaiting human labels.
       * `test_valid_matching_labels_computes_exact_precision`: Verifies precision calculation on matching human labels.
       * `test_sampling_determinism_and_cap_per_repo`: Verifies seed 1234 determinism and 40-decision-per-repo cap.
     - Full test discovery suite: **169 tests passing** (0 failures, 0 errors).
     - Demo runner: **21/21 checks passing**.
