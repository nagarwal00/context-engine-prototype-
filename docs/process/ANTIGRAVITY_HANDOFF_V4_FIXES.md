# ANTIGRAVITY HANDOFF v4 — Evaluation-Review Fixes (Integrity, Fair Evaluation, Tenancy, Docs, Release)

> **This is an ADDENDUM to `ANTIGRAVITY_HANDOFF_V2.md` and `ANTIGRAVITY_HANDOFF_V3_EXTENSION.md`.** All V2 rules (§1), V3 rules (R1–R6), the reporting format and the pitfalls still apply unless this file explicitly overrides them.
>
> **Read the whole file before changing anything.** Work **one step at a time, in order**. After each step: run its **Verify** commands, check every **Acceptance** line, make the **Commit**, then send the **Report** (§14). Never batch steps. Never mark a step done unless every acceptance line is true. Never guess: if a file, function or line does not look like this document says, **inspect it first and adapt**, and write what you found in the report.

---

## 0. Why this file exists

An independent professor-style review of the project (all docs read; test suite and `run_demo.py` executed; git history, benchmark data and code inspected) scored it about **21/30** and found problems that cost marks or create an academic-integrity risk. This file fixes them **safely and honestly**. The project's strengths (lifecycle engine, temporal graph, evidence invariant, privacy sanitizer, auth, extensions, 279 tests) must **not** be damaged.

Principle for every step: **make the project true, not just good-looking.** If an honest number is worse than the old number, the honest number goes into the docs.

---

## 1. Non-negotiable rules (breaking any = work is wrong even if code runs)

1. **Verify before you fix.** Every finding in §2 has a reproduction. Run it first. If it cannot be reproduced, record `NOT REPRODUCED` with proof and do not change code for it.
2. **Never fabricate.** No invented metrics, labels, Copilot answers, user-study data, screenshots, benchmark events, URLs or commit hashes. Anything that needs a human is a **Human Task (§12)**: leave it empty / `not measured` and list it in your report.
3. **The frozen split stays frozen.** Do **not** edit `backend/evaluation/whybench/questions.json`, any `whybench/data/*/events.json`, or `FROZEN.md` hashes. Do **not** run `tools/run_whybench.py --split test_v2` again, and **never** use `--force` or `--final` on `test_v2`. Do **not** edit `results/test_v2_*/manifest.json` or `results/latest_manifest.json` (audit trail). Corrections go in **new** files (Step 2.1).
5. **Never tune on test data.** Engine changes may be validated on `dev` and on the new hold-out set (Step 3.2). Never look at `test_v2` outputs to guide a code change.
6. **Standard library only** (Python 3.11/3.12). `cryptography` stays optional (V3 R1). No new pip packages.
7. **Windows-safe and line-ending-safe (important).** Many files use **CRLF** line endings. Before editing a file, detect its EOL style; **preserve it**. Exact-match edit tools fail on CRLF mismatch. After every step run `python tools/check_eol.py` (created in Step 0.4); it must report zero changed-EOL files. Open files with `encoding="utf-8"`. Use `pathlib`. No Unix-only shell syntax inside Python code.
8. **No secrets anywhere** (repo, logs, DB, docs, tests). Test fixtures that need token-shaped strings must build them by concatenation (`"gh" + "p_" + "a"*36`) so GitHub push-protection does not trigger.
9. **Back up before destructive/schema/data actions.** Databases: `context_intelligence.db`, `whybench.db`. Backups go to `backups/` (gitignored). Test any data repair on a **copy** first.
10. **Tests never touch the real databases and never use the network.** Use `tempfile` and mocks. (Step 1.4 enforces this.)
11. **Smallest change that satisfies the step.** No unrelated refactors, renames or reformatting.
12. **One commit per step**, conventional message given in the step. Never `git push --force`. Never rewrite history.
13. **Do not weaken any existing check.** `python -m unittest discover -s tests` and `python run_demo.py` must pass after every step from Step 1.3 onward (before that, only the two known failures from §2-F4 are allowed). A check may be changed only to make it stricter or to match an intentional, documented change.
14. **If blocked**, append to `BLOCKERS.md` (what you tried, exact error, what you need) and continue with the next *independent* step.
15. **Honest labelling.** Synthetic data is called synthetic. Heuristic scores are called uncalibrated. Anything unmeasured says `not measured`.

---

## 2. Verified findings (reproduce each before fixing)

Run these from the project root. Use `python` (Windows) — they are plain Python so they work in PowerShell and CMD.

### F1 — Unfair headline comparison (CRITICAL)
`tools/run_whybench.py` computes CIF Task-1 hits over the **26 positive** questions but passes **all 71** questions (45 negatives included) to the baselines (`baseline_evaluator.evaluate_all(split_questions)`, around line 231). Reported: CIF 80.8%, BM25 59.2% (=42/71), Docs-only 8.5% (=6/71). On the **same 26** questions BM25 = **24/26 = 92.3%** and Docs-only = **6/26 = 23.1%**. Also CIF's "top-5 hit rate" is not a ranked retrieval: it is "the single strictly-matched decision cites ≥1 expected event", which is why it equals strict recall (21/26).

Reproduce (works on a **copy**; never open the real DB directly, `Database()` runs migrations):
```python
# save as tools/_repro_f1.py (delete after use) — run: python tools/_repro_f1.py
import json, shutil, sys, tempfile, os
sys.path.insert(0, ".")
from backend.db import Database
from backend.evaluation.baselines import BaselineEvaluator
qs = [q for q in json.load(open("backend/evaluation/whybench/questions.json", encoding="utf-8")) if q["split"] == "test_v2"]
pos = [q for q in qs if q.get("expected_state") != "none"]
tmp = os.path.join(tempfile.mkdtemp(), "wb.db"); shutil.copy("whybench.db", tmp)
ev = BaselineEvaluator(Database(tmp))
for name, fn in [("A", ev.run_baseline_keyword), ("B", ev.run_baseline_docs_only)]:
    a, p = fn(qs), fn(pos)
    print(name, "all:", a["found_count"], "/", a["total_count"], "| positives:", p["found_count"], "/", p["total_count"])
```
Expected: `A all: 42 / 71 | positives: 24 / 26` and `B all: 6 / 71 | positives: 6 / 26`.

### F2 — "Real-world" WhyBench repos are synthetic (CRITICAL, integrity)
`backend/evaluation/whybench/data/{cli-cli,cloud-hypervisor,payment-core}/events.json` hold 18–20 **hand-written** events each, dated Jan 2026. `REPOS.md` lists fake-looking "Pinned Commit SHA"s (`8f9a2b1c4e5d6a7b8c9d…`, `b1a4c6e8f0123456789abcdef…`). `payment-core` is the team's own `demo_sample_repo`. One spot-check: real `cli/cli` PR #518 is an unrelated Eastern-Asian text-alignment change, not the "go-keyring provider (Closes #412)" in the data. Docs say "real-world", "open-source", "grounded in public GitHub URLs". Fix = honest relabelling (Step 2.3) and, as a Human Task, a genuinely real corpus (§12 H-1).

