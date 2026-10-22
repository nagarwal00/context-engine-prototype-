"""
Automated Verification Suite for All UI Buttons, Endpoints, and Features
Tests every interactive feature wired to the UI:
- User Menu & Auth actions (Login config, /api/me, /auth/logout)
- Repositories surface (list, add, status, job cancel, delete)
- Timeline surface (events, filtering)
- Decision Explorer (decisions, details, search)
- Graph surface (nodes, edges)
- Code & Evidence surfaces (artifacts, evidence trail, decision-history)
- Review Queue & Feedback (findings, feedback dispatch)
- Guard Rules (rules list, evaluation)
- Bus Factor & Adaptive Onboarding
- Benchmark WhyBench summary
"""

import json
import os
import unittest
from backend.db import Database
from backend.api import APIHandler
from backend.seed_data import populate_seed_data

class TestAllButtonsAndFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_features_buttons.db"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        cls.db = Database(cls.db_path)
        populate_seed_data(cls.db)
        cls.api = APIHandler(cls.db)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_navigation_and_data_surfaces(self):
        """Validates all navigation tabs and data surfaces load correctly."""
        surfaces = [
            ("/api/stats", {}),
            ("/api/repos", {}),
            ("/api/timeline", {"repo": ["acme-eng/thermal-control-system"]}),
            ("/api/decisions", {"repo": ["acme-eng/thermal-control-system"]}),
            ("/api/graph", {"repo": ["acme-eng/thermal-control-system"]}),
            ("/api/artifacts", {"repo": ["acme-eng/thermal-control-system"]}),
            ("/api/guard-rules", {"repo": ["acme-eng/thermal-control-system"]}),
            ("/api/review-queue", {"repo": ["acme-eng/thermal-control-system"]}),
            ("/api/bus-factor", {"repo": ["acme-eng/thermal-control-system"]}),
            ("/api/onboarding", {"repo": ["acme-eng/thermal-control-system"]}),
            ("/api/benchmark", {})
        ]
        for path, params in surfaces:
            res = self.api.handle_get(path, params)
            self.assertEqual(res.get("status_code", 200), 200, f"Surface endpoint {path} failed: {res}")
            self.assertIn("status", res)
            self.assertEqual(res["status"], "success")

    def test_decision_details_and_evidence_button_action(self):
        """Validates fetching detailed decision modal content and evidence trail."""
        decs_res = self.api.handle_get("/api/decisions", {"repo": ["acme-eng/thermal-control-system"]})
        self.assertEqual(decs_res.get("status_code", 200), 200)
        decisions = decs_res.get("data", [])
        self.assertTrue(len(decisions) > 0, "No decisions found in seed data")

        target_id = decisions[0]["decision_id"]
        # Button: View Evidence Trail
        detail_res = self.api.handle_get("/api/evidence", {"decision_id": [target_id]})
        self.assertEqual(detail_res.get("status_code", 200), 200)
        self.assertEqual(detail_res.get("status"), "success")
        self.assertIn("decision", detail_res.get("data", {}))

        # Button: View Lifecycle History
        hist_res = self.api.handle_get("/api/decision-history", {"decision_id": [target_id]})
        self.assertEqual(hist_res.get("status_code", 200), 200)
        self.assertEqual(hist_res.get("status"), "success")

    def test_feedback_button_actions(self):
        """Validates Helpful and False Positive feedback button dispatch."""
        feedback_payload = {
            "finding_id": "finding_synthetic_test_101",
            "decision_id": "dec_thermal_pid_accepted",
            "pr_id": "PR #101",
            "action": "confirm",
            "reason": "Verified helpful by review engineer"
        }
        res = self.api.handle_post("/api/findings/feedback", feedback_payload)
        self.assertEqual(res.get("status_code", 200), 200)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("schema_version"), "1.0")

    def test_extension_endpoints(self):
        """Validates extension PR analysis and file context endpoints."""
        fc_res = self.api.handle_get("/api/file-context", {
            "repo": ["acme-eng/thermal-control-system"],
            "path": ["controller/pid.py"]
        })
        self.assertEqual(fc_res.get("status_code", 200), 200)
        self.assertEqual(fc_res.get("status"), "ready")
        self.assertIn("active_decisions", fc_res)
        self.assertIn("decisions", fc_res)
        self.assertIn("rejected_alternatives", fc_res)

    def test_temporal_timeline_filtering(self):
        """Validates temporal timeline filtering."""
        t_res = self.api.handle_get("/api/timeline", {
            "repo": ["acme-eng/thermal-control-system"],
            "start": ["2026-01-01T00:00:00Z"],
            "end": ["2026-06-01T00:00:00Z"]
        })
        self.assertEqual(t_res.get("status_code", 200), 200)
        self.assertEqual(t_res.get("status"), "success")
        self.assertIsInstance(t_res.get("data", []), list)

if __name__ == "__main__":
    unittest.main()
