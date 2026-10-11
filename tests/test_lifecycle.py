import os
import tempfile
import unittest
from backend.db import Database
from backend.models import Event, Decision, Entity
from backend.seed_data import populate_seed_data
from backend.engine.reconciliation import ReconciliationEngine
from backend.api import APIHandler

class TestLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_lifecycle.db")
        self.db = Database(self.db_path)
        populate_seed_data(self.db)
        self.api = APIHandler(self.db)

    def tearDown(self):
        self.tmp_dir.cleanup()

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
