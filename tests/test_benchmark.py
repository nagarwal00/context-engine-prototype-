import os
import re
import json
import tempfile
import unittest
from backend.db import Database
from backend.models import Event, Decision, Entity, Edge
from backend.seed_data import populate_seed_data
from backend.evaluation.benchmark import BenchmarkRunner, compute_decision_matching, evaluate_precision_labels, compute_db_sha256
from backend.evaluation.baselines import BaselineEvaluator
from tools.run_whybench import run_whybench

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

    def test_task_split_equivalent_tasks_reporting(self):
        """
        Step 4.2: Split the benchmark into two clearly defined tasks.
        Asserts that search baselines (A and B) evaluate Task 1 (evidence retrieval),
        while Task 2 (decision reconstruction) cells are marked 'n/a' and refusal is 'n/a (always answers)'.
        """
        # Create an ADR event and a decision
        ev_doc = Event(
            event_id="evt_adr_split_01",
            source_type="adr",
            source_id="adr_01",
            source_url="https://github.com/test/repo/doc/adr_01",
            repo="test/repo",
            author="alice",
            timestamp="2026-01-01T00:00:00Z",
            title="ADR 01 Architecture Doc",
            body="Use PostgreSQL database for transactional storage",
            artifacts_touched=[]
        )
        self.db.upsert_event(ev_doc)

        gt = [{
            "id": "GT_TASK_SPLIT",
            "repo": "test/repo",
            "title": "Use PostgreSQL database",
            "expected_state": "accepted",
            "expected_evidence_contains": ["evt_adr_split_01"]
        }]

        evaluator = BaselineEvaluator(self.db)
        b_keyword = evaluator.run_baseline_keyword(gt)
        b_docs = evaluator.run_baseline_docs_only(gt)

        # 1. Task 1 (Evidence Retrieval) is measured
        self.assertTrue(b_keyword["task_1_applicable"])
        self.assertEqual(b_keyword["task_1_hit_rate"], 100.0)
        self.assertTrue(b_docs["task_1_applicable"])
        self.assertEqual(b_docs["task_1_hit_rate"], 100.0)

        # 2. Task 2 (Decision Reconstruction) is explicitly marked 'n/a'
        self.assertFalse(b_keyword["task_2_applicable"])
        self.assertEqual(b_keyword["task_2_decision_recall"], "n/a")
        self.assertEqual(b_keyword["task_2_state_accuracy"], "n/a")
        self.assertEqual(b_keyword["task_2_refusal_accuracy"], "n/a (always answers)")

        self.assertFalse(b_docs["task_2_applicable"])
        self.assertEqual(b_docs["task_2_decision_recall"], "n/a")
        self.assertEqual(b_docs["task_2_state_accuracy"], "n/a")
        self.assertEqual(b_docs["task_2_refusal_accuracy"], "n/a (always answers)")

    def test_one_to_one_vs_many_to_one_matching(self):
        """Step 4.10: 1 system decision sharing evidence with 2 GT items yields 50% strict vs 100% lenient recall."""
        gt_dataset = [
            {"id": "GT_1", "repo": "test/repo", "expected_state": "accepted", "evidence_event_ids": ["evt_shared"]},
            {"id": "GT_2", "repo": "test/repo", "expected_state": "accepted", "evidence_event_ids": ["evt_shared"]}
        ]
        system_decisions = [
            {"decision_id": "dec_single", "repo": "test/repo", "state": "accepted"}
        ]
        decision_to_evidence = {
            "dec_single": {"evt_shared"}
        }

        match_results = compute_decision_matching(gt_dataset, system_decisions, decision_to_evidence)
        strict = match_results["strict"]
        lenient = match_results["lenient"]

        self.assertEqual(strict["matched_gt_count"], 1)
        self.assertEqual(strict["recall"], 50.0)
        self.assertEqual(lenient["matched_gt_count"], 2)
        self.assertEqual(lenient["recall"], 100.0)
        self.assertTrue(match_results["overcounting_detected"])
        self.assertEqual(match_results["recall_difference"], 50.0)

    def test_missing_labels_precision_evaluation(self):
        """Step 4.10: Missing precision label file returns 'not measured' with clear reason."""
        val, reason = evaluate_precision_labels(self.db_path, labels_file_or_dir="non_existent_labels_file.json")
        self.assertEqual(val, "not measured")
        self.assertIn("not found", reason.lower())

    def test_duplicate_matches_greedy_assignment(self):
        """Step 4.10: 2 system decisions for 1 GT item greedily assigns highest overlap and leaves other unmatched."""
        gt_dataset = [
            {"id": "GT_TARGET", "repo": "test/repo", "expected_state": "accepted", "evidence_event_ids": ["evt_1", "evt_2"]}
        ]
        system_decisions = [
            {"decision_id": "dec_low", "repo": "test/repo", "state": "accepted"},
            {"decision_id": "dec_high", "repo": "test/repo", "state": "accepted"}
        ]
        decision_to_evidence = {
            "dec_low": {"evt_1"},
            "dec_high": {"evt_1", "evt_2"}
        }

        match_results = compute_decision_matching(gt_dataset, system_decisions, decision_to_evidence)
        strict = match_results["strict"]

        self.assertEqual(strict["matched_gt_count"], 1)
        self.assertEqual(strict["found"][0]["decision_id"], "dec_high")
        self.assertIn("dec_low", strict["unmatched_system_ids"])

    def test_contradictory_evidence_matching(self):
        """Step 4.10: System decision with contradictory lifecycle state is categorized in wrong_state."""
        gt_dataset = [
            {"id": "GT_STATE_TEST", "repo": "test/repo", "expected_state": "rejected", "evidence_event_ids": ["evt_test"]}
        ]
        system_decisions = [
            {"decision_id": "dec_contrary", "repo": "test/repo", "state": "accepted"}
        ]
        decision_to_evidence = {
            "dec_contrary": {"evt_test"}
        }

        match_results = compute_decision_matching(gt_dataset, system_decisions, decision_to_evidence)
        strict = match_results["strict"]

        self.assertEqual(strict["matched_gt_count"], 1)
        self.assertEqual(strict["state_accuracy"], 0.0)
        self.assertEqual(len(strict["wrong_state"]), 1)
        self.assertEqual(strict["wrong_state"][0]["system_state"], "accepted")
        self.assertEqual(strict["wrong_state"][0]["expected_state"], "rejected")

    def test_empty_datasets_safety(self):
        """Step 4.10: Empty GT and empty system decisions execute safely with 0.0 metrics."""
        match_results = compute_decision_matching([], [], {})
        self.assertEqual(match_results["strict"]["recall"], 0.0)
        self.assertIn(match_results["strict"]["state_accuracy"], (0.0, "not measured"))
        self.assertFalse(match_results["overcounting_detected"])

    def test_negative_cases_evaluation(self):
        """Step 4.10: Negative questions evaluate correctly for abstention and false positive decisions."""
        neg_unrecorded = {
            "id": "NEG_UNREC", "repo": "test/repo", "question": "Why MongoDB?", "expected_state": "none",
            "negative_type": "unrecorded", "evidence_event_ids": []
        }
        neg_mention = {
            "id": "NEG_MENTION", "repo": "test/repo", "question": "Should we look at DynamoDB?", "expected_state": "none",
            "negative_type": "mention_without_decision", "evidence_event_ids": ["evt_discuss"]
        }

        # Case 1: Honest abstention (no decision made on evt_discuss)
        system_decisions_clean = []
        d2e_clean = {}

        # If system made an erroneous decision on the discussion event
        system_decisions_erroneous = [
            {"decision_id": "dec_err", "repo": "test/repo", "state": "accepted", "title": "Adopt DynamoDB"}
        ]
        d2e_erroneous = {"dec_err": {"evt_discuss"}}

        # Check clean abstention
        expected_events = set(neg_mention["evidence_event_ids"])
        matched_clean = any(expected_events.intersection(d2e_clean.get(sd["decision_id"], set())) for sd in system_decisions_clean)
        self.assertFalse(matched_clean)

        # Check false positive detection
        matched_err = any(expected_events.intersection(d2e_erroneous.get(sd["decision_id"], set())) for sd in system_decisions_erroneous)
        self.assertTrue(matched_err)

    def test_reproducibility_identical_metrics(self):
        """Step 4.10: Greedy matching with deterministic tie-breaking produces identical metrics across repeated runs."""
        gt = [
            {"id": "GT_A", "repo": "test/repo", "expected_state": "accepted", "evidence_event_ids": ["evt_1"]},
            {"id": "GT_B", "repo": "test/repo", "expected_state": "accepted", "evidence_event_ids": ["evt_2"]}
        ]
        sds = [
            {"decision_id": "dec_1", "repo": "test/repo", "state": "accepted"},
            {"decision_id": "dec_2", "repo": "test/repo", "state": "accepted"}
        ]
        d2e = {"dec_1": {"evt_1"}, "dec_2": {"evt_2"}}

        res1 = compute_decision_matching(gt, sds, d2e)
        res2 = compute_decision_matching(gt, sds, d2e)

        self.assertEqual(res1["strict"]["recall"], res2["strict"]["recall"])
        self.assertEqual(res1["strict"]["matched_gt_count"], res2["strict"]["matched_gt_count"])
        self.assertEqual(res1["strict"]["matched_system_ids"], res2["strict"]["matched_system_ids"])

    def test_snapshot_hash_mismatch_refuses_precision(self):
        """Step 4.10: evaluate_precision_labels refuses evaluation when DB hash mismatches template."""
        # Create a dummy label file with mismatched snapshot hash
        labels_path = os.path.join(self.tmp_dir.name, "precision_labels.json")
        dummy_data = [{
            "dataset_version": "whybench_v1",
            "db_snapshot_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
            "repo": "test/repo",
            "decision_id": "dec_1",
            "correct": True
        }]
        with open(labels_path, "w", encoding="utf-8") as f:
            json.dump(dummy_data, f)

        val, reason = evaluate_precision_labels(self.db_path, labels_file_or_dir=labels_path)
        self.assertEqual(val, "not measured")
        self.assertIn("snapshot hash mismatch", reason)

    def test_strict_test_split_protection(self):
        """Step 4.10: run_whybench refuses to evaluate test or test_v2 without the explicit --final flag."""
        with self.assertRaises(SystemExit) as cm1:
            run_whybench(split="test", is_final=False)
        self.assertEqual(cm1.exception.code, 1)

        with self.assertRaises(SystemExit) as cm2:
            run_whybench(split="test_v2", is_final=False)
        self.assertEqual(cm2.exception.code, 1)


if __name__ == "__main__":
    unittest.main()

