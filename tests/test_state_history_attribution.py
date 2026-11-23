"""
state_history repository attribution (Windows failure 2026-11-23:
"Table state_history has 2 rows with unresolved repo_full_name").

Root cause: migration 007 backfilled repo_full_name once, but the ~30 code paths that later insert
state_history rows (lifecycle transitions, review actions, revalidation, backfill tools) do not set it.
Each successful review action therefore created one unattributed row.

Fix (migration 009 + backend/integrity.py): an AFTER INSERT trigger copies the repository from the
row's own decision, and a backfill repairs existing rows the same way. Rows whose decision is missing
or has no repository are left NULL — attribution is recovered, never invented.
"""
import contextlib
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import APIHandler
from backend.db import Database
from backend.migrations.runner import run_migrations
from backend.seed_data import populate_seed_data


def _unattributed(path):
    with contextlib.closing(sqlite3.connect(path)) as c:
        return c.execute("SELECT COUNT(*) FROM state_history WHERE repo_full_name IS NULL OR repo_full_name = ''").fetchone()[0]


class StateHistoryAttributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "attr.db")
        self.db = Database(self.path)
        populate_seed_data(self.db)

    def _confirm_queue_decisions(self, n):
        api = APIHandler(self.db)
        done = 0
        for it in api.handle_get("/api/review-queue", {})["data"]:
            if it["item_type"] == "decision" and done < n:
                res = api.handle_post("/api/review-action",
                                      {"action": "confirm", "target_id": it["target_id"], "item_type": "decision"})
                done += res.get("status") == "success"
        self.assertEqual(done, n, "fixture needs enough confirmable decisions")

    def test_rows_written_by_review_actions_are_attributed(self):
        self.assertEqual(_unattributed(self.path), 0)
        self._confirm_queue_decisions(2)   # exactly what produced the 2 rows on Windows
        self.assertEqual(_unattributed(self.path), 0)

    def test_attribution_matches_the_rows_own_decision(self):
        self._confirm_queue_decisions(1)
        with contextlib.closing(sqlite3.connect(self.path)) as c:
            mismatched = c.execute("""SELECT COUNT(*) FROM state_history h JOIN decisions d USING (decision_id)
                                      WHERE h.repo_full_name IS NOT COALESCE(NULLIF(d.repo_full_name, ''), d.repo)  -- NULL counts as mismatch""").fetchone()[0]
        self.assertEqual(mismatched, 0)

    def _simulate_pre_fix_database(self, orphan=False):
        """Drop the trigger, write unattributed rows the old way, and mark migration 009 unapplied."""
        with contextlib.closing(sqlite3.connect(self.path)) as c, c:
            c.execute("DROP TRIGGER IF EXISTS trg_state_history_repo_attribution")
            c.execute("DELETE FROM schema_migrations WHERE version >= 9")
            decision_id, repo = c.execute("SELECT decision_id, repo FROM decisions LIMIT 1").fetchone()
            for i in range(2):  # recoverable rows, exactly as the old code wrote them
                c.execute("""INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                             VALUES (?, ?, 'accepted', '2026-11-20T00:00:00Z', 'user:x', 'old review action')""",
                          (f"hist_old_{i}", decision_id))
            if orphan:
                c.execute("PRAGMA foreign_keys = OFF")   # an orphan row can only exist if FKs were off
                c.execute("""INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                             VALUES ('hist_orphan', 'dec_deleted_long_ago', 'accepted', '2026-01-01T00:00:00Z', 'x', 'orphan')""")
        return decision_id, repo

    def _count(self, sql):
        with contextlib.closing(sqlite3.connect(self.path)) as c:
            return c.execute(sql).fetchall()

    def test_migration_009_recovers_existing_rows_without_deleting_history(self):
        decision_id, repo = self._simulate_pre_fix_database()
        total_before = self._count("SELECT COUNT(*) FROM state_history")[0][0]
        self.assertEqual(_unattributed(self.path), 2)            # the Windows situation
        with contextlib.closing(sqlite3.connect(self.path)) as c, c:
            applied = run_migrations(c)
        self.assertIn(9, [m["version"] for m in applied])
        self.assertEqual(self._count("SELECT repo_full_name FROM state_history WHERE history_id LIKE 'hist_old_%'"),
                         [(repo,), (repo,)])                     # taken from the rows' own decision
        self.assertEqual(_unattributed(self.path), 0)
        self.assertEqual(self._count("SELECT COUNT(*) FROM state_history")[0][0], total_before)

    def test_backfill_never_invents_attribution_for_unrecoverable_rows(self):
        from backend.integrity import backfill_state_history_attribution
        _, repo = self._simulate_pre_fix_database(orphan=True)
        with contextlib.closing(sqlite3.connect(self.path)) as c, c:
            result = backfill_state_history_attribution(c)
        self.assertEqual(result, {"recovered": 2, "unrecoverable": 1})
        self.assertEqual(self._count("SELECT repo_full_name FROM state_history WHERE history_id = 'hist_orphan'"),
                         [(None,)])                              # left NULL, not guessed
        with contextlib.closing(sqlite3.connect(self.path)) as c, c:   # idempotent: second run changes nothing
            self.assertEqual(backfill_state_history_attribution(c), {"recovered": 0, "unrecoverable": 1})

    def test_startup_reinstates_missing_trigger(self):
        with contextlib.closing(sqlite3.connect(self.path)) as c, c:
            c.execute("DROP TRIGGER trg_state_history_repo_attribution")
        Database(self.path)
        self._confirm_queue_decisions(1)
        self.assertEqual(_unattributed(self.path), 0)


if __name__ == "__main__":
    unittest.main()
