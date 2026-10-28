# Software Requirements Specification (SRS)
## Context Intelligence Framework (CIF)

**Document Standard:** IEEE Std 830-1998 Compliant  
**Project:** Context Intelligence Framework — Continuous Architectural Context Recovery & Drift Interception  
**Version:** 1.4.0  
**Status:** Approved / Baselined  
**Date:** October 2026  

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) provides a complete, formal description of the Context Intelligence Framework (CIF). It defines the functional, interface, performance, and mechanical invariant requirements for capturing, grounding, querying, and enforcing architectural decisions across distributed software engineering repositories.

### 1.2 Scope
CIF is an active architectural knowledge engine and developer governance toolchain. Unlike traditional passive documentation systems (ADRs, static wikis) or offline mining tools, CIF:
1. Continuously ingests developer discourse and version control events from GitHub and Slack.
2. Extracts architectural decisions, rationales, and alternatives using deterministic heuristic and regex pipelines.
3. Enforces an immutable **Mechanical Grounding Invariant**: every persisted decision must possess verified, bi-directional evidence edges linking to concrete events.
4. Synthesizes active pre-commit lint and abstract syntax tree (AST) guard rules to intercept architectural drift before code reaches production.
5. Surfaces decision lineage and justification directly into developer workflows via a Web Dashboard, VS Code Extension, Chrome Extension, and Git Pre-commit Hooks.

### 1.3 Definitions, Acronyms, and Abbreviations
- **ADR**: Architecture Decision Record.
- **AST**: Abstract Syntax Tree.
- **CIF**: Context Intelligence Framework.
- **Drift**: Code changes or pull requests that violate, contradict, or bypass established architectural decisions.
- **Evidence Edge**: A typed graph relationship linking an architectural decision to a source event (commit, pull request, issue, or message).
- **Mechanical Grounding**: The strict database and domain invariant requiring that no decision entity exists without at least one verifiable evidence link.
- **PII**: Personally Identifiable Information.
- **Toulmin Model**: An argumentation structure comprising claims, grounds, warrants, backings, and rebuttals.
- **WAL**: Write-Ahead Logging (SQLite journaling mode).

