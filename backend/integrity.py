"""
Database-level enforcement of CIF's core invariant (audit fix DB-01):

    A decision in a grounded state (tested / accepted / rejected / superseded)
    must cite at least one evidence event.

Created by migration 008 and re-asserted on every Database start-up (all statements are
idempotent), so a database migrated before its core tables existed still gets the triggers.

What the database enforces:
  * trg_decision_grounded_state — a decision cannot be MOVED into a grounded state while it
    has no evidence rows (lifecycle transitions, upserts of existing decisions).
  * trg_event_sole_evidence — an event cannot be deleted while it is the ONLY evidence of a
    grounded decision (previously ON DELETE CASCADE silently stripped the evidence).
What it cannot enforce:
  * A brand-new decision row is inserted before its evidence rows in the same transaction,
    and SQLite has no deferred (commit-time) triggers. Inserts therefore go through
    Database.save_decision(), which validates and re-checks the evidence count before commit,
    and v_ungrounded_decisions lets tests and tools assert that nothing slipped through.
"""
import sqlite3

GROUNDED_STATES = ("tested", "accepted", "rejected", "superseded")
_STATES_SQL = "(" + ",".join(f"'{s}'" for s in GROUNDED_STATES) + ")"


def ensure_integrity_objects(conn: sqlite3.Connection) -> bool:
    """Creates the triggers and view if the core tables exist. Returns True if they exist now."""
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if not {"decisions", "decision_evidence", "events"} <= tables:
        return False
    conn.execute(f"""
    CREATE TRIGGER IF NOT EXISTS trg_decision_grounded_state
    BEFORE UPDATE OF state ON decisions
    WHEN NEW.state IN {_STATES_SQL}
     AND NOT EXISTS (SELECT 1 FROM decision_evidence WHERE decision_id = NEW.decision_id)
    BEGIN
        SELECT RAISE(ABORT, 'CIF invariant violated: a decision in a grounded state must cite at least one evidence event');
    END;
    """)
    conn.execute(f"""
    CREATE TRIGGER IF NOT EXISTS trg_event_sole_evidence
    BEFORE DELETE ON events
    WHEN EXISTS (
        SELECT 1
        FROM decision_evidence de
        JOIN decisions d ON d.decision_id = de.decision_id
        WHERE de.event_id = OLD.event_id
          AND d.state IN {_STATES_SQL}
          AND (SELECT COUNT(*) FROM decision_evidence x WHERE x.decision_id = de.decision_id) = 1
    )
    BEGIN
        SELECT RAISE(ABORT, 'CIF invariant violated: event is the only evidence of a grounded decision');
    END;
    """)
    conn.execute(f"""
    CREATE VIEW IF NOT EXISTS v_ungrounded_decisions AS
    SELECT d.decision_id, d.repo, d.state, d.title
    FROM decisions d
    WHERE d.state IN {_STATES_SQL}
      AND NOT EXISTS (SELECT 1 FROM decision_evidence e WHERE e.decision_id = d.decision_id);
    """)
    return True


def ungrounded_decisions(conn: sqlite3.Connection) -> list:
    ensure_integrity_objects(conn)
    return [tuple(r) for r in conn.execute("SELECT decision_id, repo, state FROM v_ungrounded_decisions")]
