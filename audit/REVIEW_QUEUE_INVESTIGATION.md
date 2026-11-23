# Review Queue — Investigation (before any code change)

Branch: `fix/review-queue-functionality` (from `fix/windows-sqlite-cleanup`, which contains the Windows
SQLite cleanup fix). Baseline: `python -m unittest discover -s tests` → **414 run, OK, 2 skipped**.

## 1. Components
| Layer | Location |
|---|---|
| UI rendering + buttons | `web/app.js` `loadReviewQueue()` (renders guard-rule cards and queue cards, attaches listeners after `innerHTML`) |
| Button handlers | `triggerReviewAction()`, `openCorrectModal()`, `submitCorrection()`, `approveGuardRule()`, `disableGuardRule()` |
| HTTP | `POST /api/review-action`, `POST /api/guard-rules/approve`, `POST /api/guard-rules/disable`, `GET /api/review-queue`, `GET /api/guard-rules` — all via `app.apiFetch` (JSON, same-origin, session cookie; CSRF = Origin check in `server.py`) |
| Authorization | `api.ROUTE_ROLES` → `security.authorize` → `repo_access.resolve_repo_for_request` (repo resolved from `target_id`) |
| Business logic | `backend/api.py` `handle_post('/api/review-action')`, `engine/lifecycle.transition`, `engine/rejected_idea_guard`, `engine/staleness` |
| Data | `decisions`, `state_history`, `edges`, `ambiguous_findings`, `finding_feedback`, `guard_rules` (same SQLite file via `Database.get_connection`, commit on success) |

Event wiring itself is sound: listeners are attached after rendering, buttons are `<button>` elements
outside any form (no accidental submit), no duplicate listeners (container is re-rendered).

## 2. Measured behaviour (fresh seeded DB, each button replayed exactly as `app.js` sends it)
| Item type | Button | ID sent by UI | HTTP | DB changed | Leaves queue |
|---|---|---|---|---|---|
| decision | Confirm | decision_id ✔ | 200 | decisions, state_history | yes ✔ |
| decision | Reject (accepted decision) | decision_id ✔ | 409 | nothing | no (lifecycle forbids accepted→rejected; message shown in an alert) |
| decision | Correct | decision_id ✔ | 200 | decisions, state_history | **no** ✘ |
| conflict | Confirm / Reject | edge_id ✔ | 200 | edges (row **deleted** in both cases) | yes (but "confirm" destroys the confirmed conflict) |
| conflict | Correct | edge_id | 200 "success" | **nothing** ✘ | no |
| drift | Confirm / Reject / Correct | **decision_id** ✘ (should be edge_id) | 200 "success" | **nothing** ✘ | no |
| possible_rejected_idea | Confirm / Reject | **decision_id** ✘ (should be finding_id) | 200 "success" | finding_feedback row with wrong id; finding stays pending ✘ | no |
| possible_rejected_idea | Correct | decision_id | 200 "success" | nothing ✘ | no |
| stale_decision | Confirm | decision_id | 200 | review_status only; `freshness` unchanged ✘ | no (selected by `freshness`) |
| guard rule | Approve / Disable | rule_id ✔ | 200 / 404 | guard_rules | n/a ✔ (fixed in the earlier audit) |

With the **correct** IDs, the backend persists finding actions properly (verified: finding status
becomes `confirmed` / `dismissed`).

## 3. Confirmed root causes
1. **Wrong identifier (frontend).** `const id = item.decision_id || item.edge_id` — drift items carry both
   ids and possible-rejected-idea items carry `finding_id` + `decision_id`, so the decision id is sent.
2. **Silent no-op success (backend).** `/api/review-action` returns "Action executed successfully" when
   the edge `DELETE` matches 0 rows, when the action is not supported for the item type (`correct` on
   conflict/drift/finding), and when `item_type` is unknown.
3. **Correct never clears the item.** It sets `review_status='human_corrected'`, but the queue only
   excludes `human_confirmed` / `human_rejected`. The modal also (a) pre-selects state "accepted" for
   every decision, so saving without touching it tries a lifecycle transition, and (b) sends the
   "audit justification" text as the decision's `rationale` (overwriting it) instead of as `reason`.
4. **Stale decisions** are selected by `freshness`, but Confirm only changes `review_status`.
   The backend already has the correct operation (`revalidate`).
5. **Conflict "Confirm" deletes the conflict edge**, i.e. confirming a conflict erases it from the graph;
   nothing records the human verdict.
6. **Authorization (security, found while tracing).** `resolve_repo_for_request` resolves `target_id`
   only as a decision id. Edge and finding ids fall back to the demo repository, so an action on another
   repository's conflict/drift edge or finding is authorized against the demo repo.
7. UI: results are shown with `alert(json.message)` whether the request succeeded or failed; buttons stay
   clickable while a request is in flight (double submits possible).

## 4. Minimal fix plan (Review Queue only)
- `web/app.js` (queue functions only): send the type-correct id; show **Correct** only for decision
  items (the backend supports `correct` only for decisions); pre-select the decision's current state;
  send the justification as `reason` (not `rationale`); disable buttons while a request is in flight;
  report success only when the API says so; refresh queue + stats after every successful action.
- `backend/api.py` (`/api/review-action` and the queue query only): 404 for unknown edge/finding ids,
  400 for unsupported item/action combinations; conflict/drift Confirm keeps the edge and records the
  verdict in `finding_feedback`, Reject removes the edge and records it; queue hides edges that already
  have a verdict and decisions already handled (`human_corrected`, `human_merged`); stale Confirm =
  existing `revalidate`.
- `backend/auth/repo_access.py`: also resolve `target_id` as an edge id or finding id (smallest change;
  object-level authorization stays strict).
- No schema change, no change to lifecycle rules, CSRF, authentication or other features.

## 5. Test plan
Fail-first backend tests for every item type × action (DB state before/after, queue membership,
status codes, 404/400 cases, cross-repo refusal, persistence after reopening the DB); browser E2E
clicking every button on a temp DB; full suite before/after.
