# Three-Tier Architecture Specification
## Context Intelligence Framework (CIF)

The Context Intelligence Framework is engineered as a robust, decoupled **Three-Tier Architecture** adhering to clean separation of concerns, enterprise security principles, and strict standard-library engineering constraints.

---

```
+-----------------------------------------------------------------------------------+
|                           TIER 1: PRESENTATION LAYER                              |
|                                                                                   |
|  - Modern Semantic HTML5 & CSS Design System (Single Page Application)             |
|  - 9 Interactive Decision Surfaces:                                               |
|      1. Temporal Decision Timeline Slice                                          |
|      2. Interactive Context Graph Visualization (Canvas / SVG)                    |
|      3. Module-Level Bus Factor & Concentration Map                               |
|      4. Living ADR Artifact Explorer                                              |
|      5. Guard Rule Synthesis & CI Enforcement Queue                               |
|      6. Contributor Decision Review & Disagreement Resolution Queue               |
|      7. Grounded Natural-Language Context Explanations & Citations                |
|      8. WhyBench Real-World Benchmark Evaluation Suite                            |
|      9. Adaptive Onboarding Decision Path Generator                               |
|  - Dual-Mode Runtime: Live Dynamic API Engine (localhost) & Static Snapshot       |
|  - In-App Rate Limiting Toast Banner & Reactive Countdown Button Lockout          |
|  - Real GitHub Repository Ingestion Ledger with Fallback Resilience               |
+-----------------------------------------------------------------------------------+
                                       |
                   HTTP / REST / JSON  |  Headers: X-Request-ID, Authorization
                                       v
+-----------------------------------------------------------------------------------+
|                           TIER 2: APPLICATION LAYER                               |
|                                                                                   |
|  - HTTP Web Server (server.py: ThreadingHTTPServer, Multi-threaded)               |
|  - Request Correlation Context (UUID4 X-Request-ID Injection & Propagation)        |
|  - Centralized Sliding-Window Rate Limiter (backend/rate_limiter.py):              |
|      * auth: 10 req/min | ingest: 5 req/min                                       |
|      * expensive: 15 req/min | api: 60 req/min                                    |
|      * HTTP 429 + Retry-After + X-RateLimit-* Headers                             |
|  - Structured Rotating Logging & Auditing (backend/logging_config.py):             |
|      * application.log, api.log, error.log, database.log, security.log, rate_limit|
|      * Automatic Secret Redaction Filter (GitHub PATs, Bearer tokens, secrets)    |
|  - REST API Controller & Dispatcher (backend/api.py, 30+ endpoints)              |
|  - Role-Based Access Control (RBAC: Public, User, Repo Read, Reviewer, Admin)     |
|  - GitHub Ingestion Engine & Webhook Signature Verification (HMAC-SHA256)         |
|  - Static Code Analysis (Python AST Function & Class Extractor)                   |
|  - Temporal Graph Engine & Contributor Conflict / Supersession Resolution         |
|  - Code-Level Drift Detector & Anti-Hallucination Grounded Explanations           |
|  - Health & Diagnostics Observability Subsystem (/api/diagnostics)               |
+-----------------------------------------------------------------------------------+
                                       |
                     SQLite3 Client    |  PRAGMA foreign_keys = ON;
                     Parameterized SQL |  Connection Context Management
                                       v
+-----------------------------------------------------------------------------------+
|                             TIER 3: DATA LAYER                                    |
|                                                                                   |
|  - Authoritative Relational Operational Store: context_intelligence.db            |
|  - DDL Schema (Section 13 & Invariants):                                          |
|      * events: Commits, PRs, issues, ADR revisions with JSON artifacts           |
|      * entities: Canonical file paths and AST-extracted functions/classes         |
|      * decisions: Architectural decisions with state and rationale                |
|      * decision_evidence: Strict mechanical evidence linkage invariant             |
|      * decision_artifacts: Target module & source linkage mappings                |
|      * edges: Temporal causal & dependency relationships                          |
|      * guard_rules: Synthesized architectural constraints for CI/CD               |
|      * users & sessions: User accounts, salted PBKDF2/SHA256 tokens, RBAC         |
|      * repos: Monitored repository registry and access grants                     |
|  - Offline Evaluation Benchmark Dataset: whybench.db (Ground Truth Questions)     |
|  - Zero Unsanitized Interpolation: 100% Parameterized Prepared Statements         |
+-----------------------------------------------------------------------------------+
```

