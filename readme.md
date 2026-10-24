# Context Intelligence Framework (CIF)

> A provenance-grounded architectural context engine that captures why code was written, prevents architectural regression in CI, and explains code context with verifiable evidence chains.
>
> **Notice:** For presentation scripts, demo talk tracks, and examination coaching, see [`docs/process/PRESENTER_NOTES.md`](docs/process/PRESENTER_NOTES.md). For AI coding assistance disclosure and author responsibilities, see [`AI_ASSISTANCE.md`](AI_ASSISTANCE.md).

---

## 1. What is this project about?

When developers maintain software on GitHub, version control records code changes through **commits** and **pull requests**:
- Git records **WHAT** code was changed and **WHEN**.
- Git **does NOT record WHY** the code was written that way, which alternatives were explored and rejected, or which operational incidents motivated the design.

### The Problem: Institutional Knowledge Loss
When an engineer writes a specialized algorithm or complex architectural pattern, the rationale behind that choice often remains undocumented or scattered across closed bug reports, pull request review discussions, and chat logs. Months or years later, when team members change, new developers encounter the code without context and may inadvertently reintroduce previously rejected, buggy approaches.

### The Solution: Context Intelligence Framework
CIF acts as an automated architectural context engine:
1. **Multi-Source Ingestion:** Ingests Git commits, GitHub issues, pull request review discussions, and Architectural Decision Records (ADRs).
2. **Temporal Context Graph:** Reconstructs decision lifecycles (`accepted`, `rejected`, `superseded`) linked to Python Abstract Syntax Tree (AST) code entities with verifiable evidence permalinks.
3. **Automated Conflict & Drift Detection:** Evaluates pull request diffs in CI against historical decisions and synthesized guard rules to block architectural regressions before code merges.
4. **Evidence-Grounded Explanations:** Explains why code exists on demand, citing verified historical events with zero ungrounded fabrication.

---

## 2. Architecture & Core Concepts

The framework is implemented with standard Python (3.11/3.12) with zero external database or framework dependencies.

### 1. Evidence Grounding & Mechanical Invariant
- **Concept:** Every persisted decision must link to at least one verified event record. The system physically prevents saving ungrounded assertions.
- **Implementation:** [`backend/models.py`](backend/models.py) and [`backend/db.py`](backend/db.py). The database layer strictly validates that decisions in non-unresolved states contain valid evidence event IDs.

### 2. Multi-Source Ingestion Pipeline
- **Concept:** Ingests development artifacts from Git repositories, GitHub APIs, and documentation.
- **Implementation:** [`backend/ingestion/git_adapter.py`](backend/ingestion/git_adapter.py), [`backend/ingestion/github_adapter.py`](backend/ingestion/github_adapter.py), [`backend/ingestion/adr_adapter.py`](backend/ingestion/adr_adapter.py), and [`backend/ingestion/identity.py`](backend/ingestion/identity.py).
- **Privacy Sanitization:** Pre-ingestion redaction of API keys, tokens, and credentials via [`backend/ingestion/sanitizer.py`](backend/ingestion/sanitizer.py) (see [`PRIVACY.md`](PRIVACY.md)).

### 3. Entity Resolution & AST Code Parsing
- **Concept:** Connects high-level architectural rationale directly to specific files and functions using Python's built-in `ast` module.
- **Implementation:** [`backend/engine/entity_res.py`](backend/engine/entity_res.py). Canonicalizes paths and resolves AST function entities (`file::function`).

### 4. Temporal Context Graph & Time-Travel Queries
- **Concept:** Bipartite graph connecting decisions, evidence events, and code entities across time, supporting historical "as-of" point-in-time queries to eliminate retroactive information leakage.
- **Implementation:** [`backend/engine/graph.py`](backend/engine/graph.py).

### 5. Reconciliation & Conflict Detection
- **Concept:** Identifies contradictions when contributors propose incompatible approaches or contradictory lifecycle states for the same subsystem, using whole-word boundary matching on semantic pairs.
- **Implementation:** [`backend/engine/reconciliation.py`](backend/engine/reconciliation.py) and [`backend/engine/conflict_pairs.json`](backend/engine/conflict_pairs.json).

### 6. Code Drift Detection & Decision Guard Rules
- **Concept:** Analyzes incoming pull request diffs against accepted decisions and synthesized guard rules to catch the reintroduction of rejected patterns or violations of active architecture.
- **Implementation:** [`backend/engine/drift_detector.py`](backend/engine/drift_detector.py), [`backend/engine/guard_rules.py`](backend/engine/guard_rules.py), and [`backend/engine/rejected_idea_guard.py`](backend/engine/rejected_idea_guard.py).

