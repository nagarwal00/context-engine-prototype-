"""
tests/test_copilot_baseline.py
Unit tests for Baseline D: GitHub Copilot Manual Evaluation Importer and Sheet Generator (Step 4.2).

Verifies:
1. Empty CSV / default state returns status: 'not measured' and evaluated_samples: 0.
2. Valid CSV rows calculate accuracy, invented_reason_rate, cited_real_source_rate, and Wilson 95 intervals.
3. Unknown question_id raises ValueError.
4. Non-binary value in answer_correct, answer_has_invented_reason, or cited_real_source raises ValueError.
5. Generator make_copilot_sheet creates results/copilot_sheet.md with 36 trials (26 positives + 10 negatives).
"""
import csv
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.db import Database
from backend.evaluation.baselines import BaselineEvaluator
from tools.make_copilot_sheet import generate_copilot_sheet

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestCopilotBaseline(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_copilot.db")
        self.db = Database(self.db_path)
        self.evaluator = BaselineEvaluator(self.db)

        self.sample_ground_truth = [
            {"id": "Q_POS_01", "question_id": "Q_POS_01", "repo": "repo/a", "expected_state": "accepted"},
            {"id": "Q_POS_02", "question_id": "Q_POS_02", "repo": "repo/a", "expected_state": "rejected"},
            {"id": "Q_NEG_01", "question_id": "Q_NEG_01", "repo": "repo/a", "expected_state": "none"},
            {"id": "Q_NEG_02", "question_id": "Q_NEG_02", "repo": "repo/a", "expected_state": "none"},
        ]

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_empty_csv_returns_not_measured(self):
        empty_csv = os.path.join(self.tmp_dir, "empty_copilot.csv")
        with open(empty_csv, "w", encoding="utf-8", newline="\n") as f:
            f.write("question_id,answer_correct,answer_has_invented_reason,cited_real_source,notes\n")

        res = self.evaluator.run_baseline_copilot(
            ground_truth=self.sample_ground_truth,
            csv_path=empty_csv
        )
        self.assertEqual(res["status"], "not measured")
        self.assertEqual(res["evaluated_samples"], 0)
        self.assertEqual(res["accuracy"], "not measured")
        self.assertEqual(res["decision_recall"], "not measured")

    def test_missing_csv_returns_not_measured(self):
        missing_csv = os.path.join(self.tmp_dir, "nonexistent.csv")
        res = self.evaluator.run_baseline_copilot(
            ground_truth=self.sample_ground_truth,
            csv_path=missing_csv
        )
        self.assertEqual(res["status"], "not measured")
        self.assertEqual(res["evaluated_samples"], 0)

    def test_valid_csv_computes_rates_and_wilson(self):
        csv_file = os.path.join(self.tmp_dir, "valid_copilot.csv")
        rows = [
            {"question_id": "Q_POS_01", "answer_correct": "1", "answer_has_invented_reason": "0", "cited_real_source": "1", "notes": "good"},
            {"question_id": "Q_POS_02", "answer_correct": "0", "answer_has_invented_reason": "1", "cited_real_source": "0", "notes": "invented"},
            {"question_id": "Q_NEG_01", "answer_correct": "1", "answer_has_invented_reason": "0", "cited_real_source": "0", "notes": "abstained"},
            {"question_id": "Q_NEG_02", "answer_correct": "0", "answer_has_invented_reason": "1", "cited_real_source": "0", "notes": "invented decision"},
        ]
        with open(csv_file, "w", encoding="utf-8", newline="\n") as f:
            writer = csv.DictWriter(f, fieldnames=["question_id", "answer_correct", "answer_has_invented_reason", "cited_real_source", "notes"])
            writer.writeheader()
            writer.writerows(rows)

        res = self.evaluator.run_baseline_copilot(
            ground_truth=self.sample_ground_truth,
            csv_path=csv_file
        )
        self.assertEqual(res["status"], "measured")
        self.assertEqual(res["evaluated_samples"], 4)
        # 2 correct out of 4 = 50.0%
        self.assertEqual(res["accuracy"], 50.0)
        self.assertEqual(res["accuracy_hits"], 2)
        self.assertIsNotNone(res["accuracy_wilson_95"])

        # 2 invented out of 4 = 50.0%
        self.assertEqual(res["invented_reason_rate"], 50.0)
        self.assertEqual(res["invented_reason_hits"], 2)
        self.assertIsNotNone(res["invented_reason_wilson_95"])

        # 1 cited real source out of 4 = 25.0%
        self.assertEqual(res["cited_real_source_rate"], 25.0)
        self.assertEqual(res["cited_real_source_hits"], 1)
        self.assertIsNotNone(res["cited_real_source_wilson_95"])

        # Backwards compatibility keys
        self.assertEqual(res["decision_recall"], 50.0)
        self.assertEqual(res["hallucination_rate"], 50.0)

    def test_unknown_question_id_raises_value_error(self):
        csv_file = os.path.join(self.tmp_dir, "unknown_qid.csv")
        rows = [
            {"question_id": "Q_POS_01", "answer_correct": "1", "answer_has_invented_reason": "0", "cited_real_source": "1", "notes": ""},
            {"question_id": "Q_UNKNOWN_99", "answer_correct": "1", "answer_has_invented_reason": "0", "cited_real_source": "1", "notes": ""},
        ]
        with open(csv_file, "w", encoding="utf-8", newline="\n") as f:
            writer = csv.DictWriter(f, fieldnames=["question_id", "answer_correct", "answer_has_invented_reason", "cited_real_source", "notes"])
            writer.writeheader()
            writer.writerows(rows)

        with self.assertRaises(ValueError) as ctx:
            self.evaluator.run_baseline_copilot(
                ground_truth=self.sample_ground_truth,
                csv_path=csv_file
            )
        self.assertIn("Unknown question_id", str(ctx.exception))

    def test_non_binary_values_raise_value_error(self):
        for col, bad_val in [
            ("answer_correct", "yes"),
            ("answer_correct", "2"),
            ("answer_has_invented_reason", "true"),
            ("cited_real_source", "invalid"),
        ]:
            csv_file = os.path.join(self.tmp_dir, f"bad_{col}.csv")
            row = {"question_id": "Q_POS_01", "answer_correct": "1", "answer_has_invented_reason": "0", "cited_real_source": "0", "notes": ""}
            row[col] = bad_val
            with open(csv_file, "w", encoding="utf-8", newline="\n") as f:
                writer = csv.DictWriter(f, fieldnames=["question_id", "answer_correct", "answer_has_invented_reason", "cited_real_source", "notes"])
                writer.writeheader()
                writer.writerow(row)

            with self.assertRaises(ValueError) as ctx:
                self.evaluator.run_baseline_copilot(
                    ground_truth=self.sample_ground_truth,
                    csv_path=csv_file
                )
            self.assertIn("Non-binary value", str(ctx.exception))

    def test_make_copilot_sheet_generator(self):
        out_sheet = Path(self.tmp_dir) / "copilot_sheet_test.md"
        questions_path = PROJECT_ROOT / "backend" / "evaluation" / "whybench" / "questions.json"
        generate_copilot_sheet(
            questions_path=questions_path,
            output_path=out_sheet,
            seed=1234,
            split="test_v2"
        )
        self.assertTrue(out_sheet.exists())
        content = out_sheet.read_text(encoding="utf-8")
        self.assertIn("Baseline D: GitHub Copilot Manual Evaluation Trial Sheet", content)
        self.assertIn("Trial 36", content)
        self.assertIn("Total Trials:** 36", content)
        self.assertIn("WB_PAY_09", content)
        self.assertIn("WB_CH_TEST_NEG_14", content)


if __name__ == "__main__":
    unittest.main()
