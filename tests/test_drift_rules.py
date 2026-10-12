"""
Tests for Decision-Specific Constraints and General Drift Detector (Step 3.4 & P1-a)
Verifies:
- Zero domain keywords (redis, pid, hysteresis) in backend/engine/drift_detector.py.
- >= 6 positive diffs trigger potential violations with required fields, evidence passages, signal_strength.
- >= 10 negative diffs (including near-misses, comments, docstrings, removed lines) produce 0 findings.
- Labelled drift_cases.json evaluation yields 100% precision and 100% recall.
- Only human-approved ('active') constraints are enforced.
"""
import os
import re
import json
import tempfile
import unittest
from pathlib import Path

from backend.db import Database
from backend.models import Decision, GuardRule, Event
from backend.seed_data import populate_seed_data
from backend.engine.drift_detector import DriftDetector
from backend.evaluation.benchmark import BenchmarkRunner

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestDriftRules(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_drift_rules.db")
        self.db = Database(self.db_path)
        populate_seed_data(self.db)
        self.detector = DriftDetector(self.db)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_no_domain_keywords_in_drift_detector_source(self):
        """Grep test asserting no domain keywords (redis, pid, hysteresis) remain in drift_detector.py."""
        src_path = REPO_ROOT / "backend" / "engine" / "drift_detector.py"
        self.assertTrue(src_path.exists(), "drift_detector.py must exist")

        content = src_path.read_text(encoding="utf-8").lower()
        forbidden_keywords = ["redis", "pid", "hysteresis"]

        found = []
        for kw in forbidden_keywords:
            if kw in content:
                found.append(kw)

        self.assertEqual(
            found, [],
            f"Domain keywords found in drift_detector.py: {found}. Drift detection must be purely constraint-driven."
        )

    def test_positive_diffs_trigger_potential_violations(self):
        """Verify >= 6 positive diffs produce potential_violation findings with all required fields."""
        # Setup specific active constraints for testing
        test_rules = [
            GuardRule(
                rule_id="rule_pos_forbid_mod",
                decision_id="dec_thermal_pid_accepted",
                rule_type="forbid_import",
                params={"module": "sticky_sessions", "paths": ["src/**/*.py"]},
                status="active",
                polarity="must_not",
                applies_to=["src/**/*.py"]
            ),
            GuardRule(
                rule_id="rule_pos_forbid_pat",
                decision_id="dec_thermal_pid_accepted",
                rule_type="forbid_pattern",
                params={"regex": r"\b(on_off_relay|threshold_fallback|bang_bang_step)\b", "paths": ["src/control/**/*.py"]},
                status="active",
                polarity="must_not",
                applies_to=["src/control/**/*.py"]
            ),
            GuardRule(
                rule_id="rule_pos_require_mod",
                decision_id="dec_thermal_pid_accepted",
                rule_type="require_import",
                params={"module": "stripe", "paths": ["src/billing/**/*.py"]},
                status="active",
                polarity="must",
                applies_to=["src/billing/**/*.py"]
            ),
            GuardRule(
                rule_id="rule_pos_config_val",
                decision_id="dec_thermal_pid_accepted",
                rule_type="config_value",
                params={"file": "config.json", "key": "timeout_seconds", "must_equal": "30"},
                status="active",
                polarity="must",
                applies_to=["config.json"]
            ),
        ]
        for r in test_rules:
            self.db.upsert_guard_rule(r)

        positive_cases = [
            # 1. Direct forbidden import
            ("src/service/session.py", "+++ b/src/service/session.py\n@@ -1,3 +1,4 @@\n+ import sticky_sessions\n"),
            # 2. 'from ... import' forbidden import
            ("src/auth/login.py", "+++ b/src/auth/login.py\n@@ -5,2 +5,3 @@\n+ from sticky_sessions import SessionStore\n"),
            # 3. Forbidden pattern in control module
            ("src/control/actuator.py", "+++ b/src/control/actuator.py\n@@ -10,3 +10,4 @@\n+ mode = on_off_relay(reading)\n"),
            # 4. Forbidden pattern with variable assignment
            ("src/control/heater.py", "+++ b/src/control/heater.py\n@@ -20,2 +20,3 @@\n+ output = threshold_fallback(sensor_val)\n"),
            # 5. Required import removed
            ("src/billing/charge.py", "+++ b/src/billing/charge.py\n@@ -1,3 +1,2 @@\n- import stripe\n"),
            # 6. Config value mismatch
            ("config.json", "+++ b/config.json\n@@ -4,2 +4,3 @@\n+ \"timeout_seconds\": 60,\n"),
            # 7. Code line following inline comment
            ("src/control/fan.py", "+++ b/src/control/fan.py\n@@ -15,2 +15,3 @@\n+ speed = bang_bang_step(temp)  # emergency step\n")
        ]

        self.assertGreaterEqual(len(positive_cases), 6, "Must test at least 6 positive diffs")

        for filepath, diff in positive_cases:
            report = self.detector.analyze_diff_for_drift(
                repo="acme-eng/thermal-control-system",
                commit_or_pr_id="pr_pos_test",
                author="tester",
                changed_files=[filepath],
                diff_text=diff
            )
            findings = report.get("findings", [])
            self.assertGreaterEqual(
                len(findings), 1,
                f"Expected violation for positive case {filepath} with diff:\n{diff}"
            )
            f = findings[0]
            self.assertEqual(f["status"], "potential_violation")
            self.assertIn("rule_id", f)
            self.assertIn("decision_id", f)
            self.assertEqual(f["file"], filepath)
            self.assertIsInstance(f["line_number"], int)
            self.assertIn("offending_line", f)
            self.assertIn(f["signal_strength"], ("high", "medium", "low"))
            self.assertFalse(f["reviewed"])
            self.assertFalse(f["calibrated"])
            self.assertIsInstance(f["evidence_passages"], list)

    def test_negative_diffs_produce_zero_findings(self):
        """Verify >= 10 negative diffs (near-misses, comments, removed lines, etc.) produce 0 findings."""
        test_rules = [
            GuardRule(
                rule_id="rule_neg_forbid_mod",
                decision_id="dec_thermal_pid_accepted",
                rule_type="forbid_import",
                params={"module": "sticky_sessions", "paths": ["src/**/*.py"]},
                status="active",
                polarity="must_not",
                applies_to=["src/**/*.py"]
            ),
            GuardRule(
                rule_id="rule_neg_forbid_pat",
                decision_id="dec_thermal_pid_accepted",
                rule_type="forbid_pattern",
                params={"regex": r"\b(on_off_relay|threshold_fallback)\b", "paths": ["src/control/**/*.py"]},
                status="active",
                polarity="must_not",
                applies_to=["src/control/**/*.py"]
            ),
            # Inactive/proposed rule that must NOT be enforced
            GuardRule(
                rule_id="rule_inactive_proposed",
                decision_id="dec_thermal_pid_accepted",
                rule_type="forbid_import",
                params={"module": "numpy", "paths": ["src/**/*.py"]},
                status="proposed",
                polarity="must_not",
                applies_to=["src/**/*.py"]
            ),
            GuardRule(
                rule_id="rule_neg_config",
                decision_id="dec_thermal_pid_accepted",
                rule_type="config_value",
                params={"file": "config.json", "key": "timeout_seconds", "must_equal": "30"},
                status="active",
                polarity="must",
                applies_to=["config.json"]
            ),
        ]
        for r in test_rules:
            self.db.upsert_guard_rule(r)

        negative_cases = [
            # 1. Clean code addition
            ("src/service/worker.py", "+++ b/src/service/worker.py\n@@ -1,2 +1,3 @@\n+ count = calculate_total_items(items)\n"),
            # 2. Near-miss variable name (not an import)
            ("src/service/worker.py", "+++ b/src/service/worker.py\n@@ -1,2 +1,3 @@\n+ sticky_sessions_count = 10\n"),
            # 3. Pure comment mentioning historical decommissioned pattern
            ("src/control/temp.py", "+++ b/src/control/temp.py\n@@ -1,2 +1,3 @@\n+ # Note: on_off_relay was decommissioned in ADR 0004\n"),
            # 4. Docstring / documentation note
            ("src/control/temp.py", "+++ b/src/control/temp.py\n@@ -1,2 +1,3 @@\n+ # Clean up: threshold_fallback was replaced by discrete PID\n"),
            # 5. Removed line containing forbidden pattern
            ("src/control/temp.py", "+++ b/src/control/temp.py\n@@ -10,3 +10,2 @@\n- state = on_off_relay(x)\n+ state = compute_step(x)\n"),
            # 6. Near-miss module import
            ("src/service/worker.py", "+++ b/src/service/worker.py\n@@ -1,2 +1,3 @@\n+ import sticky_sessions_client\n"),
            # 7. File outside applies_to glob
            ("docs/manual.md", "+++ b/docs/manual.md\n@@ -1,2 +1,3 @@\n+ import sticky_sessions\n"),
            # 8. Proposed/inactive rule must not trigger
            ("src/service/worker.py", "+++ b/src/service/worker.py\n@@ -1,2 +1,3 @@\n+ import numpy as np\n"),
            # 9. Config value matching must_equal exactly
            ("config.json", "+++ b/config.json\n@@ -4,2 +4,3 @@\n+ \"timeout_seconds\": 30,\n"),
            # 10. Comment-only telemetry note
            ("src/control/temp.py", "+++ b/src/control/temp.py\n@@ -1,2 +1,3 @@\n+ # Update docs for telemetry metrics\n"),
            # 11. Context line containing term (space prefix, not added)
            ("src/control/temp.py", "+++ b/src/control/temp.py\n@@ -10,3 +10,3 @@\n  # on_off_relay\n+ x = 42\n"),
        ]

        self.assertGreaterEqual(len(negative_cases), 10, "Must test at least 10 negative diffs")

        for filepath, diff in negative_cases:
            report = self.detector.analyze_diff_for_drift(
                repo="acme-eng/thermal-control-system",
                commit_or_pr_id="pr_neg_test",
                author="tester",
                changed_files=[filepath],
                diff_text=diff
            )
            findings = report.get("findings", [])
            self.assertEqual(
                findings, [],
                f"Negative case {filepath} produced unexpected findings:\n{findings}\nDiff:\n{diff}"
            )

    def test_evaluate_drift_cases_json_full_suite(self):
        """Re-runs the labelled drift_cases.json and records 100% precision and recall."""
        runner = BenchmarkRunner(self.db)
        metrics = runner._evaluate_drift_cases()

        self.assertEqual(metrics["status"], "measured")
        self.assertEqual(metrics["total_cases"], 20)
        self.assertEqual(metrics["tp"], 10, "Expected exactly 10 true positive violations")
        self.assertEqual(metrics["fp"], 0, "Expected 0 false positives")
        self.assertEqual(metrics["tn"], 10, "Expected exactly 10 true negatives")
        self.assertEqual(metrics["fn"], 0, "Expected 0 false negatives")
        self.assertEqual(metrics["precision"], 100.0, "Expected 100% drift precision")
        self.assertEqual(metrics["recall"], 100.0, "Expected 100% drift recall")


if __name__ == "__main__":
    unittest.main()