### 7. Human Review Queue
- **Concept:** Maintainer workflow where low-confidence extractions, contributor disagreements, and CI drift alerts are routed for human confirmation, correction, or rejection.
- **Implementation:** [`backend/api.py`](backend/api.py) and the web interface review panel.

### 8. Developer Extensions & CI Webhook Integration
- **Concept:** Surfacing context directly in developer workflows:
  - **Browser Extension:** Inspects GitHub PR diffs and issues ([`extension/`](extension/)).
  - **VS Code Extension:** Displays function-level architectural explanations in the editor gutter ([`vscode-extension/`](vscode-extension/)).
  - **GitHub App & CI Pass:** Evaluates PR diffs automatically via webhook or CI action ([`backend/api.py`](backend/api.py), [`tools/ci_check.py`](tools/ci_check.py), [`.github/workflows/cif-check.yml`](.github/workflows/cif-check.yml), and [`GITHUB_APP_SETUP.md`](GITHUB_APP_SETUP.md)).

---

## 3. Setup and Running

CIF requires Python 3.11 or 3.12 (standard library only; no pip packages or Node.js required).

### Step 1: Initialize Database & Seed Pilot Repositories
On a clean checkout, apply database migrations and populate the pilot repositories:
```bash
python tools/init_db.py --seed
```

### Step 2: Start the Web Server
Launch the HTTP server and API backend:
```bash
python server.py
```
Open your browser to:
👉 **http://127.0.0.1:8080/**

### Step 3: Deploy to GitHub Pages (Static Snapshot)
This repository is configured to deploy directly to GitHub Pages:
- **Automated Workflow:** `.github/workflows/deploy.yml` builds and publishes the web interface.
- **Static Distribution:** The `docs/` folder contains the static distribution for 1-click branch deployment.
- For complete deployment instructions, see [`DEPLOYMENT.md`](DEPLOYMENT.md).

---

## 4. Automated Verification Suite (`run_demo.py`)

`run_demo.py` executes an end-to-end automated verification pass across all core capabilities in approximately 3 seconds:

```bash
python run_demo.py
```

### What it tests (21 automated checks):
1. **Mechanical Invariant:** Verifies that attempting to save an accepted decision with zero evidence links raises a validation error.
2. **Git Adapter:** Ingests commit records and verifies generation of clickable GitHub source URLs.
3. **Identity Resolution:** Resolves raw committer strings to canonical maintainer IDs.
4. **GitHub Adapter:** Ingests GitHub issue events with verified issue URLs.
5. **PR Linkage:** Parses issue close references (e.g., `Closes #101`) into parent event linkages.
6. **File Entity Resolution:** Canonicalizes repository file paths into entity identifiers.
7. **AST Code Parser:** Extracts function signatures from Python source code via AST.
8. **Function Entity Resolution:** Resolves canonical function entities (`file::function`).
9. **Decision Chain Query:** Reconstructs the complete lifecycle decision chain for an artifact.
10. **Evidence Trail Query:** Reconstructs verified source events backing a decision.
11. **Timeline Slice Query:** Queries time-ordered decision histories scoped by repository.
12. **Conflict Detection:** Flags active contributor disagreements across overlapping entities.
13. **Drift Detection (Violation):** Catches diff modifications that violate accepted architectural decisions.
14. **Drift Detection (Rejection):** Detects code diffs re-introducing explicitly rejected historical patterns.
15. **Explanation Synthesis:** Synthesizes evidence-grounded architectural explanations.
16. **Citation Grounding:** Validates that citations contain verified clickable URLs.
17. **Refusal / Abstention:** Confirms the engine abstains (`status: not_found`) when queried on unrecorded artifacts.
18. **Benchmark Decision Recall:** Measures decision extraction recall.
19. **Benchmark Evidence Accuracy:** Measures evidence link accuracy.
20. **Benchmark Claim Support:** Measures unsupported claim rates.
21. **Benchmark Processing Latency:** Measures sub-second processing latency.

> **Verifiable Counts from Data:**
> To inspect machine-verified counts of automated test cases, migrations, benchmark questions, and UI surfaces directly from live code and data, run:
> ```bash
> python tools/print_facts.py
> ```

---

## 5. User Interface Surfaces

