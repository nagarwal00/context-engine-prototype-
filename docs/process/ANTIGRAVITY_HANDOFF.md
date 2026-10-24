# ANTIGRAVITY HANDOFF — Context Intelligence Framework (CIF)

> **Read this entire file before touching any code.**
> Work **one step at a time**, in order. After each step: run its **Verify** command, report the result in the format in §12, then continue. Never skip a step, never batch several steps into one change, and never mark a step done unless its acceptance criteria are met.

---

## 0. Mission

This is a 17-week university software-engineering capstone (course UCS503, four-person team). The project reconstructs **why** a software project looks the way it does: decision → alternatives → evidence → code change → present implementation.

A working prototype already exists (see §2). Your job is to take it from "demo that looks complete" to "project whose results are real and defensible in front of a professor."

The professor has already challenged the idea once: *"AI agents can do this, and developers already write READMEs/docs for this."* The project's answer must therefore be **measured evidence**, not claims. That is why Phase 1 and Phase 2 (honest evaluation) come before any new feature.

---

## 1. Non-negotiable rules

Break any of these and the work is considered wrong, even if the code runs.

1. **Never hard-code a metric, score, percentage, latency, or baseline result.** Every number shown anywhere (API, UI, README, slides) must be computed by code from real data, or be displayed as `not measured`. Inventing or "estimating" numbers is forbidden.
2. **Never tune against the test set.** Data is split into `dev` and `test` (§Phase 2). You may look at `dev` while improving the system. You may run `test` only to report final results.
3. **Keep the evidence invariant.** A decision whose state is anything except `unresolved` must have at least one evidence event. Do not weaken this check in `backend/db.py`.
4. **Do not break the existing checks.** `python run_demo.py` must stay at 21/21 passing after every step (until you intentionally replace a check in Step 1.4, and then the replacement must be stricter, not looser).
5. **Standard library only** for the backend and tests (Python 3.11 or 3.12). No new pip packages unless a step explicitly marks one as *optional*, and the code must still work when it is missing.
6. **Windows-safe.** The author runs this on Windows (`C:\Users\HP\Desktop\SE_project`). Use `os.path`/`pathlib`, open files with `encoding="utf-8"`, never assume `/` paths or a Unix shell in code.
7. **Never commit secrets.** Tokens come from environment variables (`GITHUB_TOKEN`, `CIF_LLM_API_KEY`, `CIF_WEBHOOK_SECRET`). Never print or log them.
8. **Back up before destructive actions.** `context_intelligence.db` currently holds real ingested data. `/api/clear-db` and `/api/reseed` wipe it. Copy it to `backups/` first.
9. **Smallest change that satisfies the step.** No unrelated refactors, renames, or reformatting.
10. **If blocked**, write the problem to `BLOCKERS.md` (what you tried, exact error, what you need), then move to the next *independent* step. Do not guess around a blocker.

---

## 2. Current state (verified by running the code)

### 2.1 What works

| Area | Where | Notes |
|---|---|---|
| Server | `server.py` | `ThreadingHTTPServer` on `127.0.0.1:8080`, serves `web/` + `/api/*`. Seeds DB if empty. |
| Database | `backend/db.py` | SQLite file `context_intelligence.db`. Tables: `events, entities, decisions, decision_evidence, decision_artifacts, edges, identities, state_history`. Methods: `upsert_event`, `upsert_entity`, `save_decision` (enforces evidence invariant), `upsert_edge`, `upsert_identity`, `query_decision_chain_for_artifact`, `query_full_evidence_trail`, `query_timeline_slice`. |
| Models | `backend/models.py` | Dataclasses: `Event`, `AlternativeConsidered`, `StateChange`, `Decision`, `Entity`, `Edge`, `Identity`. |
| Ingestion | `backend/ingestion/` | `git_adapter.py`, `github_adapter.py`, `adr_adapter.py` (Nygard ADR format), `identity.py`, `live_github.py` (GitHub REST API + local folder ingestion). |
| Engine | `backend/engine/` | `entity_res.py` (Python AST function-level entities), `graph.py` (temporal graph, `valid_from`/`valid_to`), `extractor.py`, `reconciliation.py` (conflict + supersession), `drift_detector.py`, `explanation.py`. |
| API | `backend/api.py` | GET: `/api/timeline /graph /artifacts /explain /decisions /evidence /review-queue /benchmark /stats /repos`. POST: `/api/review-action /drift-check /reseed /ingest-repo /clear-db`. |
| UI | `web/` (`index.html`, `app.js`, `style.css`) | 9 surfaces: timeline, graph, code-context, decision explorer, evidence panel, review queue, onboarding, live CI drift tester, metrics. |
| Static demo | `docs/` + `.github/workflows/deploy.yml` | GitHub Pages deploys `docs/`. It runs from `static_data.js` (a frozen JSON snapshot), **not** from the Python engine. |
| Checks | `run_demo.py` | 21 checks, all pass. |
| Demo data | `demo_sample_repo/`, `backend/seed_data.py` | Two synthetic pilot repos: `acme-eng/thermal-control-system` (PID vs deadband) and `acme-eng/distributed-cache-service` (LRU vs Redis). |

