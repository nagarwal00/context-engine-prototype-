import os
import unittest
from tools.analyze_failures import analyze_failures, classify_missed_item
from backend.db import Database
from backend.models import Event

class TestFailureAnalysis(unittest.TestCase):
    def test_failure_classification_categories_priority(self):
        """Verifies failure classification priorities: not_ingested, filtered, wrong_evidence, no_candidate, wrong_state."""
        # 1. not_ingested
        q_not_ingested = {
            "id": "Q1",
            "repo": "test/repo",
            "question": "Test not ingested",
            "expected_state": "accepted",
            "evidence_event_ids": ["evt_absent_123"]
        }
        res1 = classify_missed_item(q_not_ingested, db_events={}, system_decisions=[], decision_to_evidence={})
        self.assertEqual(res1["category"], "not_ingested")

        # 2. filtered
        ev_filtered = Event(
            event_id="evt_filt_1",
            source_type="git_commit",
            source_id="c1",
            source_url="https://github.com/test/repo/commit/c1",
            repo="test/repo",
            author="alice",
            timestamp="2026-01-01T00:00:00Z",
            title="fix formatting and whitespace",
            body="trivial fix",
            artifacts_touched=[]
        )
        q_filtered = {
            "id": "Q2",
            "repo": "test/repo",
            "question": "Test filtered",
            "expected_state": "accepted",
            "evidence_event_ids": ["evt_filt_1"]
        }
        res2 = classify_missed_item(q_filtered, db_events={"evt_filt_1": ev_filtered}, system_decisions=[], decision_to_evidence={})
        self.assertEqual(res2["category"], "filtered")

        # 3. wrong_state
        q_wrong_state = {
            "id": "Q3",
            "repo": "test/repo",
            "question": "Test wrong state",
            "expected_state": "rejected",
            "evidence_event_ids": ["evt_state_1"]
        }
        res3 = classify_missed_item(
            q_wrong_state,
            db_events={},
            system_decisions=[],
            decision_to_evidence={},
            found_info={"state_match": False, "decision_id": "dec_1", "system_state": "accepted"}
        )
        self.assertEqual(res3["category"], "wrong_state")

        # 4. wrong_evidence
        ev_code = Event(
            event_id="evt_code_1",
            source_type="github_pr",
            source_id="pr_1",
            source_url="https://github.com/test/repo/pull/1",
            repo="test/repo",
            author="alice",
            timestamp="2026-01-01T00:00:00Z",
            title="Database Connection Pool Optimization",
            body="Decided to adopt PostgreSQL connection pooling",
            artifacts_touched=["src/db.py"]
        )
        q_wrong_ev = {
            "id": "Q4",
            "repo": "test/repo",
            "question": "Why was Database Connection Pool adopted for storage?",
            "expected_state": "accepted",
            "evidence_event_ids": ["evt_code_1"]
        }
        dec_other = {
            "decision_id": "dec_other_pool",
            "repo": "test/repo",
            "title": "Database Connection Pool Decision",
            "rationale": "Adopting database pool for storage"
        }
        res4 = classify_missed_item(
            q_wrong_ev,
            db_events={"evt_code_1": ev_code},
            system_decisions=[dec_other],
            decision_to_evidence={"dec_other_pool": {"evt_different_99"}}
        )
        self.assertEqual(res4["category"], "wrong_evidence")

        # 5. no_candidate
        q_no_cand = {
            "id": "Q5",
            "repo": "test/repo",
            "question": "Completely unrelated architecture query",
            "expected_state": "accepted",
            "evidence_event_ids": ["evt_code_1"]
        }
        res5 = classify_missed_item(
            q_no_cand,
            db_events={"evt_code_1": ev_code},
            system_decisions=[],
            decision_to_evidence={}
        )
        self.assertEqual(res5["category"], "no_candidate")

    def test_analyze_failures_run_dev(self):
        """Runs analyze_failures on dev split and verifies report structure."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_json = os.path.join(tmp_dir, "dev_failure_analysis.json")
            tmp_md = os.path.join(tmp_dir, "dev_failure_analysis.md")
            report = analyze_failures(split="dev", output_json=tmp_json, output_md=tmp_md)
            self.assertIn("category_totals", report)
            self.assertIn("repo_breakdown", report)
            self.assertIn("failures", report)
            self.assertIn("false_positives", report)
            self.assertEqual(report["split"], "dev")

if __name__ == "__main__":
    unittest.main()
