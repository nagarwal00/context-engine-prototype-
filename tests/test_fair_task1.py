"""
tests/test_fair_task1.py
Tests for Fair Task-1 Comparison and Immutability (Step 2.1)
Verifies:
1. Baselines and CIF use the exact same n on positive questions.
2. The overlay never mutates the original frozen manifest bytes.
3. Wilson 95% confidence interval matches known mathematical inputs.
4. Regression test: baselines are never evaluated on a different question set than CIF in future runs.
"""
import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.recompute_task1_fair import compute_wilson_interval, recompute_task1_fair
from tools.generate_evaluation_report import generate_evaluation_markdown
from backend.db import Database
from backend.api import APIHandler

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestFairTask1(unittest.TestCase):
    def test_wilson_values_on_known_inputs(self):
        """Wilson score interval on known input (21, 26) must be approximately (0.62, 0.91)."""
        ci = compute_wilson_interval(21, 26)
        self.assertIsNotNone(ci)
        low, high = ci
        self.assertAlmostEqual(low, 0.62, delta=0.01)
        self.assertAlmostEqual(high, 0.91, delta=0.01)

        # Zero n returns None
        self.assertIsNone(compute_wilson_interval(0, 0))

    def test_baselines_and_cif_use_same_n(self):
        """Task-1 comparison must score CIF, BM25, and Docs-only on the exact same n (positives)."""
        corrections_path = PROJECT_ROOT / "results" / "test_v2_20261013_100423" / "corrections_task1_fair.json"
        self.assertTrue(corrections_path.exists(), "corrections_task1_fair.json must exist")

        with open(corrections_path, "r", encoding="utf-8") as f:
            corr = json.load(f)

        positives_n = corr["positives_n"]
        self.assertEqual(positives_n, 26, "test_v2 standard positive questions count must be 26")

        overall = corr["overall"]
        self.assertEqual(overall["cif"]["n"], positives_n)
        self.assertEqual(overall["baseline_keyword"]["n"], positives_n)
        self.assertEqual(overall["baseline_docs_only"]["n"], positives_n)

        # Verified hit counts
        self.assertEqual(overall["cif"]["hits"], 21)
        self.assertEqual(overall["baseline_keyword"]["hits"], 24)
        self.assertEqual(overall["baseline_docs_only"]["hits"], 6)

        # Rates
        self.assertEqual(overall["cif"]["rate"], 80.8)
        self.assertEqual(overall["baseline_keyword"]["rate"], 92.3)
        self.assertEqual(overall["baseline_docs_only"]["rate"], 23.1)

    def test_overlay_never_mutates_original_manifest_bytes(self):
        """Applying the corrections overlay must never mutate the bytes of latest_manifest.json or frozen run manifests."""
        manifest_path = PROJECT_ROOT / "results" / "latest_manifest.json"
        self.assertTrue(manifest_path.exists())

        before_bytes = manifest_path.read_bytes()
        before_hash = hashlib.sha256(before_bytes).hexdigest()

        # Call API route which loads and overlays in-memory (using a temporary DB copy)
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_db = os.path.join(tmp_dir, "test_ci.db")
            shutil.copy2(str(PROJECT_ROOT / "context_intelligence.db"), temp_db)
            db = Database(temp_db)
            api = APIHandler(db)
            res = api.handle_get("/api/benchmark", {})
            self.assertIn("whybench_manifest", res["data"])
            ov = res["data"]["whybench_manifest"]["metrics"]["overall"]
            self.assertEqual(ov["baseline_keyword"]["task_1_hit_rate"], 92.3)
            self.assertEqual(ov["baseline_keyword"]["total_count"], 26)

        # Call Markdown report generator
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_json = json.load(f)
        md = generate_evaluation_markdown(manifest_json)
        self.assertIn("92.3%", md)
        self.assertIn("24/26", md)

        after_bytes = manifest_path.read_bytes()
        after_hash = hashlib.sha256(after_bytes).hexdigest()

        self.assertEqual(before_hash, after_hash, "Original manifest file bytes must remain byte-identical!")

    def test_regression_baselines_never_scored_on_different_question_set(self):
        """Ensures tools/run_whybench.py evaluates baselines over standard_questions, not all split_questions."""
        runner_path = PROJECT_ROOT / "tools" / "run_whybench.py"
        content = runner_path.read_text(encoding="utf-8")

        # Must not pass split_questions to evaluate_all
        self.assertNotIn(
            "baseline_evaluator.evaluate_all(split_questions)",
            content,
            "Regressed: evaluate_all was passed split_questions instead of standard_questions"
        )
        self.assertIn(
            "baseline_evaluator.evaluate_all(standard_questions)",
            content,
            "Future runs must pass standard_questions to baseline_evaluator.evaluate_all"
        )


if __name__ == "__main__":
    unittest.main()
