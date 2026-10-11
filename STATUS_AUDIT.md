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
