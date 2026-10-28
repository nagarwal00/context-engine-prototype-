# Software Project Management Plan (SPMP)
## Context Intelligence Framework (CIF)

**Document Standard:** IEEE Std 1058 Compliant Project Management Plan  
**Project:** Context Intelligence Framework — Continuous Architectural Context Recovery & Drift Interception  
**Duration:** 17 Weeks (Academic Capstone Schedule)  
**Version:** 1.4.0  
**Status:** Approved / Baselined  
**Date:** October 2026  

---

## 1. Project Overview and Objectives

### 1.1 Project Charter
The Context Intelligence Framework (CIF) was undertaken as an intensive 17-week Software Engineering Capstone project to solve the problem of **architectural context loss and drift** in fast-moving software development teams. Traditional architectural documentation (such as wikis and ADRs) decays rapidly because documentation is decoupled from the code commit path.

### 1.2 Core Objectives & Success Criteria
1. **Mechanical Enforcement**: Deliver a zero-tolerance database invariant where 100% of persisted decisions are mechanically linked to verifiable evidence.
2. **Active Drift Prevention**: Move beyond passive documentation by synthesizing executable pre-commit guard rules.
3. **Zero-Ops Performance**: Execute graph context retrieval in under 15ms directly within in-process SQLite without distributed infrastructure.
4. **Multi-Surface Integration**: Seamlessly expose context to developers across their native toolchain (Web Dashboard, VS Code, Chrome, Git CLI).
5. **Rigorous Engineering Validation**: Achieve 329 passing unit tests, 21 demo verification checks, zero flaky tests, and zero database mutations.

---

## 2. Lifecycle Methodology and Process Model

The project followed an **Iterative and Incremental Unified Process** structured across four classical software engineering phases: **Inception**, **Elaboration**, **Construction**, and **Transition**, concluding with a dedicated **Evaluation & Remediation Phase**.

```
Weeks:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17
Phases: [ INCEPTION ] [   ELABORATION   ] [       CONSTRUCTION       ] [ TRANSITION ] [ REMEDIATION ]
Gates:       G1              G2                        G3                 G4             G5 (Final)
```

---

## 3. 17-Week Milestone Schedule & Work Breakdown

### Phase 1: Inception (Weeks 1–3)
- **Week 1: Literature Review & Problem Formulation**
  - Analyzed related paradigms: *Continuum* (passive commit mining), *Warrant* (Toulmin argumentation), and *Enterprise Context Graphs*.
  - Formulated the core thesis: architectural governance requires active mechanical invariants and pre-commit interception.
- **Week 2: Requirements Specification & Stakeholder Analysis**
  - Formulated Functional Requirements (FR-1 through FR-12) and Non-Functional Requirements.
  - Baselined the IEEE 830-compliant [docs/sdlc/SRS.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/SRS.md).
- **Week 3: Architectural Spikes & Feasibility Prototyping**
  - Evaluated SQLite vs Neo4j latency; established that in-process SQLite fulfills the sub-15ms latency constraint without operational overhead.
  - Developed initial pre-commit hook proof-of-concept.
  - **Milestone Gate 1 (Inception Sign-off)**: Scope, problem statement, and feasibility verified.

### Phase 2: Elaboration (Weeks 4–7)
- **Week 4: Architecture & Schema Design**
  - Authored the IEEE 1471 [docs/sdlc/ARCHITECTURE.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/ARCHITECTURE.md).
  - Designed relational schema (`events`, `decisions`, `evidence`, `graph_edges`, `state_history`).
  - Implemented the database migration framework (`backend/migrations/runner.py`).
- **Week 5: Storage Layer & Mechanical Grounding Invariant**
  - Implemented `backend/db.py` with strict foreign keys and transactional validation.
  - Codified the non-negotiable rule: any decision without an evidence edge raises `InvariantViolationError`.
- **Week 6: Ingestion Adapters & Privacy Sanitizer**
  - Implemented GitHub Webhook/REST ingestion and offline Slack export adapter (`backend/ingestion/`).
  - Implemented deterministic regex-based secret scrubbing in `PrivacySanitizer`.
- **Week 7: Decision Extraction Engine**
  - Built the heuristic and keyword-boundary extraction pipeline in `backend/engine/extractor.py`.
  - **Milestone Gate 2 (Elaboration Sign-off)**: Core database invariant, ingestion, and extraction operational.

### Phase 3: Construction (Weeks 8–13)
- **Week 8: Lifecycle State Model & Audit Logging**
  - Implemented finite state machine (`PROPOSED`, `ACCEPTED`, `SUPERSEDED`, `REJECTED`) in `backend/engine/lifecycle.py`.
  - Added historical transition logging in `state_history`.
- **Week 9: Guard Rule Synthesis & Pre-Commit Drift Interception**
  - Implemented `backend/engine/guard_rules.py` to compile rejected alternatives into executable AST and regex patterns.
  - Implemented `backend/engine/drift_detector.py` and CI check script (`tools/ci_check.py`).
