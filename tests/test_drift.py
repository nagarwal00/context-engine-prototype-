import os
import tempfile
import unittest
from backend.db import Database
from backend.seed_data import populate_seed_data
from backend.engine.drift_detector import DriftDetector
from backend.engine.reconciliation import ReconciliationEngine
from backend.evaluation.benchmark import BenchmarkRunner

class TestDriftAndConflict(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_drift.db")
        self.db = Database(self.db_path)
        populate_seed_data(self.db)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_drift_cases_evaluation(self):
        runner = BenchmarkRunner(self.db)
        metrics = runner._evaluate_drift_cases()
        self.assertEqual(metrics["status"], "measured")
        self.assertGreaterEqual(metrics["total_cases"], 20, "Must evaluate at least 20 drift cases")
        self.assertGreaterEqual(metrics["tn"], 8, "Must contain at least 8 negative (ok) cases")
        self.assertGreater(metrics["precision"], 0.0)
        self.assertGreater(metrics["recall"], 0.0)

    def test_conflict_cases_evaluation(self):
        runner = BenchmarkRunner(self.db)
        metrics = runner._evaluate_conflict_cases()
        self.assertEqual(metrics["status"], "measured")
        self.assertGreaterEqual(metrics["total_cases"], 6, "Must evaluate at least 6 conflict cases")
        self.assertGreaterEqual(metrics["tn"], 2, "Must contain at least 2 negative cases")
        self.assertGreater(metrics["precision"], 0.0)
        self.assertGreater(metrics["recall"], 0.0)

if __name__ == "__main__":
    unittest.main()
