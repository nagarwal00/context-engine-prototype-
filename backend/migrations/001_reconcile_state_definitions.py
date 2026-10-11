"""
Migration 001: Reconcile state definitions
Implements Step 2.1 of ANTIGRAVITY_HANDOFF_V2.md:
- Lifecycle state in ('proposed', 'tested', 'accepted', 'rejected', 'superseded', 'reopened')
- New column evidence_assessment in ('strong', 'moderate', 'weak', 'insufficient', 'contradicted') (default 'insufficient')
- New column freshness in ('fresh', 'stale', 'under_review', 'revalidated') (default 'fresh')
- Migrates legacy 'unresolved' -> state='proposed', evidence_assessment='insufficient'
- Preserves all columns, defaults, and foreign keys with zero data loss.
"""
import sqlite3

VERSION = 1
NAME = "reconcile_state_definitions"


def upgrade(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # Check if decisions table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='decisions'")
    if not cursor.fetchone():
        cursor.execute("""
        CREATE TABLE decisions (
            decision_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            state TEXT NOT NULL CHECK (state IN ('proposed','tested','accepted','rejected','superseded','reopened')),
            made_by TEXT,
            made_at TEXT,
            rationale TEXT,
            confidence REAL NOT NULL,
            review_status TEXT NOT NULL DEFAULT 'pending_review',
            supersedes_decision_id TEXT,
            superseded_by_decision_id TEXT,
            alternatives_json TEXT DEFAULT '[]',
            repo TEXT NOT NULL,
            evidence_assessment TEXT NOT NULL DEFAULT 'insufficient' CHECK (evidence_assessment IN ('strong','moderate','weak','insufficient','contradicted')),
            freshness TEXT NOT NULL DEFAULT 'fresh' CHECK (freshness IN ('fresh','stale','under_review','revalidated')),
            FOREIGN KEY (supersedes_decision_id) REFERENCES decisions(decision_id)
        );
        """)
        return

    # Inspect existing columns
    cursor.execute("PRAGMA table_info(decisions)")
    cols = {row[1] for row in cursor.fetchall()}

    has_ev_assess = "evidence_assessment" in cols
    has_fresh = "freshness" in cols

    ev_col_expr = "evidence_assessment" if has_ev_assess else "'insufficient'"
    fresh_col_expr = "freshness" if has_fresh else "'fresh'"

    # Step 2.1 Rebuild: Create decisions_new with new CHECK constraints
    cursor.execute("""
    CREATE TABLE decisions_new (
        decision_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('proposed','tested','accepted','rejected','superseded','reopened')),
        made_by TEXT,
        made_at TEXT,
        rationale TEXT,
        confidence REAL NOT NULL,
        review_status TEXT NOT NULL DEFAULT 'pending_review',
        supersedes_decision_id TEXT,
        superseded_by_decision_id TEXT,
        alternatives_json TEXT DEFAULT '[]',
        repo TEXT NOT NULL,
        evidence_assessment TEXT NOT NULL DEFAULT 'insufficient' CHECK (evidence_assessment IN ('strong','moderate','weak','insufficient','contradicted')),
        freshness TEXT NOT NULL DEFAULT 'fresh' CHECK (freshness IN ('fresh','stale','under_review','revalidated')),
        FOREIGN KEY (supersedes_decision_id) REFERENCES decisions(decision_id)
    );
    """)

    # Copy data mapping legacy 'unresolved' -> state='proposed', evidence_assessment='insufficient'
    cursor.execute(f"""
    INSERT INTO decisions_new (
        decision_id, title, state, made_by, made_at, rationale, confidence,
        review_status, supersedes_decision_id, superseded_by_decision_id,
        alternatives_json, repo, evidence_assessment, freshness
    )
    SELECT
        decision_id,
        title,
        CASE WHEN state = 'unresolved' THEN 'proposed' ELSE state END,
        made_by,
        made_at,
        rationale,
        confidence,
        review_status,
        supersedes_decision_id,
        superseded_by_decision_id,
        alternatives_json,
        repo,
        CASE
            WHEN state = 'unresolved' THEN 'insufficient'
            ELSE {ev_col_expr}
        END,
        {fresh_col_expr}
    FROM decisions;
    """)

    cursor.execute("DROP TABLE decisions;")
    cursor.execute("ALTER TABLE decisions_new RENAME TO decisions;")
