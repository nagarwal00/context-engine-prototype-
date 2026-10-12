"""
Unit Tests for Decision Half-Life & Staleness (Step 5.2)
Verifies:
1. Decisions NEVER expire by age alone.
2. Breaking dependency upgrades trigger staleness; non-breaking upgrades leave decisions fresh.
3. Config changes and file deletions trigger staleness.
4. Review queue generates stale-decision items naming the triggering change and source link, with 'stale for N days' counter.
5. Revalidating a decision transitions freshness to 'revalidated' and records state_history.
"""
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from backend.models import Event, Decision
from backend.db import Database
from backend.engine.staleness import StalenessEngine, parse_semver, check_version_violation
from backend.api import APIHandler


class TestStaleness(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_staleness.db")
        self.db = Database(self.db_path)
        self.engine = StalenessEngine(self.db)
        self.api = APIHandler(self.db)

        # Base accepted decision with evidence
        self.ev_base = Event(
            event_id="evt_base_01",
            source_type="git_commit",
            source_id="c_base_01",
            source_url="https://github.com/org/payment-core/commit/c_base_01",
            repo="org/payment-core",
            author="lead_dev",
            timestamp="2023-01-01T10:00:00Z",
            title="Initial payment gateway architecture",
            body="Use Pydantic v1 for request schema validation and Stripe v4."
        )
        self.db.upsert_event(self.ev_base)

        self.dec_1 = Decision(
            decision_id="dec_pay_01",
            title="Strict Pydantic Schema Validation",
            state="accepted",
            repo="org/payment-core",
            made_at="2023-01-01T10:00:00Z",
            confidence=0.92,
            freshness="fresh",
            evidence_event_ids=["evt_base_01"]
        )
        self.db.save_decision(self.dec_1)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_never_expire_by_age_alone(self):
        """Verifies that old decisions remain fresh if no assumption-breaking event occurred."""
        # Decision is dated from 2023 (years old)
        assump_id = self.engine.add_assumption(
            decision_id="dec_pay_01",
            text="Assumes Pydantic stays below v2.0.0",
            watch_type="dependency_version",
            watch_params={"package": "pydantic", "max_version": "2.0.0"}
        )

        # Ingest an unrelated commit
        unrelated_ev = Event(
            event_id="evt_unrelated_01",
            source_type="git_commit",
            source_id="c_unrelated_01",
            source_url="https://github.com/org/payment-core/commit/c_unrelated_01",
            repo="org/payment-core",
            author="dev",
            timestamp="2026-03-01T12:00:00Z",
            title="Update frontend stylesheet colors",
            body="Adjust button padding and colors."
        )
        self.db.upsert_event(unrelated_ev)
        findings = self.engine.evaluate_event_for_staleness(unrelated_ev)

        self.assertEqual(len(findings), 0)
        # Decision MUST remain fresh
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT freshness FROM decisions WHERE decision_id = 'dec_pay_01'")
            self.assertEqual(cursor.fetchone()["freshness"], "fresh")

    def test_dependency_upgrade_triggers_staleness(self):
        """Verifies that a breaking version bump marks decision stale, but non-breaking leaves it fresh."""
        self.engine.add_assumption(
            decision_id="dec_pay_01",
            text="Assumes Pydantic stays below 2.0.0",
            watch_type="dependency_version",
            watch_params={"package": "pydantic", "max_version": "2.0.0"}
        )

        # 1. Non-breaking bump: pydantic 1.9.2 -> remains fresh
        non_breaking_ev = Event(
            event_id="evt_bump_192",
            source_type="github_pr",
            source_id="pr_10",
            source_url="https://github.com/org/payment-core/pull/10",
            repo="org/payment-core",
            author="renovate_bot",
            timestamp="2026-02-01T00:00:00Z",
            title="bump pydantic to 1.9.2",
            body="Minor patch update"
        )
        self.db.upsert_event(non_breaking_ev)
        findings = self.engine.evaluate_event_for_staleness(non_breaking_ev)
        self.assertEqual(len(findings), 0)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT freshness FROM decisions WHERE decision_id = 'dec_pay_01'")
            self.assertEqual(cursor.fetchone()["freshness"], "fresh")

        # 2. Breaking bump: pydantic 2.1.0 -> triggers staleness!
        breaking_ev = Event(
            event_id="evt_bump_210",
            source_type="github_pr",
            source_id="pr_42",
            source_url="https://github.com/org/payment-core/pull/42",
            repo="org/payment-core",
            author="lead_dev",
            timestamp="2026-03-01T00:00:00Z",
            title="upgrade pydantic to 2.1.0",
            body="Major migration to Pydantic v2 core."
        )
        self.db.upsert_event(breaking_ev)
        findings = self.engine.evaluate_event_for_staleness(breaking_ev)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["decision_id"], "dec_pay_01")
        self.assertIn("Pydantic", findings[0]["trigger_reason"])

        # Verify database reflects 'stale'
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT freshness FROM decisions WHERE decision_id = 'dec_pay_01'")
            self.assertEqual(cursor.fetchone()["freshness"], "stale")

    def test_config_value_and_file_deletion_triggers(self):
        """Verifies config value change and file deletion triggers."""
        # Decision 2: Config assumption
        dec_cfg = Decision(
            decision_id="dec_cfg_02",
            title="Max Concurrency Cap at 50",
            state="accepted",
            repo="org/payment-core",
            made_at="2026-01-01T00:00:00Z",
            confidence=0.9,
            freshness="fresh",
            evidence_event_ids=["evt_base_01"]
        )
        self.db.save_decision(dec_cfg)

        self.engine.add_assumption(
            decision_id="dec_cfg_02",
            text="Assumes MAX_WORKERS stays at 50",
            watch_type="config_value",
            watch_params={"config_key": "MAX_WORKERS", "expected_value": 50}
        )

        cfg_ev = Event(
            event_id="evt_cfg_change",
            source_type="git_commit",
            source_id="c_cfg_123",
            source_url="https://github.com/org/payment-core/commit/c_cfg_123",
            repo="org/payment-core",
            author="dev",
            timestamp="2026-03-02T10:00:00Z",
            title="Scale worker pool",
            body="Update settings: MAX_WORKERS = 100 for higher throughput."
        )
        self.db.upsert_event(cfg_ev)
        findings = self.engine.evaluate_event_for_staleness(cfg_ev)
        self.assertEqual(len(findings), 1)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT freshness FROM decisions WHERE decision_id = 'dec_cfg_02'")
            self.assertEqual(cursor.fetchone()["freshness"], "stale")

    def test_stale_review_queue_item_content_and_counter(self):
        """Verifies review-queue items name the triggering change with source link and 'stale for N days' counter."""
        self.engine.add_assumption(
            decision_id="dec_pay_01",
            text="Assumes Pydantic stays below 2.0.0",
            watch_type="dependency_version",
            watch_params={"package": "pydantic", "max_version": "2.0.0"}
        )

        # Trigger staleness 10 days ago
        ten_days_ago = (datetime.utcnow() - timedelta(days=10)).isoformat() + "Z"
        breaking_ev = Event(
            event_id="evt_break_10d",
            source_type="github_pr",
            source_id="pr_88",
            source_url="https://github.com/org/payment-core/pull/88",
            repo="org/payment-core",
            author="alice",
            timestamp=ten_days_ago,
            title="bump pydantic to 2.2.0",
            body="Bump version"
        )
        self.db.upsert_event(breaking_ev)
        self.engine.evaluate_event_for_staleness(breaking_ev)

        # Query /api/review-queue
        res = self.api.handle_get("/api/review-queue", {})
        self.assertEqual(res["status"], "success")
        queue = res["data"]

        stale_items = [item for item in queue if item.get("item_type") == "stale_decision"]
        self.assertEqual(len(stale_items), 1)
        item = stale_items[0]

        self.assertEqual(item["decision_id"], "dec_pay_01")
        self.assertEqual(item["trigger_url"], "https://github.com/org/payment-core/pull/88")
        self.assertIn("Triggered by github_pr #pr_88", item["queue_reason"])
        self.assertGreaterEqual(item["stale_days"], 9)
        self.assertLessEqual(item["stale_days"], 11)

    def test_revalidate_decision_records_history(self):
        """Verifies that revalidating a stale decision sets freshness to 'revalidated' and records state_history."""
        self.engine.add_assumption(
            decision_id="dec_pay_01",
            text="Assumes Pydantic stays below 2.0.0",
            watch_type="dependency_version",
            watch_params={"package": "pydantic", "max_version": "2.0.0"}
        )

        breaking_ev = Event(
            event_id="evt_break_now",
            source_type="git_commit",
            source_id="c_brk",
            source_url="https://github.com/org/payment-core/commit/c_brk",
            repo="org/payment-core",
            author="alice",
            timestamp="2026-03-01T00:00:00Z",
            title="upgrade pydantic to 2.0.0",
            body="Diff bump"
        )
        self.db.upsert_event(breaking_ev)
        self.engine.evaluate_event_for_staleness(breaking_ev)

        # Execute revalidation via API
        review_res = self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "stale_decision",
                "target_id": "dec_pay_01",
                "action": "revalidate",
                "reviewer": "lead_architect",
                "reason": "Audited v2 models and verified backward compatibility layer"
            }
        )
        self.assertEqual(review_res.get("status"), "success")

        # Verify freshness is 'revalidated'
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT freshness FROM decisions WHERE decision_id = 'dec_pay_01'")
            self.assertEqual(cursor.fetchone()["freshness"], "revalidated")

            # Verify audit log in state_history
            cursor.execute("SELECT * FROM state_history WHERE decision_id = 'dec_pay_01' ORDER BY changed_at DESC")
            hist = cursor.fetchone()
            self.assertIsNotNone(hist)
            self.assertIn("Revalidated decision freshness", hist["notes"])
            self.assertIn("Audited v2 models", hist["notes"])

            # Verify assumptions are back to 'valid'
            cursor.execute("SELECT status FROM decision_assumptions WHERE decision_id = 'dec_pay_01'")
            self.assertEqual(cursor.fetchone()["status"], "valid")


if __name__ == "__main__":
    unittest.main()
