# Review Queue — Fix Report

Branch `fix/review-queue-functionality` (based on `fix/windows-sqlite-cleanup`). Not pushed or merged.
Investigation details and the pre-fix measurements: [REVIEW_QUEUE_INVESTIGATION.md](REVIEW_QUEUE_INVESTIGATION.md).

## A. Root cause
Not a single bug — four independent defects on the button → API → database path, all of which
ended in the same symptom ("I click, it says success, nothing changes"):

1. **Wrong identifier from the frontend.** Every card used `item.decision_id || item.edge_id`.
   Drift items carry both ids and possible-rejected-idea items carry `finding_id` + `decision_id`, so the
   decision id was sent where the backend expected an edge id or finding id.
2. **Backend reported success for no-ops.** `/api/review-action` deleted `WHERE edge_id = <decision id>`
   (0 rows) and still answered "executed successfully"; `correct` on non-decision items and unknown item
   types also fell through to "success".
3. **Handled items were never removed.** *Correct* set `review_status='human_corrected'`, but the queue
   only hides `human_confirmed`/`human_rejected`. *Confirm* on a stale decision changed `review_status`,
   but stale items are selected by `freshness`.
4. **Correct dialog sent the wrong data.** State was always pre-selected as "accepted" (causing unintended
   lifecycle transitions) and the audit justification was sent as `rationale`, overwriting the decision's
   rationale.

Also found while tracing (security): edge and finding ids were authorized against the **demo**
repository, so a signed-in user could act on another repository's private conflict/drift edges.

## B. Files changed
| File | Why |
|---|---|
| `backend/api.py` | Queue items carry `target_id`; handled items hidden; review-action validates item type and existence, 400/404 instead of fake success, verdicts recorded, stale Confirm = revalidate |
| `backend/auth/repo_access.py` | `target_id` also resolved as an edge id or finding id (authorization against the correct repository) |
| `web/app.js` | Queue functions only: correct id, Correct only for decisions, in-flight locking, honest results, re-render from the server after success, fixed Correct dialog |
| `docs/app.js` | Mirror of `web/app.js` (GitHub Pages copy; `build_static.py` requires them identical) |
| `tests/test_review_queue_actions.py` (new) | 16 tests covering every item type × action, errors, persistence, authorization |
| `audit/REVIEW_QUEUE_INVESTIGATION.md`, this file (new) | Documentation |

Not changed: database schema, lifecycle rules, authentication, CSRF/Origin checks, rate limiting,
other dashboard surfaces, CSS, ingestion, extraction, evaluation.

## C. Frontend (how it works now)
1. `loadReviewQueue()` renders each card with `data-id = item.target_id` (fallback: the type-correct
   field for older servers) and `data-type = item.item_type`.
2. **Correct** is shown only for `decision` / `stale_decision` items — the only types the backend can
   correct. Conflict, drift, supersession and possible-rejected-idea cards show Confirm / Reject.
3. `triggerReviewAction()` asks for confirmation, disables the card's buttons, sends
   `{action, target_id, item_type}`, then:
   success → message, queue and stats re-loaded **from the API**; failure → "NOT saved (HTTP code):
   server message", buttons re-enabled, queue unchanged.
4. Correct dialog: current state pre-selected and marked "(current)"; only changed title/state are sent;
   the justification is sent as `reason`; the dialog closes only after the server confirms.
5. Requests still go through `apiFetch` (JSON content type, same-origin session cookie — the existing
   CSRF protection is unchanged).

## D. Backend
| Item type | Confirm | Reject | Correct |
|---|---|---|---|
| decision | proposed/tested → accepted; accepted → history row; `human_confirmed` | proposed/tested → rejected; accepted → **409** (lifecycle rule, unchanged) | title/state (via lifecycle) + reason in history; `human_corrected` → leaves queue |
| stale_decision | `revalidate` (freshness → revalidated) | as decision | as decision |
| conflict | edge **kept**, verdict `confirm` in `finding_feedback` | edge deleted, verdict `dismiss` | 400 |
| drift | edge kept, verdict `confirm` | edge deleted, verdict `dismiss` | 400 |
| supersession_candidate | older decision → superseded (existing logic) | edge deleted | 400 |
| possible_rejected_idea | finding `confirmed` (existing logic) | finding `dismissed` | 400 |
Unknown id → 404; unknown item type → 400. All writes happen in one connection and are committed;
errors roll back. The queue hides decisions with `human_corrected`/`human_merged` and edges that already
have a verdict in `finding_feedback`.

