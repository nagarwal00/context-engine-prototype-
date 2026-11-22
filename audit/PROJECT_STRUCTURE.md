# Project Structure (verified 2026-11-21)

**Language/stack:** Python 3.11+ standard library only (`http.server`, `sqlite3`, `ast`, `urllib`).
Vanilla HTML/CSS/JS frontend. No pip install required. Optional: `cryptography` (encrypted
GitHub token storage, GitHub App JWT). Verified on Python 3.13 as well.

## Entry points

| Command | What it does |
|---|---|
| `python tools/init_db.py --seed` | Creates `context_intelligence.db`, runs migrations 001–007, loads the two synthetic demo repos |
| `python server.py` | Starts the web server + REST API on `127.0.0.1:8080` (serves `web/`) |
| `python -m unittest discover -s tests` | 368 tests (2 skipped), ≈ 38 s |
| `python run_demo.py` | 21 scripted capability checks |
| `python tools/run_whybench.py --split dev` | Benchmark on the dev split (test split needs `--final`) |
| `python tools/build_static.py` | Builds the read-only GitHub Pages snapshot into `docs/` |

## Directory map

```
SE_project/
├── server.py                 Tier-2 HTTP layer: routing, auth endpoints, rate-limit, CORS/CSP headers
├── run_demo.py               scripted demo checks
├── backend/
│   ├── api.py                APIHandler: all /api/* GET/POST/DELETE business routing (2,442 lines)
│   ├── security.py           roles, authorize(), dev mode, CORS allowlist
│   ├── rate_limiter.py       sliding-window limiter (in memory)
│   ├── config.py, logging_config.py
│   ├── db.py                 Tier-3: schema, all SQL, evidence trail queries
│   ├── models.py             dataclasses + evidence invariant (validate_invariants)
│   ├── seed_data.py          synthetic demo repositories
│   ├── migrations/           001–007 + runner (schema_migrations table)
│   ├── auth/                 GitHub OAuth, sessions, per-repo access, add-repo flow
│   ├── ingestion/            git/GitHub/ADR/Slack adapters, sanitizer, live GitHub, job runner
│   ├── engine/               extractor, evidence, graph, lifecycle, reconciliation, drift,
│   │                         guard rules, rejected-idea guard, staleness, bus factor,
│   │                         independence, explanation, onboarding, as-of, LLM (optional)
│   └── evaluation/           benchmark, baselines, calibration, WhyBench (frozen), hold-out (frozen)
├── web/                      ★ AUTHORITATIVE frontend (served by server.py)
├── docs/                     GitHub Pages copy of web/ (+ sdlc/ and process/ documents)
├── new_frontend/             obsolete third copy of web/ — not served by anything
├── extension/                Chrome MV3 extension (PR/issue overlay)
├── vscode-extension/         VS Code extension (hover, CodeLens, tree view)
├── tests/                    74 files, unittest
├── tools/                    34 maintenance / evaluation scripts
├── demo_sample_repo/         small controlled repo for local-ingest demos
├── results/                  benchmark manifests
├── user_study/               protocol + empty template (no real participant data)
└── *.md                      ~40 historical reports (see DOC-01)
```

## Databases

| File | Role | State found |
|---|---|---|
| `context_intelligence.db` | Main app DB (default `CIF_DB_PATH`) | 7 decisions, **4 users, 11 sessions** — treat as user data |
| `whybench.db` | Built by the benchmark runner | 40 decisions over 2 repos |
| `cif.db` | Stray DB, schema only | 2 repos, otherwise empty |
| `cif_dashboard.db` | 0-byte file | unused |

All four pass `PRAGMA integrity_check` and `foreign_key_check`. Originals backed up (with
SHA-256) to `../db_backups_original/` before any work.

## Frontend copies
`web/`, `docs/`, `new_frontend/context-engine-ui-refresh/` are byte-identical except
`static_data.js`. **`web/` is authoritative.**

## Configuration (`.env.example` documents all keys)
`PORT`, `CIF_BIND`, `CIF_DB_PATH`, `CIF_DEV_MODE`, `CIF_ADMIN_TOKEN`, `CIF_BASE_URL`,
`CIF_SESSION_SECRET`, `GITHUB_APP_CLIENT_ID/SECRET`, `CIF_WEBHOOK_SECRET`, `GITHUB_TOKEN`,
`CIF_CORS_ORIGINS`, `CIF_EXTENSION_IDS`, `CIF_TOKEN_ENC_KEY`, `CIF_RATE_LIMIT_*`, `CIF_LOCAL_ONLY`.