### 2.2 Verified problems (these are the work)

| # | Problem | Evidence |
|---|---|---|
| P1 | **Benchmark numbers are hard-coded.** `backend/evaluation/benchmark.py` assigns `precision = 0.941`, `recall = 0.912`, `conflict_precision = 0.923`, `drift_precision = 0.947`, `avg_processing_latency_ms = 42.6`, and the whole `baselines` dictionary (grep 18.5%, Copilot 54% / 16.8% hallucination, ADR 31%, onboarding "4.2 min" etc.) as literals. The code that computes matches (`matched_gt`, `correct_states`) is never used in the output. | Read the file. |
| P2 | **Ground truth does not match the seed data.** `ground_truth.py` has **32** labelled decisions; `populate_seed_data()` creates only **4** decisions. A fresh seed + the existing matching logic matches **5 of 32**. Reported recall (91.2%) is therefore false. | Ran it. |
| P3 | **Evaluation is circular.** The seeded repos and the ground truth were written by the same team, so the system is tested on data written for it. | By construction. |
| P4 | **"Unsupported claim rate 0.0%" is true by construction.** It only checks that each chain step has *some* citation, not that the claim is supported by the cited text. | `benchmark.py`, section 4. |
| P5 | **Extractor is keyword/regex only.** `extractor.py` uses markers like `"decided to"`, `"instead of"`. The spec (`implementation.md` §6.4) says LLM-assisted. | Read the file. |
| P6 | **Noisy decisions on real repos.** The current DB holds decisions such as "Added README" and "Added requirements.txt" (ingested from a real repo). Trivial commits are being treated as architectural decisions. | Query `decisions` in `context_intelligence.db`. |
| P7 | `state_history` table has **0 rows** — lifecycle transitions are not being recorded in practice. | DB query. |
| P8 | No GitHub App / webhook / CI integration exists although the scope requires one. No Slack source. | `grep` shows none. |
| P9 | `docs/static_data.js` is described as "auto-generated" but **no generator script exists** in the repo. `docs/` is a manual copy of `web/`. | `grep -rn build_static` → nothing. |
| P10 | `test_suite.db` is empty; `__pycache__/*.pyc` files are in the zip; no real unit-test suite (only `run_demo.py`). | File listing. |
| P11 | Docs overclaim: `readme.md` says "6 UI surfaces" (there are 9) and quotes the hard-coded metrics; `task.md` marks everything 100% complete. | Read files. |

---

## 3. Working environment checklist (do this once, first)

```text
cd C:\Users\HP\Desktop\SE_project        # or the folder where the project was unzipped
python --version                         # must be 3.11 or 3.12
python run_demo.py                       # must print 21/21
python server.py                         # must print SERVER LIVE on 127.0.0.1:8080
```

Open `http://127.0.0.1:8080/` once and confirm the dashboard loads, then stop the server (Ctrl+C).

If any command fails, **stop and fix the environment before changing code** (write the error to `BLOCKERS.md` if you cannot).

---

# PHASES

Order is fixed: **0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9**. Phase 6 is optional stretch.

---

## PHASE 0 — Safety net

### Step 0.1 — Version control and backups
- **Do:** If the folder is not a git repo, run `git init`, commit everything as `chore: baseline before handoff work`. Create `backups/` and copy `context_intelligence.db` to `backups/context_intelligence.pre_handoff.db`. Add `backups/` and `*.pyc` to `.gitignore`.
- **Accept:** `git log` shows the baseline commit; backup file exists; `.gitignore` updated.
- **Verify:** `git status` clean; `python run_demo.py` → 21/21.

### Step 0.2 — Create the test scaffold
- **Do:** Create `tests/__init__.py` and `tests/test_smoke.py` using `unittest`. One test: import `backend.db.Database`, create it on a temporary file path, call `populate_seed_data`, assert decisions count > 0. Tests must **never** touch `context_intelligence.db` — always use `tempfile`.
- **Accept:** `python -m unittest discover -s tests -v` passes.
- **Verify:** that command, plus `python run_demo.py`.

