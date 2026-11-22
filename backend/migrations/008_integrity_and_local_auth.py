"""
Migration 008: database-level evidence invariant + local password authentication.

Audit references (audit/KNOWN_ISSUES.md): DB-01, SEC-01.

Additive only — no existing row is modified or deleted.

1. users.password_hash (nullable). Accounts created by GitHub OAuth keep NULL and therefore
   can never be signed into with a username/password.
2. Trigger trg_decision_grounded_state: refuses to move a decision INTO a grounded state
   (tested / accepted / rejected / superseded) unless it has at least one evidence row.
3. Trigger trg_event_sole_evidence: refuses to delete an event that is the ONLY evidence of a
   decision in a grounded state (previously the ON DELETE CASCADE silently left the decision
   'accepted' with zero evidence).
4. View v_ungrounded_decisions: lists any grounded decision without evidence. SQLite cannot
   check a freshly INSERTed decision before its evidence rows are written in the same
   transaction, so inserts are guarded by Database.save_decision() (the single write path)
   and this view is asserted empty by the test suite and tools/check_db_integrity.py.
"""
import sqlite3

VERSION = 8
NAME = "integrity_and_local_auth"

def upgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(users)")
    user_cols = {row[1] for row in cursor.fetchall()}
    if user_cols:
        if "password_hash" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        # Fast case-insensitive login lookup (uniqueness for new local accounts is checked in code,
        # so pre-existing duplicate rows cannot make this migration fail).
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_login_nocase ON users(login COLLATE NOCASE)")

    # Triggers + v_ungrounded_decisions (skipped on a bare database; Database start-up
    # re-runs this idempotently once the core tables exist).
    from backend.integrity import ensure_integrity_objects
    ensure_integrity_objects(conn)


def downgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("DROP VIEW IF EXISTS v_ungrounded_decisions")
    cursor.execute("DROP TRIGGER IF EXISTS trg_event_sole_evidence")
    cursor.execute("DROP TRIGGER IF EXISTS trg_decision_grounded_state")
    cursor.execute("DROP INDEX IF EXISTS idx_users_login_nocase")
    # users.password_hash is left in place (SQLite column drops require a table rebuild).
