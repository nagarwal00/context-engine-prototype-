import itertools
import os
import tempfile
import unittest

from backend.db import Database
from backend.models import Event, Decision, Entity, ALLOWED_DECISION_STATES
from backend.seed_data import populate_seed_data
from backend.engine.reconciliation import ReconciliationEngine
from backend.engine.lifecycle import (
    transition,
    record_initial_state,
    InvalidTransition,
    ALLOWED_TRANSITIONS,
)
from backend.api import APIHandler


class TestLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_lifecycle.db")
        self.db = Database(self.db_path)
        populate_seed_data(self.db)
        self.api = APIHandler(self.db)

        # Ingest a standalone event for isolated transition testing
        self.ev = Event(
            event_id="evt_iso_lifecycle_01",
            source_type="adr",
            source_id="adr_iso_01",
            source_url="https://github.com/acme/iso/adr/01.md",
            repo="acme/iso",
            author="tester",
            timestamp="2026-01-01T00:00:00Z"
        )
        self.db.upsert_event(self.ev)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _create_decision(self, dec_id: str, state: str, has_evidence: bool = True) -> Decision:
        dec = Decision(
            decision_id=dec_id,
            title=f"Decision {dec_id}",
            state=state,
            evidence_assessment="strong" if has_evidence else "insufficient",
            freshness="fresh",
            made_by="tester",
            made_at="2026-01-01T00:00:00Z",
            artifacts_affected=["src/iso.py"],
            rationale="Test rationale",
            evidence_event_ids=["evt_iso_lifecycle_01"] if has_evidence else [],
            confidence=0.9,
            repo="acme/iso"
        )
        self.db.save_decision(dec)
        return dec

    def test_every_legal_transition_passes(self):
        """Every transition declared in ALLOWED_TRANSITIONS passes and logs to state_history."""
        for from_state, targets in ALLOWED_TRANSITIONS.items():
            for to_state in targets:
                dec_id = f"dec_legal_{from_state}_{to_state}"
                self._create_decision(dec_id, from_state, has_evidence=True)

                res = transition(
                    db=self.db,
                    decision_id=dec_id,
                    to_state=to_state,
                    actor="alice_reviewer",
                    reason=f"Transitioning from {from_state} to {to_state}",
                    at="2026-02-01T12:00:00Z"
                )
                self.assertEqual(res["from_state"], from_state)
                self.assertEqual(res["to_state"], to_state)
                self.assertEqual(res["changed_by"], "alice_reviewer")

                # Verify updated in database
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT state FROM decisions WHERE decision_id = ?", (dec_id,))
                    self.assertEqual(cursor.fetchone()["state"], to_state)

                    cursor.execute(
                        "SELECT * FROM state_history WHERE decision_id = ? AND state = ? ORDER BY changed_at DESC",
                        (dec_id, to_state)
                    )
                    sh = cursor.fetchone()
                    self.assertIsNotNone(sh)
                    self.assertEqual(sh["changed_by"], "alice_reviewer")
                    self.assertIn(f"Transition: {from_state} -> {to_state}", sh["notes"])

    def test_every_illegal_pair_raises_invalid_transition(self):
        """Every transition not in ALLOWED_TRANSITIONS raises InvalidTransition."""
        tested_pairs = 0
        for from_state, to_state in itertools.product(ALLOWED_DECISION_STATES, ALLOWED_DECISION_STATES):
            allowed_targets = ALLOWED_TRANSITIONS.get(from_state, set())
            if to_state not in allowed_targets:
                tested_pairs += 1
                dec_id = f"dec_illegal_{from_state}_{to_state}"
                self._create_decision(dec_id, from_state, has_evidence=True)

                with self.assertRaises(InvalidTransition, msg=f"Expected ({from_state} -> {to_state}) to raise InvalidTransition"):
                    transition(
                        db=self.db,
                        decision_id=dec_id,
                        to_state=to_state,
                        actor="bob",
                        reason="Illegal jump test"
                    )

        self.assertGreater(tested_pairs, 15, "Must test all illegal combinations across state pairs")

    def test_superseded_is_terminal(self):
        """A decision in 'superseded' state cannot transition to any other state."""
        dec_id = "dec_terminal_test"
        self._create_decision(dec_id, "superseded", has_evidence=True)

        for target in ALLOWED_DECISION_STATES:
            with self.assertRaises(InvalidTransition):
                transition(
                    db=self.db,
                    decision_id=dec_id,
                    to_state=target,
                    actor="charlie",
                    reason="Attempt resurrecting terminal superseded decision"
                )

    def test_rejected_reopened_accepted_workflow(self):
        """Full lifecycle progression: proposed -> rejected -> reopened -> accepted."""
        dec_id = "dec_workflow_progression"
        self._create_decision(dec_id, "proposed", has_evidence=True)

        # 1. proposed -> rejected
        res1 = transition(self.db, dec_id, "rejected", actor="lead_arch", reason="Deadlock potential")
        self.assertEqual(res1["to_state"], "rejected")

        # 2. rejected -> reopened
        res2 = transition(self.db, dec_id, "reopened", actor="contributor", reason="Lock ordering fixed in patch")
        self.assertEqual(res2["to_state"], "reopened")

        # 3. reopened -> accepted
        res3 = transition(self.db, dec_id, "accepted", actor="lead_arch", reason="Verified deadlock-free in benchmark")
        self.assertEqual(res3["to_state"], "accepted")

        # Verify full audit chain in state_history
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state, changed_by, notes FROM state_history WHERE decision_id = ? ORDER BY changed_at ASC", (dec_id,))
            history_rows = cursor.fetchall()
            states = [r["state"] for r in history_rows]
            self.assertIn("rejected", states)
            self.assertIn("reopened", states)
            self.assertIn("accepted", states)

    def test_actor_and_reason_are_required(self):
        """Transitions without non-empty actor or reason raise ValueError."""
        dec_id = "dec_validation_checks"
        self._create_decision(dec_id, "proposed", has_evidence=True)

        with self.assertRaises(ValueError):
            transition(self.db, dec_id, "accepted", actor="", reason="Valid reason")

        with self.assertRaises(ValueError):
            transition(self.db, dec_id, "accepted", actor="alice", reason="   ")

    def test_evidence_required_for_tested_accepted_rejected_superseded(self):
        """Transitioning to tested/accepted/rejected/superseded requires evidence."""
        dec_id = "dec_no_ev_test"
        # Proposed decision with 0 evidence
        self._create_decision(dec_id, "proposed", has_evidence=False)

        # Transitioning to accepted without evidence must fail
        with self.assertRaises(ValueError):
            transition(self.db, dec_id, "accepted", actor="alice", reason="Accepting without evidence")

        # Supplying evidence during transition must succeed
        res = transition(
            self.db,
            dec_id,
            "accepted",
            actor="alice",
            reason="Supplying evidence now",
            evidence_event_ids=["evt_iso_lifecycle_01"]
        )
        self.assertEqual(res["to_state"], "accepted")

    def test_state_history_recording(self):
        """Asserts that state_history rows are recorded after seeding and review actions."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS count FROM state_history")
            initial_count = cursor.fetchone()["count"]

        self.assertGreater(initial_count, 0, "state_history should contain entries after seeding")

        # Perform review action triage via API
        self.api.handle_post("/api/review-action", {
            "action": "confirm",
            "target_id": "dec_thermal_pid_accepted",
            "item_type": "decision",
            "notes": "Verified in architecture review"
        })

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS count FROM state_history")
            after_count = cursor.fetchone()["count"]

        self.assertGreater(after_count, initial_count, "Review action should append to state_history")

        # Verify query_full_evidence_trail returns state_history
        trail = self.db.query_full_evidence_trail("dec_thermal_pid_accepted")
        self.assertIn("state_history", trail)
        self.assertGreater(len(trail["state_history"]), 0)

    def test_supersession_chain(self):
        """Asserts that supersession flips older state to superseded and updates symmetry and edges."""
        # Insert older decision
        dec_v1 = Decision(
            decision_id="dec_db_v1",
            title="Use SQLite embedded database",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T00:00:00Z",
            artifacts_affected=["src/db.py"],
            alternatives_considered=[],
            rationale="Initial lightweight storage",
            evidence_event_ids=["evt_adr_thermal_0004"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/test-app"
        )
        self.db.save_decision(dec_v1)

        # Insert newer decision superseding v1
        dec_v2 = Decision(
            decision_id="dec_db_v2",
            title="Migrate to PostgreSQL cluster (replaces SQLite embedded database)",
            state="accepted",
            made_by="bob",
            made_at="2026-02-01T00:00:00Z",
            artifacts_affected=["src/db.py"],
            alternatives_considered=[],
            rationale="Replaces SQLite embedded database to support concurrent multi-worker writes",
            evidence_event_ids=["evt_adr_thermal_0004"],
            confidence=0.95,
            review_status="auto_confirmed",
            repo="acme/test-app"
        )
        self.db.save_decision(dec_v2)

        recon = ReconciliationEngine(self.db)
        supersessions = recon.detect_supersessions("acme/test-app")
        self.assertGreater(len(supersessions), 0)

        # Verify state transition on older decision
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state, superseded_by_decision_id FROM decisions WHERE decision_id = 'dec_db_v1'")
            old_row = cursor.fetchone()
            self.assertEqual(old_row["state"], "superseded")
            self.assertEqual(old_row["superseded_by_decision_id"], "dec_db_v2")

            # Verify state_history audit trail for older decision
            cursor.execute("SELECT * FROM state_history WHERE decision_id = 'dec_db_v1' AND state = 'superseded'")
            sh_row = cursor.fetchone()
            self.assertIsNotNone(sh_row, "Superseded transition must be logged in state_history")


if __name__ == "__main__":
    unittest.main()
