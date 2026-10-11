"""
Tests for Decision History & Audit View API Endpoint (Step 2.5)
Verifies GET /api/decision-history with decision_id (transitions, supersession chain)
and without decision_id (global audit log with actor/date filters).
"""
import os
import tempfile
import unittest
from backend.db import Database
from backend.seed_data import populate_seed_data
from backend.api import APIHandler


class TestDecisionHistoryAPI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_history_api.db")
        self.db = Database(self.db_path)
        populate_seed_data(self.db)
        self.handler = APIHandler(self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_seeded_superseded_decision_history(self):
        """
        Acceptance criterion Step 2.5:
        For a seeded superseded decision (dec_cache_local_lru_proposed),
        the endpoint returns proposed -> accepted -> superseded with actors and reasons.
        """
        res = self.handler.handle_get("/api/decision-history", {"decision_id": ["dec_cache_local_lru_proposed"]})
        self.assertEqual(res.get("status"), "success")
        data = res.get("data", {})

        decision = data.get("decision", {})
        self.assertEqual(decision.get("decision_id"), "dec_cache_local_lru_proposed")
        self.assertEqual(decision.get("state"), "superseded")
        self.assertEqual(decision.get("superseded_by_decision_id"), "dec_cache_redis_accepted")

        transitions = data.get("transitions", [])
        self.assertEqual(len(transitions), 3)

        # 1. Initial state (proposed)
        self.assertIsNone(transitions[0]["from_state"])
        self.assertEqual(transitions[0]["to_state"], "proposed")
        self.assertEqual(transitions[0]["changed_by"], "marcus_vance")
        self.assertFalse(transitions[0]["reconstructed"])

        # 2. Accepted
        self.assertEqual(transitions[1]["from_state"], "proposed")
        self.assertEqual(transitions[1]["to_state"], "accepted")
        self.assertEqual(transitions[1]["changed_by"], "marcus_vance")
        self.assertIn("soft memory cap", transitions[1]["notes"].lower())
        self.assertFalse(transitions[1]["reconstructed"])

        # 3. Superseded
        self.assertEqual(transitions[2]["from_state"], "accepted")
        self.assertEqual(transitions[2]["to_state"], "superseded")
        self.assertEqual(transitions[2]["changed_by"], "priya_patel")
        self.assertIn("adr 0009", transitions[2]["notes"].lower())
        self.assertFalse(transitions[2]["reconstructed"])

        # Supersession chain
        chain = data.get("supersession_chain", {})
        self.assertEqual(chain.get("current", {}).get("decision_id"), "dec_cache_local_lru_proposed")
        self.assertEqual(len(chain.get("preceding", [])), 0)
        succeeding = chain.get("succeeding", [])
        self.assertEqual(len(succeeding), 1)
        self.assertEqual(succeeding[0]["decision_id"], "dec_cache_redis_accepted")

    def test_superseding_decision_chain(self):
        """
        The succeeding decision (dec_cache_redis_accepted) shows the preceding decision
        (dec_cache_local_lru_proposed) in its supersession chain.
        """
        res = self.handler.handle_get("/api/decision-history", {"decision_id": ["dec_cache_redis_accepted"]})
        self.assertEqual(res.get("status"), "success")
        data = res.get("data", {})

        chain = data.get("supersession_chain", {})
        preceding = chain.get("preceding", [])
        self.assertEqual(len(preceding), 1)
        self.assertEqual(preceding[0]["decision_id"], "dec_cache_local_lru_proposed")
        self.assertEqual(len(chain.get("succeeding", [])), 0)

    def test_nonexistent_decision_returns_404(self):
        res = self.handler.handle_get("/api/decision-history", {"decision_id": ["nonexistent_dec"]})
        self.assertEqual(res.get("status"), "error")
        self.assertEqual(res.get("status_code"), 404)

    def test_global_audit_log_without_decision_id(self):
        """Global audit log returns all transition history rows."""
        res = self.handler.handle_get("/api/decision-history", {})
        self.assertEqual(res.get("status"), "success")
        data = res.get("data", {})
        audit_log = data.get("audit_log", [])
        self.assertGreaterEqual(len(audit_log), 6)
        self.assertIn("decision_title", audit_log[0])
        self.assertIn("reconstructed", audit_log[0])

    def test_global_audit_log_filtered_by_actor(self):
        """Global audit log filters by actor substring."""
        res = self.handler.handle_get("/api/decision-history", {"actor": ["priya"]})
        self.assertEqual(res.get("status"), "success")
        audit_log = res.get("data", {}).get("audit_log", [])
        self.assertGreaterEqual(len(audit_log), 1)
        for entry in audit_log:
            self.assertIn("priya", entry["changed_by"].lower())

    def test_global_audit_log_filtered_by_date(self):
        """Global audit log filters by date prefix."""
        res = self.handler.handle_get("/api/decision-history", {"date": ["2026-02-04"]})
        self.assertEqual(res.get("status"), "success")
        audit_log = res.get("data", {}).get("audit_log", [])
        self.assertGreaterEqual(len(audit_log), 1)
        for entry in audit_log:
            self.assertTrue(entry["changed_at"].startswith("2026-02-04"))


if __name__ == "__main__":
    unittest.main()
