"""
Unit tests for Confidence Quality & Calibration (Step 4.7).
Verifies:
  - Sub-100 sample threshold protection (prints 'not enough labels for calibration')
  - Exact analytical Expected Calibration Error (ECE) computation on toy datasets
  - Monotonicity verification
  - Evidence assessment tier accuracy breakdown
"""
import unittest
from backend.evaluation.calibration import compute_calibration, format_calibration_markdown


class TestCalibration(unittest.TestCase):

    def test_sub_100_labels_reports_not_enough_labels(self):
        """Fewer than 100 labels must return 'not measured' per Step 4.7."""
        # 50 items with boolean labels
        toy_items = [
            {"confidence": 0.8, "correct": True, "evidence_assessment": "strong"}
            for _ in range(50)
        ]
        res = compute_calibration(toy_items, min_labels_for_ece=100)

        self.assertEqual(res["status"], "not measured")
        self.assertEqual(res["reason"], "not enough labels for calibration")
        self.assertIsNone(res["ece"])
        self.assertFalse(res["calibrated"])
        self.assertEqual(res["labeled_count"], 50)
        self.assertEqual(res["min_required"], 100)

        # Markdown should contain the reason and notice
        md = format_calibration_markdown(res)
        self.assertIn("not enough labels for calibration", md)
        self.assertIn("50", md)
        self.assertIn("uncalibrated", md.lower())

    def test_unfilled_labels_are_filtered_out(self):
        """Items with correct=None are excluded from count."""
        toy_items = [
            {"confidence": 0.8, "correct": None, "evidence_assessment": "strong"}
            for _ in range(120)
        ]
        res = compute_calibration(toy_items, min_labels_for_ece=100)
        self.assertEqual(res["status"], "not measured")
        self.assertEqual(res["labeled_count"], 0)

    def test_toy_dataset_perfect_calibration_ece_zero(self):
        """
        100 items distributed evenly into 5 bins:
          Bin 1: 20 items, conf=0.10, 2 correct  -> acc = 0.10, err = 0.0
          Bin 2: 20 items, conf=0.30, 6 correct  -> acc = 0.30, err = 0.0
          Bin 3: 20 items, conf=0.50, 10 correct -> acc = 0.50, err = 0.0
          Bin 4: 20 items, conf=0.70, 14 correct -> acc = 0.70, err = 0.0
          Bin 5: 20 items, conf=0.90, 18 correct -> acc = 0.90, err = 0.0
        Expected ECE = 0.0.
        """
        items = []
        # Bin 1 (0.0 to 0.2)
        items.extend([{"confidence": 0.1, "correct": True}] * 2)
        items.extend([{"confidence": 0.1, "correct": False}] * 18)

        # Bin 2 (0.2 to 0.4)
        items.extend([{"confidence": 0.3, "correct": True}] * 6)
        items.extend([{"confidence": 0.3, "correct": False}] * 14)

        # Bin 3 (0.4 to 0.6)
        items.extend([{"confidence": 0.5, "correct": True}] * 10)
        items.extend([{"confidence": 0.5, "correct": False}] * 10)

        # Bin 4 (0.6 to 0.8)
        items.extend([{"confidence": 0.7, "correct": True}] * 14)
        items.extend([{"confidence": 0.7, "correct": False}] * 6)

        # Bin 5 (0.8 to 1.0)
        items.extend([{"confidence": 0.9, "correct": True}] * 18)
        items.extend([{"confidence": 0.9, "correct": False}] * 2)

        self.assertEqual(len(items), 100)

        res = compute_calibration(items, num_bins=5, min_labels_for_ece=100)
        self.assertEqual(res["status"], "measured")
        self.assertAlmostEqual(res["ece"], 0.0, places=3)
        self.assertEqual(res["higher_scores_more_accurate"], "yes")
        self.assertTrue(res["calibrated"])

        for b in res["reliability_table"]:
            self.assertAlmostEqual(b["calibration_error"], 0.0, places=3)

    def test_toy_dataset_known_ece_ten_percent(self):
        """
        100 items distributed evenly into 5 bins with constant 0.1 calibration error:
          Bin 1: 20 items, conf=0.10, 4 correct  -> acc = 0.20, err = 0.10
          Bin 2: 20 items, conf=0.30, 8 correct  -> acc = 0.40, err = 0.10
          Bin 3: 20 items, conf=0.50, 12 correct -> acc = 0.60, err = 0.10
          Bin 4: 20 items, conf=0.70, 16 correct -> acc = 0.80, err = 0.10
          Bin 5: 20 items, conf=0.90, 20 correct -> acc = 1.00, err = 0.10
        Expected ECE = 5 * (20/100) * 0.10 = 0.100.
        """
        items = []
        items.extend([{"confidence": 0.1, "correct": True}] * 4)
        items.extend([{"confidence": 0.1, "correct": False}] * 16)

        items.extend([{"confidence": 0.3, "correct": True}] * 8)
        items.extend([{"confidence": 0.3, "correct": False}] * 12)

        items.extend([{"confidence": 0.5, "correct": True}] * 12)
        items.extend([{"confidence": 0.5, "correct": False}] * 8)

        items.extend([{"confidence": 0.7, "correct": True}] * 16)
        items.extend([{"confidence": 0.7, "correct": False}] * 4)

        items.extend([{"confidence": 0.9, "correct": True}] * 20)
        items.extend([{"confidence": 0.9, "correct": False}] * 0)

        self.assertEqual(len(items), 100)

        res = compute_calibration(items, num_bins=5, min_labels_for_ece=100)
        self.assertEqual(res["status"], "measured")
        self.assertAlmostEqual(res["ece"], 0.100, places=3)
        self.assertAlmostEqual(res["ece_pct"], 10.0, places=1)
        self.assertEqual(res["higher_scores_more_accurate"], "yes")

    def test_non_monotonic_confidence_fails_calibration(self):
        """If higher confidence does not yield higher accuracy, calibrated must be False."""
        items = []
        # Bin 1 (0.1): 10 correct
        items.extend([{"confidence": 0.1, "correct": True}] * 10)
        items.extend([{"confidence": 0.1, "correct": False}] * 10)

        # Bin 2 (0.3): 15 correct
        items.extend([{"confidence": 0.3, "correct": True}] * 15)
        items.extend([{"confidence": 0.3, "correct": False}] * 5)

        # Bin 3 (0.5): 18 correct
        items.extend([{"confidence": 0.5, "correct": True}] * 18)
        items.extend([{"confidence": 0.5, "correct": False}] * 2)

        # Bin 4 (0.7): 20 correct
        items.extend([{"confidence": 0.7, "correct": True}] * 20)
        items.extend([{"confidence": 0.7, "correct": False}] * 0)

        # Bin 5 (0.9): collapses to only 2 correct!
        items.extend([{"confidence": 0.9, "correct": True}] * 2)
        items.extend([{"confidence": 0.9, "correct": False}] * 18)

        res = compute_calibration(items, num_bins=5, min_labels_for_ece=100)
        self.assertEqual(res["status"], "measured")
        self.assertFalse(res["monotonic_confidence"])
        self.assertEqual(res["higher_scores_more_accurate"], "no")
        self.assertFalse(res["calibrated"])

    def test_evidence_assessment_tier_breakdown(self):
        """Accuracy by evidence assessment label is computed accurately."""
        items = [
            {"confidence": 0.9, "correct": True, "evidence_assessment": "strong"},
            {"confidence": 0.9, "correct": True, "evidence_assessment": "strong"},
            {"confidence": 0.8, "correct": False, "evidence_assessment": "strong"},
            {"confidence": 0.7, "correct": True, "evidence_assessment": "moderate"},
            {"confidence": 0.6, "correct": False, "evidence_assessment": "moderate"},
            {"confidence": 0.4, "correct": False, "evidence_assessment": "weak"},
        ]
        res = compute_calibration(items, min_labels_for_ece=10)
        tiers = res["assessment_accuracy"]

        self.assertEqual(tiers["strong"]["total"], 3)
        self.assertEqual(tiers["strong"]["correct"], 2)
        self.assertAlmostEqual(tiers["strong"]["accuracy_pct"], 66.7, places=1)

        self.assertEqual(tiers["moderate"]["total"], 2)
        self.assertEqual(tiers["moderate"]["correct"], 1)
        self.assertEqual(tiers["moderate"]["accuracy_pct"], 50.0)

        self.assertEqual(tiers["weak"]["total"], 1)
        self.assertEqual(tiers["weak"]["correct"], 0)
        self.assertEqual(tiers["weak"]["accuracy_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