---

## 1. Tier 1: Presentation Layer (Frontend)

### Structure & Responsibilities
The presentation layer is located under `web/` (mirrored to `docs/` for GitHub Pages and `new_frontend/` for UI evaluation). It consists of standard semantic HTML5, clean scoped CSS (`web/style.css`), and an asynchronous modular JavaScript runtime (`web/app.js`).

### Core Capabilities
1. **Interactive Dashboard (`web/dashboard.html`)**: Single page interface hosting all 9 decision intelligence views.
2. **Unified API Gateway (`apiFetch`)**: Centralized HTTP client managing authentication Bearer tokens, request timeouts, and structured error responses.
3. **Reactive Rate-Limiting Protection**: When the server returns HTTP 429, `apiFetch` intercepts the error, parses `Retry-After`, triggers a non-intrusive red banner at the top of the viewport, locks the triggering button, displays a live seconds countdown, and automatically re-enables the UI when the window expires.
4. **Dual-Mode Engine Detection**: Detects whether it is connected to a live local backend (`http://127.0.0.1:8080`) or running as a static GitHub Pages deployment (`nagarwal00.github.io`). The top bar badge displays `⬤ Live engine` or `⬤ Static snapshot`.
5. **Real Repository Ingestion UI**: Ingestion modal allows connecting any public or authenticated GitHub repository (such as `nagarwal00/breathwise-innovation-hackathon`), streaming ingestion logs, and visualizing real commits, authors, and AST entities.

---

## 2. Tier 2: Application Layer (Backend)

### Structure & Responsibilities
The application layer runs on Python standard library modules (`http.server.ThreadingHTTPServer`, `sqlite3`, `urllib`, `json`, `logging`, `threading`).

### Core Subsystems
1. **HTTP Server (`server.py`)**:
   - Multi-threaded connection pool.
   - Secure host binding verification (`check_bind_safety`).
   - CSRF Origin verification for cookie-authenticated requests.
   - Body size caps (`MAX_BODY_SIZE = 1MB`) with socket-draining logic preventing TCP reset errors across platforms.
   - Un-silenced, high-visibility request logging to console and rotating log files.
2. **Centralized Rate Limiter (`backend/rate_limiter.py`)**:
   - Sliding-window algorithm tracking per-IP (unauthenticated) and per-user (token hash) usage.
   - Granular quotas: `auth` (10/min), `ingest` (5/min), `expensive` (15/min), `api` (60/min).
   - Injects standard RFC rate limit headers: `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
3. **Logging & Observability Architecture (`backend/logging_config.py`)**:
   - Rotating file handlers (5 MB max, 5 backups) across 6 dedicated log streams.
   - Thread-local request correlation (`X-Request-ID`).
   - Automated secret redaction masking GitHub PATs and Bearer tokens.
4. **Context Intelligence Engines**:
   - **Temporal Context Graph (`backend/engine/graph.py`)**: Traverses causal chains, decision supersession, and validity intervals.
   - **Drift Detector (`backend/engine/drift_detector.py`)**: Evaluates incoming git diffs against accepted decisions and guard rules.
   - **Grounded Explanations (`backend/engine/explanation.py`)**: Synthesizes verified rationale with mandatory provenance URLs.

---

## 3. Tier 3: Data Layer (Database)

### Structure & Responsibilities
The data layer is managed by `backend/db.py` utilizing SQLite 3 with strict relational integrity.

### Core Guarantees
1. **Authoritative Operational Store**: `context_intelligence.db` is the primary database for all CIF entities, decisions, events, edges, and guard rules.
2. **Foreign Key Invariants**: Every connection executes `PRAGMA foreign_keys = ON;`.
3. **Transaction Safety**: Context managers (`with self.get_connection() as conn:`) ensure atomic commits and automatic rollback on unhandled exceptions.
4. **Mechanical Evidence Invariant (Section 5.2)**: An architectural decision cannot enter the `accepted` state without at least one verified evidence link in `decision_evidence`. Attempting to persist an unevidenced accepted decision raises an `InvariantViolationError`.
5. **Zero SQL Injection**: All queries utilize parameterized parameter substitution (`?`). Zero dynamic SQL string concatenation is permitted.
