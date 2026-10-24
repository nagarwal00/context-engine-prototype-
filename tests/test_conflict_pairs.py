import os
import tempfile
import unittest
from backend.db import Database
from backend.models import Decision, Event
from backend.engine.reconciliation import ReconciliationEngine, load_conflict_pairs


class TestConflictPairs(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_conflict.db")
        self.db = Database(self.db_path)
        self.recon = ReconciliationEngine(self.db)

        # Base event to satisfy foreign key in decision_evidence
        ev = Event(
            event_id="evt_mock_evidence",
            source_type="adr",
            source_id="adr_mock",
            source_url="https://github.com/acme/platform/docs/adr/001.md",
            repo="acme/platform",
            author="tester",
            timestamp="2026-01-01T00:00:00Z"
        )
        self.db.upsert_event(ev)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_two_async_decisions_do_not_conflict(self):
        """F6: Two decisions that both use 'async' must NOT be flagged as conflicting."""
        dec1 = Decision(
            decision_id="dec_async_1",
            title="Adopt async workers for background processing",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T10:00:00Z",
            artifacts_affected=["src/io/worker.py"],
            alternatives_considered=[],
            rationale="Async provides high throughput for I/O bound tasks",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        dec2 = Decision(
            decision_id="dec_async_2",
            title="Use async event loop for telemetry collection",
            state="accepted",
            made_by="bob",
            made_at="2026-01-02T10:00:00Z",
            artifacts_affected=["src/io/worker.py"],
            alternatives_considered=[],
            rationale="Telemetry needs nonblocking async execution",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        self.db.save_decision(dec1)
        self.db.save_decision(dec2)

        conflicts = self.recon.check_for_conflicts()
        self.assertEqual(len(conflicts), 0, "Two async decisions must not conflict (F6 substring bug)")

    def test_sync_vs_async_conflict_detected(self):
        """Sync vs async whole-word match triggers contradiction."""
        dec1 = Decision(
            decision_id="dec_sync_model",
            title="Adopt sync worker model",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T10:00:00Z",
            artifacts_affected=["src/io/worker.py"],
            alternatives_considered=[],
            rationale="Synchronous execution is simple, deterministic, and robust",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        dec2 = Decision(
            decision_id="dec_async_model",
            title="Migrate to async worker model",
            state="accepted",
            made_by="bob",
            made_at="2026-01-02T10:00:00Z",
            artifacts_affected=["src/io/worker.py"],
            alternatives_considered=[],
            rationale="Async allows higher concurrency on network calls",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        self.db.save_decision(dec1)
        self.db.save_decision(dec2)

        conflicts = self.recon.check_for_conflicts()
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["contradiction_topic"], "sync vs async")

    def test_asynchronous_alone_does_not_match_async(self):
        """Word boundary ensures 'asynchronous' does not match '\\basync\\b'."""
        dec1 = Decision(
            decision_id="dec_sync_isolated",
            title="Use sync processing loops",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T10:00:00Z",
            artifacts_affected=["src/io/worker.py"],
            alternatives_considered=[],
            rationale="Strict sync loops",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        dec2 = Decision(
            decision_id="dec_asynchronous_word",
            title="Adopt asynchronous task execution",
            state="accepted",
            made_by="bob",
            made_at="2026-01-02T10:00:00Z",
            artifacts_affected=["src/io/worker.py"],
            alternatives_considered=[],
            rationale="Run heavy jobs in an asynchronous worker pool",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        self.db.save_decision(dec1)
        self.db.save_decision(dec2)

        conflicts = self.recon.check_for_conflicts()
        # dec1 has 'sync', but dec2 has 'asynchronous' which does not match '\basync\b'
        self.assertEqual(len(conflicts), 0, "'asynchronous' must not match whole-word '\\basync\\b'")

    def test_demo_pairs_apply_only_to_demo_repos(self):
        """Demo pairs (pid/bang-bang, redis/in-memory lru) only apply when repos.visibility = 'demo'."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO repos (repo_full_name, visibility, added_at)
            VALUES ('demo-org/demo-repo', 'demo', '2026-01-01T00:00:00Z');
            """)
            cur.execute("""
            INSERT OR REPLACE INTO repos (repo_full_name, visibility, added_at)
            VALUES ('prod-org/prod-repo', 'public', '2026-01-01T00:00:00Z');
            """)

        # 1. Non-demo repo with pid vs bang-bang
        dec_prod1 = Decision(
            decision_id="dec_prod_pid",
            title="Implement PID control loop",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T10:00:00Z",
            artifacts_affected=["src/control/loop.py"],
            alternatives_considered=[],
            rationale="PID algorithm with anti-windup clamping",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="prod-org/prod-repo"
        )
        dec_prod2 = Decision(
            decision_id="dec_prod_bang",
            title="Evaluate bang-bang controller",
            state="proposed",
            made_by="bob",
            made_at="2026-01-02T10:00:00Z",
            artifacts_affected=["src/control/loop.py"],
            alternatives_considered=[],
            rationale="Simple bang-bang threshold relay",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.85,
            review_status="pending_review",
            repo="prod-org/prod-repo"
        )
        self.db.save_decision(dec_prod1)
        self.db.save_decision(dec_prod2)

        prod_conflicts = self.recon.check_for_conflicts(repo="prod-org/prod-repo")
        self.assertEqual(len(prod_conflicts), 0, "Demo pair must NOT apply to public/production repo")

        # 2. Demo repo with pid vs bang-bang
        dec_demo1 = Decision(
            decision_id="dec_demo_pid",
            title="Implement PID control loop",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T10:00:00Z",
            artifacts_affected=["src/control/loop.py"],
            alternatives_considered=[],
            rationale="PID algorithm with anti-windup clamping",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="demo-org/demo-repo"
        )
        dec_demo2 = Decision(
            decision_id="dec_demo_bang",
            title="Evaluate bang-bang controller",
            state="proposed",
            made_by="bob",
            made_at="2026-01-02T10:00:00Z",
            artifacts_affected=["src/control/loop.py"],
            alternatives_considered=[],
            rationale="Simple bang-bang threshold relay",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.85,
            review_status="pending_review",
            repo="demo-org/demo-repo"
        )
        self.db.save_decision(dec_demo1)
        self.db.save_decision(dec_demo2)

        demo_conflicts = self.recon.check_for_conflicts(repo="demo-org/demo-repo")
        self.assertEqual(len(demo_conflicts), 1, "Demo pair MUST apply to demo repo")
        self.assertEqual(demo_conflicts[0]["contradiction_topic"], "pid vs bang-bang")


if __name__ == "__main__":
    unittest.main()
