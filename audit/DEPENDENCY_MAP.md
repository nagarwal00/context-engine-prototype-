# Dependency Map (generated from actual `import` statements)

## Backend module graph
```
server.py ──► backend.api ──► (24 modules — see below)
          ├─► backend.security ──► auth.sessions, auth.repo_access, rate_limiter, config, db
          └─► backend.auth.* (login/logout/me handled inline in server.py)

api            → auth.{app_token,repo_access,repo_add,sessions}, config, db, models, security,
                 rate_limiter, seed_data, logging_config,
                 engine.{as_of,bus_factor,drift_detector,explanation,graph,lifecycle,onboarding,
                         reconciliation,rejected_idea_guard,staleness},
                 evaluation.benchmark, ingestion.{job_runner,live_github}
db             → models, migrations, engine.{evidence,independence,lifecycle}, ingestion.sanitizer
engine.*       → db, models   (+ guard_rules/rejected_idea_guard → identifiers, entity_res, lifecycle)
ingestion.*    → db, models, identity, sanitizer, (live_github/job_runner → engine.extractor, graph, entity_res)
auth.*         → db, config, sessions
evaluation.*   → db, engine.*, baselines, ground_truth
```

**Cycle found:** `db → engine.lifecycle → db` (data layer depends on business logic) — ARCH-03.

## Request lifecycle (traced)
```
Browser (web/app.js  app.apiFetch)
  → HTTP GET/POST /api/...            server.py ContextIntelligenceServer.do_GET/do_POST
  → rate limit                        rate_limiter.check_rate_limit (key: session/bearer/IP)
  → CSRF Origin check (POST)          auth.sessions.validate_csrf_origin
  → route→role lookup                 api.ROUTE_ROLES   (default deny → 404)
  → authorize()                       security.authorize → authenticate_caller → authorize_repo
  → business logic                    api.APIHandler.handle_get/handle_post → engine.* 
  → SQL                               db.Database (sqlite3, foreign_keys=ON per connection)
  → JSON response (+request_id)       server._send_json
  → DOM update                        app.js render functions (esc() for HTML escaping)
```

## Ingestion pipeline (traced)
```
GitHub REST / local dir / ADR files
  → ingestion.{git,github,adr}_adapter   (Event objects)
  → ingestion.sanitizer                  (secret redaction before storage)
  → ingestion.identity                   (author → canonical identity)
  → engine.entity_res                    (file / file::function via ast)
  → engine.extractor                     (Decision candidates, evidence_event_ids)
  → models.Decision.validate_invariants  (grounded states need ≥1 evidence)
  → db.save_decision                     (decisions, decision_evidence, claims)
  → engine.graph                         (edges: affects / evidenced_by / supersedes …)
  → engine.reconciliation / guard_rules  (conflicts, supersession, guard-rule synthesis)
  → /api/timeline, /api/graph, /api/decisions, /api/explain → dashboard
```
Two ingestion entry points exist: `POST /api/ingest-repo` (admin, synchronous,
`live_github.py`) and `POST /api/repos` (signed-in user, background job, `job_runner.py`).

## Frontend
`dashboard.html` → `static_data.js` (snapshot) + `app.js` (single `app` object, 4,100 lines).
`index.html` → `landing.js`. `login.html` inline script. No build step, no framework.
