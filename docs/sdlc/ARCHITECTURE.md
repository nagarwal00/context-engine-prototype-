# Software Architecture Document (SAD)
## Context Intelligence Framework (CIF)

**Document Standard:** IEEE Std 1471 / ISO/IEC 42010 Architecture Description  
**Project:** Context Intelligence Framework — Continuous Architectural Context Recovery & Drift Interception  
**Version:** 1.4.0  
**Status:** Approved / Baselined  
**Date:** October 2026  

---

## 1. Architectural Representation and Style

The Context Intelligence Framework (CIF) is designed using a **Layered Hexagonal Architecture** (Ports and Adapters) coupled with an **In-Process Temporal Graph Engine**. 

```
+-------------------------------------------------------------------------------+
|                             DEVELOPER SURFACES                                |
|   Web Dashboard (SPA)   |   VS Code Extension   |   Chrome Ext   |   CLI/Git  |
+-------------------------+-----------------------+----------------+------------+
                                     | REST / JSON / Hooks
                                     v
+-------------------------------------------------------------------------------+
|                            API & APPLICATION LAYER                            |
|        API Handler (`backend/api.py`)  |  Server Dispatch (`server.py`)       |
+-------------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------------+
|                              CORE ENGINE LAYER                                |
|  Decision Extractor   |  Lifecycle State   |  Drift Interceptor |  Sanitizer  |
|  Conflict Matcher     |  Calibration       |  Guard Synthesizer |  Resolver   |
+-------------------------------------------------------------------------------+
                                     | Invariant Enforcement
                                     v
+-------------------------------------------------------------------------------+
|                            STORAGE & GRAPH LAYER                              |
|           Database Layer (`backend/db.py`) with Mechanical Grounding          |
|                 In-Process SQLite Engine (WAL Mode, Graph Edges)              |
+-------------------------------------------------------------------------------+
                                     ^
                                     | Normalized Ingestion
+-------------------------------------------------------------------------------+
|                              INGESTION ADAPTERS                               |
|        GitHub Webhooks / REST API       |        Offline Slack Export         |
+-------------------------------------------------------------------------------+
```

### Key Architectural Principles
1. **Mechanical Grounding Invariant**: Architectural decisions cannot exist in isolation. The data access layer enforces that every decision entity has at least one verified evidence edge to a source event.
2. **Lightweight In-Process Persistence**: Zero external database dependencies (e.g., Neo4j, PostgreSQL). Graph traversal and temporal state tracking operate directly within SQLite via Python standard libraries.
3. **Deterministic Pre-Commit Interception**: Architectural rules are not merely advisory; they are compiled into executable AST and regex guards validated at the developer's commit boundary.
4. **Privacy-by-Design**: Sanitization occurs immediately upon payload ingestion prior to database writes.

---

## 2. Component Architecture

The following diagram illustrates the component interactions across the ingestion, analysis, storage, and developer interface subsystems:

```mermaid
graph TD
    subgraph Ingestion["Ingestion Subsystem"]
        GH["GitHub Webhook / REST"] -->|Raw JSON| PS["Privacy Sanitizer"]
        SL["Slack Export Adapter"] -->|Raw JSON| PS
        PS -->|Scrubbed Event| EVT["Event Factory"]
    end

    subgraph CoreEngine["Core Intelligence Engine"]
        EVT --> EXT["Decision Extractor"]
        EXT -->|Candidate Decision| MGI{"Mechanical Invariant Validator"}
        MGI -->|Valid Evidence Link| DB[("SQLite Database Layer")]
        MGI -->|Missing Evidence| REJ["Raise InvariantViolationError"]
        
        EXT --> GS["Guard Synthesizer"]
        GS -->|Compiled Rules| CR["cif_rules.json"]
        
        DB --> CM["Conflict Matcher"]
        DB --> CAL["Calibration Engine"]
        DB --> LC["Lifecycle Manager"]
    end

    subgraph DeveloperSurfaces["Developer Touchpoints"]
        CR --> PC["Git Pre-Commit Hook"]
        DB --> API["REST API Handler"]
        API --> WEB["Web Dashboard"]
        API --> EXT_CH["Chrome Extension"]
        API --> EXT_VS["VS Code Extension"]
    end
```

---

## 3. Data Model and Schema Architecture

The relational schema is optimized for graph edge traversals, multi-tenant isolation, and temporal audit logging.

