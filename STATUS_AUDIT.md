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