The interactive web dashboard (`http://127.0.0.1:8080/`) provides nine dedicated surfaces:
- **Project Timeline:** Chronological decision stream with historical "as-of" point-in-time time-travel queries.
- **Context Graph:** Force-directed network mapping decisions, code entities, and GitHub events with contributor conflict highlighting.
- **Code-Context View:** Function-level architectural explanations answering why code exists, citing accepted and rejected decisions with evidence links.
- **Decision Explorer:** Searchable catalog of architectural decisions with state filtering and alternative comparisons.
- **Evidence Panel:** Raw event inspector displaying verified commit diffs, PR discussions, and issue bodies.
- **Review Queue:** Maintainer triage queue for validating low-confidence decisions, resolving contributor conflicts, and inspecting drift alerts.
- **Live CI Drift Check:** Interactive diff evaluation simulating pull request checks against active decisions and guard rules.
- **Metrics & Baselines:** Dynamic scorecard displaying evaluation results, Wilson confidence intervals, and baseline comparisons.
- **Onboarding Tour:** Guided architectural walkthrough summarizing core subsystems for new developers.

For a structured demo walkthrough and speaker presentation script, see [`docs/process/PRESENTER_NOTES.md`](docs/process/PRESENTER_NOTES.md).

---

## 6. Evaluation Summary & Baselines

CIF was evaluated on **WhyBench-Synth**, a hand-authored synthetic benchmark of 71 questions across three domain repositories (`payment-core`, `cloud-hypervisor`, `cli-cli`) on the frozen `test_v2` split (26 positive questions, 45 unrecorded-topic negative questions):

### Task 1 — Evidence Retrieval (Evaluated on identical 26 positive questions)
- **Baseline A (BM25 Keyword Search):** 92.3% retrieval (24/26, 95% CI: [75.9%, 97.9%])
- **Baseline B (Docs-only Search):** 23.1% retrieval (6/26, 95% CI: [11.0%, 42.1%])
- **CIF (Task 1 Decision-Evidence Match):** 80.8% retrieval (21/26, 95% CI: [62.1%, 91.5%])

*Methodology Note:* CIF's Task-1 metric measures whether the single strictly-matched decision cites ≥1 expected event (matching strict recall), not a ranked retrieval list. BM25 raw event retrieval is higher. CIF's primary value is in lifecycle classification, structured refusal, and active CI guard rules.

### Task 2 — Decision Reconstruction & Refusal
- **Strict Recall:** 80.8% (21/26)
- **State Classification Accuracy:** 100.0% on matched decisions (21/21, Wilson 95% CI: [84.0%, 100.0%]; note small sample size $n=21$)
- **Refusal / Abstention Accuracy:** 64.4% on unrecorded-topic negatives (29/45 correctly refused; 16/45 receive an unsupported decision — see [`LIMITATIONS.md`](LIMITATIONS.md))

For complete evaluation manifests, Wilson confidence intervals, and corrections, see [`evaluation_results.md`](evaluation_results.md) and [`results/test_v2_20261013_100423/corrections_task1_fair.json`](results/test_v2_20261013_100423/corrections_task1_fair.json).

---

## 7. Key Project Documentation

- [`LIMITATIONS.md`](LIMITATIONS.md) — Measured limitations, known boundary conditions, and refusal performance analysis.
- [`PRIVACY.md`](PRIVACY.md) — Pre-ingestion redaction of secrets, API keys, and privacy guidelines.
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — Deployment instructions for local servers, Docker, and GitHub Pages.
- [`DEPLOY_LIVE.md`](DEPLOY_LIVE.md) — Live deployment runbook, hosting checklist, and verification guide.
- [`GITHUB_APP_SETUP.md`](GITHUB_APP_SETUP.md) — GitHub App registration, webhook configuration, and live tunnel setup.
- [`extension/`](extension/) — Chrome / browser developer extension.
- [`vscode-extension/`](vscode-extension/) — Visual Studio Code extension.
- [`docs/process/PRESENTER_NOTES.md`](docs/process/PRESENTER_NOTES.md) — Speaker notes, demo talk tracks, and exam preparation.
- [`AI_ASSISTANCE.md`](AI_ASSISTANCE.md) — Transparent disclosure of AI coding assistance, author responsibilities, and integrity notices.
- [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md) — Team contribution record template with verifiable git history facts.
- [`explanation.md`](explanation.md) — Deep architectural walkthrough of data models, database schema, and engine pipelines.