### Step 0.3 — Remove junk from the repo
- **Do:** Delete all `__pycache__` folders from the tracked files (`git rm -r --cached` if tracked). Delete empty `test_suite.db`. Do **not** delete `context_intelligence.db`.
- **Accept:** `git ls-files | findstr pyc` (or `grep pyc`) returns nothing.
- **Verify:** `python run_demo.py` still 21/21 (Python regenerates caches; they are now ignored).

---

## PHASE 1 — Make the evaluation honest (HIGHEST PRIORITY)

Goal: every metric is computed from data. Baselines are real runnable baselines or are marked `not measured`.

### Step 1.1 — Define the metrics precisely (write the spec first)
Create `backend/evaluation/METRICS.md` containing exactly these definitions (the code in later steps must match them):

- **Matching rule (GT decision ↔ system decision).** A ground-truth decision is *found* if at least one non-`human_rejected` system decision in the same repo **shares at least one event id with the GT item's `expected_evidence_contains`**. Title word overlap is **not** used for matching (it is fragile).
- **Decision recall** = found GT decisions ÷ total GT decisions.
- **State accuracy** = found GT decisions whose system state equals `expected_state` ÷ found GT decisions.
- **Decision precision** = correct system decisions ÷ sampled system decisions, where "correct" comes from a human label file `backend/evaluation/precision_labels.json` (Step 1.3). Precision is reported `not measured` if the label file is missing.
- **Evidence-link validity** = evidence links where the event exists in `events` **and** `source_url` is a non-empty http(s) URL ÷ all evidence links. (State clearly that this checks the link exists, not that the link is correct.)
- **Claim support rate** (replaces "unsupported claim rate") = for each sentence in every generated explanation, the sentence is *supported* if it cites ≥1 event **and** at least 50% of its content words (lower-cased, stop-words removed, words >3 chars) appear in the cited events' title+body. Unsupported rate = 1 − support rate. Define the stop-word list in code, in one place.
- **Conflict precision / drift precision & recall** = computed on a labelled case file (Step 1.5).
- **Latency** = measured wall-clock milliseconds using `time.perf_counter()` for (a) ingesting a repo bundle and (b) answering one `explain` query; report the median of ≥5 runs.

- **Accept:** file exists and is unambiguous.
- **Verify:** read it back; no number appears in it other than thresholds like 50%.

### Step 1.2 — Replace the benchmark with a computing version
- **Do:** Rewrite `BenchmarkRunner.run_full_evaluation()` in `backend/evaluation/benchmark.py` to implement §1.1 exactly. **Delete** every literal metric and the whole hard-coded `baselines` dict. Return `None`/the string `"not measured"` for any metric whose inputs are missing. Return per-item detail lists (`found`, `missed`, `wrong_state`) so the UI and humans can inspect failures.
- **Accept:** `grep -n "0\.941\|0\.912\|0\.923\|0\.947\|42\.6\|18\.5\|16\.8" backend/evaluation/benchmark.py` returns nothing. Running the function on a freshly seeded temp DB returns real numbers (they may be low — that is correct and expected).
- **Verify:** unit test `tests/test_benchmark.py` (see Step 1.6).

### Step 1.3 — Precision labels
- **Do:** Create `backend/evaluation/precision_labels.json` as a list of `{ "decision_id": "...", "correct": true|false, "note": "..." }`. Create a helper script `tools/make_precision_sample.py` that samples up to 30 system decisions (fixed random seed `1234`) from the DB and writes a template with `"correct": null` for a **human** to fill in. **You must not fill the labels yourself** — leave them `null` and treat `null` as "not labelled".
- **Accept:** helper runs; precision metric reports `not measured` while labels are `null`.
- **Verify:** `python tools/make_precision_sample.py` then run the benchmark.

### Step 1.4 — Real baselines (only the ones that can be run honestly)
Create `backend/evaluation/baselines.py`:
- **Baseline A — keyword search.** For each GT question, tokenise the GT title, score every event by token overlap, take the top 5. *Found* if any top-5 event id is in `expected_evidence_contains`.
- **Baseline B — docs-only.** Same, but restricted to events with `source_type in ("adr","doc")`.
- **Baseline C — plain LLM over repo text.** Optional. Implement only if `CIF_LLM_API_KEY` and `CIF_LLM_MODEL` are set (see Step 3.2 for the HTTP helper). If not set, return `"not measured"`. Never fabricate.
- **Baseline D — GitHub Copilot.** Cannot be automated. Create `backend/evaluation/manual_copilot_results.csv` with header `question_id,answer_correct,answer_has_invented_reason,notes` and no rows. Load it if rows exist; otherwise `"not measured"`.
- Wire all four into the benchmark output under `baselines`, each with its **computed** recall and a `status` field (`measured` | `not measured`).
- **Accept:** the metrics dashboard shows real baseline numbers for A and B, and "not measured" for C/D until provided.
- **Verify:** unit test asserts the baselines dict contains no numeric value that is not produced by code (e.g. test that changing the GT file changes the output).