### 1.4 References
- IEEE Std 830-1998: *IEEE Recommended Practice for Software Requirements Specifications*.
- Architecture Documentation: [docs/sdlc/ARCHITECTURE.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/ARCHITECTURE.md)
- Software Test Plan: [docs/sdlc/TEST_PLAN.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/TEST_PLAN.md)
- Software Project Plan: [docs/sdlc/PROJECT_PLAN.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/PROJECT_PLAN.md)
- Engineering Status Audit: [STATUS_AUDIT.md](file:///c:/Users/HP/Desktop/SE_project/STATUS_AUDIT.md)
- System Limitations: [LIMITATIONS.md](file:///c:/Users/HP/Desktop/SE_project/LIMITATIONS.md)

---

## 2. Overall Description

### 2.1 Product Perspective
CIF operates as a self-contained, lightweight context engine embedded directly within modern engineering toolchains. It interfaces upstream with developer event streams (GitHub REST/Webhooks and Slack workspace exports) and downstream with developer touchpoints (IDE, browser, terminal, and CI/CD).

```
[GitHub / Slack] --> [Ingestion & Sanitization] --> [Extractor Engine]
                                                           |
                                                           v
[Developer Tooling] <-- [REST API / Engine] <-- [Grounded SQLite DB]
 (Web, IDE, Pre-commit)
```

### 2.2 Product Functions
- **Multi-Source Ingestion**: Ingests commits, PRs, issues, comments, and threaded chat messages.
- **Automated Decision Extraction**: Identifies candidate architectural decisions, alternatives rejected, and rationale.
- **Mechanical Grounding Validation**: Rejects ungrounded assertions prior to SQLite database write.
- **Bidirectional Traceability**: Links code artifacts back to originating discussions and decisions.
- **Active Drift Interception**: Validates staged git diffs against synthesized guard rules.
- **Conflict Detection**: Flags contradictory or mutually exclusive architectural directives across repositories.
- **Privacy & Security Scrubbing**: Strips credentials, API keys, tokens, and PII before database persistence.

### 2.3 User Classes and Characteristics
1. **Software Architect**: Defines strategic patterns, inspects cross-repository drift, resolves architectural conflicts.
2. **Software Engineer**: Authors commits and PRs; receives contextual decision cards in VS Code and pre-commit drift alerts.
3. **Engineering Manager**: Evaluates architectural compliance, team consensus, and documentation velocity via the Web Dashboard.
4. **Capstone Evaluator / Auditor**: Verifies reproducibility, test suites, cryptographic manifests, and mechanical guarantees.

### 2.4 Operating Environment
- **Operating Systems**: Cross-platform (Windows 10/11, macOS 12+, Ubuntu Linux 20.04+).
- **Runtime**: Python 3.10+ (Standard Library preferred; minimal external dependencies).
- **Database Engine**: Embedded SQLite 3.35+ with WAL mode enabled.
- **Browser Environments**: Modern Chromium-based browsers (Chrome, Edge, Brave) and Firefox.

### 2.5 Design and Implementation Constraints
- **Zero Heavyweight DB Dependency**: The engine must operate entirely without requiring external database servers (e.g., PostgreSQL, Neo4j, Redis).
- **Sub-15ms Query Latency**: All context retrieval and path-traversal queries must execute within 15 milliseconds on commodity hardware.
- **Strict Privacy Invariant**: Zero raw authentication tokens, secret keys, or unscrubbed PII may enter the database.
- **Immutability of Frozen Benchmarks**: Benchmark fixtures (`whybench.db`, `backend/evaluation/whybench/`) must remain cryptographically frozen and never mutated during test runs.

---

## 3. Specific Requirements

### 3.1 External Interface Requirements

#### 3.1.1 User Interfaces
- **Web Dashboard (`web/`)**: Single-page application rendering decision trees, evidence timelines, drift alerts, and lifecycle state management controls.
- **VS Code Extension (`vscode-extension/`)**: Language server client / side-panel surfacing decision rationale when cursor enters annotated code ranges.
- **Chrome Extension (`extension/`)**: Injects context cards and evidence links directly into GitHub PR and Issue web views.

#### 3.1.2 Software Interfaces
- **GitHub App / Webhook Receiver (`backend/api.py`)**: Consumes `push`, `pull_request`, and `issues` JSON payloads.
- **Slack Adapter (`backend/ingestion/slack_adapter.py`)**: Parses standard Slack directory export structures (`channels.json`, `users.json`, daily logs).
- **CI Guard Client (`tools/ci_check.py`)**: Intercepts pull request diff violations in CI and local workflows.

---

### 3.2 Functional Requirements (FR)

| Req ID | Requirement Title | Detailed Specification |
|---|---|---|
| **FR-1** | Multi-Source Ingestion | The system shall ingest developer events from GitHub webhooks, REST APIs, and offline Slack exports, standardizing them into an immutable `Event` schema with unique IDs, timestamps, and authorship metadata. |
| **FR-2** | PII and Secret Sanitization | Prior to database persistence, all text payloads must pass through `PrivacySanitizer` to scrub email addresses, AWS/GitHub access keys, bearer tokens, and private keys using deterministic regular expressions. |
| **FR-3** | Decision Extraction | The system shall extract candidate decisions from structured discourse using heuristic rules and keyword boundary patterns, identifying title, rationale, status, and rejected alternatives. |
| **FR-4** | Mechanical Grounding Enforcement | The storage subsystem (`backend/db.py`) shall enforce that every `Decision` record has at least one associated `Evidence` link pointing to an existing `Event`. Unbacked decisions must raise an `InvariantViolationError` and abort the transaction. |
| **FR-5** | Graph Storage & Query | The system shall maintain an in-process directed property graph in SQLite (`graph_edges`), supporting sub-15ms traversal of causal paths between events, decisions, and files. |
| **FR-6** | Active Guard Rule Synthesis | When a decision documents rejected patterns or forbidden libraries (e.g., in backticked tokens), the engine shall automatically synthesize AST/regex guard rules (`cif_rules.json`). |
| **FR-7** | Pre-Commit Drift Interception | The pre-commit hook shall inspect staged file diffs against active guard rules and reject commits that re-introduce forbidden patterns, returning non-zero exit codes with actionable remediation messages. |
| **FR-8** | Conflict Detection | The system shall detect mutually contradictory decisions (e.g., adopting conflicting concurrency models or protocols) across repositories using word-boundary token matching, flagging conflicts in the dashboard. |
| **FR-9** | Lifecycle State Transition | The system shall manage decision lifecycles across valid states (`PROPOSED`, `ACCEPTED`, `SUPERSEDED`, `REJECTED`), enforcing valid transition paths and logging every state change in `state_history` with audit timestamps. |
| **FR-10** | Multi-Tenant Repository Isolation | Queries and operations scoped to a specific repository (`repo_full_name`) must strictly isolate data, preventing cross-tenant leakage of events, decisions, or drift rules. |
| **FR-11** | Source Independence Calibration | The engine shall compute confidence scores based on multi-source verification (e.g., consensus across PR reviews and Slack discussions), discounting uncorroborated single-author claims. |
| **FR-12** | Reproducible Evaluation & Export | The system shall provide deterministic benchmark reproduction (`tools/validate_whybench.py`, `run_demo.py`) with cryptographic SHA-256 manifests validating dataset and database integrity. |

---

### 3.3 Non-Functional Requirements (NFR)

#### 3.3.1 NFR-1: Performance & Latency
- The median query latency for context graph lookups and explanation retrieval shall not exceed **15 milliseconds** on standard developer hardware.
- Pre-commit hook inspection of staged diffs shall complete in less than **500 milliseconds**.

#### 3.3.2 NFR-2: Security & Privacy
- The system shall produce **zero secret leaks** across all logs, tables, and serialized payloads, verified by `tools/scan_secrets.py`.
- Authentication for management endpoints shall use API keys and timing-safe token verification.

#### 3.3.3 NFR-3: Reliability & Determinism
- Full test suite execution (`329 tests`) shall run with **100% pass rate** and zero non-deterministic or timing-dependent failures.
- Testing operations must run exclusively against isolated temporary databases and never modify shipping reference databases (`tools/verify_db_untouched.py`).

#### 3.3.4 NFR-4: Portability & Zero-Ops
- The core backend shall require only Python 3.10+ standard libraries and SQLite, running out-of-the-box without Docker, daemon processes, or cloud accounts.
- Optional containerized deployment must be provided via a minimal `Dockerfile`.

---

## 4. Verification and Traceability Matrix

| Requirement | Implementation Artifacts | Verification Method / Test Suite |
|---|---|---|
| **FR-1: Ingestion** | `backend/ingestion/`, `backend/models.py` | `tests/test_adapters_and_engine.py`, `run_demo.py` |
| **FR-2: Sanitizer** | `backend/ingestion/sanitizer.py` | `tests/test_sanitizer.py`, `tools/scan_secrets.py` |
| **FR-3: Extraction** | `backend/engine/extractor.py` | `tests/test_extractor.py`, `tests/test_benchmark.py` |
| **FR-4: Grounding** | `backend/db.py`, `backend/models.py` | `tests/test_independence.py`, `run_demo.py` Check 1 |
| **FR-5: Graph Engine** | `backend/engine/graph.py`, `backend/db.py` | `tests/test_graph_temporal.py`, `tests/test_all_features_and_buttons.py` |
| **FR-6: Guard Synthesis**| `backend/engine/guard_rules.py` | `tests/test_generic_guard_synthesis.py` |
| **FR-7: Drift Intercept**| `backend/engine/drift_detector.py`, `tools/ci_check.py` | `tests/test_drift.py`, `run_demo.py` Check 4 |
| **FR-8: Conflict Match**| `backend/engine/reconciliation.py` | `tests/test_conflict_pairs.py`, `run_demo.py` Check 7 |
| **FR-9: Lifecycle** | `backend/engine/lifecycle.py`, `backend/db.py` | `tests/test_state_model.py`, `tests/test_history_recorded.py` |
| **FR-10: Isolation** | `backend/db.py`, `backend/api.py` | `tests/test_repo_isolation.py` |
| **FR-11: Calibration** | `backend/engine/extractor.py` | `tests/test_extractor.py` |
| **FR-12: Benchmark** | `backend/evaluation/`, `tools/validate_whybench.py` | `tools/validate_whybench.py`, `tools/print_facts.py` |
