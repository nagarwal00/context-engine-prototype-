"""
tests/test_user_study.py
Unit tests for user study protocol, templates, and statistical analyzer (Step 4.4).

Verifies:
1. All protocol and kit files exist in user_study/ (PROTOCOL.md, CONSENT.md, TASKS.md, results_template.csv).
2. Empty CSV refuses conclusions and returns status 'not measured'.
3. Small sample (N < 5) refuses conclusions and returns status 'not measured'.
4. Full valid sample (N >= 5, synthetic test data) calculates mean/median time, correctness, Wilson intervals, and paired deltas.
5. Invalid rows (bad tool, invalid confidence, non-binary correctness) raise ValueError.
"""
import csv
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.analyze_user_study import (
    analyze_user_study_data,
    compute_wilson_interval,
    parse_and_validate_row
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestUserStudyKit(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.csv_path = Path(self.tmp_dir) / "test_user_study.csv"

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_protocol_and_kit_files_exist(self):
        user_study_dir = PROJECT_ROOT / "user_study"
        self.assertTrue((user_study_dir / "PROTOCOL.md").exists())
        self.assertTrue((user_study_dir / "CONSENT.md").exists())
        self.assertTrue((user_study_dir / "TASKS.md").exists())
        self.assertTrue((user_study_dir / "results_template.csv").exists())

        # Verify template has header only and 0 data rows
        with open(user_study_dir / "results_template.csv", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("participant_id", lines[0])
        self.assertIn("time_seconds", lines[0])

    def test_empty_csv_refuses_conclusions(self):
        with open(self.csv_path, "w", encoding="utf-8", newline="\n") as f:
            f.write("participant_id,condition,task_id,tool,time_seconds,correct,confidence,notes\n")

        res = analyze_user_study_data(self.csv_path)
        self.assertEqual(res["status"], "not measured")
        self.assertEqual(res["participants_n"], 0)
        self.assertIn("awaiting human participant data", res["reason"])

    def test_underpowered_sample_refuses_conclusions(self):
        # 3 participants < 5 minimum
        rows = [
            {"participant_id": "P01", "condition": "c1", "task_id": "TA", "tool": "cif", "time_seconds": "180", "correct": "1", "confidence": "4", "notes": ""},
            {"participant_id": "P01", "condition": "c2", "task_id": "TB", "tool": "baseline", "time_seconds": "360", "correct": "0", "confidence": "2", "notes": ""},
            {"participant_id": "P02", "condition": "c1", "task_id": "TA", "tool": "baseline", "time_seconds": "420", "correct": "1", "confidence": "3", "notes": ""},
            {"participant_id": "P02", "condition": "c2", "task_id": "TB", "tool": "cif", "time_seconds": "150", "correct": "1", "confidence": "5", "notes": ""},
            {"participant_id": "P03", "condition": "c1", "task_id": "TA", "tool": "cif", "time_seconds": "210", "correct": "1", "confidence": "4", "notes": ""},
            {"participant_id": "P03", "condition": "c2", "task_id": "TB", "tool": "baseline", "time_seconds": "390", "correct": "1", "confidence": "3", "notes": ""}
        ]
        with open(self.csv_path, "w", encoding="utf-8", newline="\n") as f:
            writer = csv.DictWriter(f, fieldnames=["participant_id", "condition", "task_id", "tool", "time_seconds", "correct", "confidence", "notes"])
            writer.writeheader()
            writer.writerows(rows)

        res = analyze_user_study_data(self.csv_path)
        self.assertEqual(res["status"], "not measured")
        self.assertEqual(res["participants_n"], 3)
        self.assertIn("insufficient sample size", res["reason"])

    def test_valid_sample_computes_statistics(self):
        # 6 participants (P01..P06) >= 5, synthetic test data
        rows = [
            {"participant_id": "P01", "condition": "c1", "task_id": "TA", "tool": "cif", "time_seconds": "120", "correct": "1", "confidence": "5", "notes": "fast"},
            {"participant_id": "P01", "condition": "c2", "task_id": "TB", "tool": "baseline", "time_seconds": "300", "correct": "0", "confidence": "2", "notes": "slow"},
            {"participant_id": "P02", "condition": "c1", "task_id": "TA", "tool": "baseline", "time_seconds": "360", "correct": "1", "confidence": "3", "notes": ""},
            {"participant_id": "P02", "condition": "c2", "task_id": "TB", "tool": "cif", "time_seconds": "140", "correct": "1", "confidence": "4", "notes": ""},
            {"participant_id": "P03", "condition": "c1", "task_id": "TA", "tool": "cif", "time_seconds": "180", "correct": "1", "confidence": "4", "notes": ""},
            {"participant_id": "P03", "condition": "c2", "task_id": "TB", "tool": "baseline", "time_seconds": "400", "correct": "0", "confidence": "2", "notes": ""},
            {"participant_id": "P04", "condition": "c1", "task_id": "TA", "tool": "baseline", "time_seconds": "280", "correct": "1", "confidence": "3", "notes": ""},
            {"participant_id": "P04", "condition": "c2", "task_id": "TB", "tool": "cif", "time_seconds": "160", "correct": "1", "confidence": "4", "notes": ""},
            {"participant_id": "P05", "condition": "c1", "task_id": "TA", "tool": "cif", "time_seconds": "200", "correct": "1", "confidence": "5", "notes": ""},
            {"participant_id": "P05", "condition": "c2", "task_id": "TB", "tool": "baseline", "time_seconds": "450", "correct": "1", "confidence": "3", "notes": ""},
            {"participant_id": "P06", "condition": "c1", "task_id": "TA", "tool": "baseline", "time_seconds": "350", "correct": "0", "confidence": "2", "notes": ""},
            {"participant_id": "P06", "condition": "c2", "task_id": "TB", "tool": "cif", "time_seconds": "150", "correct": "1", "confidence": "4", "notes": ""}
        ]
        with open(self.csv_path, "w", encoding="utf-8", newline="\n") as f:
            writer = csv.DictWriter(f, fieldnames=["participant_id", "condition", "task_id", "tool", "time_seconds", "correct", "confidence", "notes"])
            writer.writeheader()
            writer.writerows(rows)

        res = analyze_user_study_data(self.csv_path)
        self.assertEqual(res["status"], "measured")
        self.assertEqual(res["participants_n"], 6)
        self.assertEqual(res["trials_n"], 12)

        # Check CIF stats
        cif_stats = res["cif"]
        self.assertEqual(cif_stats["n"], 6)
        self.assertEqual(cif_stats["correct_hits"], 6)
        self.assertEqual(cif_stats["accuracy_rate"], 100.0)
        self.assertIsNotNone(cif_stats["accuracy_wilson_95"])
        # Times: 120, 140, 180, 160, 200, 150 -> mean = 158.3
        self.assertEqual(cif_stats["mean_time_seconds"], 158.3)

        # Check Baseline stats
        base_stats = res["baseline"]
        self.assertEqual(base_stats["n"], 6)
        self.assertEqual(base_stats["correct_hits"], 3)
        self.assertEqual(base_stats["accuracy_rate"], 50.0)

        # Check paired differences
        paired = res["paired"]
        self.assertEqual(paired["paired_participants_n"], 6)
        # CIF saved time on all participants
        self.assertGreater(paired["mean_time_saved_seconds"], 0)
        self.assertEqual(paired["mean_accuracy_delta"], 50.0)

    def test_invalid_row_raises_value_error(self):
        # Invalid tool
        with self.assertRaises(ValueError):
            parse_and_validate_row({"participant_id": "P01", "tool": "invalid_tool", "time_seconds": "100", "correct": "1", "confidence": "3"}, 2)

        # Invalid time
        with self.assertRaises(ValueError):
            parse_and_validate_row({"participant_id": "P01", "tool": "cif", "time_seconds": "-50", "correct": "1", "confidence": "3"}, 2)

        # Invalid correct
        with self.assertRaises(ValueError):
            parse_and_validate_row({"participant_id": "P01", "tool": "cif", "time_seconds": "100", "correct": "maybe", "confidence": "3"}, 2)

        # Invalid confidence
        with self.assertRaises(ValueError):
            parse_and_validate_row({"participant_id": "P01", "tool": "cif", "time_seconds": "100", "correct": "1", "confidence": "7"}, 2)


if __name__ == "__main__":
    unittest.main()
