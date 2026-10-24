"""
Migration 005: Finding feedback and review routing table
Implements Step 3.5 & 3.6 of docs/process/ANTIGRAVITY_HANDOFF_V2.md:
- Creates finding_feedback table:
    feedback_id TEXT PRIMARY KEY,
    finding_id TEXT NOT NULL,
    finding_type TEXT NOT NULL,
    action TEXT NOT NULL, -- confirm, dismiss, reopen
    reason TEXT,
    actor TEXT NOT NULL,
    pr_id TEXT,
    decision_id TEXT,
    created_at TEXT NOT NULL
"""
import sqlite3

VERSION = 5
NAME = "finding_feedback"


def upgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS finding_feedback (
        feedback_id TEXT PRIMARY KEY,
        finding_id TEXT NOT NULL,
        finding_type TEXT NOT NULL,
        action TEXT NOT NULL,
        reason TEXT,
        actor TEXT NOT NULL,
        pr_id TEXT,
        decision_id TEXT,
        created_at TEXT NOT NULL
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_finding_feedback_target ON finding_feedback(pr_id, decision_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_finding_feedback_finding ON finding_feedback(finding_id);")


def downgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS finding_feedback;")