Reproduce: `python -c "import json;d=json.load(open('backend/evaluation/whybench/data/cli-cli/events.json',encoding='utf-8'));print(len(d));print(d[2]['title'],d[2]['source_url'])"` and `git grep -n -i "real-world\|pinned commit\|open-source repositories\|public GitHub URLs" -- *.md`.

### F3 — Phase 7–9 work is not in git
`git ls-tree -r HEAD --name-only` contains **0** files under `backend/auth/`, `extension/`, `vscode-extension/`; last commit is 2026-10-14; Phase 7–9 files are dated 2026-10-17/18. Reproduce:
`python -c "import subprocess;o=subprocess.run(['git','ls-tree','-r','HEAD','--name-only'],capture_output=True,text=True).stdout.splitlines();print(sum(1 for f in o if f.startswith(('backend/auth','extension/','vscode-extension/'))))"` → `0`.

### F4 — Two failing tests (277/279 pass)
* `tests/test_extension_api.py::test_per_repo_isolation_rule_r3` — fixture inserts `repo_access.verified_at = '2026-10-18T10:00:00Z'` but `backend/auth/repo_access.py` has a **15-minute TTL (private) / 1-hour TTL (public)**, so the test only passes within 15 minutes of that fixed date (time-bomb; also fails in CI).
* `tests/test_migration_auth_tables.py::test_migration_on_real_db_copy_without_data_loss` — shipped `context_intelligence.db` has **2 `drifts_from` edges with `repo_full_name IS NULL`**. Cause: `Database.upsert_edge()` (`backend/db.py` ~line 858) and the raw inserts at `backend/engine/lifecycle.py` ~129 and `backend/engine/reconciliation.py` ~316 never write `repo_full_name`. Also `backend/api.py` ~291 and ~379 run `SELECT ... FROM edges WHERE edge_type='drifts_from'` with **no repo scoping** (cross-tenant leak risk).

Reproduce: `python -m unittest discover -s tests 2>&1 | tail -30` and `python -c "import sqlite3;c=sqlite3.connect('file:context_intelligence.db?mode=ro',uri=True);print(c.execute('select count(*) from edges where repo_full_name is null').fetchone())"` → `(2,)`.

### F5 — Hard-coded demo vocabulary in the "general" engine (HIGH)
STATUS_AUDIT marks P1-a RESOLVED and `drift_detector.py` claims "Zero domain keywords", but: `backend/engine/guard_rules.py` (~lines 60–160) hard-codes `braintree`, `userfaultfd`, `psycopg2`, `stripe`, `redis cluster`, `bang-bang`, `hysteresis`, `dict_cache`, and paths `src/thermal/**`, `src/cache/**`, `src/payments/**`; `backend/engine/reconciliation.py` (~lines 78–79) hard-codes `("pid","bang-bang")`, `("redis","in-memory lru")`; `backend/engine/rejected_idea_guard.py` (~lines 420–430) hard-codes `deadband`, `on_off_relay`, `hysteresis`, `bang_bang`, `dict_cache`, `sticky_sessions`. All 20 drift cases (`drift_cases.json`) are variations of the same two demo stories, so "100% recall" is a self-test.

Reproduce: `git grep -n -i -E "pid|redis|thermal|bang|deadband|stripe|braintree|userfaultfd|psycopg2|hysteresis|dict_cache" -- backend/engine`.

### F6 — Conflict-detector substring bug (HIGH)
`reconciliation.py` uses `k1 in text` substring tests, so `"sync"` matches inside `"async"`: two decisions that both say "async" are flagged as conflicting.
Reproduce: `python -c "d1='adopt async workers';d2='use async io';print((('sync' in d1) and ('async' in d2)) or (('async' in d1) and ('sync' in d2)))"` → `True`.

### F7 — Swallowed exceptions remain
`backend/engine/rejected_idea_guard.py` (~line 410, regex compile `except Exception: pass`) and `backend/security.py::get_cors_origin` (`except Exception: pass`). Reproduce: `git grep -n -A1 "except Exception" -- backend/engine/rejected_idea_guard.py backend/security.py`.

### F8 — Required comparisons/measurements missing
`manual_copilot_results.csv` has only a header; Baseline C (LLM) and D (Copilot) are `not measured`; all 105 precision labels are `null` (`backend/evaluation/precision_labels.json` 40, `backend/evaluation/whybench/precision_labels.json` 65) and the manifest says `snapshot hash mismatch: labels generated from 'db0b1b05…', current DB hash is '26bd603a…'`; no user study exists; calibration `not measured`.

### F9 — Documentation drift and tone
* `LIMITATIONS.md` §2 says "61 labelled questions (24 dev, 37 test)" — actual: 134 total, 63 dev, 71 `test_v2`.
* `LIMITATIONS.md` §3 says Baseline A "achieves higher raw event hit rates" while `evaluation_results.md` says CIF is higher — they contradict (and after F1 is fixed, the LIMITATIONS statement is the true one).
* `DEPLOYMENT.md` says "6 core surfaces" and "migrations v001-v006" (actual: 9 surfaces + repositories screen; migrations through 007).
* `readme.md` says "169+ tests" / hard-coded counts; `STATUS_AUDIT.md` contains the typo path `bbackend/`.
* `readme.md` contains presenter coaching ("What to say to your professor", "Answering the Professor") and calls refusal behaviour an "anti-hallucination guarantee" although measured refusal accuracy is 64.4%.
* Root contains `ANTIGRAVITY_HANDOFF*.md` and `implementation.md` (AI-agent prompts) with no AI-assistance disclosure; `scratch/extension_dev.key` (a private key) is inside the submitted zip (gitignored, but shipped).
* All 52 commits have a single author while the docs say "four-person team".

### F10 — Hosted product not live
No GitHub App registered, no public URL connected to a real repo; GitHub Pages is a static snapshot. Human Tasks H-A…H-E in `GITHUB_APP_SETUP.md` are open.

### F11 — Smaller defects
`datetime.utcnow()` deprecation (`backend/engine/staleness.py` ~284, `tests/test_staleness.py` ~196); sanitizer misses `sk-…`/`sk-ant-…`/`glpat-`/`sk_live_` style keys; shipped DB contains placeholder-titled decisions ("Architectural Decision dec_thermal_pid_01") created by running the demo against it.

---

## 3. Environment checklist (run once, report results)

```text
python --version                      # must be 3.11.x or 3.12.x
git --version
git status --short | more             # note what is untracked/modified
python -m unittest discover -s tests 2>&1 | tail -5     # expect: FAILED (failures=2) ONLY (F4)
python run_demo.py | tail -5          # expect 21/21
```
Create `BLOCKERS.md` (empty) if missing. Create `backups/` if missing.

