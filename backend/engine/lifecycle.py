"""
Context Intelligence Framework - Decision Lifecycle Engine
Implements Step 2.2 of ANTIGRAVITY_HANDOFF_V2.md
"""
import datetime
import time
from typing import Dict, Set, List, Optional, Any
from backend.db import Database
from backend.models import ALLOWED_DECISION_STATES


class InvalidTransition(Exception):
    """Raised when an illegal lifecycle transition is attempted."""
    pass


# Data-driven transition table per Section 5.2 & Step 2.2:
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "proposed": {"tested", "accepted", "rejected"},
    "tested": {"accepted", "rejected"},
    "accepted": {"superseded", "reopened"},
    "rejected": {"reopened"},
    "reopened": {"tested", "accepted", "rejected"},
    "superseded": set(),  # terminal state: no transitions allowed
}


def transition(
    db: Database,
    decision_id: str,
    to_state: str,
    actor: str,
    reason: str,
    at: Optional[str] = None,
    evidence_event_ids: Optional[List[str]] = None,
    superseded_by_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes a lifecycle transition inside one database transaction.
    1. Validates against the ALLOWED_TRANSITIONS table (raises InvalidTransition otherwise).
    2. Requires non-empty actor and reason.
    3. If to_state is tested/accepted/rejected/superseded, requires evidence (existing or supplied).
    4. Updates decisions.state, inserts state_history row, and for superseded sets superseded_by_decision_id
       and closes edge validity (valid_to).
    5. Returns audit summary dict.
    """
    if not actor or not str(actor).strip():
        raise ValueError("Lifecycle transition requires non-empty actor")
    if not reason or not str(reason).strip():
        raise ValueError("Lifecycle transition requires non-empty reason")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,))
        dec_row = cursor.fetchone()
        if not dec_row:
            raise ValueError(f"Decision '{decision_id}' not found")

        dec = dict(dec_row)
        from_state = dec["state"]

        allowed_targets = ALLOWED_TRANSITIONS.get(from_state, set())
        if to_state not in allowed_targets:
            raise InvalidTransition(
                f"Invalid transition from '{from_state}' to '{to_state}'. Allowed transitions: {sorted(allowed_targets)}"
            )

        # Evidence requirement for tested, accepted, rejected, superseded
        if to_state in ("tested", "accepted", "rejected", "superseded"):
            cursor.execute("SELECT COUNT(*) AS c FROM decision_evidence WHERE decision_id = ?", (decision_id,))
            existing_ev = cursor.fetchone()["c"]
            new_ev = len(evidence_event_ids or [])
            if existing_ev + new_ev == 0:
                raise ValueError(
                    f"Transition to '{to_state}' requires at least 1 evidence event. "
                    f"Decision '{decision_id}' has 0 existing evidence records and 0 supplied."
                )

        now_iso = at or (datetime.datetime.now(datetime.timezone.utc).isoformat())

        # Insert new evidence links if provided
        if evidence_event_ids:
            for eid in evidence_event_ids:
                cursor.execute("""
                INSERT OR IGNORE INTO decision_evidence (decision_id, event_id)
                VALUES (?, ?)
                """, (decision_id, eid))

        # Check state_history schema
        cursor.execute("PRAGMA table_info(state_history)")
        sh_cols = {r["name"] for r in cursor.fetchall()}
        hist_id = f"hist_{decision_id}_{int(time.time()*1000)}"

        # Update decision state and optional superseded pointers
        if to_state == "superseded":
            cursor.execute("""
            UPDATE decisions
            SET state = 'superseded', superseded_by_decision_id = COALESCE(?, superseded_by_decision_id)
            WHERE decision_id = ?
            """, (superseded_by_id, decision_id))

            # Close edges touching older decision
            cursor.execute("""
            UPDATE edges
            SET valid_to = ?
            WHERE (from_id = ? OR to_id = ?) AND (valid_to IS NULL OR valid_to > ?)
            """, (now_iso, decision_id, decision_id, now_iso))

            if superseded_by_id:
                cursor.execute("""
                UPDATE decisions
                SET supersedes_decision_id = ?
                WHERE decision_id = ?
                """, (decision_id, superseded_by_id))

                cursor.execute("""
                INSERT OR REPLACE INTO edges (edge_id, edge_type, from_id, from_type, to_id, to_type, valid_from, valid_to)
                VALUES (?, 'supersedes', ?, 'decision', ?, 'decision', ?, NULL)
                """, (f"edge_super_{superseded_by_id}_{decision_id}", superseded_by_id, decision_id, now_iso))
        else:
            cursor.execute("""
            UPDATE decisions SET state = ? WHERE decision_id = ?
            """, (to_state, decision_id))

        # Insert history record
        notes_text = f"Transition: {from_state} -> {to_state}. Reason: {reason}"
        if "from_state" in sh_cols:
            cursor.execute("""
            INSERT INTO state_history (history_id, decision_id, from_state, state, changed_at, changed_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (hist_id, decision_id, from_state, to_state, now_iso, actor, notes_text))
        else:
            cursor.execute("""
            INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (hist_id, decision_id, to_state, now_iso, actor, notes_text))

        conn.commit()

        return {
            "decision_id": decision_id,
            "from_state": from_state,
            "to_state": to_state,
            "changed_at": now_iso,
            "changed_by": actor,
            "notes": notes_text
        }


def record_initial_state(
    db: Database,
    decision_id: str,
    initial_state: str,
    actor: str = "system:ingestion",
    reason: str = "Initial decision creation",
    at: Optional[str] = None
) -> Dict[str, Any]:
    """Records the initial creation history entry with from_state = NULL."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(state_history)")
        sh_cols = {r["name"] for r in cursor.fetchall()}
        hist_id = f"hist_init_{decision_id}_{int(time.time()*1000)}"
        now_iso = at or (datetime.datetime.now(datetime.timezone.utc).isoformat())
        notes_text = f"Initial state: {initial_state}. Reason: {reason}"

        if "from_state" in sh_cols:
            cursor.execute("""
            INSERT INTO state_history (history_id, decision_id, from_state, state, changed_at, changed_by, notes)
            VALUES (?, ?, NULL, ?, ?, ?, ?)
            """, (hist_id, decision_id, initial_state, now_iso, actor, notes_text))
        else:
            cursor.execute("""
            INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (hist_id, decision_id, initial_state, now_iso, actor, notes_text))

        conn.commit()
        return {
            "decision_id": decision_id,
            "from_state": None,
            "to_state": initial_state,
            "changed_at": now_iso,
            "changed_by": actor,
            "notes": notes_text
        }
