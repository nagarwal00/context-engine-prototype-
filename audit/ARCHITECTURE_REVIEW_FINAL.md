# Architecture Review — Final

## 1. Is it really three-tier?
| Tier | Where | Verdict |
|---|---|---|
| Presentation | `web/` (HTML, CSS, `app.js`) | **Now mostly yes.** Before the audit `app.js` contained a second engine that ingested, extracted and stored data in the browser (≈600 lines). That is gone from live mode. A read-only snapshot reader and simulated review buttons remain for the static GitHub Pages preview, clearly labelled. |
| Application | `server.py` (HTTP), `backend/security.py` + `backend/auth/` (identity, authorization), `backend/api.py` (routing), `backend/engine/` (business logic), `backend/ingestion/` | **Yes, with leaks.** Login/registration logic moved to `backend/auth/local_accounts.py`, but `server.py` still holds the demo-login SQL and the auth routing. `api.py` is a 2,500-line class that depends on 24 modules. |
| Data | `backend/db.py`, `backend/migrations/`, `backend/integrity.py` | **Yes, with two caveats.** Several engine modules and `api.py` run their own SQL instead of going through `db.py`; and `db.py` imports `engine.lifecycle` (a data → business dependency, the only import cycle). |

Validation happens on the backend (input checks, invariant checks, triggers). Authentication and
authorization are enforced in Tier 2 (`check_authorization` before every `/api` handler) —
the frontend gate in `dashboard.html` is only a convenience redirect.

## 2. Principles
| Principle | Assessment |
|---|---|
| Separation of concerns | Good inside `backend/engine` (one module per capability). Weak in `api.py` (routing + business logic + SQL). |
| Single responsibility | `APIHandler` violates it; the engines mostly respect it. |
| DRY | Improved: three different extraction algorithms (API ingest, local ingest, background job) now share `DecisionExtractor`; five copies of the live/static rule replaced by `cif-mode.js`. Still duplicated: three frontend copies (`web/`, `docs/`, `new_frontend/`). |
| Coupling | High fan-in on `db.py` (expected); high fan-out from `api.py` (24 modules). |
| Fault tolerance | Improved: global JSON error handler; frontend reports outages instead of faking data. |
| Configuration | Environment variables only, documented in `.env.example`; no hard-coded secrets. |
| Dependencies | Standard library only (good for a course project); optional `cryptography`. |

## 3. Documentation vs implementation
| Document claim | Reality |
|---|---|
| README: "zero ungrounded fabrication" | Was false in the frontend and in local ingest; true after fixes for live mode. |
| README/SRS: evidence invariant "physically prevented" by the DB layer | Was Python-only; now partially DB-enforced (state promotion and event deletion). Raw INSERT of a grounded decision without evidence is still possible at the SQL level and is caught by `v_ungrounded_decisions`. |
| `PROJECT_AUDIT_REPORT.md`: "352 tests, 100 % pass" | Outdated (368 before, 409 now). |
| Repo-access docstring: demo repos read-only | Code allowed signed-in writes; docstring corrected. |
| `THREE_TIER_ARCHITECTURE.md` | Did not mention the browser mock engine; now accurate for live mode. |

## 4. Recommended next refactors (not done — would be a large change)
1. Split `APIHandler` into per-area handlers (`decisions`, `review`, `ingest`, `admin`) behind the existing `ROUTE_ROLES` table.
2. Move remaining raw SQL from `api.py` / engines into `db.py` query functions.
3. Delete `new_frontend/` and generate `docs/` only in CI (needs your permission — see FINAL_PROJECT_STATUS).
4. Replace inline `onclick` handlers so CSP can drop `'unsafe-inline'`.
