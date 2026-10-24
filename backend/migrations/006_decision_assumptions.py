"""
Migration 006: Decision Assumptions table for Staleness & Decision Half-Life
Implements Step 5.2 of docs/process/ANTIGRAVITY_HANDOFF_V2.md:
- Creates decision_assumptions table:
    assumption_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    text TEXT NOT NULL,
    watch_type TEXT NOT NULL CHECK(watch_type IN ('dependency_version', 'config_value', 'file_exists', 'infrastructure_note', 'manual')),
    watch_params_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'valid' CHECK(status IN ('valid', 'broken', 'under_review')),
    last_checked_at TEXT,
    trigger_event_id TEXT,
    trigger_notes TEXT,
    FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
"""
import sqlite3

VERSION = 6
NAME = "decision_assumptions"


def upgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS decision_assumptions (
        assumption_id TEXT PRIMARY KEY,
        decision_id TEXT NOT NULL,
        text TEXT NOT NULL,
        watch_type TEXT NOT NULL CHECK(watch_type IN ('dependency_version', 'config_value', 'file_exists', 'infrastructure_note', 'manual')),
        watch_params_json TEXT NOT NULL DEFAULT '{}',
        status TEXT NOT NULL DEFAULT 'valid' CHECK(status IN ('valid', 'broken', 'under_review')),
        last_checked_at TEXT,
        trigger_event_id TEXT,
        trigger_notes TEXT,
        FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE,
        FOREIGN KEY (trigger_event_id) REFERENCES events(event_id) ON DELETE SET NULL
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision_assumptions_dec ON decision_assumptions(decision_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision_assumptions_status ON decision_assumptions(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision_assumptions_watch ON decision_assumptions(watch_type);")


def downgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS decision_assumptions;")
