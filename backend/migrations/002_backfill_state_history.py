"""
Migration 002: Backfill state history
Implements Step 2.3 of docs/process/ANTIGRAVITY_HANDOFF_V2.md:
- Adds from_state TEXT and reconstructed INTEGER columns to state_history if missing.
- Reconstructs one history record per existing decision currently lacking a history row:
  - notes = 'reconstructed from current state at backfill'
  - changed_by = 'system:backfill'
  - changed_at = decision.made_at
  - reconstructed = 1
- Completely idempotent: running repeatedly is a safe no-op.
"""
import sqlite3

VERSION = 2
NAME = "backfill_state_history"


def upgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    # Ensure state_history table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='state_history'")
    if not cursor.fetchone():
        cursor.execute("""
        CREATE TABLE state_history (
            history_id TEXT PRIMARY KEY,
            decision_id TEXT NOT NULL,
            from_state TEXT,
            state TEXT NOT NULL,
            changed_at TEXT NOT NULL,
            changed_by TEXT NOT NULL,
            notes TEXT,
            reconstructed INTEGER DEFAULT 0,
            FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
        );
        """)
        return

    # Check for from_state and reconstructed columns
    cursor.execute("PRAGMA table_info(state_history)")
    cols = {row[1] for row in cursor.fetchall()}

    if "from_state" not in cols:
        cursor.execute("ALTER TABLE state_history ADD COLUMN from_state TEXT;")
    if "reconstructed" not in cols:
        cursor.execute("ALTER TABLE state_history ADD COLUMN reconstructed INTEGER DEFAULT 0;")

    # Find decisions lacking any state_history
    cursor.execute("""
    SELECT d.decision_id, d.state, d.made_at, d.made_by
    FROM decisions d
    LEFT JOIN state_history sh ON d.decision_id = sh.decision_id
    WHERE sh.decision_id IS NULL
    """)
    missing = cursor.fetchall()

    for row in missing:
        dec_id = row[0]
        state = row[1]
        made_at = row[2] or "1970-01-01T00:00:00Z"
        hist_id = f"hist_backfill_{dec_id}"
        notes = "reconstructed from current state at backfill"
        changed_by = "system:backfill"

        cursor.execute("""
        INSERT INTO state_history (
            history_id, decision_id, from_state, state, changed_at, changed_by, notes, reconstructed
        ) VALUES (?, ?, NULL, ?, ?, ?, ?, 1)
        """, (hist_id, dec_id, state, made_at, changed_by, notes))
