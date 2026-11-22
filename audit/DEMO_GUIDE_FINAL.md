# Demo Guide (final, verified 2026-11-21)

Every step below was executed during the audit. Approximate time: 12 minutes.
Use this guide instead of the older `DEMO_GUIDE.md` / `DEMO_READINESS_REPORT.md`.

## 0. Before the demo (5 minutes, the day before)
```bash
python -m unittest discover -s tests
```
```bash
python run_demo.py
```
Expect 409 OK and 21/21. Use a **fresh demo database** so earlier experiments do not show up:
```bash
python tools/init_db.py --db demo_day.db --seed
```
```bash
CIF_DB_PATH=demo_day.db CIF_DEV_MODE=1 python server.py
```
(Windows PowerShell: `$env:CIF_DB_PATH="demo_day.db"; $env:CIF_DEV_MODE="1"; python server.py`)

## 1. Sign in (security story)
1. Open http://127.0.0.1:8080/login.html → **Register** → user `examiner`, password ≥ 8 chars.
2. Point out: wrong password → "Invalid username or password" (401). Passwords are PBKDF2-hashed.
3. Badge top-right shows **Live engine** (green) = real backend.

## 2. Decision history (core idea)
1. **Project Timeline**: accepted / rejected / superseded decisions.
2. Open *Reject Simple Deadband Hysteresis* → **Evidence Panel**: the events that prove it.
   Say: "every decision in a grounded state must cite ≥1 event; the database refuses otherwise."
3. **Context Graph**: decisions ↔ code entities ↔ events.
4. **Code-Context View** → `regulate_temperature`: grounded explanation with citations.

## 3. Lifecycle & review
1. **Review Queue** → *Confirm* a pending item → success.
2. Try an illegal transition (e.g. *Reject* an accepted decision) → **409** with explanation.

## 4. Drift detection (CI story)
1. **Live CI Drift Check** → preset **thermal_revert** → *Run* → violation citing the governing
   decision and an *uncalibrated* signal strength.
2. Preset **clean_change** → no drift.

## 5. Ingest a repository you control
Local folder with real git history:
```bash
git clone https://github.com/npryce/adr-tools /tmp/adr-tools
```
In the dashboard: **Workspace → Connect & Ingest** → enter the folder path
(`/tmp/adr-tools`). Result (measured): 136 commits, 9 ADRs → accepted decisions with the real
author and dates. Citations show as `local://adr-tools/...` (a local repo has no web URL).

GitHub repositories (`owner/name`) need internet access and preferably a `GITHUB_TOKEN`
(60 unauthenticated requests/hour). If GitHub refuses, the UI shows GitHub's error — it never
invents commits.

## 6. Honesty checks (good to show)
- Stop the server (Ctrl+C) and click around: badge turns **Backend unreachable**, a red notice
  appears, nothing is fabricated. Restart the server and reload.
- **Metrics & Baselines**: say the real numbers: recall 80.8 % (21/26, CI 62–92 %), refusal
  64.4 % (29/45), BM25 baseline retrieves more evidence (92.3 %) but cannot classify state or refuse.

## Fallback if something breaks
- Server won't start → see TROUBLESHOOTING.md.
- No network → skip step 5's GitHub part; the local-folder ingest works offline.
- Total failure → open `docs/dashboard.html` from the GitHub Pages site: a clearly labelled
  **Static snapshot** of the demo data (read-only; ingestion and sign-in are not real there).
