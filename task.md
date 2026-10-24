# Task Management: Context Intelligence Framework Prototype

This document tracks all tasks, milestones, and deliverables for the **Context Intelligence Framework** prototype according to `docs/process/implementation.md` and `Context_Intelligence_FrameworkReport_Reviewed.docx`.

---

## Milestone 1: Data Model, Ingestion Pipeline & Ground Truth
- [x] **Task 1.1: Core Data Model & Storage Engine**
  - [x] Create SQLite database schema implementing tables: `events`, `entities`, `decisions`, `decision_evidence`, `decision_artifacts`, `edges`, `identities`, `state_history` ([`backend/db.py`](file:///c:/Users/HP/Desktop/SE_project/backend/db.py)).
  - [x] Implement application-level invariant checks (e.g., non-empty evidence for non-unresolved decisions per Section 5.2 and Section 13).
  - [x] Implement database helper methods and seed data migrations.
- [x] **Task 1.2: Multi-Source Ingestion Pipeline**
  - [x] Ingestion Adapter 1: Git Commits & Diffs with changed files and modified functions ([`backend/ingestion/git_adapter.py`](file:///c:/Users/HP/Desktop/SE_project/backend/ingestion/git_adapter.py)).
  - [x] Ingestion Adapter 2: GitHub Issues & Pull Requests with inline review comments and issue-PR linkage `Closes #...` ([`backend/ingestion/github_adapter.py`](file:///c:/Users/HP/Desktop/SE_project/backend/ingestion/github_adapter.py)).
  - [x] Ingestion Adapter 3: Architectural Decision Records (ADRs) & Docs with Nygard template parsing ([`backend/ingestion/adr_adapter.py`](file:///c:/Users/HP/Desktop/SE_project/backend/ingestion/adr_adapter.py)).
  - [x] Implement identity resolution table mapping contributors across Git emails and GitHub logins ([`backend/ingestion/identity.py`](file:///c:/Users/HP/Desktop/SE_project/backend/ingestion/identity.py)).
  - [x] Ensure every event provides an immutable, clickable `source_url`.
- [x] **Task 1.3: Pilot Repositories & Ground Truth Dataset**
  - [x] Build pilot repository 1: `acme-eng/thermal-control-system` (PID vs bang-bang controller, overheating incident, controlled drift scenario) ([`backend/seed_data.py`](file:///c:/Users/HP/Desktop/SE_project/backend/seed_data.py)).
  - [x] Build pilot repository 2: `acme-eng/distributed-cache-service` (in-memory LRU vs Redis cluster, memory leak, conflicting proposals) ([`backend/seed_data.py`](file:///c:/Users/HP/Desktop/SE_project/backend/seed_data.py)).
  - [x] Construct ground truth dataset with 32 labeled decisions, evidence pointers, and ground-truth states ([`backend/evaluation/ground_truth.py`](file:///c:/Users/HP/Desktop/SE_project/backend/evaluation/ground_truth.py)).

---

## Milestone 2: Context Engine, Graph & Drift Detection
- [x] **Task 2.1: Entity Resolution & Temporal Context Graph**
  - [x] File and module level entity resolution with path normalization ([`backend/engine/entity_res.py`](file:///c:/Users/HP/Desktop/SE_project/backend/engine/entity_res.py)).
  - [x] Function-level AST resolution (Python AST parser mapping function entities down to methods).
  - [x] Dependency manifest parser (`requirements.txt` tracking version bumps).
  - [x] Temporal context graph with edge time-bounding (`valid_from`, `valid_to`) ([`backend/engine/graph.py`](file:///c:/Users/HP/Desktop/SE_project/backend/engine/graph.py)).
  - [x] Implement canonical queries:
    - Query 1: Artifact Decision Chain (`decision_chain_for_artifact`)
    - Query 2: Full Evidence Trail (`full_evidence_trail`)
    - Query 3: Timeline Slice (`timeline_slice`)
- [x] **Task 2.2: Decision Extraction & State Machine**
  - [x] Structured candidate decision extractor with rationale, alternatives, and confidence ([`backend/engine/extractor.py`](file:///c:/Users/HP/Desktop/SE_project/backend/engine/extractor.py)).
  - [x] Decision lifecycle manager (`proposed`, `accepted`, `rejected`, `superseded`, `unresolved`).
  - [x] Strict evidence grounding validator (rejects ungrounded claims).
- [x] **Task 2.3: Reconciliation & Drift Detection Engine**
  - [x] Conflict detection detecting contributor disagreements on overlapping entities ([`backend/engine/reconciliation.py`](file:///c:/Users/HP/Desktop/SE_project/backend/engine/reconciliation.py)).
  - [x] Supersession detection (explicit phrasing & implicit contradictory rationale).
  - [x] Code-level drift detection (diff vs accepted decision rationale, flagging `drifts_from`) ([`backend/engine/drift_detector.py`](file:///c:/Users/HP/Desktop/SE_project/backend/engine/drift_detector.py)).
  - [x] Routing unconfident, conflicting, and drifting items to Review Queue.

---

## Milestone 3: Web Application, Evaluation & Documentation
- [x] **Task 3.1: Backend REST API & Server**
  - [x] API endpoints for graph queries, timeline, artifact context, decision details, evidence trail ([`backend/api.py`](file:///c:/Users/HP/Desktop/SE_project/backend/api.py)).
  - [x] Review Queue triage API: confirm, reject, merge, correct.
  - [x] Ingestion trigger & live drift check API endpoints.
  - [x] Standalone zero-dependency Python server ([`server.py`](file:///c:/Users/HP/Desktop/SE_project/server.py)).
- [x] **Task 3.2: Interactive Hosted Web Application (All 9 Surfaces)**
  - [x] Surface 1: **Project Timeline** (interactive chronological milestone view) ([`web/index.html`](file:///c:/Users/HP/Desktop/SE_project/web/index.html)).
  - [x] Surface 2: **Context Graph** (visual node-link interactive graph with color-coded edge types).
  - [x] Surface 3: **Code-Context View** (file/function tree with direct "Why does this exist?" decision chains).
  - [x] Surface 4: **Decision Explorer** (faceted filtering by state, search, rationale & alternatives).
  - [x] Surface 5: **Evidence Panel** (deep citation inspector with clickable `source_url` links).
  - [x] Surface 6: **Review Queue** (human review actions: confirm, reject, merge, correct).
  - [x] Surface 7: **Onboarding Tour** (curated walkthrough for new team members).
  - [x] Surface 8: **Live CI Drift Tester** (interactive unified diff simulation & Decision Guard Rules).
  - [x] Surface 9: **Evaluation Dashboard** (live benchmark metrics vs computed baselines).
  - [x] Responsive dark-mode styling and modern typography ([`web/style.css`](file:///c:/Users/HP/Desktop/SE_project/web/style.css)).
  - [x] Frontend dynamic controller and SVG canvas renderer ([`web/app.js`](file:///c:/Users/HP/Desktop/SE_project/web/app.js)).
- [x] **Task 3.3: Evaluation Pipeline & Baseline Comparison**
  - [x] Automated benchmark metrics calculation computed from reproducible data without literals (see [`evaluation_results.md`](file:///c:/Users/HP/Desktop/SE_project/evaluation_results.md)).
  - [x] Benchmark comparison against Baselines (Keyword token search, Docs-only search, Plain LLM, Copilot Q&A).
  - [x] WhyBench-Synth (hand-authored synthetic benchmark) evaluation across benchmark splits (metrics dynamically computed in [`evaluation_results.md`](file:///c:/Users/HP/Desktop/SE_project/evaluation_results.md)).
- [x] **Task 3.4: Comprehensive Documentation & Delivery**
  - [x] Generated `explanation.md` detailing architecture, schema, graph algorithms, and drift detection ([`explanation.md`](file:///c:/Users/HP/Desktop/SE_project/explanation.md)).
  - [x] Generated `readme.md` with step-by-step setup, installation, and live demo script for professors ([`readme.md`](file:///c:/Users/HP/Desktop/SE_project/readme.md)).
  - [x] Documented limitations, benchmark boundaries, and pilot scope in [`LIMITATIONS.md`](file:///c:/Users/HP/Desktop/SE_project/LIMITATIONS.md).
  - [x] Automated verification suite passing 100% of checks ([`run_demo.py`](file:///c:/Users/HP/Desktop/SE_project/run_demo.py)).
