"""
Database-level evidence invariant (audit fix DB-01, migration 008 / backend/integrity.py).
"""
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import Database
from backend.integrity import ungrounded_decisions
from backend.models import Decision
from backend.seed_data import populate_seed_data


class EvidenceInvariantTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "integrity.db")
        self.db = Database(self.path)
        populate_seed_data(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def _conn(self):
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _single_evidence_accepted(self, conn):
        return conn.execute("""
            SELECT d.decision_id, MIN(e.event_id) FROM decisions d
            JOIN decision_evidence e USING (decision_id)
            WHERE d.state = 'accepted' GROUP BY d.decision_id HAVING COUNT(*) = 1 LIMIT 1
        """).fetchone()

    def test_seed_data_is_fully_grounded(self):
        with self._conn() as conn:
            self.assertEqual(ungrounded_decisions(conn), [])

    def test_cannot_delete_the_only_evidence_event_of_an_accepted_decision(self):
        with self._conn() as conn:
            dec_id, event_id = self._single_evidence_accepted(conn)
            with self.assertRaises(sqlite3.IntegrityError) as ctx:
                conn.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
            self.assertIn("only evidence", str(ctx.exception))
            n = conn.execute("SELECT COUNT(*) FROM decision_evidence WHERE decision_id = ?", (dec_id,)).fetchone()[0]
            self.assertEqual(n, 1)

    def test_cannot_promote_a_decision_without_evidence(self):
        with self._conn() as conn:
            conn.execute("""INSERT INTO decisions (decision_id, title, state, made_by, made_at, rationale,
                            confidence, review_status, repo, evidence_assessment)
                            VALUES ('dec_bare', 'bare', 'proposed', 'x', '2026-01-01', 'r', 0.5,
                                    'pending_review', 'acme-eng/thermal-control-system', 'insufficient')""")
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE decisions SET state = 'accepted' WHERE decision_id = 'dec_bare'")

    def test_save_decision_still_rejects_ungrounded_accepted(self):
        d = Decision(decision_id="dec_x", title="x", state="accepted", made_by="a", made_at="2026-01-01T00:00:00Z",
                     evidence_event_ids=[], repo="acme-eng/thermal-control-system")
        with self.assertRaises(ValueError):
            self.db.save_decision(d)

    def test_resaving_existing_decision_with_new_evidence_works(self):
        """save_decision links new evidence before updating state, so the trigger allows it."""
        with self._conn() as conn:
            dec_id, old_ev = self._single_evidence_accepted(conn)
            other_ev = conn.execute("SELECT event_id FROM events WHERE event_id != ? LIMIT 1", (old_ev,)).fetchone()[0]
        dec = self.db.get_decision(dec_id)
        dec.evidence_event_ids = [other_ev]  # swap the evidence completely
        self.db.save_decision(dec)
        with self._conn() as conn:
            rows = [r[0] for r in conn.execute("SELECT event_id FROM decision_evidence WHERE decision_id = ?", (dec_id,))]
            self.assertEqual(rows, [other_ev])
            self.assertEqual(ungrounded_decisions(conn), [])

    def test_purge_repo_and_reseed_still_work(self):
        counts = self.db.purge_repo("acme-eng/thermal-control-system")
        self.assertGreater(counts.get("decisions", 0), 0)
        populate_seed_data(self.db)
        with self._conn() as conn:
            self.assertEqual(ungrounded_decisions(conn), [])

    def test_existing_database_without_triggers_gets_them_on_startup(self):
        with self._conn() as conn:
            conn.execute("DROP TRIGGER trg_event_sole_evidence")
        Database(self.path)  # start-up re-asserts the integrity objects
        with self._conn() as conn:
            names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        self.assertIn("trg_event_sole_evidence", names)


if __name__ == "__main__":
    unittest.main()
