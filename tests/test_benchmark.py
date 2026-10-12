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

    def test_one_to_one_matching_cannot_satisfy_two_labels_in_strict_mode(self):
        """
        Step 4.1 Acceptance Test:
        Proves that one system decision cannot satisfy two labels in strict mode.
        In lenient mode, 1 system decision matches 2 labels (100% recall, overcounting).
        In strict mode, exactly 1 label is matched (50% recall, 0 overcounting).
        """
        # Create 1 event and 1 decision in DB
        ev = Event(
            event_id="evt_shared_step41",
            source_type="git_commit",
            source_id="c_shared",
            source_url="https://github.com/test/repo/commit/c_shared",
            repo="test/repo",
            author="alice",
            timestamp="2026-01-01T00:00:00Z",
            title="Shared Evidence Event",
            body="Body of shared commit",
            artifacts_touched=["file.py"]
        )
        self.db.upsert_event(ev)

        dec = Decision(
            decision_id="dec_shared_step41",
            title="Single System Decision",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T00:00:00Z",
            artifacts_affected=[],
            alternatives_considered=[],
            rationale="Shared rationale",
            evidence_event_ids=["evt_shared_step41"],
            confidence=1.0,
            review_status="auto_confirmed",
            repo="test/repo"
        )
        self.db.save_decision(dec)

        # 2 GT items expecting the SAME evidence event
        gt_two_labels = [
            {
                "id": "GT_LABEL_A",
                "repo": "test/repo",
                "title": "Ground Truth Item A",
                "expected_state": "accepted",
                "expected_evidence_contains": ["evt_shared_step41"]
            },
            {
                "id": "GT_LABEL_B",
                "repo": "test/repo",
                "title": "Ground Truth Item B",
                "expected_state": "accepted",
                "expected_evidence_contains": ["evt_shared_step41"]
            }
        ]

        runner = BenchmarkRunner(self.db)
        res = runner.run_full_evaluation(custom_ground_truth=gt_two_labels)

        # 1. Strict recall is 50.0% (exactly 1 label satisfied)
        self.assertEqual(res["metrics"]["decision_recall_strict"], 50.0)
        self.assertEqual(res["metrics"]["decision_extraction_recall"], 50.0)
        self.assertEqual(res["matched_gt_count"], 1)

        # 2. Lenient recall is 100.0% (both labels satisfied by the single system decision)
        self.assertEqual(res["metrics"]["decision_recall_lenient"], 100.0)
        self.assertEqual(res["matched_gt_count_lenient"], 2)

        # 3. Recall difference exposes the 50.0% overcounting gap
        self.assertEqual(res["metrics"]["recall_difference"], 50.0)
        self.assertTrue(res["details"]["overcounting_detected"])

        # 4. In strict mode, exactly one GT is found and one is missed
        self.assertEqual(len(res["details"]["strict"]["found"]), 1)
        self.assertEqual(len(res["details"]["strict"]["missed"]), 1)
        # In lenient mode, both are found
        self.assertEqual(len(res["details"]["lenient"]["found"]), 2)

    def test_greedy_descending_overlap_bipartite_assignment(self):
        """
        Step 4.1 Bipartite Assignment:
        Candidate edge with higher overlap (2) is assigned first, ensuring global optimal matching.
        """
        # Create 2 events
        e1 = Event(event_id="evt_e1", source_type="git_commit", source_id="c1",
                   source_url="https://github.com/test/repo/commit/c1", repo="test/repo",
                   author="alice", timestamp="2026-01-01T00:00:00Z", title="E1", body="E1", artifacts_touched=[])
        e2 = Event(event_id="evt_e2", source_type="git_commit", source_id="c2",
                   source_url="https://github.com/test/repo/commit/c2", repo="test/repo",
                   author="alice", timestamp="2026-01-01T00:00:00Z", title="E2", body="E2", artifacts_touched=[])
        self.db.upsert_event(e1)
        self.db.upsert_event(e2)

        # Decision 1 has both e1 and e2; Decision 2 has only e1
        d1 = Decision(decision_id="dec_both", title="Both", state="accepted", made_by="alice",
                      made_at="2026-01-01T00:00:00Z", artifacts_affected=[], alternatives_considered=[],
                      rationale="R1", evidence_event_ids=["evt_e1", "evt_e2"], confidence=1.0,
                      review_status="auto_confirmed", repo="test/repo")
        d2 = Decision(decision_id="dec_single", title="Single", state="accepted", made_by="alice",
                      made_at="2026-01-01T00:00:00Z", artifacts_affected=[], alternatives_considered=[],
                      rationale="R2", evidence_event_ids=["evt_e1"], confidence=1.0,
                      review_status="auto_confirmed", repo="test/repo")
        self.db.save_decision(d1)
        self.db.save_decision(d2)

        # GT_1 expects both [e1, e2] (overlap 2 with d1); GT_2 expects [e1] (overlap 1 with d1 or d2)
        gt_dataset = [
            {"id": "GT_1", "repo": "test/repo", "title": "Expect Both", "expected_state": "accepted",
             "expected_evidence_contains": ["evt_e1", "evt_e2"]},
            {"id": "GT_2", "repo": "test/repo", "title": "Expect One", "expected_state": "accepted",
             "expected_evidence_contains": ["evt_e1"]}
        ]

        runner = BenchmarkRunner(self.db)
        res = runner.run_full_evaluation(custom_ground_truth=gt_dataset)

        self.assertEqual(res["metrics"]["decision_recall_strict"], 100.0)
        self.assertEqual(res["metrics"]["recall_difference"], 0.0)
        self.assertFalse(res["details"]["overcounting_detected"])

        found_map = {f["gt_id"]: f["decision_id"] for f in res["details"]["strict"]["found"]}
        self.assertEqual(found_map["GT_1"], "dec_both")
        self.assertEqual(found_map["GT_2"], "dec_single")

    def test_unmatched_system_decisions_tracked(self):
        """Step 4.1: Unmatched system decisions count against precision and are listed in details."""
        ev = Event(event_id="evt_u1", source_type="git_commit", source_id="c_u",
                   source_url="https://github.com/test/repo/commit/u", repo="test/repo",
                   author="alice", timestamp="2026-01-01T00:00:00Z", title="U", body="U", artifacts_touched=[])
        self.db.upsert_event(ev)

        # Decision 1 matches GT
        dec1 = Decision(
            decision_id="dec_extra_1",
            title="Extra 1",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T00:00:00Z",
            artifacts_affected=[],
            alternatives_considered=[],
            rationale="Extra 1",
            evidence_event_ids=["evt_u1"],
            confidence=1.0,
            review_status="auto_confirmed",
            repo="test/repo"
        )
        self.db.save_decision(dec1)

        # Decisions 2 & 3 have different evidence and do NOT match GT
        for i in (2, 3):
            ev_extra = Event(event_id=f"evt_u{i}", source_type="git_commit", source_id=f"c_u{i}",
                             source_url=f"https://github.com/test/repo/commit/u{i}", repo="test/repo",
                             author="alice", timestamp="2026-01-01T00:00:00Z", title=f"U{i}", body=f"U{i}", artifacts_touched=[])
            self.db.upsert_event(ev_extra)
            dec = Decision(
                decision_id=f"dec_extra_{i}",
                title=f"Extra {i}",
                state="accepted",
                made_by="alice",
                made_at="2026-01-01T00:00:00Z",
                artifacts_affected=[],
                alternatives_considered=[],
                rationale=f"Extra {i}",
                evidence_event_ids=[f"evt_u{i}"],
                confidence=1.0,
                review_status="auto_confirmed",
                repo="test/repo"
            )
            self.db.save_decision(dec)

        gt = [{"id": "GT_SINGLE", "repo": "test/repo", "title": "Single", "expected_state": "accepted",
               "expected_evidence_contains": ["evt_u1"]}]

        runner = BenchmarkRunner(self.db)
        res = runner.run_full_evaluation(custom_ground_truth=gt)

        self.assertEqual(res["matched_gt_count"], 1)
        self.assertEqual(res["unmatched_system_decisions_count"], 2)
        self.assertEqual(len(res["details"]["strict"]["unmatched_system_ids"]), 2)
        self.assertIn("dec_extra_2", res["details"]["strict"]["unmatched_system_ids"])
        self.assertIn("dec_extra_3", res["details"]["strict"]["unmatched_system_ids"])

    def test_evidence_link_replacement_metrics(self):
        """Step 4.1: url_format_ok, event_exists, and claim_supported replace legacy validity."""
        ev_valid = Event(event_id="evt_valid_link", source_type="git_commit", source_id="c_v",
                         source_url="https://github.com/test/repo/commit/v", repo="test/repo",
                         author="alice", timestamp="2026-01-01T00:00:00Z", title="Valid", body="Valid", artifacts_touched=[])
        self.db.upsert_event(ev_valid)

        dec = Decision(
            decision_id="dec_link_test",
            title="Link Test Decision",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T00:00:00Z",
            artifacts_affected=[],
            alternatives_considered=[],
            rationale="Testing link validity",
            evidence_event_ids=["evt_valid_link"],
            confidence=1.0,
            review_status="auto_confirmed",
            repo="test/repo"
        )
        self.db.save_decision(dec)

        runner = BenchmarkRunner(self.db)
        res = runner.run_full_evaluation()
        metrics = res["metrics"]

        self.assertIn("url_format_ok", metrics)
        self.assertIn("event_exists", metrics)
        self.assertIn("claim_supported", metrics)
        self.assertIn("evidence_link_accuracy", metrics)
        self.assertEqual(metrics["url_format_ok"], 100.0)
        self.assertEqual(metrics["event_exists"], 100.0)
        self.assertEqual(metrics["evidence_link_accuracy"], metrics["url_format_ok"])

if __name__ == "__main__":
    unittest.main()

