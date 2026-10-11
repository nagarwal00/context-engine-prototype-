"""
Tests for Drift Detector Failure Isolation and Error Reporting (P1-b / Step 1.4)
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from backend.db import Database
from backend.seed_data import populate_seed_data
from backend.engine.drift_detector import DriftDetector
from backend.models import GuardRule

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestDriftErrors(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_drift_errors.db")
        self.db = Database(self.db_path)
        populate_seed_data(self.db)
        self.detector = DriftDetector(self.db)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_broken_rule_yields_incomplete_and_healthy_rule_still_reports(self):
        """
        A deliberately broken rule (malformed params_json or invalid regex)
        yields status: 'incomplete' plus a sanitized error entry.
        A healthy rule evaluated in the same pass still reports its finding.
        """
        # 1. Add healthy active rule forbidding sticky_sessions
        healthy_rule = GuardRule(
            rule_id="rule_healthy_sticky",
            decision_id="dec_thermal_pid_accepted",
            rule_type="forbid_import",
            params={"module": "sticky_sessions", "paths": ["src/**/*.py"]},
            status="active"
        )
        self.db.upsert_guard_rule(healthy_rule)

        # 2. Add deliberately broken rule directly via SQL with malformed params_json
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO guard_rules (
                rule_id, decision_id, rule_type, params_json, status, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "rule_broken_malformed_json",
                "dec_thermal_pid_accepted",
                "forbid_pattern",
                "{malformed_json_syntax: true",
                "active",
                "test",
                "2026-01-01T00:00:00Z"
            ))
            conn.commit()

        # 3. Add second broken rule with uncompilable regex
        broken_regex_rule = GuardRule(
            rule_id="rule_broken_regex",
            decision_id="dec_thermal_pid_accepted",
            rule_type="forbid_pattern",
            params={"regex": "[unclosed_character_class", "paths": ["src/**/*.py"]},
            status="active"
        )
        self.db.upsert_guard_rule(broken_regex_rule)

        # Diff introducing forbidden import and some other text
        diff_text = """+++ b/src/service/worker.py
+ import sticky_sessions
+ x = 42
"""

        report = self.detector.analyze_diff_for_drift(
            repo="acme-eng/thermal-control-system",
            commit_or_pr_id="pr_test_broken",
            author="dev",
            changed_files=["src/service/worker.py"],
            diff_text=diff_text
        )

        # Status must be incomplete
        self.assertEqual(report["status"], "incomplete")

        # Healthy rule must still report finding
        findings = report["findings"]
        self.assertGreaterEqual(len(findings), 1)
        found_healthy_violation = any(
            f.get("rule_id") == "rule_healthy_sticky" for f in findings
        )
        self.assertTrue(found_healthy_violation, "Healthy rule must report violation despite broken rules")

        # Errors list must contain errors for broken rules
        errors = report["errors"]
        self.assertGreaterEqual(len(errors), 1)
        error_rule_ids = [e.get("rule_id") for e in errors]
        self.assertTrue(
            "rule_broken_malformed_json" in error_rule_ids or "rule_broken_regex" in error_rule_ids
        )

        # Ensure errors are sanitized (no diff text, no params dump)
        for err in errors:
            self.assertIn("stage", err)
            self.assertIn("rule_id", err)
            self.assertIn("error_type", err)
            self.assertIn("message", err)
            self.assertNotIn("+++ b/src/service/worker.py", err["message"])
            self.assertNotIn("import sticky_sessions", err["message"])

    def test_clean_diff_with_all_rules_ok_is_complete(self):
        """Clean diff with all healthy rules yields complete with empty findings and errors."""
        healthy_rule = GuardRule(
            rule_id="rule_healthy_clean_test",
            decision_id="dec_thermal_pid_accepted",
            rule_type="forbid_import",
            params={"module": "sticky_sessions", "paths": ["src/**/*.py"]},
            status="active"
        )
        self.db.upsert_guard_rule(healthy_rule)

        clean_diff = """+++ b/src/service/worker.py
+ # Normal harmless comment update
+ y = 100
"""
        report = self.detector.analyze_diff_for_drift(
            repo="acme-eng/thermal-control-system",
            commit_or_pr_id="pr_clean",
            author="dev",
            changed_files=["src/service/worker.py"],
            diff_text=clean_diff
        )

        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["errors"], [])

    def test_ci_check_exit_codes(self):
        """
        Verify tools/ci_check.py exit codes:
          0 = complete and clean
          1 = violations
          2 = incomplete (or bad arguments/errors)
        """
        from backend.engine.guard_rules import check_diff_against_guard_rules_with_report

        # 1. Clean change -> exit code 0 equivalent
        clean_rules = [{
            "rule_id": "r1",
            "decision_id": "d1",
            "rule_type": "forbid_import",
            "params": {"module": "banned_lib", "paths": ["*.py"]},
            "status": "active"
        }]
        clean_report = check_diff_against_guard_rules_with_report(
            clean_rules,
            ["app.py"],
            "+++ b/app.py\n+ import safe_lib\n"
        )
        self.assertEqual(clean_report["status"], "complete")
        self.assertEqual(clean_report["violations"], [])
        self.assertEqual(clean_report["errors"], [])

        # 2. Violating change -> exit code 1 equivalent
        violating_report = check_diff_against_guard_rules_with_report(
            clean_rules,
            ["app.py"],
            "+++ b/app.py\n+ import banned_lib\n"
        )
        self.assertEqual(violating_report["status"], "complete")
        self.assertEqual(len(violating_report["violations"]), 1)
        self.assertEqual(violating_report["errors"], [])

        # 3. Broken rule -> exit code 2 equivalent (incomplete)
        broken_rules = [{
            "rule_id": "r_bad_regex",
            "decision_id": "d1",
            "rule_type": "forbid_pattern",
            "params": {"regex": "(?P<bad", "paths": ["*.py"]},
            "status": "active"
        }]
        broken_report = check_diff_against_guard_rules_with_report(
            broken_rules,
            ["app.py"],
            "+++ b/app.py\n+ x = 1\n"
        )
        self.assertEqual(broken_report["status"], "incomplete")
        self.assertGreaterEqual(len(broken_report["errors"]), 1)

        # 4. CLI invocation test with temporary rules files
        rules_clean_file = Path(self.tmp_dir.name) / "rules_clean.json"
        rules_clean_file.write_text(json.dumps(clean_rules), encoding="utf-8")

        rules_broken_file = Path(self.tmp_dir.name) / "rules_broken.json"
        rules_broken_file.write_text(json.dumps(broken_rules), encoding="utf-8")

        ci_check_script = str(REPO_ROOT / "tools" / "ci_check.py")

        # Missing required args should exit 2
        res = subprocess.run([sys.executable, ci_check_script], capture_output=True, text=True)
        self.assertEqual(res.returncode, 2)


if __name__ == "__main__":
    unittest.main()