### Step 1.5 — Drift and conflict labelled cases
- **Do:** Create `backend/evaluation/drift_cases.json` with **at least 20** cases, each `{ "id", "repo", "files", "diff_text", "expected": "violation" | "ok", "decision_id" }`. Include **at least 8 `ok` cases** (negatives) and cases that look similar to violations but are fine. Create the same style file `conflict_cases.json` (≥6 cases, ≥2 negatives). Compute drift/conflict **precision, recall** from these using the real `DriftDetector` / `ReconciliationEngine`.
- **Accept:** metrics computed, negatives exist, nothing hard-coded.
- **Verify:** unit tests in `tests/test_drift.py`.

### Step 1.6 — Tests for the evaluation itself
- **Do:** `tests/test_benchmark.py`: (1) metrics are floats in [0,1] or `"not measured"`; (2) when the DB is empty, recall is 0, not an error; (3) a tiny GT of 2 items against a hand-built DB gives exactly the expected recall (prove the maths); (4) no literal metric constants remain (grep the source in the test).
- **Accept:** all tests pass.
- **Verify:** `python -m unittest discover -s tests -v`.

### Step 1.7 — Fix the replaced demo checks
- **Do:** In `run_demo.py`, the checks "Benchmark: ... computed" must assert **real** properties (values are numbers or `"not measured"`, never None-crash) — do **not** assert that recall is ≥ some target. Update any text that prints "92.6% accuracy" to print the computed value.
- **Accept:** `run_demo.py` passes with honest numbers.
- **Verify:** `python run_demo.py`.

### Step 1.8 — Fix the seed vs ground-truth mismatch (P2) correctly
Two legitimate options. **Choose option B.**
- **A (not allowed here):** edit the seed so it produces exactly the 32 GT decisions. This is tuning to the test.
- **B (required):** Label the two pilot repos as **"synthetic pilot (smoke test)"** in code comments, in the UI metrics page, and in the README. Reduce `ground_truth.py` to the decisions that the pilot seed *actually contains and that are documented in the seed's own ADRs/PRs/issues*, so the pilot check is a smoke test of the pipeline, not a headline result. Move the headline evaluation to real repositories (Phase 2).
- **Accept:** the metrics page labels pilot numbers as smoke-test only.
- **Verify:** visual check at `http://127.0.0.1:8080/` → Metrics & Baselines.

---

## PHASE 2 — Real-repository benchmark ("WhyBench")

Goal: evidence that works on projects the team did **not** write.

### Step 2.1 — Pick repositories
- **Do:** Choose **2–3 public open-source repositories** that (a) have ADRs or a `docs/decisions`/`rfcs` folder, **and** (b) have rich issue/PR discussion, **and** (c) are small enough to ingest in minutes (≤ ~300 relevant PRs/issues). Record the choices in `backend/evaluation/whybench/REPOS.md` with the URL, the commit SHA/date you snapshot at, and why it was chosen.
- **Accept:** file exists; snapshots pinned by SHA/date so results are reproducible.
- **Verify:** another person can re-ingest the same snapshot.

### Step 2.2 — Ingest snapshots
- **Do:** Use `backend/ingestion/live_github.py` (it already supports the GitHub API with a `GITHUB_TOKEN`, and local-folder ingestion). Prefer **cloning to a local folder + a one-time JSON export of issues/PRs** over live API calls, so the benchmark is reproducible offline. Save raw exports under `backend/evaluation/whybench/data/<repo>/` (keep each under ~20 MB).
- **Accept:** a script `tools/ingest_whybench.py` rebuilds a fresh DB `whybench.db` from the saved exports with one command.
- **Verify:** `python tools/ingest_whybench.py` creates the DB; counts printed.

### Step 2.3 — Label the questions (human-in-the-loop)
- **Do:** Create `backend/evaluation/whybench/questions.json`. Target **20–30 questions per repo**, each:
  `{ "id", "repo", "question", "answer_summary", "evidence_urls": [...], "evidence_event_ids": [...], "expected_state", "split": "dev"|"test" }`.
  Rules: every question's answer must be supported by a **public URL** (issue/PR/commit/ADR). Include some questions whose honest answer is *"no recorded decision"* (`expected_state: "unresolved"`) to test refusal. Assign `split` **before** looking at any system output: ~40% `dev`, ~60% `test`.
