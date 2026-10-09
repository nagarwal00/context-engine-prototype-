import os
import re
import tempfile
import unittest
from backend.db import Database
from backend.models import Event, Decision, Entity, Edge
from backend.seed_data import populate_seed_data
from backend.evaluation.benchmark import BenchmarkRunner
from backend.evaluation.baselines import BaselineEvaluator

class TestBenchmark(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_bench.db")
        self.db = Database(self.db_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_metrics_on_empty_db(self):
        """When DB is empty, recall is 0.0 (or 'not measured') and does not crash."""
        runner = BenchmarkRunner(self.db)
        res = runner.run_full_evaluation()
        self.assertIn("metrics", res)
        metrics = res["metrics"]
        self.assertEqual(metrics["decision_extraction_recall"], 0.0)
        self.assertIn(metrics["decision_extraction_precision"], (0.0, "not measured"))

    def test_metrics_range_and_types_on_seeded_db(self):
        """Metrics are floats in [0, 100] or string 'not measured'."""
        populate_seed_data(self.db)
        runner = BenchmarkRunner(self.db)
        res = runner.run_full_evaluation()
        metrics = res["metrics"]

        for metric_name, val in metrics.items():
            if val != "not measured":
                self.assertIsInstance(val, (int, float), f"Metric {metric_name} should be float or int")
                if "latency" not in metric_name:
                    self.assertGreaterEqual(val, 0.0, f"{metric_name} >= 0")
                    self.assertLessEqual(val, 100.0, f"{metric_name} <= 100")

    def test_tiny_gt_maths(self):
        """Proves ground truth matching maths: 2 GT items, 1 matching -> exactly 50% recall."""
        # Create 1 event and 1 decision in DB
        ev = Event(
            event_id="evt_test_math_1",
            source_type="git_commit",
            source_id="c1",
            source_url="https://github.com/test/repo/commit/c1",
            repo="test/repo",
            author="alice",
            timestamp="2026-01-01T00:00:00Z",
            title="Commit 1",
            body="Body 1",
            artifacts_touched=["file.py"]
        )
        self.db.upsert_event(ev)

        dec = Decision(
            decision_id="dec_test_math_1",
            title="Decision 1",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T00:00:00Z",
            artifacts_affected=[],
            alternatives_considered=[],
            rationale="Test rationale",
            evidence_event_ids=["evt_test_math_1"],
            confidence=1.0,
            review_status="auto_confirmed",
            repo="test/repo"
        )
        self.db.save_decision(dec)

        # 2 GT items: one matches evt_test_math_1, one expects missing evt_test_math_2
        tiny_gt = [
            {
                "id": "GT_1",
                "repo": "test/repo",
                "title": "Decision 1",
                "expected_state": "accepted",
                "expected_evidence_contains": ["evt_test_math_1"]
            },
            {
                "id": "GT_2",
                "repo": "test/repo",
                "title": "Decision 2",
                "expected_state": "accepted",
                "expected_evidence_contains": ["evt_test_math_2"]
            }
        ]

        runner = BenchmarkRunner(self.db)
        res = runner.run_full_evaluation(custom_ground_truth=tiny_gt)

        self.assertEqual(res["ground_truth_total"], 2)
        self.assertEqual(res["matched_gt_count"], 1)
        self.assertEqual(res["metrics"]["decision_extraction_recall"], 50.0)
        self.assertEqual(res["metrics"]["state_accuracy"], 100.0)

    def test_no_hardcoded_literals_in_source(self):
        """Validates that benchmark.py source has no hardcoded metric values."""
        bench_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "evaluation", "benchmark.py")
        with open(bench_file, "r", encoding="utf-8") as f:
            content = f.read()

        forbidden = ["0.941", "0.912", "0.923", "0.947", "42.6", "18.5", "16.8"]
        for lit in forbidden:
            self.assertNotIn(lit, content, f"Hardcoded literal {lit} found in benchmark.py")

if __name__ == "__main__":
    unittest.main()
