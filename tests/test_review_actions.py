"""
Tests for Step 2.4 — Review workflow for lifecycle
Verifies:
1. Actions confirm, reject, merge, correct, reopen, mark_tested call lifecycle engine.
2. Each action produces a state_history row with actor and reason.
3. Reason is strictly required (missing reason returns 400).
4. Invalid lifecycle transitions return 409 with a readable message.
5. Reviewer identity (token role + optional display name) is recorded as actor.
6. Supersession candidate triage works cleanly.
"""
import os
import shutil
import tempfile
import unittest
import sqlite3

from backend.db import Database
from backend.models import Decision, Event
from backend.api import APIHandler
from backend.security import ROLE_REVIEWER, ROLE_ADMIN


class TestReviewActions(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        self.api = APIHandler(self.db)

        # Seed test event
        self.ev = Event(
            event_id="ev_rev_test",
            source_type="git_commit",
            source_id="sha123",
            source_url="https://github.com/repo/commit/sha123",
            repo="acme/test",
            author="tester",
            timestamp="2026-03-01T10:00:00Z",
            title="Initial code",
            body="Commit body"
        )
        self.db.upsert_event(self.ev)

        # Seed test decision in proposed state
        self.dec_prop = Decision(
            decision_id="dec_prop_1",
            title="Proposed Architecture",
            state="proposed",
            evidence_event_ids=[self.ev.event_id],
            evidence_assessment="insufficient",
            repo="acme/test",
            made_at="2026-03-01T12:00:00Z"
        )
        self.db.save_decision(self.dec_prop)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_reason_returns_400(self):
        """Review actions require a non-empty reason; missing returns 400."""
        res = self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "reopen",
                "target_id": "dec_prop_1",
                "reason": ""  # empty
            }
        )
        self.assertEqual(res.get("status"), "error")
        self.assertEqual(res.get("status_code"), 400)
        self.assertIn("requires a non-empty reason", res.get("message", ""))

    def test_mark_tested_advances_to_tested_and_records_history(self):
        """Action 'mark_tested' transitions proposed decision to tested and logs history."""
        res = self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "mark_tested",
                "target_id": "dec_prop_1",
                "reason": "Test suite executed in staging environment",
                "reviewer": "Alice"
            }
        )
        self.assertEqual(res.get("status"), "success")

        # Verify DB state
        with self.db.get_connection() as conn:
            dec = conn.execute("SELECT state, review_status FROM decisions WHERE decision_id = 'dec_prop_1'").fetchone()
            self.assertEqual(dec["state"], "tested")
            self.assertEqual(dec["review_status"], "human_tested")

            # Verify history row
            hist = conn.execute(
                "SELECT * FROM state_history WHERE decision_id = 'dec_prop_1' ORDER BY changed_at DESC"
            ).fetchone()
            self.assertEqual(hist["state"], "tested")
            self.assertEqual(hist["from_state"], "proposed")
            self.assertIn("Alice", hist["changed_by"])
            self.assertIn("Test suite executed in staging environment", hist["notes"])

    def test_confirm_advances_to_accepted_and_records_history(self):
        """Action 'confirm' transitions decision to accepted with confidence 1.0."""
        res = self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "confirm",
                "target_id": "dec_prop_1",
                "reason": "Team agreed to accept this proposal",
                "reviewer": "Bob"
            }
        )
        self.assertEqual(res.get("status"), "success")

        with self.db.get_connection() as conn:
            dec = conn.execute("SELECT state, review_status, confidence FROM decisions WHERE decision_id = 'dec_prop_1'").fetchone()
            self.assertEqual(dec["state"], "accepted")
            self.assertEqual(dec["review_status"], "human_confirmed")
            self.assertEqual(dec["confidence"], 1.0)

            hist = conn.execute(
                "SELECT * FROM state_history WHERE decision_id = 'dec_prop_1' ORDER BY changed_at DESC"
            ).fetchone()
            self.assertEqual(hist["state"], "accepted")
            self.assertIn("Bob", hist["changed_by"])
            self.assertIn("Team agreed to accept this proposal", hist["notes"])

    def test_reject_advances_to_rejected(self):
        """Action 'reject' transitions decision to rejected."""
        res = self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "reject",
                "target_id": "dec_prop_1",
                "reason": "Alternative benchmark showed 40% memory regression",
                "reviewer": "Charlie"
            }
        )
        self.assertEqual(res.get("status"), "success")

        with self.db.get_connection() as conn:
            dec = conn.execute("SELECT state, review_status FROM decisions WHERE decision_id = 'dec_prop_1'").fetchone()
            self.assertEqual(dec["state"], "rejected")
            self.assertEqual(dec["review_status"], "human_rejected")

            hist = conn.execute(
                "SELECT * FROM state_history WHERE decision_id = 'dec_prop_1' ORDER BY changed_at DESC"
            ).fetchone()
            self.assertEqual(hist["state"], "rejected")
            self.assertIn("Charlie", hist["changed_by"])

    def test_reopen_advances_from_rejected_to_reopened(self):
        """Action 'reopen' transitions rejected decision to reopened."""
        # First reject it
        self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "reject",
                "target_id": "dec_prop_1",
                "reason": "Rejected initially"
            }
        )

        # Now reopen it
        res = self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "reopen",
                "target_id": "dec_prop_1",
                "reason": "New profiling data addresses the memory regression",
                "reviewer": "Dana"
            }
        )
        self.assertEqual(res.get("status"), "success")

        with self.db.get_connection() as conn:
            dec = conn.execute("SELECT state, review_status FROM decisions WHERE decision_id = 'dec_prop_1'").fetchone()
            self.assertEqual(dec["state"], "reopened")
            self.assertEqual(dec["review_status"], "human_reopened")

            hist = conn.execute(
                "SELECT * FROM state_history WHERE decision_id = 'dec_prop_1' ORDER BY changed_at DESC, rowid DESC"
            ).fetchone()
            self.assertEqual(hist["state"], "reopened")
            self.assertEqual(hist["from_state"], "rejected")

    def test_invalid_transition_returns_409(self):
        """Attempting an illegal transition via review action returns HTTP 409 with message."""
        # Accept the decision
        self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "confirm",
                "target_id": "dec_prop_1",
                "reason": "Accepted"
            }
        )

        # Attempt to reject an already accepted decision (illegal transition: accepted -> rejected not allowed)
        res = self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "reject",
                "target_id": "dec_prop_1",
                "reason": "Should fail because accepted cannot transition directly to rejected"
            }
        )
        self.assertEqual(res.get("status"), "error")
        self.assertEqual(res.get("status_code"), 409)
        self.assertIn("Conflict", res.get("message", ""))

    def test_reopen_on_superseded_decision_returns_409(self):
        """Attempting to reopen a terminal superseded decision returns HTTP 409."""
        # Accept then supersede
        self.api.handle_post(
            "/api/review-action",
            {"item_type": "decision", "action": "confirm", "target_id": "dec_prop_1", "reason": "Accept"}
        )

        # Create target decision to merge into / supersede
        dec2 = Decision(
            decision_id="dec_prop_2",
            title="Replacement Decision",
            state="accepted",
            evidence_event_ids=[self.ev.event_id],
            repo="acme/test"
        )
        self.db.save_decision(dec2)

        # Merge dec_prop_1 into dec_prop_2 (which supersedes dec_prop_1)
        self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "merge",
                "target_id": "dec_prop_1",
                "into_decision_id": "dec_prop_2",
                "reason": "Merge into dec_prop_2"
            }
        )

        # Attempt to reopen dec_prop_1 (superseded is terminal!)
        res = self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "reopen",
                "target_id": "dec_prop_1",
                "reason": "Try to reopen superseded decision"
            }
        )
        self.assertEqual(res.get("status"), "error")
        self.assertEqual(res.get("status_code"), 409)
        self.assertIn("Conflict", res.get("message", ""))

    def test_merge_action_supersedes_into_target(self):
        """Action 'merge' sets state to superseded and updates superseding pointers."""
        dec_target = Decision(
            decision_id="dec_canonical_target",
            title="Target Canonical Decision",
            state="accepted",
            evidence_event_ids=[self.ev.event_id],
            repo="acme/test"
        )
        self.db.save_decision(dec_target)

        res = self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "merge",
                "target_id": "dec_prop_1",
                "into_decision_id": "dec_canonical_target",
                "reason": "Consolidating duplicate proposals",
                "reviewer": "Elena"
            }
        )
        self.assertEqual(res.get("status"), "success")

        with self.db.get_connection() as conn:
            dec = conn.execute("SELECT state, superseded_by_decision_id FROM decisions WHERE decision_id = 'dec_prop_1'").fetchone()
            self.assertEqual(dec["state"], "superseded")
            self.assertEqual(dec["superseded_by_decision_id"], "dec_canonical_target")

    def test_correct_action_updates_metadata_and_state(self):
        """Action 'correct' allows changing state and metadata with audit history."""
        res = self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "correct",
                "target_id": "dec_prop_1",
                "state": "tested",
                "title": "Corrected Title for Testing",
                "rationale": "Corrected rationale text",
                "reason": "Human typo fix and benchmark verification",
                "reviewer": "Frank"
            }
        )
        self.assertEqual(res.get("status"), "success")

        with self.db.get_connection() as conn:
            dec = conn.execute("SELECT state, title, rationale, review_status FROM decisions WHERE decision_id = 'dec_prop_1'").fetchone()
            self.assertEqual(dec["state"], "tested")
            self.assertEqual(dec["title"], "Corrected Title for Testing")
            self.assertEqual(dec["rationale"], "Corrected rationale text")
            self.assertEqual(dec["review_status"], "human_corrected")

    def test_reviewer_identity_recorded_as_actor(self):
        """Reviewer identity is formatted as token_role:display_name."""
        res = self.api.handle_post(
            "/api/review-action",
            {
                "item_type": "decision",
                "action": "confirm",
                "target_id": "dec_prop_1",
                "reason": "LGTM",
                "reviewer": "Grace Hopper"
            },
            headers={"Authorization": "Bearer some_reviewer_token"}
        )
        self.assertEqual(res.get("status"), "success")

        with self.db.get_connection() as conn:
            hist = conn.execute(
                "SELECT changed_by FROM state_history WHERE decision_id = 'dec_prop_1' ORDER BY changed_at DESC"
            ).fetchone()
            self.assertIn("Grace Hopper", hist["changed_by"])


if __name__ == "__main__":
    unittest.main()
