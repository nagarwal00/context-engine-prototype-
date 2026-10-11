import os
import shutil
import sqlite3
import tempfile
import unittest

from backend.db import Database
from backend.models import (
    Decision,
    Event,
    ALLOWED_DECISION_STATES,
    ALLOWED_EVIDENCE_ASSESSMENTS,
    ALLOWED_FRESHNESS,
)
from backend.migrations import run_migrations


class TestStateModel(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "state_test.db")
        self.db = Database(self.db_path)

        # Ingest a valid event to satisfy foreign key in decision_evidence
        self.ev = Event(
            event_id="evt_test_state_ev",
            source_type="adr",
            source_id="adr_0001",
            source_url="https://github.com/org/repo/adr/001.md",
            repo="org/repo",
            author="alice",
            timestamp="2026-01-01T00:00:00Z"
        )
        self.db.upsert_event(self.ev)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_every_allowed_state_saves_successfully(self):
        """Every allowed state in ('proposed', 'tested', 'accepted', 'rejected', 'superseded', 'reopened') saves."""
        for state in ALLOWED_DECISION_STATES:
            dec = Decision(
                decision_id=f"dec_state_{state}",
                title=f"Decision with state {state}",
                state=state,
                evidence_assessment="strong" if state in ("tested", "accepted") else "insufficient",
                freshness="fresh",
                made_by="alice",
                made_at="2026-01-01T00:00:00Z",
                artifacts_affected=["src/app.py"],
                rationale="Valid test rationale",
                evidence_event_ids=["evt_test_state_ev"],
                confidence=0.9,
                repo="org/repo"
            )
            self.db.save_decision(dec)

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT state, evidence_assessment, freshness FROM decisions WHERE decision_id = ?", (dec.decision_id,))
                row = cursor.fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row["state"], state)
                self.assertEqual(row["evidence_assessment"], dec.evidence_assessment)
                self.assertEqual(row["freshness"], dec.freshness)

    def test_illegal_state_rejected(self):
        """Illegal states (e.g. 'invented', 'uncertain') are rejected by validation and schema."""
        illegal_states = ["invented", "uncertain", "done", "active", "pending"]
        for bad_state in illegal_states:
            with self.assertRaises(ValueError):
                dec = Decision(
                    decision_id=f"dec_bad_{bad_state}",
                    title="Bad state decision",
                    state=bad_state,
                    evidence_event_ids=["evt_test_state_ev"]
                )
                dec.validate_invariants()

    def test_illegal_evidence_assessment_rejected(self):
        """Illegal evidence assessments are rejected."""
        with self.assertRaises(ValueError):
            dec = Decision(
                decision_id="dec_bad_assess",
                title="Bad assessment",
                state="proposed",
                evidence_assessment="unknown_quality",
                evidence_event_ids=["evt_test_state_ev"]
            )
            dec.validate_invariants()

    def test_illegal_freshness_rejected(self):
        """Illegal freshness values are rejected."""
        with self.assertRaises(ValueError):
            dec = Decision(
                decision_id="dec_bad_fresh",
                title="Bad freshness",
                state="proposed",
                freshness="expired",
                evidence_event_ids=["evt_test_state_ev"]
            )
            dec.validate_invariants()

    def test_evidence_invariant_enforced(self):
        """
        Evidence invariant (Step 2.1):
        - states 'tested', 'accepted', 'rejected', 'superseded' require >= 1 evidence event.
        - 'proposed' and 'reopened' may have none, but then evidence_assessment must be 'insufficient'.
        """
        # Tested, accepted, rejected, superseded with 0 evidence must FAIL
        for state in ("tested", "accepted", "rejected", "superseded"):
            with self.assertRaises(ValueError):
                dec = Decision(
                    decision_id=f"dec_no_ev_{state}",
                    title=f"No evidence for {state}",
                    state=state,
                    evidence_event_ids=[]
                )
                self.db.save_decision(dec)

        # Proposed with 0 evidence and evidence_assessment='insufficient' must SUCCEED
        dec_prop_ok = Decision(
            decision_id="dec_prop_zero_ev",
            title="Proposed zero evidence insufficient",
            state="proposed",
            evidence_assessment="insufficient",
            evidence_event_ids=[],
            repo="org/repo"
        )
        self.db.save_decision(dec_prop_ok)

        # Reopened with 0 evidence and evidence_assessment='insufficient' must SUCCEED
        dec_reopen_ok = Decision(
            decision_id="dec_reopen_zero_ev",
            title="Reopened zero evidence insufficient",
            state="reopened",
            evidence_assessment="insufficient",
            evidence_event_ids=[],
            repo="org/repo"
        )
        self.db.save_decision(dec_reopen_ok)

        # Proposed with 0 evidence but evidence_assessment='strong' must FAIL
        with self.assertRaises(ValueError):
            dec_prop_fail = Decision(
                decision_id="dec_prop_zero_ev_fail",
                title="Proposed zero evidence strong",
                state="proposed",
                evidence_assessment="strong",
                evidence_event_ids=[],
                repo="org/repo"
            )
            self.db.save_decision(dec_prop_fail)

    def test_legacy_unresolved_compatibility_alias(self):
        """Legacy 'unresolved' state is mapped to state='proposed' and evidence_assessment='insufficient'."""
        dec = Decision(
            decision_id="dec_legacy_unresolved",
            title="Legacy unresolved decision",
            state="unresolved",
            evidence_event_ids=[],
            repo="org/repo"
        )
        self.assertEqual(dec.state, "proposed")
        self.assertEqual(dec.evidence_assessment, "insufficient")
        self.db.save_decision(dec)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state, evidence_assessment FROM decisions WHERE decision_id = 'dec_legacy_unresolved'")
            row = cursor.fetchone()
            self.assertEqual(row["state"], "proposed")
            self.assertEqual(row["evidence_assessment"], "insufficient")

    def test_migration_001_on_pre_v2_db_copy(self):
        """Runs migration 001 on a copy of pre_v2 backup, asserting zero data loss and foreign_key_check empty."""
        backup_path = os.path.join("backups", "context_intelligence.pre_v2.db")
        if not os.path.exists(backup_path):
            self.skipTest(f"Pre-v2 backup not found at {backup_path}; skipping.")

        copy_path = os.path.join(self.tmp_dir.name, "pre_v2_copy.db")
        shutil.copyfile(backup_path, copy_path)

        # Inspect pre-migration counts
        pre_conn = sqlite3.connect(copy_path)
        pre_conn.row_factory = sqlite3.Row
        cur = pre_conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM decisions")
        pre_decisions_count = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM events")
        pre_events_count = cur.fetchone()["c"]
        pre_conn.close()

        # Run migration runner
        mig_conn = sqlite3.connect(copy_path)
        mig_conn.row_factory = sqlite3.Row
        try:
            results = run_migrations(mig_conn, dry_run=False)

            cur = mig_conn.cursor()
            # Foreign key check must be completely empty
            cur.execute("PRAGMA foreign_key_check;")
            fk_violations = cur.fetchall()
            self.assertEqual(len(fk_violations), 0, f"PRAGMA foreign_key_check reported violations: {fk_violations}")

            # Row counts must equal exactly
            cur.execute("SELECT COUNT(*) AS c FROM decisions")
            post_decisions_count = cur.fetchone()["c"]
            self.assertEqual(post_decisions_count, pre_decisions_count)

            cur.execute("SELECT COUNT(*) AS c FROM events")
            post_events_count = cur.fetchone()["c"]
            self.assertEqual(post_events_count, pre_events_count)

            # Check that columns evidence_assessment and freshness exist
            cur.execute("PRAGMA table_info(decisions)")
            col_names = {r["name"] for r in cur.fetchall()}
            self.assertIn("evidence_assessment", col_names)
            self.assertIn("freshness", col_names)

            # Check that zero decisions have state 'unresolved'
            cur.execute("SELECT COUNT(*) AS c FROM decisions WHERE state = 'unresolved'")
            self.assertEqual(cur.fetchone()["c"], 0)
        finally:
            mig_conn.close()


if __name__ == "__main__":
    unittest.main()
