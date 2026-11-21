# Test Execution Report — 2026-11-21

Environment: Linux, Python 3.13.18 (project targets 3.11/3.12; CI uses 3.11), Node 22,
Chromium via Playwright. All numbers below were produced by commands run during this audit.

## 1. Automated suite
| Run | Command | Result |
|---|---|---|
| Baseline, original code, fresh clone | `python tools/init_db.py --seed && python -m unittest discover -s tests` | 368 run, 0 fail, 2 skipped, 37.9 s |
| Original code, user's folder (demo repo populated) | `python -m unittest tests.test_ingest_registration` | **2 failures + 1 error** (pre-existing; CI never saw it because `demo_sample_repo` is empty in clones) |
| After fixes | `python -m unittest discover -s tests` | **409 run, 0 fail, 2 skipped, ~44 s** |
| New HTTP-level tests against original code | `python -m unittest tests.test_http_security` | 20 of 22 fail (proves the tests detect the bugs) |
| DB checksums of the four real databases before/after every suite run | `sha256sum -c` | identical |

New test files (41 tests): `test_http_security.py` (24, real `server.py` subprocess),
`test_db_integrity.py` (7), `test_local_ingest.py` (5), `test_extractor_precision.py` (5).

## 2. Other CI steps
| Check | Result |
|---|---|
| `python run_demo.py` | 21/21 checks pass |
| `python tools/check_docs.py` | pass |
| `python tools/check_eol.py` | pass |
| `python tools/check_js.py` (now `node --check`) | 20/20 files parse |
| `python -m compileall backend tools tests` | pass |
| `pyflakes` (undefined names) over `backend/ tools/ server.py` | 0 undefined names after fixes (found the `DELETE` `NameError`) |
| `python tools/validate_whybench.py` | pass (failed before fix on Linux due to CRLF hash) |

## 3. Browser end-to-end (Playwright / Chromium)
| Scenario | Result |
|---|---|
| Original code on port 8091 | login page made 62 `/api/me` calls in 2.5 s → 429, never reached dashboard |
| Fixed code on port 8095: register (real password) → dashboard | "Live engine" badge; all 10 surfaces render; 26 API calls, all 2xx (one expected 401 before sign-in) |
| Drift check preset "thermal_revert" | violation reported with decision title and signal strength |
| Review queue "confirm" | 200; history row actor `user:<login>` |
| Backend killed mid-session | badge "Backend unreachable" + notice; no fabricated data |
| Static snapshot (`docs/` via `http.server`) | "Static snapshot" badge, 7 snapshot decisions, ingestion refused with `STATIC_MODE` |
| Console/page errors | none in any scenario |

## 4. Performance (fresh DB, 20 requests each, signed-in user, local machine)
| Endpoint | median | p95 |
|---|---|---|
| /api/decisions | 9.1 ms | 11.2 ms |
| /api/timeline | 8.5 ms | 12.4 ms |
| /api/graph | 9.4 ms | 11.4 ms |
| /api/explain | 11.5 ms | 15.5 ms |
| /api/evidence | 9.3 ms | 12.0 ms |
| /api/review-queue | 9.6 ms | 11.7 ms |
| /api/stats | 9.9 ms | 11.5 ms |
| /api/bus-factor | 7.0 ms | 8.3 ms |
| Ingest real repo `npryce/adr-tools` (136 commits, 9 ADRs) via HTTP | 0.55 s total | — |
| `init_db.py --seed` on empty folder | 0.36 s | — |

Small-data numbers only; no load test with large repositories was performed.

## 5. Benchmark reproduction
| Run | Recall (strict) | State accuracy | Refusal accuracy |
|---|---|---|---|
| Committed `results/latest_manifest.json` (test_v2) | 80.8 % (21/26) | 100 % (21/21) | 64.4 % (29/45) |
| Reproduced on original code | 80.8 % (21/26) | 100 % | 64.4 % (29/45) |
| After all fixes (one run, scratch copy) | 80.8 % (21/26) | 100 % | 64.4 % (29/45) |
| Dev split before / after | 100 % (18/18) / 100 % | 100 % / 100 % | 64.4 % / 64.4 % |
| Hold-out drift (`tools/run_holdout.py`) | 16/16 cases correct; regenerated file byte-identical | | |

Wilson 95 % CI for 21/26 = 62.1 %–91.5 %; for 29/45 = 49.8 %–76.8 %.
Decision precision: **not measured** (label file keyed to a SQLite file hash that changes on rebuild).

## 6. Not tested (and why)
| Item | Reason |
|---|---|
| GitHub REST ingestion against live GitHub | This environment's proxy only permits `git clone` of public repos, not REST calls. Covered by mocked unit tests only. |
| GitHub OAuth login end-to-end | Needs a registered OAuth app and a browser session at github.com. |
| Webhook from real GitHub | Needs a public URL; HMAC verified with unit tests. |
| Chrome / VS Code extensions in their hosts | JS syntax and Python-side tests only. |
| Firefox / Edge / mobile layouts | Only Chromium at 1366×900 was exercised. |
| Docker image build | Docker not available here; `Dockerfile` and `.dockerignore` reviewed only. |
| Python 3.11 specifically | Ran on 3.13; CI (3.11) not executed from here. |
