"""
Unit Tests for Human-Labelled Precision & Snapshot Hash Protection (Step 4.5)
Verifies:
1. tools/make_precision_sample.py records dataset_version, db_snapshot_sha256, repo, decision_id, and correct: null.
2. Snapshot hash mismatch causes evaluate_precision_labels to refuse labels with clear reason.
3. Unfilled labels (correct: null) report 'not measured' awaiting human task H2.
4. Valid human labels with matching snapshot hash compute exact precision.
5. Deterministic sampling with seed 1234 up to 40 per repository.
"""
import os
import sys
import json
import sqlite3
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db import Database
from backend.models import Decision, Event
from backend.evaluation.benchmark import compute_db_sha256, evaluate_precision_labels, BenchmarkRunner
from tools.make_precision_sample import make_precision_sample

class TestPrecisionSampling(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_snapshot.db")
        self.db = Database(self.db_path)

        # Seed sample events & decisions across 2 repositories
        for i in range(1, 46):
            ev1 = Event(
                event_id=f"evt_a_{i}",
                source_type="git_commit",
                source_id=f"c_a_{i}",
                source_url=f"http://example.com/a/{i}",
                repo="org/repoA",
                author="alice",
                timestamp="2026-01-01T00:00:00Z",
                title=f"Event A {i}"
            )
            self.db.upsert_event(ev1)
            d1 = Decision(
                decision_id=f"dec_repoA_{i:03d}",
                title=f"Architecture Decision A {i}",
                state="accepted",
                made_by="alice",
                made_at=f"2026-01-{i%28+1:02d}T10:00:00Z",
                artifacts_affected=[f"src/module_{i}.py"],
                alternatives_considered=[],
                rationale=f"Rationale for design A {i}",
                evidence_event_ids=[f"evt_a_{i}"],
                confidence=0.85,
                review_status="auto_confirmed",
                repo="org/repoA"
            )
            self.db.save_decision(d1)

        for j in range(1, 26):
            ev2 = Event(
                event_id=f"evt_b_{j}",
                source_type="git_commit",
                source_id=f"c_b_{j}",
                source_url=f"http://example.com/b/{j}",
                repo="org/repoB",
                author="bob",
                timestamp="2026-01-01T00:00:00Z",
                title=f"Event B {j}"
            )
            self.db.upsert_event(ev2)
            d2 = Decision(
                decision_id=f"dec_repoB_{j:03d}",
                title=f"Architecture Decision B {j}",
                state="rejected",
                made_by="bob",
                made_at=f"2026-01-{j%28+1:02d}T11:00:00Z",
                artifacts_affected=[f"src/sub_{j}.py"],
                alternatives_considered=[],
                rationale=f"Rejected design B {j}",
                evidence_event_ids=[f"evt_b_{j}"],
                confidence=0.80,
                review_status="auto_confirmed",
                repo="org/repoB"
            )
            self.db.save_decision(d2)

    def tearDown(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except Exception:
            pass

    def test_make_precision_sample_schema_and_per_row_metadata(self):
        """tools/make_precision_sample.py records dataset_version, db_snapshot_sha256, repo, decision_id, correct=null."""
        output_labels = os.path.join(self.temp_dir, "precision_labels.json")
        samples = make_precision_sample(
            db_path=self.db_path,
            output_path=output_labels,
            sample_size_per_repo=40,
            dataset_version="whybench_v1",
            seed=1234
        )
        self.assertTrue(os.path.exists(output_labels))
        expected_hash = compute_db_sha256(self.db_path)

        with open(output_labels, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, list)
        # repoA had 45 (capped at 40), repoB had 25 -> total 65
        self.assertEqual(len(data), 65)

        for row in data:
            self.assertEqual(row["dataset_version"], "whybench_v1")
            self.assertEqual(row["db_snapshot_sha256"], expected_hash)
            self.assertIn(row["repo"], ["org/repoA", "org/repoB"])
            self.assertTrue(row["decision_id"].startswith("dec_"))
            self.assertIsNone(row["correct"], "correct must be null until filled by human")
            self.assertIn("title", row)
            self.assertIn("state", row)

    def test_snapshot_hash_mismatch_refuses_labels_with_clear_reason(self):
        """The benchmark refuses to use labels whose snapshot hash does not match the DB being evaluated."""
        output_labels = os.path.join(self.temp_dir, "mismatched_labels.json")
        stale_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        mismatched_data = [
            {
                "dataset_version": "whybench_v1",
                "db_snapshot_sha256": stale_hash,
                "repo": "org/repoA",
                "decision_id": "dec_repoA_001",
                "correct": True
            }
        ]
        with open(output_labels, "w", encoding="utf-8") as f:
            json.dump(mismatched_data, f)

        precision, reason = evaluate_precision_labels(self.db_path, output_labels)
        self.assertEqual(precision, "not measured")
        self.assertIn("snapshot hash mismatch", reason)
        self.assertIn(stale_hash, reason)

    def test_unfilled_labels_reports_not_measured_awaiting_human(self):
        """Precision reports 'not measured' when human has not filled correct=true/false."""
        output_labels = os.path.join(self.temp_dir, "unfilled_labels.json")
        real_hash = compute_db_sha256(self.db_path)
        unfilled_data = [
            {
                "dataset_version": "whybench_v1",
                "db_snapshot_sha256": real_hash,
                "repo": "org/repoA",
                "decision_id": "dec_repoA_001",
                "correct": None
            }
        ]
        with open(output_labels, "w", encoding="utf-8") as f:
            json.dump(unfilled_data, f)

        precision, reason = evaluate_precision_labels(self.db_path, output_labels)
        self.assertEqual(precision, "not measured")
        self.assertIn("awaiting human labels", reason)

    def test_valid_matching_labels_computes_exact_precision(self):
        """When snapshot hash matches and human has provided boolean labels, precision is computed."""
        output_labels = os.path.join(self.temp_dir, "filled_labels.json")
        real_hash = compute_db_sha256(self.db_path)
        filled_data = [
            {"dataset_version": "whybench_v1", "db_snapshot_sha256": real_hash, "repo": "org/repoA", "decision_id": "dec_repoA_001", "correct": True},
            {"dataset_version": "whybench_v1", "db_snapshot_sha256": real_hash, "repo": "org/repoA", "decision_id": "dec_repoA_002", "correct": True},
            {"dataset_version": "whybench_v1", "db_snapshot_sha256": real_hash, "repo": "org/repoA", "decision_id": "dec_repoA_003", "correct": True},
            {"dataset_version": "whybench_v1", "db_snapshot_sha256": real_hash, "repo": "org/repoA", "decision_id": "dec_repoA_004", "correct": False}
        ]
        with open(output_labels, "w", encoding="utf-8") as f:
            json.dump(filled_data, f)

        precision, reason = evaluate_precision_labels(self.db_path, output_labels)
        self.assertEqual(precision, 75.0)
        self.assertIn("evaluated 4/4", reason)

    def test_sampling_determinism_and_cap_per_repo(self):
        """Sampling with seed 1234 caps each repo at sample_size_per_repo and is deterministic."""
        out1 = os.path.join(self.temp_dir, "sample_run1.json")
        out2 = os.path.join(self.temp_dir, "sample_run2.json")

        s1 = make_precision_sample(self.db_path, out1, sample_size_per_repo=40, seed=1234)
        s2 = make_precision_sample(self.db_path, out2, sample_size_per_repo=40, seed=1234)

        # Assert deterministic equality
        self.assertEqual(len(s1), len(s2))
        self.assertEqual([x["decision_id"] for x in s1], [x["decision_id"] for x in s2])

        # Assert cap per repo
        repoA_count = sum(1 for x in s1 if x["repo"] == "org/repoA")
        repoB_count = sum(1 for x in s1 if x["repo"] == "org/repoB")
        self.assertEqual(repoA_count, 40)
        self.assertEqual(repoB_count, 25)

if __name__ == "__main__":
    unittest.main()
