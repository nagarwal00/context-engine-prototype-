# Database Architecture Specification
## Context Intelligence Framework (CIF)

This document formalizes the Tier 3 relational persistence architecture, DDL schema, migration pipeline, and integrity invariants implemented in `backend/db.py`.

---

## 1. Database Identification & Roles

The project root contains distinct database files with clearly defined roles:

| Database File | File Size | Role & Status |
|---|---|---|
| `context_intelligence.db` | ~389 KB | **Authoritative Operational Store**. Primary relational database utilized by `server.py` and `backend/api.py`. Contains 7 migrations and all active decisions, entities, events, edges, and guard rules. |
| `whybench.db` | ~520 KB | **Evaluation Benchmark Dataset**. Contains offline WhyBench evaluation split data, 134 questions, and ground-truth references. |
| `cif.db` | ~364 KB | **Schema Prototype**. Empty baseline schema structure used for migration template testing. |
| `cif_dashboard.db` | 0 KB | **Legacy Stub**. Superseded by `context_intelligence.db`. |

---

## 2. Core Relational Schema

### 1. `events` Table
Captures raw developmental provenance (commits, pull request discussions, issues, ADR revisions):
```sql
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,       -- commit | issue | pr | adr
    source_id TEXT NOT NULL,         -- git sha | PR # | issue #
    source_url TEXT NOT NULL,        -- verified clickable HTTPS URL
    repo TEXT NOT NULL,              -- owner/repo
    author TEXT,                     -- author identity string
    ts TEXT NOT NULL,                -- ISO 8601 UTC timestamp
    title TEXT,
    body TEXT,
    artifacts_touched TEXT,          -- JSON array of file paths
    parent_event_ids TEXT,           -- JSON array of parent event IDs
    raw_metadata TEXT,               -- JSON dict
    UNIQUE (source_type, source_id, repo)
);
```

### 2. `entities` Table
Represents software components, files, and AST-parsed functions and classes:
```sql
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,       -- file | module | function | class
    canonical_path TEXT NOT NULL,    -- standardized repository-relative path
    aliases TEXT DEFAULT '[]',       -- JSON array of known aliases
    repo TEXT NOT NULL,
    current_state_summary TEXT,
    UNIQUE (canonical_path, repo)
);
```

### 3. `decisions` Table
Represents substantive architectural choices:
```sql
CREATE TABLE IF NOT EXISTS decisions (
    decision_id TEXT PRIMARY KEY,
    repo TEXT NOT NULL,
    title TEXT NOT NULL,
    state TEXT NOT NULL,             -- proposed | accepted | rejected | superseded
    rationale TEXT,
    key_assumptions TEXT,
    author TEXT,
    date_recorded TEXT NOT NULL,
    adr_path TEXT
);
```

### 4. `decision_evidence` Table & Mechanical Invariant (Section 5.2)
Links architectural decisions to verified historical events:
```sql
CREATE TABLE IF NOT EXISTS decision_evidence (
    decision_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,     -- adr | pr_discussion | commit_msg
    strength TEXT NOT NULL,          -- strong | medium | weak
    PRIMARY KEY (decision_id, event_id),
    FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
);
```
> [!IMPORTANT]
> **Mechanical Evidence Invariant**: An architectural decision in `accepted` state must possess `>= 1` verified link in `decision_evidence`. Inserting or updating a decision to `accepted` without evidence triggers an `InvariantViolationError`.

### 5. `edges` Table (Temporal Context Graph)
Links entities and decisions with causal and dependency relationships:
```sql
CREATE TABLE IF NOT EXISTS edges (
    edge_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,         -- affects | derives_from | supersedes
    repo TEXT NOT NULL,
    valid_from TEXT NOT NULL,        -- ISO 8601 timestamp
    valid_to TEXT,                   -- NULL if currently active
    metadata TEXT DEFAULT '{}'
);
```

### 6. `guard_rules` Table
Synthesized architectural invariants enforced during CI/CD drift detection passes:
```sql
CREATE TABLE IF NOT EXISTS guard_rules (
    rule_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    repo TEXT NOT NULL,
    target_pattern TEXT NOT NULL,
    forbidden_pattern TEXT NOT NULL,
    rule_type TEXT NOT NULL,         -- forbid_pattern | require_pattern
    enforcement_level TEXT NOT NULL, -- blocking | advisory
    rationale TEXT,
    active INTEGER DEFAULT 1,
    FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
);
```

---

## 3. Relational Integrity & Performance

1. **Foreign Key Enforcement**: `PRAGMA foreign_keys = ON;` is executed on every connection checkout in `Database.get_connection()`.
2. **Transaction Scoping**: Connection context manager wraps executions in `BEGIN IMMEDIATE` transactions, ensuring atomic writes and automatic rollback on runtime errors.
3. **Structured Database Logging**: All connection checkouts, query transaction failures, and migration runs are logged to `logs/database.log`.
