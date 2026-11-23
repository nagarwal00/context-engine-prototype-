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


# ---------------------------------------------------------------------------------------------
# state_history repository attribution (migration 009)
#
# Migration 007 added state_history.repo_full_name and backfilled it once. Rows inserted later
# by lifecycle transitions, review actions, revalidation and backfill tools did not set it, so
# every successful review action produced one unattributed history row. Instead of editing ~30
# insert statements, an AFTER INSERT trigger copies the repository from the row's own decision.
# A row whose decision is missing (only possible with foreign keys off) or has no repository is
# left NULL: attribution is recovered from data, never invented.
# ---------------------------------------------------------------------------------------------
_DECISION_REPO_SQL = ("SELECT COALESCE(NULLIF(d.repo_full_name, ''), NULLIF(d.repo, '')) "
                      "FROM decisions d WHERE d.decision_id = {ref}")


def ensure_state_history_attribution(conn: sqlite3.Connection) -> bool:
    """Creates the attribution trigger (idempotent). Returns False on a bare database."""
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if not {"state_history", "decisions"} <= tables:
        return False
    cols = {r[1] for r in conn.execute("PRAGMA table_info(state_history)")}
    if "repo_full_name" not in cols:
        return False  # column is added by migration 007
    conn.execute(f"""
    CREATE TRIGGER IF NOT EXISTS trg_state_history_repo_attribution
    AFTER INSERT ON state_history
    WHEN NEW.repo_full_name IS NULL OR NEW.repo_full_name = ''
    BEGIN
        UPDATE state_history
        SET repo_full_name = ({_DECISION_REPO_SQL.format(ref='NEW.decision_id')})
        WHERE rowid = NEW.rowid;
    END;
    """)
    return True


def backfill_state_history_attribution(conn: sqlite3.Connection) -> dict:
    """Fills missing repo_full_name from each row's own decision.

    Returns {"recovered": n, "unrecoverable": m}. Only rows that are NULL/empty are touched.
    """
    if not ensure_state_history_attribution(conn):
        return {"recovered": 0, "unrecoverable": 0}
    missing = "(repo_full_name IS NULL OR repo_full_name = '')"
    source = _DECISION_REPO_SQL.format(ref="state_history.decision_id")
    cur = conn.execute(f"UPDATE state_history SET repo_full_name = ({source}) "
                       f"WHERE {missing} AND ({source}) IS NOT NULL")
    recovered = cur.rowcount
    unrecoverable = conn.execute(f"SELECT COUNT(*) FROM state_history WHERE {missing}").fetchone()[0]
    return {"recovered": recovered, "unrecoverable": unrecoverable}
