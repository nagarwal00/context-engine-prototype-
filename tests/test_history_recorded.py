"""
Unit and integration tests for state history recording and backfill.
Implements Step 2.3 of ANTIGRAVITY_HANDOFF_V2.md:
1. Freshly seeded DB has SELECT COUNT(*) FROM state_history >= COUNT(*) FROM decisions.
2. Review action increases state_history count.
3. Backfill tool on legacy DB copy correctly populates state_history with reconstructed=1.
4. Database save_decision enforces valid transitions and records audit entries.
5. Migration 002 is idempotent.
"""
import os
import shutil
import tempfile
import unittest
import sqlite3

from backend.db import Database
from backend.models import Decision, Event
from backend.seed_data import populate_seed_data
from backend.api import APIHandler
from backend.engine.lifecycle import InvalidTransition
from tools.backfill_state_history import backfill_state_history
import backend.migrations.runner as migration_runner


class TestHistoryRecorded(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fresh_seeded_db_has_history(self):
        """On a freshly seeded DB, SELECT COUNT(*) FROM state_history >= decisions count."""
        populate_seed_data(self.db)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS c FROM decisions")
            dec_count = cursor.fetchone()["c"]

            cursor.execute("SELECT COUNT(*) AS c FROM state_history")
            sh_count = cursor.fetchone()["c"]

            self.assertGreater(dec_count, 0)
            self.assertGreaterEqual(
                sh_count,
                dec_count,
                f"Freshly seeded DB must have state_history count ({sh_count}) >= decisions count ({dec_count})"
            )

            # Verify every decision has at least one history row
            cursor.execute("""
            SELECT d.decision_id
            FROM decisions d
            LEFT JOIN state_history sh ON d.decision_id = sh.decision_id
            WHERE sh.decision_id IS NULL
            """)
            missing = cursor.fetchall()
            self.assertEqual(len(missing), 0, "No seeded decision should lack history rows")

            # Verify dec_cache_local_lru_proposed has full progression proposed -> accepted -> superseded
            cursor.execute("""
            SELECT state, changed_by, notes FROM state_history
            WHERE decision_id = 'dec_cache_local_lru_proposed'
            ORDER BY changed_at ASC
            """)
            rows = cursor.fetchall()
            states = [r["state"] for r in rows]
            self.assertIn("proposed", states)
            self.assertIn("accepted", states)
            self.assertIn("superseded", states)

    def test_review_action_increases_history_count(self):
        """After a review action, state_history count increases."""
        populate_seed_data(self.db)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS c FROM state_history")
            count_before = cursor.fetchone()["c"]

        api = APIHandler(self.db)
        # Perform review action on a decision
        res = api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "confirm",
                "target_id": "dec_thermal_pid_accepted",
                "notes": "Verified in manual code review"
            }
        )
        self.assertEqual(res.get("status"), "success")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS c FROM state_history")
            count_after = cursor.fetchone()["c"]

        self.assertGreater(
            count_after,
            count_before,
            f"Review action must increase state_history count (before: {count_before}, after: {count_after})"
        )

    def test_backfill_tool_on_legacy_db_copy(self):
        """Tests tools/backfill_state_history.py on a copy of backups/context_intelligence.pre_v2.db."""
        backup_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "backups",
            "context_intelligence.pre_v2.db"
        )
        copy_path = os.path.join(self.temp_dir, "legacy_copy.db")

        if os.path.exists(backup_path):
            shutil.copyfile(backup_path, copy_path)
        else:
            # Create synthetic legacy DB without state_history
            conn = sqlite3.connect(copy_path)
            conn.execute("""
            CREATE TABLE decisions (
                decision_id TEXT PRIMARY KEY,
                title TEXT,
                state TEXT,
                made_by TEXT,
                made_at TEXT,
                rationale TEXT,
                confidence REAL,
                repo TEXT
            );
            """)
            conn.execute("""
            CREATE TABLE state_history (
                history_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                state TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                changed_by TEXT NOT NULL,
                notes TEXT
            );
            """)
            conn.execute("""
            INSERT INTO decisions VALUES
            ('dec_legacy_1', 'Legacy 1', 'accepted', 'alice', '2026-01-01T00:00:00Z', 'Test', 0.9, 'repo'),
            ('dec_legacy_2', 'Legacy 2', 'rejected', 'bob', '2026-01-02T00:00:00Z', 'Test', 0.8, 'repo');
            """)
            conn.commit()
            conn.close()

        # Run backfill tool
        result = backfill_state_history(copy_path, dry_run=False)

        self.assertGreater(result["decisions"], 0)
        self.assertEqual(result["before"], 0)
        self.assertGreaterEqual(result["after"], result["decisions"])
        self.assertEqual(result["backfilled"], result["decisions"])

        # Inspect DB contents directly
        conn = sqlite3.connect(copy_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM state_history WHERE reconstructed = 1")
        reconstructed_rows = cursor.fetchall()
        self.assertEqual(len(reconstructed_rows), result["decisions"])

        for row in reconstructed_rows:
            self.assertEqual(row["changed_by"], "system:backfill")
            self.assertIn("reconstructed from current state at backfill", row["notes"])
            self.assertIsNone(row["from_state"])

        conn.close()

    def test_save_decision_lifecycle_enforcement(self):
        """db.save_decision records initial history and prevents illegal state mutation."""
        ev = Event(
            event_id="ev_hist_test",
            source_type="git_commit",
            source_id="sha123",
            source_url="https://github.com/repo/commit/sha123",
            repo="test/repo",
            author="tester",
            timestamp="2026-03-01T10:00:00Z",
            title="Initial commit",
            body="Code commit"
        )
        self.db.upsert_event(ev)

        dec = Decision(
            decision_id="dec_hist_1",
            title="Test Decision",
            state="proposed",
            evidence_event_ids=[ev.event_id],
            evidence_assessment="insufficient",
            repo="test/repo"
        )
        self.db.save_decision(dec)

        # Initial history recorded
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM state_history WHERE decision_id = 'dec_hist_1'")
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["state"], "proposed")
            self.assertIsNone(rows[0]["from_state"])

        # Legal transition proposed -> accepted
        dec.state = "accepted"
        dec.evidence_assessment = "strong"
        self.db.save_decision(dec)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM state_history WHERE decision_id = 'dec_hist_1' ORDER BY changed_at ASC")
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1]["from_state"], "proposed")
            self.assertEqual(rows[1]["state"], "accepted")

        # Illegal transition accepted -> proposed (not allowed in ALLOWED_TRANSITIONS)
        dec.state = "proposed"
        with self.assertRaises(InvalidTransition):
            self.db.save_decision(dec)

    def test_migration_002_idempotency(self):
        """Applying migration 002 repeatedly is a safe no-op."""
        # Database already initialized migrations up to latest
        with sqlite3.connect(self.db_path) as conn:
            applied = migration_runner.run_migrations(conn)
            self.assertEqual(len(applied), 0)  # None pending

        # Run backfill tool on it again
        res = backfill_state_history(self.db_path, dry_run=False)
        self.assertEqual(res["backfilled"], 0)


if __name__ == "__main__":
    unittest.main()
