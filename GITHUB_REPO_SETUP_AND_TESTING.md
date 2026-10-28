# 🚀 GitHub Repo Setup & Complete Testing Guide
## Context Intelligence Framework (CIF) — SE Lab Project

> **Purpose:** This document is your step-by-step playbook to publish your project to a real GitHub repository and demonstrate every testable feature to your professor. Testing is worth 10 marks — follow every phase in order.

---

## 📋 Table of Contents

1. [Phase 1 — Create the GitHub Repository](#phase-1--create-the-github-repository)
2. [Phase 2 — Push Your Code](#phase-2--push-your-code)
3. [Phase 3 — Enable GitHub Pages (Live Demo)](#phase-3--enable-github-pages-live-demo)
4. [Phase 4 — Enable GitHub Actions (CI Badge)](#phase-4--enable-github-actions-ci-badge)
5. [Phase 5 — Run the Full Test Suite Locally](#phase-5--run-the-full-test-suite-locally)
6. [Phase 6 — Feature-by-Feature Testing Checklist](#phase-6--feature-by-feature-testing-checklist)
7. [Phase 7 — Show Your Professor (Demo Script)](#phase-7--show-your-professor-demo-script)
8. [Troubleshooting](#troubleshooting)

---

## Phase 1 — Create the GitHub Repository

### Step 1.1 — Create a new repo on GitHub

1. Go to [https://github.com/new](https://github.com/new)
2. Fill in these exact settings:

| Field | Value |
|---|---|
| **Repository name** | `context-intelligence-framework` |
| **Description** | `Provenance-grounded architectural context engine — SE Lab Project` |
| **Visibility** | **Public** ✅ (required for GitHub Pages and CI badge) |
| **Initialize with README** | ❌ **Uncheck** (you will push your own) |
| **Add .gitignore** | ❌ **None** (your project already has one) |
| **Choose a license** | ❌ **None** |

3. Click **Create repository**.
4. Copy the URL shown on the next page — it will look like:
   ```
   https://github.com/YOUR_USERNAME/context-intelligence-framework.git
   ```

---

## Phase 2 — Push Your Code

### Step 2.1 — Prepare your local folder

Open a terminal (Command Prompt or PowerShell on Windows, Terminal on Mac/Linux) and navigate to the project folder:

```bash
cd path/to/SE_project
```

> If you are already inside the folder and git is initialised (you will see a `.git` folder), skip to Step 2.3.

### Step 2.2 — Initialise git (only if not already done)

```bash
git init
git branch -M main
```

### Step 2.3 — Remove the old remote and add your new one

```bash
# Remove any existing remote called origin (safe to run even if none exists)
git remote remove origin 2>/dev/null || true

# Add YOUR new repository as origin
git remote add origin https://github.com/YOUR_USERNAME/context-intelligence-framework.git
```

> ⚠️ Replace `YOUR_USERNAME` with your actual GitHub username everywhere below.

### Step 2.4 — Stage and commit everything

```bash
git add .
git commit -m "feat: initial push — Context Intelligence Framework SE Lab Project"
```

### Step 2.5 — Push to GitHub

```bash
git push -u origin main
```

When asked, enter your GitHub username and a **Personal Access Token** (PAT) as the password.

> **How to create a PAT:** GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic) → Generate new token → tick `repo` scope → copy the token. Use it as your password when pushing.

### Step 2.6 — Verify

Go to `https://github.com/YOUR_USERNAME/context-intelligence-framework` in your browser. You should see all your files listed.

---

## Phase 3 — Enable GitHub Pages (Live Demo)

Your project already contains a pre-built static web interface in the `docs/` folder and the deploy workflow in `.github/workflows/deploy.yml`.

### Step 3.1 — Enable Pages in repository settings

1. On your repository page, click **Settings** (top navigation bar).
2. In the left sidebar, click **Pages**.
3. Under **Source**, select **GitHub Actions** (not "Deploy from a branch").
4. Click **Save**.

### Step 3.2 — Trigger the deploy workflow

The workflow runs automatically on every push to `main`. To trigger it manually right now:

1. Click the **Actions** tab on your repository.
2. Find the workflow named **Deploy to GitHub Pages**.
3. Click **Run workflow** → **Run workflow** (green button).

### Step 3.3 — Find your live URL

After the workflow finishes (takes about 60–90 seconds), your live URL will appear at:

```
https://YOUR_USERNAME.github.io/context-intelligence-framework/
```

Bookmark this — it is what you show your professor as the **live hosted demo**.

---

## Phase 4 — Enable GitHub Actions (CI Badge)

The test suite badge is already wired in `readme.md`. The CI workflow runs automatically on every push, but you can confirm it here:

### Step 4.1 — Verify the badge is live

1. Go to the **Actions** tab.
2. Look for the workflow **CIF Test Suite**.
3. Wait for it to complete — it should show a green ✅ **passing** badge.

If it is red, see [Troubleshooting](#troubleshooting).

### Step 4.2 — What the CI pipeline does (show this to your professor)

The `.github/workflows/tests.yml` file runs four steps automatically on every push:

| Step | Command | What it checks |
|---|---|---|
| 1 | `python -m unittest discover -s tests` | All 329 unit tests |
| 2 | `python run_demo.py` | 21-point end-to-end verification |
| 3 | `python tools/check_docs.py` | Documentation consistency |
| 4 | `python tools/check_eol.py` | Line-ending hygiene |

---

## Phase 5 — Run the Full Test Suite Locally

Run these commands from the project root (`SE_project/` folder). Python 3.11 or 3.12 is required — **no pip install needed** (the project uses only the standard library).

### Step 5.1 — Verify Python version

```bash
python --version
# Must show Python 3.11.x or 3.12.x
```

### Step 5.2 — Initialise the database with seed data

```bash
python tools/init_db.py --seed
```

Expected output: `Database initialised and seed data populated.`

### Step 5.3 — Run the 21-point automated verification suite

```bash
python run_demo.py
```

Expected output:
```
===========================================================================
  CONTEXT INTELLIGENCE FRAMEWORK -- AUTOMATED VERIFICATION SUITE
===========================================================================
  [PASS] Mechanical Invariant
  [PASS] Git Adapter
  [PASS] Identity Resolution
  [PASS] GitHub Adapter
  [PASS] PR Linkage
  ...
  [PASS] Benchmark Processing Latency
===========================================================================
  RESULT: 21/21 checks passed
===========================================================================
```

### Step 5.4 — Run the full unit test suite (329 tests)

```bash
python -m unittest discover -s tests -v
```

Expected output: `Ran 329 tests ... OK` (takes under 10 seconds)

### Step 5.5 — Run specific test modules (feature-wise)

Use these to demonstrate individual features:

```bash
# Core engine
python -m unittest tests.test_adapters_and_engine -v

# Drift detection
python -m unittest tests.test_drift -v
python -m unittest tests.test_drift_rules -v

# Conflict / reconciliation
python -m unittest tests.test_conflict_pairs -v

# Decision lifecycle
python -m unittest tests.test_lifecycle -v
python -m unittest tests.test_state_model -v

# Graph and temporal queries
python -m unittest tests.test_as_of -v
python -m unittest tests.test_graph_temporal -v

# API and all UI surfaces
python -m unittest tests.test_all_features_and_buttons -v

# Authentication flow
python -m unittest tests.test_auth_flow -v

# Repository isolation (multi-tenant)
python -m unittest tests.test_repo_isolation -v

# Ingestion pipeline
python -m unittest tests.test_job_runner -v

# Security: secret sanitizer
python -m unittest tests.test_sanitizer -v

# Database migrations
python -m unittest tests.test_migrations -v

# Evidence grounding invariant
python -m unittest tests.test_independence -v

# Explanation synthesis
python -m unittest tests.test_explanation -v

# Benchmark evaluation
python -m unittest tests.test_benchmark -v

# Rejected idea guard
python -m unittest tests.test_rejected_idea_guard -v
```

### Step 5.6 — Start the local web server

```bash
python server.py
```

Then open your browser at: **http://127.0.0.1:8080/**

---

## Phase 6 — Feature-by-Feature Testing Checklist

Use this checklist during your professor demo. Tick each box as you demonstrate it.

---

### 🟢 Feature Group 1 — Core Data Integrity (Mechanical Invariant)

**What it tests:** The database physically prevents saving an architectural decision without verified evidence links — the foundational correctness guarantee of the system.

**How to test:**
```bash
python -m unittest tests.test_independence -v
```

**What to show:** Every test in this file verifies that attempting to insert an accepted decision with zero evidence links raises an `InvariantViolationError`. This is the "mechanical invariant" — the system cannot lie.

**Relevant files:** `backend/db.py`, `backend/models.py`

---

### 🟢 Feature Group 2 — Multi-Source Ingestion Pipeline

**What it tests:** The system ingests Git commits, GitHub Issues/PRs, Architectural Decision Records, and resolves contributor identities.

**How to test:**
```bash
python -m unittest tests.test_adapters_and_engine -v
python -m unittest tests.test_job_runner -v
```

**What to show in the browser (http://127.0.0.1:8080/):**
- Navigate to the **Evidence Panel** tab → you will see ingested commit events, PR review comments, and issue bodies with clickable `source_url` permalinks.
- Navigate to the **Project Timeline** → events are ordered chronologically across both pilot repositories.

**Relevant files:** `backend/ingestion/`

---

### 🟢 Feature Group 3 — Temporal Context Graph & Time-Travel Queries

**What it tests:** The bipartite graph connecting decisions, events, and code entities across time. Point-in-time queries prevent retroactive information leakage.

**How to test:**
```bash
python -m unittest tests.test_as_of -v
python -m unittest tests.test_graph_temporal -v
```

**What to show in the browser:**
- Navigate to the **Context Graph** tab → see the force-directed network of decisions (blue nodes), events (green), and code entities (orange).
- Colour-coded edges represent `drifts_from`, `superseded_by`, `conflicts_with` relationships.

**Relevant files:** `backend/engine/graph.py`

---

### 🟢 Feature Group 4 — Decision Lifecycle State Machine

**What it tests:** Decisions transition through states: `proposed → accepted → superseded` or `proposed → rejected`. The state machine enforces legal transitions only.

**How to test:**
```bash
python -m unittest tests.test_lifecycle -v
python -m unittest tests.test_state_model -v
python -m unittest tests.test_supersession -v
```

**What to show in the browser:**
- Navigate to **Decision Explorer** → filter by state (Accepted / Rejected / Superseded).
- Click any decision card → a modal shows the full decision chain with evidence links.

**Relevant files:** `backend/engine/lifecycle.py`

---

### 🟢 Feature Group 5 — Conflict Detection (Contributor Disagreements)

**What it tests:** When two contributors propose contradictory approaches for the same subsystem, the engine flags an active conflict.

**How to test:**
```bash
python -m unittest tests.test_conflict_pairs -v
```

**What to show in the browser:**
- In the **Context Graph**, red-highlighted edges mark conflicting proposals.
- In **Review Queue**, conflicting items appear as `conflict` type and require human resolution.

**Relevant files:** `backend/engine/reconciliation.py`, `backend/engine/conflict_pairs.json`

---

### 🟢 Feature Group 6 — Code Drift Detection & Guard Rules

**What it tests:** Incoming PR diffs are evaluated against accepted architectural decisions. The system blocks re-introduction of explicitly rejected patterns (e.g., `bang-bang controller` after `PID` was accepted).

**How to test:**
```bash
python -m unittest tests.test_drift -v
python -m unittest tests.test_drift_rules -v
python -m unittest tests.test_rejected_idea_guard -v
python -m unittest tests.test_guard_rules -v
```

**What to show in the browser:**
- Navigate to **Live CI Drift Tester** tab.
- Paste this sample diff into the text box and click **Check Drift**:

```diff
--- a/controller/pid.py
+++ b/controller/pid.py
@@ -1,3 +1,8 @@
-def control_loop(error):
-    return kp * error + ki * integral + kd * derivative
+def control_loop(error, setpoint, current):
+    # Reverting to bang-bang for simplicity
+    if current < setpoint:
+        return MAX_OUTPUT
+    return 0
```

  Expected result: **DRIFT ALERT** — the system detects reintroduction of the rejected `bang-bang` pattern and cites the original decision that rejected it.

**Relevant files:** `backend/engine/drift_detector.py`, `backend/engine/guard_rules.py`, `backend/engine/rejected_idea_guard.py`

---

### 🟢 Feature Group 7 — Evidence-Grounded Explanation Synthesis

**What it tests:** On-demand explanations of why code exists, with zero fabrication — every claim cites a verifiable historical event.

**How to test:**
```bash
python -m unittest tests.test_explanation -v
```

**What to show in the browser:**
- Navigate to **Code-Context View**.
- Click on any file (e.g., `controller/pid.py`) → click **Why does this exist?**
- The explanation panel opens with the decision chain and clickable evidence links.

**Relevant files:** `backend/engine/explanation.py`, `backend/engine/evidence.py`

---

### 🟢 Feature Group 8 — Review Queue (Human-in-the-Loop)

**What it tests:** Low-confidence extractions, drift alerts, and conflicts are routed to a human review triage queue with confirm / reject / merge / correct actions.

**How to test:**
```bash
python -m unittest tests.test_review_actions -v
python -m unittest tests.test_feedback -v
```

**What to show in the browser:**
- Navigate to **Review Queue**.
- You will see pending items. Click **Confirm** on one → the item is accepted into the knowledge base.
- Click **Reject** on another → it is marked as false positive.

**Relevant files:** `backend/api.py` (Review Queue endpoints)

---

### 🟢 Feature Group 9 — All 9 UI Surfaces (End-to-End)

**What it tests:** Every tab, button, and API endpoint of the web interface is wired and responsive.

**How to test:**
```bash
python -m unittest tests.test_all_features_and_buttons -v
python -m unittest tests.test_extension_api -v
```

**What to show in the browser — go through every tab:**

| Tab | What to click |
|---|---|
| **Project Timeline** | Use the date range filter; click any event card |
| **Context Graph** | Drag nodes; click a node to see its decision chain |
| **Code-Context View** | Expand a file; click "Why?" on a function |
| **Decision Explorer** | Type in the search box; use the State filter dropdown |
| **Evidence Panel** | Click any decision → click a `source_url` link (opens GitHub) |
| **Review Queue** | Confirm and reject one item each |
| **Live CI Drift Tester** | Paste a diff; click Check Drift |
| **Metrics & Baselines** | Scroll through the benchmark scorecard |
| **Onboarding Tour** | Click through all 5 walkthrough steps |

---

### 🟢 Feature Group 10 — Security & Privacy

**What it tests:** Pre-ingestion sanitization strips API keys, tokens, and credentials before they are stored. Secret scanning tool verifies zero leakage.

**How to test:**
```bash
python -m unittest tests.test_sanitizer -v
python -m unittest tests.test_tls_safety -v
python tools/scan_secrets.py
```

**Expected output for scan_secrets:** `No secrets detected.`

**Relevant files:** `backend/ingestion/sanitizer.py`, `backend/security.py`, `PRIVACY.md`

---

### 🟢 Feature Group 11 — Authentication & Session Management

**What it tests:** GitHub OAuth login flow, sliding session tokens, CSRF protection, HMAC webhook verification.

**How to test:**
```bash
python -m unittest tests.test_auth_flow -v
python -m unittest tests.test_api_auth -v
python -m unittest tests.test_add_repo.py -v
```

**Note for professor:** Full end-to-end OAuth requires a live GitHub App. The tests run against mocked payloads (as documented in `GITHUB_APP_SETUP.md`) and verify all backend logic — session creation, token exchange, CSRF state validation, and HMAC signature verification of webhook payloads.

**Relevant files:** `backend/auth/`, `backend/auth/sessions.py`, `backend/auth/app_token.py`

---

### 🟢 Feature Group 12 — Benchmark Evaluation Suite

**What it tests:** CIF's evidence retrieval and decision reconstruction are measured against WhyBench-Synth (71 questions, 3 domain repositories) and compared to 4 baselines (BM25, Docs-only, LLM, Copilot).

**How to test:**
```bash
python -m unittest tests.test_benchmark -v
python -m unittest tests.test_fair_task1 -v
```

**What to show in the browser:**
- Navigate to **Metrics & Baselines** tab.
- Show the Wilson confidence interval table and the CIF vs baseline comparison chart.

**Relevant files:** `backend/evaluation/benchmark.py`, `backend/evaluation/baselines.py`, `evaluation_results.md`

---

### 🟢 Feature Group 13 — Database Migrations (SDLC Integrity)

**What it tests:** The 7 sequential migration scripts that evolve the schema — state definitions, claim evidence independence, auth tables, decision constraints, etc.

**How to test:**
```bash
python -m unittest tests.test_migrations -v
python -m unittest tests.test_migration_auth_tables -v
```

**Relevant files:** `backend/migrations/001_*.py` through `007_*.py`

---

### 🟢 Feature Group 14 — Repository Isolation (Multi-Tenant)

**What it tests:** Data from `acme-eng/thermal-control-system` (PID controller repo) and `acme-eng/distributed-cache-service` (Redis cache repo) cannot cross-pollinate — strict tenant boundaries.

**How to test:**
```bash
python -m unittest tests.test_repo_isolation -v
python -m unittest tests.test_edge_tenancy -v
```

**Relevant files:** `backend/db.py` (repo scoping), `backend/api.py`

---

### 🟢 Feature Group 15 — Browser & VS Code Extensions

**What it tests:** The Chrome browser extension and VS Code extension surface CIF context directly inside developer workflows.

**How to test:**
```bash
python -m unittest tests.test_extension_api -v
# Extension unit tests
python -m unittest discover -s extension/tests -v
python -m unittest discover -s vscode-extension/tests -v
```

**To install the Chrome extension manually:**
1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked** → select the `extension/` folder
4. The CIF icon appears in your toolbar

**Relevant files:** `extension/`, `vscode-extension/`, `extension/README.md`

---

## Phase 7 — Show Your Professor (Demo Script)

Follow this exact sequence for a smooth 10-minute professor demo:

### 🎤 Opening (1 min)
> "This is the Context Intelligence Framework. Git records *what* changed and *when*, but not *why*. CIF recovers the *why* — automatically, from commits, PRs, and issues — and prevents architectural regressions in CI."

### 💻 Show 1 — Live Hosted App (1 min)
- Open: `https://YOUR_USERNAME.github.io/context-intelligence-framework/`
- Show the project running publicly, with the GitHub Actions badge showing green.

### 💻 Show 2 — CI Badge & Automated Tests (2 min)
- Go to the **Actions** tab on GitHub.
- Show the **CIF Test Suite** workflow running on every push.
- In terminal: run `python run_demo.py` → show all 21 checks passing.

### 💻 Show 3 — Drift Detection (2 min)
- Start the local server: `python server.py`
- Open `http://127.0.0.1:8080/` → go to **Live CI Drift Tester**
- Paste the bang-bang diff from Feature Group 6 → show the drift alert.

### 💻 Show 4 — Context Graph (1 min)
- Click the **Context Graph** tab.
- Point out: blue = decisions, green = events, orange = code entities.
- Show a red conflict edge.

### 💻 Show 5 — Decision Explorer + Evidence (1 min)
- Click **Decision Explorer** → search for "PID" → open the decision card.
- Click "View Evidence" → show the GitHub source URL link.

### 💻 Show 6 — Review Queue (1 min)
- Click **Review Queue** → confirm one item → show it disappears from the queue.

### 💻 Show 7 — Test Count (1 min)
- Run `python -m unittest discover -s tests -v 2>&1 | tail -5`
- Show: `Ran 329 tests in X.XXXs — OK`

### 🎤 Close (1 min)
> "329 automated tests, a 5-level test pyramid, CI that runs on every commit, and a live hosted demo — all zero external dependencies. Thank you."

---

## Troubleshooting

### Tests fail with `ModuleNotFoundError`
Run everything from the project root (`SE_project/` folder), not from inside `backend/` or `tests/`.
```bash
cd path/to/SE_project
python -m unittest discover -s tests -v
```

### `python` not found
Try `python3` instead of `python`. On Windows, use the full path or ensure Python 3.11/3.12 is in your PATH.

### GitHub Actions badge is red
Click the failing run in the Actions tab → expand the failed step → look for `ImportError` or `ModuleNotFoundError`. This usually means the push included a local path reference. All imports in the project use relative module paths and should work correctly.

### GitHub Pages not showing
- Confirm the repository is **Public**.
- In Settings → Pages → confirm Source is set to **GitHub Actions**, not "Deploy from branch".
- Wait 2–3 minutes after the deploy workflow finishes.

### Port 8080 already in use
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8080 | xargs kill
```

Then re-run `python server.py`.

### Database errors on first run
Delete any stale database files and reinitialise:
```bash
rm -f context_intelligence.db
python tools/init_db.py --seed
```

---

## 📁 Quick Reference: Key Files

| File / Folder | Purpose |
|---|---|
| `readme.md` | Main project README with badges |
| `server.py` | Start the local web server (port 8080) |
| `run_demo.py` | 21-point automated verification suite |
| `tools/init_db.py` | Database initialisation + seed data |
| `backend/api.py` | All REST API endpoints |
| `backend/db.py` | Database engine + invariant enforcement |
| `backend/engine/` | Core analysis engines (drift, graph, explanation) |
| `backend/ingestion/` | Git, GitHub, ADR ingestion adapters |
| `backend/migrations/` | 7 sequential schema migrations |
| `tests/` | 329 unit/integration tests (58 files) |
| `web/` | Frontend: HTML, CSS, JavaScript |
| `docs/` | Pre-built static site for GitHub Pages |
| `.github/workflows/` | CI (tests.yml) + Deploy (deploy.yml) |
| `extension/` | Chrome browser extension |
| `vscode-extension/` | VS Code extension |
| `docs/sdlc/SRS.md` | IEEE 830 Software Requirements Specification |
| `docs/sdlc/TEST_PLAN.md` | IEEE 829 Test Plan |
| `docs/sdlc/ARCHITECTURE.md` | IEEE 1471 Architecture Document |
| `LIMITATIONS.md` | Known boundaries and refusal analysis |
| `AI_ASSISTANCE.md` | AI coding assistance disclosure |

---

*Made for UCS503 Software Engineering Lab — Thapar Institute of Engineering and Technology*