- **Week 10: Multi-Tenant Repository Isolation & Conflict Detection**
  - Added strict repository-level isolation across all query surfaces (`backend/db.py`, `backend/api.py`).
  - Implemented cross-decision conflict detection using word-boundary pattern matching (`backend/engine/reconciliation.py`).
- **Week 11: Developer Surfaces — Web Dashboard**
  - Developed responsive single-page application in `web/` rendering decision trees, drift monitors, and evidence links.
- **Week 12: Developer Surfaces — Extensions**
  - Developed Google Chrome Extension (`extension/`) for GitHub PR injection.
  - Developed VS Code Extension (`vscode-extension/`) for in-editor context cards.
- **Week 13: Baseline Search & Retrieval Engines**
  - Implemented Lexical / BM25 baseline retrieval engine (`backend/evaluation/baselines.py`) for comparative benchmarking.
  - **Milestone Gate 3 (Construction Sign-off)**: Full functional feature set complete across backend, UI, and extensions.

### Phase 4: Transition & Verification (Weeks 14–16)
- **Week 14: Benchmark Curation (WhyBench)**
  - Authored WhyBench evaluation dataset (134 items, 26 question sets) and froze SHA-256 cryptographic manifests.
  - Verified BM25 vs CIF performance with Wilson 95% confidence intervals.
- **Week 15: Pilot Repositories & Hold-Out Generalization**
  - Created synthetic pilot repositories (`acme-eng/thermal-control-system`, `acme-eng/distributed-cache-service`).
  - Added independent hold-out drift evaluation set (`acme-eng/job-queue-service`).
- **Week 16: Packaging, Static Deployment, and User Study Protocol**
  - Created offline release packaging tool (`tools/package_release.py`) and static snapshot generator (`tools/build_static.py`).
  - Authored formal user study protocol (`user_study/PROTOCOL.md`, `TASKS.md`, `CONSENT.md`).
  - **Milestone Gate 4 (Transition Sign-off)**: Benchmarks frozen, documentation prepared, pilot tests passing.

### Phase 5: Evaluation & Review Remediation (Week 17)
- **Week 17: Capstone Review Response & Hardening**
  - Conducted thorough audit against [Re-evaluation_CIF_v4.md](file:///c:/Users/HP/Desktop/SE_project/Re-evaluation_CIF_v4.md).
  - Hardened local HTTP server and test clients against socket teardown flakiness (`BrokenPipeError`, `ConnectionResetError`).
  - Corrected tool discovery paths in `tools/print_facts.py` to accurately report all 329 tests.
  - Cleaned repository clutter (purged `temp_ci.db`, `backups/`, stale release archives in `dist/`, and placeholder decision titles).
  - Authored formal SDLC suite: [SRS.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/SRS.md), [ARCHITECTURE.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/ARCHITECTURE.md), [TEST_PLAN.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/TEST_PLAN.md), and [PROJECT_PLAN.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/PROJECT_PLAN.md).
  - **Milestone Gate 5 (Final Release Gate)**: All 7 verification gates passing 100%.

---

## 4. Risk Management Matrix

| Risk ID | Risk Description | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|---|
| **R-1** | Test flakiness due to ephemeral socket resets on Windows | Med | High | Implemented socket retry handlers and caught `(BrokenPipeError, ConnectionResetError)` in `server.py` and test harnesses. |
| **R-2** | Inadvertent credential leakage in Git repository | Low | Critical | Deployed `tools/scan_secrets.py` as an automated gate and enforced `PrivacySanitizer` at ingestion boundary. |
| **R-3** | Database state mutation during automated test runs | Med | High | Enforced ephemeral SQLite sandboxes via `tempfile.mkdtemp` and validated with `tools/verify_db_untouched.py`. |
| **R-4** | Benchmark dataset contamination or circular reasoning | High | High | Cryptographically locked WhyBench JSON files with SHA-256 hashes and introduced an independent third-domain hold-out set. |
| **R-5** | Documentation drift and stale metric citations | High | Med | Implemented `tools/print_facts.py` and `tools/check_docs.py` to enforce automated consistency. |

---

## 5. Traceability and Quality Assurance Mapping

Every phase of the project plan was governed by continuous test automation:
- **Requirements Traceability**: Defined in [docs/sdlc/SRS.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/SRS.md) and mapped to test scripts in [docs/sdlc/TEST_PLAN.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/TEST_PLAN.md).
- **Architecture Compliance**: Defined in [docs/sdlc/ARCHITECTURE.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/ARCHITECTURE.md) and validated via `run_demo.py` (21/21 checks).
- **Engineering Authenticity**: Fully documented in [STATUS_AUDIT.md](file:///c:/Users/HP/Desktop/SE_project/STATUS_AUDIT.md) with verified file citations and zero fabricated statistics.