- **Important:** Antigravity may draft candidate questions, but a **human teammate must verify each against the source URL** and flip `"verified": true`. The benchmark only uses `verified: true` items.
- **Accept:** ≥ 20 verified questions per repo, `test` split frozen (add a note: "do not edit after first test run").
- **Verify:** `python tools/validate_whybench.py` (write it) checks schema, URLs present, split ratio, no duplicate ids.

### Step 2.4 — Run and report
- **Do:** `tools/run_whybench.py [--split dev|test]` runs the system **and baselines A–D** on the chosen split and writes `backend/evaluation/whybench/results_<split>_<date>.json`. The `test` split may only be run via an explicit `--final` flag and the script must refuse to run it twice without `--force`.
- **Accept:** results JSON contains per-question outcomes plus aggregate recall, state accuracy, refusal accuracy (for `unresolved` items), hallucination/claim-support rate, per baseline.
- **Verify:** run on `dev`; confirm numbers differ between system and baselines and that failures are listed.

---

## PHASE 3 — Better extraction (reduce noise, add LLM safely)

### Step 3.1 — Filter trivial commits (fixes P6)
- **Do:** In `backend/engine/extractor.py` add a pre-filter `is_decision_candidate(event)` that rejects: commit messages that are only `Added/Updated/Fix typo/Merge branch/Initial commit/bump`, changes touching only docs/README/lockfiles, and bodies under a minimum meaningful length. Keep ADR events always. Make the rules data-driven (a constant list at the top of the file).
- **Accept:** re-ingesting the Placement-Tracker repo no longer yields "Added README"-style decisions. Add a unit test with 10 positive and 10 negative examples.
- **Verify:** `python -m unittest discover -s tests -v`; re-run the dev split and record precision/recall before vs after in `docs_changelog.md`.

### Step 3.2 — LLM extractor behind an interface
- **Do:** Create `backend/engine/llm_client.py` using only `urllib.request`. Read `CIF_LLM_PROVIDER`, `CIF_LLM_API_KEY`, `CIF_LLM_MODEL` from the environment; **do not hard-code a model name or key**. If any are missing, `available()` returns False and the system silently uses the heuristic extractor. Add a 30 s timeout, 2 retries with backoff, and never log the key.
- Create `backend/engine/llm_extractor.py` implementing the same method signature as `DecisionExtractor.extract_from_event_bundle`. It sends the bundle text and asks for **strict JSON**: `[{ "title", "state", "rationale", "alternatives": [{ "description", "rejection_reason", "evidence_event_ids" }], "evidence_event_ids": [...], "confidence" }]`.
- **Accept:** with no env vars, behaviour is identical to before (tests pass). With env vars, the LLM path runs.
- **Verify:** unit test that mocks `llm_client` (no network) and returns canned JSON.

### Step 3.3 — Grounding validator (anti-hallucination that actually checks)
- **Do:** After the LLM returns candidates, run `validate_grounding(candidate, events)`: (1) every `evidence_event_id` must exist in the bundle; (2) at least 50% of the content words of `rationale` must occur in the cited events' text (same stop-word list as METRICS.md); (3) otherwise set `state="unresolved"`, `confidence <= 0.3`, `review_status="pending_review"`. Never drop a candidate silently — route it to the review queue.
- **Accept:** a test feeds an LLM response containing an invented rationale and asserts it is downgraded to `unresolved`.
- **Verify:** `python -m unittest discover -s tests -v`.

### Step 3.4 — Compare extractors on the dev split
- **Do:** Extend `tools/run_whybench.py` with `--extractor heuristic|llm|both`. Record both results.
- **Accept:** a table in `evaluation_results.md` comparing heuristic vs LLM on `dev` (computed). If no API key is available, the LLM column says `not measured`.
- **Verify:** run on `dev` only. **Do not run `test` yet.**

---

## PHASE 4 — Decision lifecycle that is actually recorded (fixes P7)

### Step 4.1 — Write `state_history`
- **Do:** In `Database.save_decision` and in the review-action handler (`/api/review-action`), insert a row into `state_history` on **every** state change (`decision_id, from_state, to_state, changed_at, changed_by, notes`). Inspect the existing schema in `_init_schema` first and use its real column names.
- **Accept:** after seeding and one review action, `SELECT COUNT(*) FROM state_history` > 0 and the decision's history is returned by `query_full_evidence_trail`.
- **Verify:** unit test.

