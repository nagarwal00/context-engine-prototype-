# Feature Inventory — status as found (before fixes)

Legend: ✅ verified working · 🟡 partially working / caveats · ❌ broken · ⛔ blocked by external
credentials · ⬜ not tested yet. "Verified" means exercised live or by a test I ran, not a report.

| # | Feature | Status | Evidence |
|---|---|---|---|
| 1 | DB init + migrations on clean clone | ✅ | `init_db.py --seed` on fresh clone, 0.36 s |
| 2 | Server startup | ✅ | `server.py` serves `/healthz` 200 |
| 3 | Unit test suite | ✅ | 368 run, 0 failures, 2 skipped (fresh clone) |
| 4 | `run_demo.py` | ✅ | 21/21 checks |
| 5 | GitHub OAuth login | ⛔ | Code reviewed (sound); needs a real OAuth app + browser to test end-to-end |
| 6 | Username login / register | ❌ | Works, but password-less → account takeover (SEC-01) |
| 7 | Demo login | ❌ | Open redirect (SEC-04) |
| 8 | Logout | ✅ | session deleted, cookie cleared *(tested via existing tests)* |
| 9 | Dashboard live data on :8080 | ✅ | Browser: badge "Live engine", 13 real `/api/*` calls |
| 10 | Dashboard on any other port / HTTPS | ❌ | login loop / canned data (FE-01) |
| 11 | Timeline, decisions, artifacts, graph, review queue APIs | ✅ | 200 with DB data |
| 12 | Explain / evidence | 🟡 | Work, but cross-repo IDOR (SEC-03) |
| 13 | Review actions (confirm/reject/reopen…) | 🟡 | Lifecycle rules enforced (409 on illegal transition) but IDOR + actor not recorded |
| 14 | Delete repository (`DELETE /api/repos/…`) | ❌ | NameError — empty reply (APP-01) |
| 15 | Ingest public GitHub repo | ⬜ | Requires GitHub network access — to test in Phase 9 |
| 16 | Ingest local directory | 🟡 | Works; reachable via CSRF in dev mode (SEC-02) |
| 17 | Clear DB / reseed / purge | 🟡 | Work, admin-only, but CSRF-able in dev mode; clear is global (DB-02) |
| 18 | Live CI drift check | ✅ | `run_demo`, tests; hold-out 16/16 reproduced |
| 19 | Conflict detection | 🟡 | Works on demo pairs; tiny vocabulary (ALG-04) |
| 20 | Decision extraction | 🟡 | Works; many false positives (ALG-01/02) |
| 21 | Evidence-grounding invariant | 🟡 | Python-enforced; not DB-enforced (DB-01) |
| 22 | Rate limiting | 🟡 | 429 + Retry-After correct; bypassable (SEC-05) |
| 23 | Webhook receiver | ✅ | HMAC verified; tests pass |
| 24 | Static GitHub Pages snapshot | 🟡 | Read-only snapshot OK; mock engine fabricates on ingest (INT-01) |
| 25 | WhyBench benchmark | ✅ | Reproduced: recall 80.8 %, refusal 64.4 % |
| 26 | Hold-out drift evaluation | ✅ | Reproduced byte-identical results file |
| 27 | Chrome extension | ⬜ | Python tests pass; not loaded in a browser |
| 28 | VS Code extension | ⬜ | JS syntax OK; not run inside VS Code |
| 29 | User study | ⬜ | Protocol only; **no real participant data exists** |
| 30 | LLM extractor | ⛔ | Optional; needs an API key |
