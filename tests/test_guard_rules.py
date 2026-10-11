import os
import tempfile
import unittest
from backend.db import Database
from backend.models import Decision, GuardRule
from backend.seed_data import populate_seed_data
from backend.engine.guard_rules import propose_rules_from_decision, check_diff_against_guard_rules

class TestGuardRules(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_guard_rules.db")
        self.db = Database(self.db_path)
        populate_seed_data(self.db)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_guard_rule_db_crud(self):
        """Tests creating, reading, and updating guard rules in SQLite."""
        rule = GuardRule(
            rule_id="rule_test_01",
            decision_id="dec_thermal_pid_accepted",
            rule_type="forbid_import",
            params={"module": "sticky_sessions", "paths": ["*.py"]},
            status="proposed"
        )
        self.db.upsert_guard_rule(rule)

        rules = self.db.get_guard_rules(decision_id="dec_thermal_pid_accepted", status="proposed")
        self.assertGreaterEqual(len(rules), 1)
        found_test_rule = any(r["rule_id"] == "rule_test_01" for r in rules)
        self.assertTrue(found_test_rule)


        # Approve rule -> status='active'
        self.db.update_guard_rule_status("rule_test_01", "active", approved_by="admin_alice")
        active_rules = self.db.get_guard_rules(status="active")
        self.assertEqual(len(active_rules), 1)
        self.assertEqual(active_rules[0]["approved_by"], "admin_alice")

        # Disable rule -> status='disabled'
        self.db.update_guard_rule_status("rule_test_01", "disabled")
        disabled_rules = self.db.get_guard_rules(status="disabled")
        self.assertEqual(len(disabled_rules), 1)

    def test_forbid_import_rule(self):
        """Tests forbid_import rule against positive violations and negative clean diffs."""
        rules = [{
            "rule_id": "rule_forbid_sticky",
            "decision_id": "dec_01",
            "rule_type": "forbid_import",
            "params": {"module": "sticky_sessions", "paths": ["src/**/*.py"]},
            "status": "active"
        }]

        positives = [
            ("src/web/session.py", "+ import sticky_sessions"),
            ("src/auth/login.py", "+ from sticky_sessions import SessionCookie"),
            ("src/net/router.py", "+ import sticky_sessions as ss"),
            ("src/api/handler.py", "+ from sticky_sessions.store import RedisStore")
        ]

        negatives = [
            ("src/web/session.py", "- import sticky_sessions"), # deleted line
            ("src/web/session.py", "+ import secure_cookies"),
            ("src/auth/login.py", "+ from session_manager import TokenStore"),
            ("docs/architecture.md", "+ import sticky_sessions") # docs path outside paths
        ]

        for filepath, diff_line in positives:
            violations = check_diff_against_guard_rules(rules, [filepath], f"+++ b/{filepath}\n{diff_line}")
            self.assertEqual(len(violations), 1, f"Expected violation for positive: {diff_line}")

        for filepath, diff_line in negatives:
            violations = check_diff_against_guard_rules(rules, [filepath], f"+++ b/{filepath}\n{diff_line}")
            self.assertEqual(len(violations), 0, f"Expected no violation for negative: {diff_line}")

    def test_forbid_pattern_rule(self):
        """Tests forbid_pattern rule with regex."""
        rules = [{
            "rule_id": "rule_forbid_bangbang",
            "decision_id": "dec_02",
            "rule_type": "forbid_pattern",
            "params": {
                "regex": r"(?:on_off_relay|threshold_high|hysteresis_loop)",
                "paths": ["src/thermal/**/*.py"]
            },
            "status": "active"
        }]

        positives = [
            ("src/thermal/control.py", "+ state = on_off_relay(temp)"),
            ("src/thermal/control.py", "+ if temp > threshold_high:"),
            ("src/thermal/chamber.py", "+ run_hysteresis_loop()"),
            ("src/thermal/regulator.py", "+ return on_off_relay_step()")
        ]

        negatives = [
            ("src/thermal/control.py", "- state = on_off_relay(temp)"),
            ("src/thermal/control.py", "+ output = pid_controller.compute(temp)"),
            ("src/thermal/sensor.py", "+ filter_adc_samples()"),
            ("src/other/test.py", "+ state = on_off_relay(temp)")
        ]

        for filepath, diff_line in positives:
            violations = check_diff_against_guard_rules(rules, [filepath], f"+++ b/{filepath}\n{diff_line}")
            self.assertEqual(len(violations), 1, f"Expected violation for positive: {diff_line}")

        for filepath, diff_line in negatives:
            violations = check_diff_against_guard_rules(rules, [filepath], f"+++ b/{filepath}\n{diff_line}")
            self.assertEqual(len(violations), 0, f"Expected no violation for negative: {diff_line}")

    def test_config_value_rule(self):
        """Tests config_value rule."""
        rules = [{
            "rule_id": "rule_timeout_30",
            "decision_id": "dec_03",
            "rule_type": "config_value",
            "params": {"file": "config.json", "key": "timeout_seconds", "must_equal": "30"},
            "status": "active"
        }]

        positives = [
            ("config.json", '+   "timeout_seconds": 120,'),
            ("config.json", '+   "timeout_seconds": 5,'),
            ("config.json", '+   "timeout_seconds": "60",'),
            ("config.json", '+   "timeout_seconds": 0,')
        ]

        negatives = [
            ("config.json", '+   "timeout_seconds": 30,'),
            ("config.json", '+   "timeout_seconds": "30",'),
            ("config.json", '+   "other_param": 120,'),
            ("settings.py", '+   "timeout_seconds": 120,') # different file
        ]

        for filepath, diff_line in positives:
            violations = check_diff_against_guard_rules(rules, [filepath], f"+++ b/{filepath}\n{diff_line}")
            self.assertEqual(len(violations), 1, f"Expected violation for positive: {diff_line}")

        for filepath, diff_line in negatives:
            violations = check_diff_against_guard_rules(rules, [filepath], f"+++ b/{filepath}\n{diff_line}")
            self.assertEqual(len(violations), 0, f"Expected no violation for negative: {diff_line}")

    def test_propose_rules_from_decision(self):
        """Tests proposing guard rules from decision rationale and rejected alternatives."""
        dec = Decision(
            decision_id="dec_sample_01",
            title="Adopt Redis Distributed Cluster",
            state="accepted",
            made_by="sarah",
            made_at="2026-01-01T00:00:00Z",
            artifacts_affected=["src/cache/store.py"],
            alternatives_considered=[{
                "description": "In-memory dict cache",
                "rejection_reason": "Causes OOM and stampedes"
            }],
            rationale="Redis cluster guarantees shared state",
            evidence_event_ids=["evt_adr_thermal_0004"],
            repo="acme/cache"
        )
        proposed = propose_rules_from_decision(dec)
        self.assertGreater(len(proposed), 0)
        for p in proposed:
            self.assertEqual(p.status, "proposed", "Rules must never be auto-activated")
            self.assertIn(p.rule_type, ("forbid_import", "require_import", "forbid_pattern", "config_value"))

if __name__ == "__main__":
    unittest.main()