### Step 4.2 — Supersession chain
- **Do:** Ensure `ReconciliationEngine` sets `supersedes_decision_id`/`superseded_by_decision_id` symmetrically, flips the older decision to `superseded`, writes a `supersedes` edge with `valid_to` on the old edge, and logs both transitions in `state_history`.
- **Accept:** unit test with two decisions on the same entity, the later explicitly saying it replaces the earlier.
- **Verify:** `python -m unittest discover -s tests -v`.

---

## PHASE 5 — Headline novelty: Decision Guard Rules

**Why:** Today a decision is text. A professor can say "a README is text too." A decision that can be **enforced automatically on every pull request** is something a README and a one-off chat answer cannot do. Keep scope small and finish it.

### Step 5.1 — Data model
- **Do:** Add table `guard_rules(rule_id TEXT PRIMARY KEY, decision_id TEXT NOT NULL, rule_type TEXT NOT NULL, params_json TEXT NOT NULL, status TEXT NOT NULL, created_by TEXT, created_at TEXT, approved_by TEXT, approved_at TEXT)` using a safe migration (`CREATE TABLE IF NOT EXISTS`). `status`: `proposed | active | disabled`. Add a `GuardRule` dataclass in `models.py`.
- **Allowed `rule_type` values (exactly these four, no more):**
  1. `forbid_import` — params `{ "module": "x" , "paths": ["glob", ...] }`
  2. `require_import` — params `{ "module": "x", "paths": [...] }`
  3. `forbid_pattern` — params `{ "regex": "...", "paths": [...], "message": "..." }`
  4. `config_value` — params `{ "file": "...", "key": "...", "must_equal": "..." }`
- **Accept:** migration runs on a fresh DB and on the existing DB without data loss.
- **Verify:** unit test creating, reading, and updating a rule.

### Step 5.2 — Rule proposal from a decision
- **Do:** `backend/engine/guard_rules.py` → `propose_rules(decision)`: use deterministic patterns on the decision's rationale/alternatives to propose rules (e.g. a rejected alternative that names a library → `forbid_import`). If the LLM client is available it may *suggest* rules as JSON, but every proposal is validated against the four allowed types and stored as `proposed`. **Never auto-activate.**
- **Accept:** a human must click **Approve** in the review queue to make a rule `active`.
- **Verify:** unit tests for each rule type's proposal.

### Step 5.3 — Rule checking in the drift pass
- **Do:** In `DriftDetector.analyze_diff_for_drift`, after existing logic, evaluate all `active` rules against the diff: parse **added lines only** (`+` lines), match `paths` with `fnmatch`, check each rule type. Return findings that include `rule_id`, `decision_id`, the matching added line, and the citation of the original decision's evidence. Keep the existing non-rule drift findings.
- **Accept:** a diff adding `import sticky_sessions` with an active `forbid_import` rule yields a violation; a diff that only *removes* that line yields none.
- **Verify:** `tests/test_guard_rules.py` with ≥ 4 positive and ≥ 4 negative cases per rule type.

### Step 5.4 — API + UI
- **Do:** Endpoints `GET /api/guard-rules`, `POST /api/guard-rules/approve`, `POST /api/guard-rules/disable`. In the review queue UI, show proposed rules with **Approve / Edit / Disable** buttons. In the Live CI Drift Tester, show rule violations with the rule and decision citations. Reuse existing styles in `web/style.css`.
- **Accept:** end-to-end: ingest → rule proposed → approve → submit violating diff → violation shown with a clickable evidence link.
- **Verify:** manual run through that exact scenario, then `python run_demo.py` plus new unit tests.

### Step 5.5 — Measure it
- **Do:** Reuse `drift_cases.json` (Step 1.5): add cases that only a guard rule can catch. Report drift precision/recall **with and without rules enabled**.
- **Accept:** a computed with/without table in `evaluation_results.md`.
- **Verify:** `python tools/run_whybench.py --split dev` plus the drift evaluation.

---

## PHASE 6 — Optional stretch: Assumption tracking (do only if Phases 0–5 are finished and verified)

- **Do:** Add table `decision_assumptions(assumption_id, decision_id, text, watch_type, watch_params_json, status, last_checked_at)`. `watch_type` ∈ `dependency_version | config_value | file_exists`. A decision may carry assumptions (extracted or human-entered). A scheduled/on-demand check compares current repo state (from `requirements.txt` parser already in `entity_res.py`) to each assumption; if violated, mark the decision `review_status="pending_review"` with a `stale_assumption` reason and add it to the review queue.
- **Accept/Verify:** unit tests with a version bump that breaks an assumption, and one that does not.

---

## PHASE 7 — GitHub integration (required by scope, fixes P8 partly)