## E. Database evidence (browser clicks on a temp DB, checked with direct SQL)
| Click | Request (from the Network log) | HTTP | Result in DB / queue |
|---|---|---|---|
| drift → Confirm | `target_id=edge_drift_src/cach_dec_cach, item_type=drift` | 200 | verdict stored, edge kept, card gone |
| conflict → Reject | `target_id=edge_conflicts_with_…` | 200 | edge deleted, verdict stored, card gone |
| possible rejected idea → Confirm | `target_id=af_queue_test` | 200 | finding `confirmed`, card gone |
| supersession → Confirm | `target_id=edge_supersede_test` | 200 | older decision `superseded`, card gone |
| stale decision → Confirm | `item_type=stale_decision` | 200 | freshness `revalidated`, card gone |
| decision (accepted) → Reject | `target_id=dec_cache_redis_01` | 409 | nothing changed, "NOT saved" shown, card stays |
| decision → Confirm | same id | 200 | `human_confirmed`, card gone |
| decision → Correct | `title="Corrected in E2E", reason="title was wrong"` (no state, no rationale) | 200 | title changed; state and rationale unchanged; history `user:queue_tester — Correction applied: title was wrong` |
| guard rule → Approve | `rule_id=rule_forbid_pattern_…` | 200 | `proposed → active`, approved_by `user:queue_tester` |
| guard rule → Disable | `rule_id=rule_constraint_cache_redis_01` | 200 | `active → disabled` |
| Page reload | — | — | 6 items before and after reload; badge 6 |
No browser console errors.

## F. Test results (Linux, Python 3.13 — actual output)
| Suite | Result |
|---|---|
| New `tests/test_review_queue_actions.py` on the old code | 16/16 fail (5 failures, 11 errors) |
| New tests on the fix | 16/16 pass |
| Full suite before | 414 run, OK, 2 skipped |
| Full suite after | **430 run, OK, 2 skipped** |
| Full suite with `-X dev -W always::ResourceWarning` | 430 OK; **0** unclosed SQLite connections (Windows fix intact) |
| `run_demo.py`, `check_docs.py`, `check_eol.py`, `check_js.py` | pass (21/21, pass, OK, 20/20) |
| Regression of login/CSRF/rate-limit/authorization | covered by `test_http_security.py` (passes) |

## G. Remaining issues / not verified
- **Not run on Windows.** All new code closes its SQLite connections (`contextlib.closing`), uses
  `TemporaryDirectory` + `addCleanup` and no hard-coded paths; please run the suite on Windows 11 /
  Python 3.11 (the tests ran on Python 3.13).
- **Rejecting an accepted decision is refused (409) by design** — the lifecycle requires reopen or
  supersede first. The queue has no "reopen" button; adding one would be a new feature (not done).
- Reject on a stale decision follows the normal decision rules (usually 409 for accepted decisions).
- The same decision can appear twice (as `decision` and `stale_decision`) when it is both low-confidence
  and stale; handling one card does not remove the other. Pre-existing behaviour, left unchanged.
- Demo repositories can be reviewed by any signed-in user (documented design, unchanged).

## H. Demonstration checklist
1. `python tools/init_db.py --db demo_day.db --seed`, then start with `CIF_DB_PATH=demo_day.db`
   (PowerShell: `$env:CIF_DB_PATH="demo_day.db"; python server.py`). Register a user.
2. Open **Review Queue**; note the badge count.
3. Open browser DevTools → Network.
4. **Conflict → Reject**: request shows `item_type: conflict` and an `edge_…` id; HTTP 200; card disappears; badge −1.
5. **Drift → Confirm**: request shows the `edge_drift_…` id (not a decision id); card disappears.
6. **Decision → Correct**: dialog shows the current state; change the title, add a justification,
   Save; the card disappears; open **Decision Explorer** to see the new title.
7. **Accepted decision → Reject**: alert "NOT saved (HTTP 409)": the lifecycle protection working.
8. **Guard rule → Approve**: rule badge turns ACTIVE.
9. Press F5: everything stays as it was (persisted in SQLite).
10. Optional proof in a terminal:
    `python -c "import sqlite3;c=sqlite3.connect('demo_day.db');print(c.execute('select finding_id,finding_type,action,actor from finding_feedback').fetchall())"`