---

# PHASES

## PHASE 0 — Safety net and tooling

### Step 0.1 — Backups and baseline hashes
**Do:**
```text
python -c "import shutil,datetime;t=datetime.datetime.now().strftime('%Y%m%d_%H%M');shutil.copy('context_intelligence.db',f'backups/context_intelligence.pre_v4_{t}.db');shutil.copy('whybench.db',f'backups/whybench.pre_v4_{t}.db');print('ok',t)"
python -c "import hashlib;[print(f,hashlib.sha256(open(f,'rb').read()).hexdigest()) for f in ('context_intelligence.db','whybench.db')]"
```
Save the two hashes in your report (used by Step 1.4).
**Accept:** two backup files exist; hashes recorded.
**Commit:** none (backups are gitignored).

### Step 0.2 — Snapshot commit of the current (untracked) work, history-honest
Goal: get Phase 7–9 into version control **before** any change, so history shows what existed.
**Do:**
1. `git status --short` — list everything. Confirm `.gitignore` excludes `*.db`, `*.key`, `*.pem`, `scratch/`, `dist/`, `backups/`, `__pycache__/`, `.env`.
2. **Move the private key out of the project folder** (do not delete, do not commit): create `%USERPROFILE%\cif-private\` and move `scratch/extension_dev.key` and `scratch/extension_dev.der` there. (The extension ID `pmkcmkalbgefpllgfmhgieeajolmefpi` is derived from the **public** key already embedded in `extension/manifest.json`, so nothing breaks.) Tell the human in the report.
3. `python tools/scan_secrets.py` — must report zero active secrets. If it reports anything, **stop** (Blocker), do not commit.
4. Commit in these groups (use `git add <paths>` explicitly; run `git status` between commits; never `git add -A` blindly):
   * `feat(auth): github login, sessions, repo access, ingestion jobs, webhook sync (phase 7)` → `backend/auth/ backend/config.py backend/security.py backend/ingestion/ backend/migrations/007_auth_and_repo_tables.py backend/db.py backend/api.py server.py tests/fixtures/ tests/test_auth_flow.py tests/test_add_repo.py tests/test_api_auth.py tests/test_config.py tests/test_job_runner.py tests/test_migration_auth_tables.py tests/test_repo_delete.py tests/test_repo_isolation.py tests/test_webhook_sync.py .env.example GITHUB_APP_SETUP.md PRIVACY.md`
   * `feat(web): login page, repository manager, mode badge (phase 7.9)` → `web/ docs/`
   * `feat(extension): chrome mv3 extension (phase 8)` → `extension/ tools/build_extension.py tools/generate_icons.py tests/test_extension_api.py`
   * `feat(vscode): vs code extension (phase 9)` → `vscode-extension/ tools/check_js.py`
   * `docs: status audit phases 7-9, deployment notes` → remaining docs + `STATUS_AUDIT.md DEPLOYMENT.md`
   * Anything left that `git status` still shows (inspect each file; if it is a build output or secret, add it to `.gitignore` instead).
5. `git tag pre-v4`.
**Verify:** `python -c "import subprocess;o=subprocess.run(['git','ls-tree','-r','HEAD','--name-only'],capture_output=True,text=True).stdout.splitlines();print(sum(1 for f in o if f.startswith(('backend/auth','extension/','vscode-extension/'))))"` prints a number **> 0**; `git status --short` shows nothing untracked except ignored items.
**Accept:** F3 resolved; no key/`.db`/`.env` in `git ls-tree -r HEAD --name-only`.
**Note:** Do **not** push here. Pushing is Human Task H-0 (§12) — GitHub push-protection may reject token-shaped strings; the human handles that.

### Step 0.3 — Line-ending guard tool
Create `tools/check_eol.py`: for each file in `git diff --name-only HEAD` that exists in HEAD, compare the EOL style of the HEAD version (`git show HEAD:path`, count `\r\n` vs bare `\n`) with the working copy; print `EOL CHANGED: path` and exit 1 if any differ; otherwise print `EOL OK` and exit 0. Use `subprocess` + `bytes` only.
**Verify:** `python tools/check_eol.py` → `EOL OK`. Add a unit test `tests/test_check_eol.py` using a temporary git repo (`git init` in `tempfile`) that proves it detects a CRLF→LF change.
**Commit:** `chore(tools): add EOL guard`

---

## PHASE 1 — Repository integrity (tests, tenancy, DB hygiene)

### Step 1.1 — Fix the time-bomb test (F4a)
**Do:**
1. Create `tests/helpers_time.py` with `def iso_z(offset_seconds=0): return (datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=offset_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")`.
2. In `tests/test_extension_api.py` replace the literal `'2026-10-18T10:00:00Z'` used for `repo_access.verified_at` with `iso_z()` (use a bound parameter, not string concatenation into SQL).
3. Run `git grep -n -E "20[0-9]{2}-[0-9]{2}-[0-9]{2}T" -- tests` and, for **every** hit, decide: does the value interact with "now", a TTL, an expiry or a lifetime (`repo_access`, `sessions`, `oauth_states`, `ext_codes`, `user_tokens`, webhook replay cache, staleness)? If yes, replace it with a relative value from `helpers_time`. Fixed historical data (event timestamps in fixtures, `as_of` cutoffs) stays. List every hit and your decision in the report.
4. Add `tests/test_no_clock_dependence.py` that scans `tests/*.py` for the pattern `verified_at.*20[0-9]{2}-` and `expires.*20[0-9]{2}-` and fails if found.
**Verify:** `python -m unittest tests.test_extension_api -v` passes; if `faketime` is available (Linux/WSL) also run it with `faketime '+90 days'`; otherwise note "faketime unavailable".
**Accept:** `test_per_repo_isolation_rule_r3` passes today and does not depend on the date.
**Commit:** `fix(tests): remove clock-dependent fixture in extension api test`

### Step 1.2 — Edges always carry `repo_full_name`; scope edge queries (F4b)
**Inspect first:** `git grep -n "INSERT.*INTO edges" -- backend tools tests`; `python -c "import sqlite3;c=sqlite3.connect('file:context_intelligence.db?mode=ro',uri=True);print([r[1] for r in c.execute('pragma table_info(edges)')])"` (expect a `repo_full_name` column as the last column).
**Do:**
1. In `backend/db.py` add `Database.resolve_edge_repo(conn, from_id, from_type, to_id, to_type)`: look up `repo_full_name` for each endpoint (`decisions`, `entities`, `events` tables, by id and type); return the first non-empty value; if endpoints disagree, return the **decision** endpoint's repo; if none found return `None`.
2. Change `upsert_edge()` and the raw inserts in `backend/engine/lifecycle.py` and `backend/engine/reconciliation.py` (and any other site found by the grep, including `drift_detector.py` ~470 which goes through `upsert_edge`) to write `repo_full_name`. If `resolve_edge_repo` returns `None`, raise `ValueError("cannot resolve repo for edge <id>")`. **If this breaks seeds or tests, fix the order of operations (persist the endpoint rows first) — do not relax the check or write NULL.**
3. Audit `backend/api.py` (~291 and ~379, and any other `FROM edges` / `FROM decisions` / `FROM events` query that serves HTTP) so results are filtered to repos the caller may read (reuse `authorize_repo` / the existing visible-repos helper from V3 Step 7.4). Anonymous users see only `visibility='demo'` repos.
4. Create `tools/repair_edge_repo.py` (pattern: `tools/repair_edge_validity.py`): dry-run by default, `--apply` makes an automatic backup into `backups/` first, fills NULL `repo_full_name` on `edges` using `resolve_edge_repo`, prints before/after counts.
5. Run the tool in dry-run on the real DB, then `--apply`.
6. Add `tests/test_edge_tenancy.py` (temp DB only): create decisions in repo X and repo Y; trigger (a) a supersession via `lifecycle.transition`, (b) a conflict via reconciliation, (c) a drift check that writes `drifts_from`; assert **no** edge has NULL `repo_full_name`, each equals its decision's repo, and that a user with access only to repo X never receives repo-Y drift edges from the two API routes.
**Verify:** `python -m unittest tests.test_edge_tenancy tests.test_migration_auth_tables tests.test_repo_isolation -v`; `python -c "import sqlite3;c=sqlite3.connect('file:context_intelligence.db?mode=ro',uri=True);print(c.execute('select count(*) from edges where repo_full_name is null').fetchone())"` → `(0,)`; full suite → **279+ tests, 0 failures**.
**Accept:** F4 fully resolved; run `python tools/check_eol.py`.
**Commit:** `fix(tenancy): write repo_full_name on every edge, scope edge queries, repair tool`

### Step 1.3 — Tests and demo must not touch the real databases
**Inspect:** how the DB path is chosen (`git grep -n "context_intelligence.db" -- backend server.py run_demo.py tests tools`).
**Do:**
1. Make `run_demo.py` operate on a **temporary copy** of a freshly seeded DB by default (add `--db PATH` to use a specific one; never default to the shipped DB).
2. Make any test or tool that currently opens `context_intelligence.db` / `whybench.db` use a temp copy (many already do — find the rest).
3. Create `tools/verify_db_untouched.py`: hash both DBs → run `python run_demo.py` and `python -m unittest discover -s tests` as subprocesses → hash again → exit 1 with a clear message if any hash changed.
4. Restore the shipped `context_intelligence.db` to a clean seeded state: `python tools/init_db.py --seed --fresh` **on a copy first**, inspect (6 or 7 decisions, no `Architectural Decision dec_*` placeholder titles unless they are produced by the seed itself, 0 NULL `repo_full_name`), then replace. Keep a backup.
**Verify:** `python tools/verify_db_untouched.py` → `DB UNTOUCHED`.
**Accept:** the guarantee in V2 rule 11 is now real and machine-checked.
**Commit:** `fix(tests): demo and tests never mutate shipped databases; add verifier`

---

## PHASE 2 — Honest evaluation (the most valuable phase)

### Step 2.1 — Fair Task-1 comparison without touching the frozen results
**Goal:** every system in a Task-1 table is scored on the **same questions**, and the correction is recorded as a *new* file.
**Do:**
1. Create `tools/recompute_task1_fair.py`:
   * Args: `--split test_v2` (default), `--db whybench.db`, `--out results/test_v2_20261013_100423/corrections_task1_fair.json`.
   * **Copies** the DB to a temp file, opens `Database(temp)`, loads questions for the split, defines positives as `expected_state != "none"`.
   * Runs `BaselineEvaluator.run_baseline_keyword` and `.run_baseline_docs_only` on **positives only**, overall and per repository.
   * Reads CIF numbers **from the existing manifest** (`results/latest_manifest.json`) — never re-runs CIF.
   * Writes JSON with: `generated_by`, `reason` ("baselines were originally scored over all questions incl. negatives; CIF over positives only"), `positives_n`, per-system `{hits, n, rate, wilson95_low, wilson95_high}`, per-repo equivalents, `cif_metric_definition` ("single strictly-matched decision cites ≥1 expected evidence event; not a ranked top-5 retrieval"), and `original_values` (the old 59.2 / 8.5 for traceability).
   * Wilson interval: `p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; (c-h, c+h)` with `z=1.96`; return `None` when `n==0`.
2. **Expected values to verify** (if they differ, report the actual values and stop to explain; do not force them): BM25 24/26 = 92.3%, Docs-only 6/26 = 23.1%, CIF 21/26 = 80.8% (Wilson ≈ 62%–91%).
3. Fix the **runner for future splits** (`tools/run_whybench.py`, around the `evaluate_all(split_questions)` call): pass `standard_questions` to the Task-1 baseline evaluation. Keep a separate "all questions" run only if a field explicitly named `*_all_questions` is needed. Rename the CIF metric **label** (not the JSON key, to avoid breaking the UI/tests) to "Decision-evidence hit rate" and add a `task_1_cif_metric_definition` field.
4. Make the report generator (`tools/generate_evaluation_report.py`) and the benchmark API route (find with `git grep -n "latest_manifest" -- backend tools web`) **overlay** `corrections_task1_fair.json` onto the baseline Task-1 numbers when present, while leaving the original manifest bytes untouched. The Task-1 table must show for every row: `hits/n`, rate, Wilson 95% interval, and a footnote: *"CIF's metric is decision-evidence match, not ranked retrieval; BM25 retrieval is higher. CIF's value is state classification, abstention and guard rules (see Task 2)."*
5. Update/add tests in `tests/test_benchmark.py` / a new `tests/test_fair_task1.py`: (a) baselines and CIF use the same `n`; (b) the overlay never mutates the original manifest; (c) Wilson values on known inputs (`wilson(21,26)` ≈ (0.62, 0.91)); (d) a regression test that fails if baselines are ever scored on a different question set than CIF.
6. Regenerate `evaluation_results.md` via the generator; run `python tools/build_static.py` so the Metrics page matches.
**Verify:** `python tools/recompute_task1_fair.py`; `python -m unittest tests.test_fair_task1 tests.test_benchmark -v`; `python tools/check_eol.py`; confirm `results/latest_manifest.json` and `results/test_v2_*/manifest.json` are **byte-identical** (`git diff --stat -- results` shows no change to them).
**Accept:** Metrics page, `evaluation_results.md`, README and `EVALUATION.md` all show BM25 **92.3%** vs CIF **80.8%** with the honest footnote.
**Commit:** `fix(evaluation): score all systems on the same questions, add intervals, keep frozen manifest intact`

### Step 2.2 — Replace over-claims with measured statements
**Do:** search `git grep -n -i -E "guarantee|never hallucinat|anti-hallucination|zero hallucination|100% accuracy" -- *.md web/*.html web/*.js docs/*.html docs/*.js backend tools`. For each hit decide:
* About **grounding invariant** (a decision cannot be saved without evidence): keep, it is mechanically enforced — but say "invariant", not "never lies".
* About **refusal/abstention**: replace with the measured value from the manifest: "abstains correctly on 29/45 (64.4%) of unrecorded-topic questions; 16/45 receive an unsupported decision — see LIMITATIONS". Compute the text from the manifest in the generator, do not type numbers by hand.
* "100% state accuracy": always write "100% (21/21 matched decisions)" and note small n.
**Accept:** no unqualified "guarantee"/"never hallucinates" remains. Mirror `web/` → `docs/` with `tools/build_static.py`.
**Commit:** `docs: replace over-claims with measured statements`

### Step 2.3 — Honest labelling of WhyBench as synthetic (F2)
**Do (docs/labels only — no data or hash changes):**
1. Rename the display name everywhere from "WhyBench (real-world corpus)" to **"WhyBench-Synth (hand-authored synthetic benchmark)"**. Keep the dataset id `whybench_v1` and file/directory names unchanged (they are hashed).
2. Rewrite `backend/evaluation/whybench/REPOS.md`: remove "Pinned Commit SHA", "Tagged", "Snapshot Date" and "Why Chosen: real…" claims. State plainly: *"These repositories are **fictional event sets** hand-written by the team to resemble the decision style of well-known projects. Project names are used only as realistic domain labels. No event, quote, author handle, PR/issue number or URL is claimed to exist in the real project, and no statement is attributed to any real person. Source URLs are illustrative and may not resolve."* `payment-core` = "team-authored synthetic repository (same domain as `demo_sample_repo`)".
3. Update `EVALUATION.md`, `LIMITATIONS.md`, `evaluation_results.md` generator text, README, `explanation.md`, `task.md`, `web/index.html` + `web/app.js` strings, `FROZEN.md` prose (prose only; do not touch the hash tables) so none says "real-world", "open-source repositories", "grounded in public GitHub URLs" for WhyBench. Add to `LIMITATIONS.md` a first section: **"WhyBench is synthetic; results show internal consistency, not generalisation to real repositories."**
4. Add a UI/report banner on the Metrics page: "Synthetic benchmark — see LIMITATIONS".
5. Add `tests/test_docs_honesty.py`: fails if any tracked `.md`/`.html`/`.js` under repo root, `web/`, `docs/` contains `real-world benchmark`, `Pinned Commit SHA`, `open-source repositories` or `public GitHub URLs` (allow in `docs/process/` and `STATUS_AUDIT.md` historical quotes by exact-path allowlist).
**Verify:** `python tools/validate_whybench.py` still passes (hashes unchanged); `python -m unittest tests.test_docs_honesty -v`.
**Accept:** `git diff --stat` shows **no change** to `questions.json`, any `events.json`, `precision_labels.json`, or hash values.
**Commit:** `docs(evaluation): label whybench as synthetic; remove fabricated provenance claims`

### Step 2.4 — Make LIMITATIONS and EVALUATION internally consistent (F9a)
Derive numbers from data, not by hand: add `tools/print_facts.py` that prints question counts per split/repo (from `questions.json`), number of tests (`unittest` discovery count), migrations count (`backend/migrations/*.py` numbered), UI surface count (`data-view` ids in `web/index.html`). Use its output to fix: `LIMITATIONS.md` §2 (134 total: 63 dev, 71 `test_v2`), §3 (state truthfully: BM25 retrieves more events than CIF on the 26 positives; CIF adds state/abstention/guard), `DEPLOYMENT.md` (surfaces, migrations v001–v007), README counts (replace hard numbers with "run `python tools/print_facts.py`"), `STATUS_AUDIT.md` (`bbackend/` → `backend/`, exact-string replace, nothing else).
**Commit:** `docs: fix stale counts and contradictions`

---

## PHASE 3 — Engine correctness

### Step 3.1 — Conflict detector: word boundaries and data-driven pairs (F6, F5-part)
**Do:**
1. In `backend/engine/reconciliation.py` replace substring tests with word-boundary regex (`re.search(rf"\b{re.escape(term)}\b", text)`).
2. Move the pair list out of code into `backend/engine/conflict_pairs.json` with two sections: `"generic"` (`sync/async`, `polling/websocket`, `stateless/stateful`, `monolith/microservice`, add a few more generic ones) and `"demo"` (`pid/bang-bang`, `redis/in-memory lru`) — the `"demo"` section applies **only** to repos whose `repos.visibility = 'demo'`. The engine contains no domain words.
3. Tests `tests/test_conflict_pairs.py`: two async decisions → **no** conflict; sync vs async (whole words) → conflict; "asynchronous" alone does not match `async`; demo pairs apply only to demo repos; the existing demo conflict check in `run_demo.py` still passes.
**Verify:** F6 reproduction now prints `False` when run through the new function; full suite green.
**Commit:** `fix(reconciliation): word-boundary conflict matching, data-driven pairs`

### Step 3.2 — Generic guard-rule synthesis + untouched hold-out evaluation (F5)
**Goal:** no scenario vocabulary in engine code; honest, held-out drift metrics.
**Order matters — do 3.2a first and commit it before touching any engine code.**

**3.2a — Create the hold-out set (frozen before the fix):**
1. Create `backend/evaluation/holdout/decisions.json` (3–4 decisions in a **third domain** unrelated to thermal/cache/payments, e.g. job queue / auth tokens / logging) written as plain decision text (title, rationale, state, rejected alternative description) — the kind of text the synthesizer will actually see.
2. Create `backend/evaluation/holdout/cases.json`: **≥15** diff cases (≥7 violations, ≥8 clean/negative, including tricky negatives: the forbidden word appearing in a comment, in a deletion line, or as a substring of a different word) in the same schema as `drift_cases.json`.
3. Write `backend/evaluation/holdout/FROZEN.md` with SHA-256 of both files (`python -c "import hashlib;..."`). Commit: `test(evaluation): freeze drift hold-out set before generalising guard rules`.
4. **Do not look at hold-out results while changing the synthesizer.** Run the hold-out evaluator **once** at the end of 3.2c.

**3.2b — Generalise the engine:**
1. `backend/engine/guard_rules.py`: delete every scenario-specific branch (the lists/paths named in F5). Replace by generic extraction from the decision's **own text and links**:
   * identifier candidates = backticked spans, `import X` / `from X import` / `require("X")` / `use X` patterns, `snake_case` tokens with `_` (≥5 chars), `CamelCase` tokens, dotted module names;
   * for a **rejected** decision (or the "rejected alternatives" of an accepted one): identifiers that appear in the rejected text but **not** in the accepted decision's text → `forbid_pattern` with a word-boundary regex (`\b…\b`, regex-escaped), `forbid_import` when it looks like a module;
   * `paths` come from the decision's affected entities (directory of each artifact + same extension glob), falling back to `**/*` — never from hard-coded globs;
   * `require_import` only from explicit backticked phrases such as "must use `X`";
   * all synthesized rules keep `status="proposed"` (a human activates them) and `source="synthesized"`.
2. `backend/engine/rejected_idea_guard.py`: delete the hard-coded `alt_sig_words` list; derive concept tokens with the same extraction function (share the helper, put it in `backend/engine/identifiers.py`).
3. For the two demo repos, keep the demo working by **authoring** their rules as data: add explicit guard rules in `backend/seed_data.py` with `source="authored"` (data, not engine code). Reproduce the previous demo behaviour (Scenarios 1–4 in the UI, `run_demo.py` checks, `tests/test_guard_rules.py`, `tests/test_drift_rules.py`).
4. Fix the docstring claim in `drift_detector.py` so it is true; remove stale words in docstrings (`redis==4.5.1` → `requests==2.31.0` in `entity_res.py` / `staleness.py`).
5. Tests: `tests/test_generic_guard_synthesis.py` — table-driven on neutral text (no domain words) covering each extraction pattern, word-boundary behaviour, path derivation, and "no rule from accepted-only words".
**Verify:** `git grep -n -i -E "pid|redis|thermal|bang|deadband|stripe|braintree|userfaultfd|psycopg2|hysteresis|dict_cache|sticky_sessions" -- backend/engine` returns **no hits** (allowed elsewhere: `seed_data.py`, `ingestion/`, `tests/`, `evaluation/`, `conflict_pairs.json` demo section).

**3.2c — Measure honestly:**
Create `tools/run_holdout.py` (copy-based, no network): synthesizes rules from `holdout/decisions.json`, runs them over `holdout/cases.json`, writes `backend/evaluation/holdout/results.json` with TP/FP/TN/FN, precision, recall, per-case outcomes. Also re-run the original `drift_cases.json` evaluation and report both **separately**. **Report whatever comes out.** If hold-out recall is lower than 100%, that is the true, defensible number; put it in `evaluation_results.md` (generator) with the sentence "original 20 cases use authored demo rules; hold-out measures generalisation".
**Accept:** engine has no domain vocabulary; `run_demo.py` 21/21; full suite green; hold-out results recorded once.
**Commit (3 commits):** `test(...) freeze hold-out` → `refactor(guard): generic rule synthesis; author demo rules as data` → `feat(evaluation): hold-out drift evaluation`

### Step 3.3 — No more swallowed exceptions (F7)
1. `rejected_idea_guard.py` regex compile: catch `re.error` only, `logger.warning("invalid guard regex", extra rule_id...)` (no diff content), and append to the report's `errors` list so the result is `status: "incomplete"` (same contract as V2 Step 1.4).
2. `security.py::get_cors_origin`: catch only `(ImportError, AttributeError, ValueError)`, log at warning level, return `None`.
3. `git grep -n -B1 -A2 "except Exception" -- backend` → for every remaining hit confirm it logs and does not silently continue; list them in the report.
4. Tests for both paths (invalid regex → incomplete status; config failure → origin denied + warning logged).
**Commit:** `fix(reliability): surface guard-rule and cors errors instead of swallowing`

### Step 3.4 — Sanitizer coverage
In `backend/ingestion/sanitizer.py` add patterns (and replacement tokens) for: `sk-` + 20+ url-safe chars (`[REDACTED:API_KEY]`), `sk-ant-…`, `sk_live_`/`rk_live_` (Stripe), `glpat-` (GitLab), `npm_` + 36 chars, `xapp-`, `Bearer`-less `Authorization: Basic …`. Keep optional PII flags unchanged (emails stay opt-in; state this in `PRIVACY.md`). Tests in `tests/test_sanitizer.py`: build every sample token **by concatenation**; add false-positive guards (`task-force-1`, `sk-learn` must not be redacted — require ≥20 following chars). Update the table in `PRIVACY.md`.
**Commit:** `feat(privacy): redact more provider key formats`

### Step 3.5 — `utcnow()` deprecation
Replace `datetime.utcnow()` everywhere in `backend/`, `tools/`, `tests/` with `datetime.now(timezone.utc)`. **Keep output format byte-identical**: where the old code did `datetime.utcnow().isoformat() + "Z"` use `datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"`. Verify no `DeprecationWarning` in `python -W error::DeprecationWarning -m unittest discover -s tests` (if third-party noise appears, report it).
**Commit:** `chore: replace deprecated utcnow`

---

## PHASE 4 — Close the measurement gaps (tooling; humans supply keys/labels)

### Step 4.1 — Baseline C (plain LLM) implementation
Implement `BaselineEvaluator.run_baseline_llm` (currently a stub at `backend/evaluation/baselines.py` ~179). Requirements:
* Runs only when `CIF_LLM_API_KEY` and `CIF_LLM_MODEL` are set **and** `CIF_LOCAL_ONLY != "1"`; otherwise returns `status: "not measured"` with the reason (current behaviour).
* Provider switch via `CIF_LLM_PROVIDER` (`openai` = any OpenAI-compatible chat-completions endpoint via optional `CIF_LLM_BASE_URL`; `anthropic` = messages API). Standard library `urllib` only, TLS verification on (reuse the project's secure SSL context), timeout 60 s, 2 retries.
* Input per question = **sanitized** repo event stream for that repo (all events, title/body/source_id/event_id) + the question. Prompt: *answer only from the events; return JSON `{"decision_found": bool, "state": "...", "evidence_event_ids": [...], "answer": "..."}`; if there is no recorded decision set `decision_found=false`*. Temperature 0.
* Scoring: **same 26 positives and same 45 negatives**; Task-1 hit = cited ids intersect expected ids; Task-2 state accuracy among found; refusal accuracy = `decision_found=false` on negatives; unsupported-claim rate = cited ids not present in the event stream. Report `n`, rate, Wilson interval.
* Cache raw model outputs to `results/llm_baseline_<model>_<date>.jsonl` (no keys inside) so the run is auditable. Never print the key.
* Unit tests with a **mock transport** only (no network): parse good/garbled JSON, retries, local-only short-circuit, key never in logs.
**Commit:** `feat(evaluation): implement plain-LLM baseline with audit log`
**Human Task H-2 runs it** (needs an API key and costs money).

### Step 4.2 — Baseline D (Copilot) importer
Replace the empty CSV workflow with: `backend/evaluation/manual_copilot_results.csv` columns `question_id,answer_correct,answer_has_invented_reason,cited_real_source,notes` (values `1/0`), and a `tools/make_copilot_sheet.py` that writes a **printable sheet** (`results/copilot_sheet.md`) listing the 26 positive + 10 sampled negative questions (fixed seed 1234) with the repo's event text so a human can paste them into Copilot. The runner reads the CSV and reports `evaluated_samples`, accuracy, invented-reason rate with Wilson intervals; with 0 rows it stays `not measured`. Validate rows (unknown ids, non-binary values → error, not skip).
**Commit:** `feat(evaluation): copilot manual-trial sheet generator and importer`
**Human Task H-3 fills it.**

### Step 4.3 — Precision labelling that survives snapshot changes
The manifest reports `snapshot hash mismatch`. Do:
1. Regenerate the labelling sample against the **current** DB hash using `tools/make_precision_sample.py` (read it first; it already records the snapshot hash). Output to a **new** file `backend/evaluation/whybench/precision_labels.json` only if the existing one has all `correct: null` (it does — confirm), keeping the old one in `backups/`.
2. Add `tools/precision_sheet.py` that exports the sample to `results/precision_sheet.csv` (id, decision title, rationale, cited events text, blank `correct`, blank `reason`) and `--import` that validates and writes labels back (only `true`/`false`; hash must match).
3. Never fill labels yourself.
**Commit:** `feat(evaluation): precision labelling sheet export/import bound to snapshot hash`
**Human Task H-4 labels** (aim ≥ 65; ≥ 100 enables calibration).

### Step 4.4 — User-study kit
Create `user_study/` containing: `PROTOCOL.md` (goal; 5–8 participants; two tasks of "find why X exists in repo Y" — one with CIF, one with GitHub search only; counterbalanced order; 10-minute cap; measure time-to-answer, correctness vs ground truth, confidence 1–5), `CONSENT.md` (anonymous, voluntary), `TASKS.md` (tasks drawn from **dev** questions on the demo repos), `results_template.csv`, and `tools/analyze_user_study.py` (reads the CSV; prints per-condition mean/median time, correctness rate, paired differences, Wilson intervals; refuses to print conclusions when n < 5; **no fabricated rows**). Unit test with a tiny synthetic CSV marked as test data.
**Commit:** `feat(evaluation): user-study protocol, templates and analyzer`
**Human Task H-5 runs the study.**

---

## PHASE 5 — Documentation, disclosure, professionalism

### Step 5.1 — README becomes project documentation
Move the presenter coaching out of `readme.md` into `docs/process/PRESENTER_NOTES.md` (keep it — the author may need it; mark it "speaker notes, not project documentation"). `readme.md` keeps: what/why, architecture, setup, run, test, evaluation summary (numbers pulled from the manifest/corrections by `tools/print_facts.py` or quoted with their source file), limitations link, privacy link, extension setup links. Fix the "What it tests" claims in §4 to match `run_demo.py`. Remove every hard-coded count that can go stale; point to the command.
**Commit:** `docs(readme): separate project documentation from presenter notes`

### Step 5.2 — Process documents and AI-assistance disclosure
1. `git mv` `ANTIGRAVITY_HANDOFF.md`, `ANTIGRAVITY_HANDOFF_V2.md`, `ANTIGRAVITY_HANDOFF_V3_EXTENSION.md`, `ANTIGRAVITY_HANDOFF_V4_FIXES.md`, `implementation.md` into `docs/process/`. Fix every reference (`git grep -n "ANTIGRAVITY_HANDOFF\|implementation.md"` across docs, `FROZEN.md`, tools, tests) — **update paths, do not delete references**. Do not delete any process file.
2. Create `AI_ASSISTANCE.md` at root with **facts only**: that AI coding agents were used, which tool(s), for what (implementation from written specifications, test writing, documentation), and a section **"Author responsibilities"** with placeholders marked `TODO(human)` for: what the student designed/decided, what they reviewed, which modules they can explain. Do **not** invent anything the student did; leave `TODO(human)` markers. Add the course-policy reminder: "check UCS503 policy on AI tool use". (Human Task H-6.)
3. Add a one-line link to `AI_ASSISTANCE.md` in `readme.md`.
**Commit:** `docs: move process docs, add AI assistance disclosure template`

### Step 5.3 — Team contribution record
Create `CONTRIBUTIONS.md` with a table template (member name, areas owned, evidence = commit/PR links) containing only `TODO(human)` cells. Run `git shortlog -sn HEAD` and put the **actual** author counts in a "Git history facts" section. Do not infer or assign work to people.
**Commit:** `docs: contribution record template with git facts`

### Step 5.4 — Docs consistency checker in CI
Create `tools/check_docs.py` (reuses `print_facts.py`): fails on banned strings (`bbackend`, `61 labelled`, `169+`, `6 core surfaces`, `v001-v006`), on references to missing files (parse markdown links `](path)` and backticked `*.md`/`*.py` paths that look repo-relative and check existence, ignore URLs and `file:///c:/Users/...` legacy links — **convert those legacy absolute `file:///c:/Users/HP/...` links to repo-relative links** in the root docs so they work for every reader), and on `TODO(human)` only if run with `--strict`. Add it to `.github/workflows/tests.yml` as a step after the unit tests.
**Commit:** `ci: docs consistency check; make doc links repo-relative`

---

## PHASE 6 — Deployment readiness and release

### Step 6.1 — Make the app deployable and checkable
1. Add `GET /healthz` (public, no DB write, returns `{"status":"ok","mode":"live|static","db":"ok"}`) and a test.
2. Verify the `Dockerfile` builds and runs: if Docker is available, `docker build -t cif .` and `docker run -p 8080:8080 -e CIF_BIND=0.0.0.0 cif`, then `curl /healthz`; otherwise state "docker unavailable" and static-review the file (persistent volume for the SQLite DB path, non-root user, `PORT` env). Add a `VOLUME`/documented mount for the DB.
3. Create `DEPLOY_LIVE.md`: exact checklist for a free host (Render/Fly.io/Railway or a Cloudflare tunnel from a laptop): env variables from `.env.example`, persistent disk, HTTPS, GitHub App callback/webhook URLs, how to verify with `GET /healthz`, `GET /api/auth-config`, webhook "Recent Deliveries", and where to save screenshots (`docs/evidence/`). Mark every step that needs a human account as Human Task.
**Commit:** `feat(deploy): healthz endpoint, deployment checklist`

### Step 6.2 — Pages workflow must work from a clean checkout
`*.db` is gitignored, but `.github/workflows/deploy.yml` runs `python tools/build_static.py`. Verify on a clean clone (`python tools/clean_clone_check.py` or `git clone . %TEMP%\cif_clean`) whether it needs a seeded DB; if so add `python tools/init_db.py --seed` before the build step. Confirm the workflow's `git diff --exit-code web docs` check passes after `build_static.py`. Add the test workflow badge to README.
**Commit:** `ci: deploy workflow seeds db on clean checkout`

### Step 6.3 — Clean-clone and package verification
Run `python tools/clean_clone_check.py` (must: clone to temp dir, init DB, secret scan, full unit tests, demo — all pass). Run `python tools/package_release.py` and verify the produced zip contains **no** `*.key`, `*.pem`, `.env`, `*.db`, `scratch/`, `backups/`, `__pycache__/`, and **does** contain `extension/`, `vscode-extension/`, `backend/auth/`, `docs/process/`. Print the zip's file list to the report. Re-run `python tools/scan_secrets.py` and update `SECURITY_SCAN.md` (date, scope now includes Phase 7–9 files, honest counts).
**Commit:** `chore(release): verify clean clone and package contents; refresh security scan`

### Step 6.4 — Final audit and tags
1. Append **"Phase 10 — Review fixes (v4)"** to `STATUS_AUDIT.md`: for each of F1–F11 status (RESOLVED / PARTIAL / OPEN-HUMAN), file list, verification output. Honest: items needing humans stay `OPEN-HUMAN`.
2. Final gates (all must pass; paste outputs in the report):
   * `python -m unittest discover -s tests` → 0 failures
   * `python run_demo.py` → 21/21
   * `python tools/verify_db_untouched.py` → DB UNTOUCHED
   * `python tools/validate_whybench.py` → frozen hashes intact
   * `python tools/check_docs.py` → OK
   * `python tools/check_eol.py` → EOL OK
   * `python tools/scan_secrets.py` → 0 active
   * `git status --short` → clean
3. `git tag v4-review-fixes`. **Do not push.**
**Commit:** `docs(audit): phase 10 review fixes`

---

## 12. Human tasks (never fake; list in the final report with status)

| ID | Task | Needed for |
|---|---|---|
| H-0 | `git push origin main` and `git push --tags`; if GitHub push-protection blocks a token-shaped string, report the file/line (do not bypass the protection). Check Actions tab: tests, docs check, Pages deploy all green. | F3, CI |
| H-1 | **Build a genuinely real corpus (strongly recommended, biggest eval upgrade):** pick 2 public repos that really contain decision records (candidates to *verify by opening them first*: `backstage/backstage` → `docs/architecture-decisions/`, `adr/madr` → `docs/decisions/`), ingest with CIF's own GitHub ingestion (needs `GITHUB_TOKEN` or the GitHub App), hand-label 25+ real decisions with real URLs, freeze a new split **before** running CIF, run once. Name it `WhyBench-Real`. | F2 |
| H-2 | Run Baseline C with a real API key (`CIF_LLM_API_KEY`, `CIF_LLM_MODEL`), keep the audit log. | F8 |
| H-3 | Fill `manual_copilot_results.csv` from real Copilot answers for the sheet. | F8 |
| H-4 | Label the precision sheet (≥65, ideally ≥100). | F8 |
| H-5 | Run the user study with real participants. | F8 |
| H-6 | Fill every `TODO(human)` in `AI_ASSISTANCE.md` and `CONTRIBUTIONS.md` truthfully; check the course AI-use policy. | F9 |
| H-A…H-E | Register the GitHub App, live login walk-through with screenshots, load the Chrome extension, public HTTPS tunnel/host, two demo PRs (one violating, one clean) — per `GITHUB_APP_SETUP.md`. | F10 |
| H-7 | Deploy per `DEPLOY_LIVE.md`, connect one of the team's **own** repos, save screenshots/video to `docs/evidence/`. | F10 |
| H-8 | Review the extension private key location (`%USERPROFILE%\cif-private\`) and keep it out of any submission zip. | F9 |

---

## 13. Pitfalls (read before coding)

* **CRLF.** Exact-match replacement fails or silently converts EOLs. Detect, preserve, run `check_eol.py`.
* **`Database(path)` runs migrations.** Never point it at a shipped DB for experiments; always copy.
* **Frozen files.** A one-byte change to `questions.json` or an `events.json` changes hashes and invalidates the frozen split. If `validate_whybench.py` fails, `git checkout -- <file>` the file and find another way.
* **Do not "fix" numbers by changing the denominator back.** The honest values are BM25 92.3%, Docs-only 23.1%, CIF 80.8% on the same 26.
* **Do not hide the AI-assistance files.** Move and disclose; never delete.
* **Generalising the guard may lower the demo metrics.** That is acceptable and expected; report it. Never re-add domain words to make a number look better.
* **Windows paths in tests.** Use `pathlib`/`os.path.join`; avoid hard-coded `/` in assertions.
* **Token-shaped test strings** must be concatenated (rule 8) or push-protection will block the push.
* **Do not run `python tools/run_whybench.py --split test_v2`** in any form.
* **Never default to the real DB** in new scripts.

---

## 14. Reporting format (after every step)

```text
STEP <n.m> — <title>
Status: DONE | PARTIAL | BLOCKED | NOT REPRODUCED
Reproduction (before): <command + short output>
Files changed: <list>
Verification (after): <commands + key output lines>
Acceptance: <each line ✔/✘>
EOL check: OK | list
Commit: <short hash> <message>
Deviations / findings: <anything that differed from this document and what you did>
Human tasks raised: <ids or none>
```

---

## 15. Definition of done (v4)

- [x] Phase 7–9 code is committed (F3) and tagged `pre-v4`; no secrets/keys/DBs in git.
- [x] 0 failing tests; no clock-dependent fixtures; edges always carry `repo_full_name`; edge API queries are repo-scoped (F4).
- [x] Tests/demo never modify the shipped databases, verified by a tool (Step 1.3).
- [x] Every Task-1 table compares systems on the **same** questions with intervals and an honest footnote; frozen manifests untouched (F1).
- [x] WhyBench is labelled synthetic everywhere; no fabricated provenance claims remain; frozen hashes intact (F2).
- [x] No domain vocabulary in `backend/engine`; hold-out drift results recorded once and reported as-is (F5); word-boundary conflicts (F6); no silent exceptions (F7).
- [x] Baseline C/D, precision-labelling and user-study **tooling** exists; unmeasured items still say `not measured` until a human runs them (F8).
- [x] README is project documentation; process docs moved to `docs/process/`; `AI_ASSISTANCE.md` and `CONTRIBUTIONS.md` exist with `TODO(human)` markers for the student (F9).
- [x] Docs checker, EOL checker and tests run in CI; clean-clone check and package contents verified; `STATUS_AUDIT.md` has a Phase 10 section with honest `OPEN-HUMAN` items.
- [x] Final report lists every Human Task (§12) with its status.

If any box is unchecked, that is the remaining work.

---

## 16. Start here

1. Read this file completely, then `ANTIGRAVITY_HANDOFF_V2.md` §1 and `ANTIGRAVITY_HANDOFF_V3_EXTENSION.md` §1.
2. Do §3 (environment checklist) and send its report.
3. Begin at **Step 0.1**. Do not skip ahead. Do not start Phase 2 before Step 1.3 is green.