### Step 7.1 — Webhook receiver
- **Do:** Add `POST /api/webhook/github` in `api.py`. Verify the `X-Hub-Signature-256` header with `hmac.compare_digest` against `CIF_WEBHOOK_SECRET` (reject with 401 if missing/invalid; if the env var is unset, reject all). Handle only `pull_request` events with `action` in `opened|synchronize|reopened`; ignore the rest with 200.
- **Accept:** a unit test posts a signed sample payload (store a sample under `tests/fixtures/pr_opened.json`) and gets 200; unsigned/invalid gets 401.
- **Verify:** `python -m unittest discover -s tests -v`.

### Step 7.2 — Diff fetch + analysis + feedback
- **Do:** On a valid PR event, fetch the diff with the GitHub API (`Accept: application/vnd.github.v3.diff`, token from `GITHUB_TOKEN`), run `analyze_diff_for_drift`, store findings, then **post a PR comment** summarising violations with links to the decision and evidence. If no token is set, store findings and skip posting (log a clear message, no crash). Keep API calls inside `live_github.py` helpers.
- **Accept:** with a mocked HTTP layer, a violating PR yields a stored finding and one comment call; a clean PR yields no comment.
- **Verify:** unit tests with mocks (no real network).

### Step 7.3 — CI alternative (no server needed)
- **Do:** Add `.github/workflows/cif-check.yml` that runs on `pull_request`, checks out the repo, runs `python tools/ci_check.py --base ${{ github.event.pull_request.base.sha }} --head ${{ github.sha }}`, and fails the job (exit 1) if violations of `active` rules exist. `tools/ci_check.py` must use `git diff` only (stdlib `subprocess`) and read rules from an exported `cif_rules.json` committed to the repo.
- **Accept:** running the script locally against a sample branch returns the correct exit code.
- **Verify:** run it on a branch with and without a violating change.

### Step 7.4 — Document real setup
- **Do:** Write `GITHUB_APP_SETUP.md`: how to create the GitHub App (permissions: Pull requests read/write, Contents read, Issues read; event: Pull request), where to put the webhook secret, how to expose the local server for testing (any tunnel tool), and how to confirm delivery. **Do not claim it works against a live repo unless it was actually tested** — say so explicitly.
- **Verify:** another teammate follows it from scratch.

---

## PHASE 8 — Make the hosted demo run the real engine (fixes P9)

### Step 8.1 — Static snapshot generator
- **Do:** Create `tools/build_static.py` that starts the API handler **in-process** (no network), calls each GET endpoint the UI uses, and writes `web/static_data.js` (same `window.__CIF_STATIC_DATA__` shape the UI already reads — open `web/app.js` around the `__CIF_STATIC_DATA__` usage and match its keys exactly). It then copies `web/*` into `docs/`.
- **Accept:** running it twice produces identical output (deterministic ordering); `docs/` equals `web/` afterwards.
- **Verify:** `python tools/build_static.py`, then `diff -r web docs` shows no differences except none.

### Step 8.2 — Deploy the real backend
- **Do:** Add a `Dockerfile` (python slim, no pip installs, `CMD ["python","server.py"]`). Make `server.py` read `PORT` from the environment (default 8080) and bind to `0.0.0.0` **only** when `CIF_BIND=0.0.0.0` is set (default stays `127.0.0.1`). Make the DB path configurable via `CIF_DB_PATH`. Seed on first start if empty (already implemented).
- Deploy to any free container host the team chooses. Add `DEPLOYMENT.md` instructions for it.
- **Accept:** the hosted URL serves the UI and `/api/stats` returns JSON.
- **Verify:** open the URL, run the drift tester, confirm it calls `/api/drift-check` (browser dev-tools network tab) rather than reading static data.

### Step 8.3 — Show the mode in the UI
- **Do:** Add a small badge in the header: `Live engine` when API calls succeed, `Static snapshot` when falling back to `__CIF_STATIC_DATA__`.
- **Accept:** badge visible and correct in both modes.
- **Verify:** manual check, both modes.

---

## PHASE 9 — Tests, docs, and honesty pass

### Step 9.1 — Test coverage
- **Do:** Ensure `tests/` covers: db invariant, each adapter, entity resolution (AST), graph queries, extractor (heuristic + grounding validator), reconciliation, drift detector, guard rules, benchmark maths, webhook signature. Add `.github/workflows/tests.yml` running `python -m unittest discover -s tests -v` on push/PR.
- **Accept:** CI green.
- **Verify:** push and check the Actions tab, or run the command locally.