```mermaid
erDiagram
    EVENT ||--o{ EVIDENCE : "evidenced_by"
    DECISION ||--|{ EVIDENCE : "grounded_in"
    DECISION ||--o{ STATE_HISTORY : "tracks_lifecycle"
    DECISION ||--o{ GRAPH_EDGE : "originates"
    DECISION ||--o{ GUARD_RULE : "synthesizes"
    EVENT ||--o{ GRAPH_EDGE : "participates"

    EVENT {
        string event_id PK
        string repo_full_name
        string source_type
        string author
        string title
        string content
        datetime created_at
    }

    DECISION {
        string decision_id PK
        string repo_full_name
        string title
        string status
        string rationale
        string alternatives_rejected
        datetime created_at
    }

    EVIDENCE {
        string evidence_id PK
        string decision_id FK
        string event_id FK
        string quote
        float confidence
    }

    STATE_HISTORY {
        int history_id PK
        string decision_id FK
        string old_status
        string new_status
        string changed_by
        datetime changed_at
    }

    GRAPH_EDGE {
        string edge_id PK
        string repo_full_name
        string source_node
        string target_node
        string edge_type
        float weight
    }

    GUARD_RULE {
        string rule_id PK
        string decision_id FK
        string pattern
        string rule_type
        string message
    }
```

### Schema Guarantees
- **Referential Integrity**: SQLite `PRAGMA foreign_keys = ON;` is enforced on every connection.
- **Atomic Migrations**: Managed via `backend/migrations/runner.py` with idempotent migration scripts.
- **Repo Isolation**: Every table carries `repo_full_name`, indexed for constant-time multi-tenant filtering.

---

## 4. Dynamic Process Views (Sequence Diagrams)

### 4.1 Webhook Ingestion & Mechanical Grounding Enforcement

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant GH as GitHub Platform
    participant API as CIF API Handler
    participant SAN as Privacy Sanitizer
    participant EXT as Decision Extractor
    participant DB as SQLite DB Layer

    Dev->>GH: Push Commit / Open PR
    GH->>API: POST /api/webhook/github
    API->>SAN: sanitize_payload(payload)
    SAN-->>API: scrubbed_payload (zero secrets)
    API->>EXT: extract_decisions(scrubbed_payload)
    EXT->>EXT: Identify rationale & alternatives
    EXT-->>API: [Candidate Decisions + Evidence Links]
    API->>DB: save_decision_with_evidence(decision, evidence)
    alt Evidence Link Present
        DB->>DB: INSERT INTO decisions & INSERT INTO evidence
        DB-->>API: Success (201 Created)
    else Missing Evidence Link
        DB-->>API: InvariantViolationError (Transaction Aborted)
        API-->>GH: HTTP 422 Unprocessable Entity
    end
```

### 4.2 Pre-Commit Drift Interception

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant Git as Local Git Hook
    participant Drift as CIF Drift Engine
    participant Rules as cif_rules.json

    Dev->>Git: git commit -m "Add feature"
    Git->>Drift: run_pre_commit(staged_diffs)
    Drift->>Rules: Load active guard rules
    Drift->>Drift: Scan diffs against regex / AST rules
    alt No Violations Detected
        Drift-->>Git: Exit Code 0 (Clean)
        Git-->>Dev: Commit Accepted
    else Violation Found (e.g. Forbidden Dependency)
        Drift-->>Git: Exit Code 1 (Violation Detected)
        Git-->>Dev: Commit Aborted with Rationale & Remediation
    end
```

---

## 5. Security & Privacy Architecture

1. **Sanitization Pipeline**: All raw strings pass through `PrivacySanitizer` before tokenization or storage:
   - AWS Keys (`AKIA[0-9A-Z]{16}`)
   - GitHub Personal Access Tokens (`ghp_[0-9a-zA-Z]{36}`)
   - Generic Bearer Tokens and Private Keys (`BEGIN PRIVATE KEY`)
   - Personal email addresses and identity tokens
2. **Timing-Safe Auth Verification**: API management requests authenticate via SHA-256 tokens evaluated using constant-time string comparison (`hmac.compare_digest`) to prevent timing attacks.
3. **Read-Only Test Execution**: Automated test execution runs against isolated in-memory or temporary database instances, guaranteeing that reference databases are never modified.

---

## 6. Architectural Positioning Against Related Frameworks

| Paradigm | Key Distinction from CIF |
|---|---|
| **Continuum** | Continuum performs post-hoc mining of historical commit logs. CIF enforces active runtime invariants and pre-commit drift interception. |
| **Warrant (Toulmin)** | Toulmin models define conceptual argumentation schemas. CIF operationalizes warrants into bi-directional, machine-checkable evidence edges. |
| **Context Graph** | Enterprise context graphs rely on distributed graph engines (Neo4j). CIF implements lightweight in-process graph traversal directly in SQLite with sub-15ms latency. |