### Step 9.2 — Final test-split run
- **Do:** Only now, run `python tools/run_whybench.py --split test --final` **once**. Save the JSON. Do not change code afterwards to improve it.
- **Accept:** results file committed; `evaluation_results.md` reports the numbers exactly as computed, including where the system loses to a baseline.
- **Verify:** numbers in the UI Metrics page equal the numbers in the results JSON.

### Step 9.3 — Rewrite the docs to match reality (fixes P11)
- **Do:** Update `readme.md` (9 surfaces, no hard-coded metrics — point to `evaluation_results.md`), `task.md` (mark only truly finished items), `explanation.md` (extractor is heuristic and/or LLM-assisted with grounding validation; GitHub Pages shows a static snapshot). Create `LIMITATIONS.md` listing honestly: pilot repos are synthetic; benchmark size; heuristic extraction errors; baselines not measured; GitHub App tested only with mocks unless a live test was done.
- **Accept:** `grep -rn "92.6\|98.4\|0.0%" readme.md task.md explanation.md` shows no stale hard-coded claims.
- **Verify:** read each file once, top to bottom.

### Step 9.4 — Update the demo script
- **Do:** In `readme.md` section 5, update the demo walkthrough: replace the metrics talking points with the measured values, add the guard-rule scenario, and add a 3-line answer to "why not just a README or an AI agent?" using the measured baseline numbers.
- **Verify:** a teammate rehearses it once against the running app.

---

## 10. Common pitfalls (read before coding)

- **SQLite + threads:** `ThreadingHTTPServer` handles requests on multiple threads. Use a **new connection per request** (the existing `get_connection()` pattern). Do not share one connection across threads.
- **`row_factory`:** existing code relies on `sqlite3.Row` (`row["col"]`, `dict(row)`). Keep it on every connection you create.
- **Schema changes:** only `CREATE TABLE IF NOT EXISTS` / additive `ALTER TABLE ... ADD COLUMN` guarded by a column-exists check. Never drop tables on the user's DB.
- **Timestamps:** the models use ISO-8601 strings (`current_iso`). Compare as parsed datetimes, never as raw strings across formats.
- **Deterministic IDs:** extractor decision ids are built from repo + source ids. Keep them deterministic so re-ingesting is idempotent (upsert, not duplicate).
- **Windows console:** keep the `sys.stdout.reconfigure(encoding="utf-8")` guard; avoid printing characters that fail on cp1252 in new scripts.
- **SSL on Windows:** `live_github.py` already falls back across SSL contexts. Do not remove that.
- **GitHub rate limits:** unauthenticated API calls are heavily limited. Use `GITHUB_TOKEN`, cache raw exports to disk, and never call the API inside tests.
- **Tests must not network and must not touch the real DB.** Use `tempfile` and mocks.
- **Seeds vs real data:** `/api/reseed` and `/api/clear-db` are destructive. Never call them from tests or tools against the real DB path.
- **Relative paths:** scripts in `tools/` must compute the project root from `__file__`, not from the current working directory, and insert it into `sys.path`.

---

## 11. Definition of done

All of the following must be true:

- [ ] `python run_demo.py` passes; `python -m unittest discover -s tests -v` passes; CI is green.
- [ ] No hard-coded metric anywhere (`grep` check in a test).
- [ ] WhyBench: ≥ 2 real repositories, ≥ 20 verified questions each, `test` split run exactly once, results committed.
- [ ] Baselines A and B measured; C and D either measured or explicitly `not measured`.
- [ ] Extractor noise fixed; grounding validator active; LLM path optional and mocked-tested.
- [ ] `state_history` populated; supersession chain recorded.
- [ ] Guard rules: propose → approve → enforce → measured, with citations back to evidence.
- [ ] Webhook with signature check + CI script, both tested with fixtures/mocks; setup doc is honest about what was live-tested.
- [ ] Hosted demo runs the Python backend and shows a `Live engine` badge; GitHub Pages fallback labelled `Static snapshot`.
- [ ] `readme.md`, `task.md`, `explanation.md`, `LIMITATIONS.md` match reality.

---

## 12. Reporting format (after every step)

Reply with exactly this block, then wait for the next instruction or continue to the next step if running autonomously:

```text
STEP: <number and name>
STATUS: done | partial | blocked
FILES CHANGED: <list>
VERIFY COMMAND: <what you ran>
RESULT: <exact output summary, real numbers only>
ACCEPTANCE CRITERIA MET: yes | no (list any not met)
NEXT: <next step number>
```

If `STATUS` is `blocked`, also append the entry to `BLOCKERS.md` before moving on.

---

## 13. Start here

Begin with **Step 0.1**. Do not start Phase 1 until Phase 0 is verified.
