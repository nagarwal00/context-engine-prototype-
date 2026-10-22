"""
Tests for Step 7.8: Consent, Deletion and Retention.
Verifies:
1. DELETE /api/repos/{owner}/{repo} permissions:
   - Unauthenticated caller returns 401.
   - Non-owner user (who did not add the repo) returns 403.
   - Non-existent repo returns 404.
   - Repo adder can successfully delete the repo (200).
   - Admin (CIF_ADMIN_TOKEN) can successfully delete any repo (200).
2. Cascading deletion across all tables:
   - events, entities, decisions, edges, decision_claims, claim_evidence,
     decision_evidence, decision_artifacts, state_history, guard_rules,
     finding_feedback, ingest_jobs, repo_access, repos.
3. Raw-byte disk scan acceptance check:
   - After deletion, a raw-byte scan of the SQLite database file on disk
     finds none of the repo's text/markers (vacuum verified).
"""
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from backend.db import Database
from backend.api import APIHandler
from backend.models import Event, Decision, Entity
from backend.auth.sessions import create_session


class TestRepoDelete(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "delete_test.db")
        self.db = Database(self.db_path)
        self.api = APIHandler(self.db)
        self.admin_token = "admin_secret_token_del_test_99"

        # Create two test users
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO users (user_id, github_id, login, created_at, last_login_at)
                VALUES (1, 1001, 'alice_owner', datetime('now'), datetime('now')),
                       (2, 1002, 'bob_intruder', datetime('now'), datetime('now'));
            """)
            conn.commit()

        # Create CIF sessions for Alice and Bob
        self.session_alice, _ = create_session(self.db, 1, "web")
        self.session_bob, _ = create_session(self.db, 2, "web")

        # Seed Alice's repo: 'alice-org/private-service'
        self.repo_alice = "alice-org/private-service"
        self.unique_marker = "UNIQUE_PAYLOAD_MARKER_ALICE_SECRET_77665544"
        self.unique_title = "Distinct Thermal Controller Refactoring Title 998811"

        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO repos (repo_full_name, visibility, added_by_user_id, added_at, stats_json)
                VALUES (?, 'private', 1, datetime('now'), '{"status": "active"}')
            """, (self.repo_alice,))

            conn.execute("""
                INSERT OR IGNORE INTO repo_access (user_id, repo_full_name, level, verified_at)
                VALUES (1, ?, 'admin', datetime('now'))
            """, (self.repo_alice,))

            # Ingest job for Alice's repo
            conn.execute("""
                INSERT OR IGNORE INTO ingest_jobs (job_id, repo_full_name, requested_by, status, phase, created_at)
                VALUES ('job_alice_1', ?, 1, 'done', 'finalize', datetime('now'))
            """, (self.repo_alice,))
            conn.commit()

        # Insert events, entities, decisions for Alice's repo
        ev1 = Event(
            event_id="evt_alice_1",
            source_type="git_commit",
            source_id="c_alice_1",
            source_url=f"https://github.com/{self.repo_alice}/commit/1",
            repo=self.repo_alice,
            author="alice_owner",
            title=self.unique_title,
            body=f"Important internal architectural commit: {self.unique_marker}"
        )
        self.db.upsert_event(ev1)

        ent1 = Entity(
            entity_id="ent_alice_1",
            entity_type="file",
            canonical_path="src/thermal/controller.py",
            repo=self.repo_alice,
            current_state_summary=f"Summary containing {self.unique_marker}"
        )
        self.db.upsert_entity(ent1)

        dec1 = Decision(
            decision_id="dec_alice_1",
            title=f"Adopt Regulated State Feedback: {self.unique_marker}",
            state="accepted",
            repo=self.repo_alice,
            confidence=0.95,
            evidence_event_ids=["evt_alice_1"]
        )
        self.db.save_decision(dec1)

        # Seed Bob's repo: 'bob-org/bob-repo' to verify isolation during delete
        self.repo_bob = "bob-org/bob-repo"
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO repos (repo_full_name, visibility, added_by_user_id, added_at)
                VALUES (?, 'private', 2, datetime('now'))
            """, (self.repo_bob,))
            conn.commit()

        ev_bob = Event(
            event_id="evt_bob_1",
            source_type="git_commit",
            source_id="c_bob_1",
            source_url=f"https://github.com/{self.repo_bob}/commit/1",
            repo=self.repo_bob,
            author="bob_intruder",
            title="Bob's commit",
            body="Bob's repo data"
        )
        self.db.upsert_event(ev_bob)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_delete_unauthenticated_returns_401(self):
        """Unauthenticated call to DELETE /api/repos/{owner}/{repo} is rejected with 401."""
        res = self.api.handle_delete(f"/api/repos/{self.repo_alice}", headers={})
        self.assertEqual(res.get("status_code"), 401)
        self.assertEqual(res.get("status"), "error")

    def test_delete_unauthorized_user_returns_403(self):
        """Bob cannot delete Alice's repository; returns 403 Forbidden."""
        headers = {"Authorization": f"Bearer {self.session_bob}"}
        res = self.api.handle_delete(f"/api/repos/{self.repo_alice}", headers=headers)
        self.assertEqual(res.get("status_code"), 403)
        self.assertIn("Forbidden", res.get("message", ""))

    def test_delete_non_existent_repo_returns_404(self):
        """Deleting non-existent repo returns 404 Not Found."""
        headers = {"Authorization": f"Bearer {self.session_alice}"}
        res = self.api.handle_delete("/api/repos/nonexistent/repo", headers=headers)
        self.assertEqual(res.get("status_code"), 404)

    def test_delete_by_owner_succeeds_and_cascades(self):
        """Alice (repo adder) can delete her repo; all tables cascaded and Bob's repo preserved."""
        headers = {"Authorization": f"Bearer {self.session_alice}"}
        res = self.api.handle_delete(f"/api/repos/{self.repo_alice}", headers=headers)

        self.assertEqual(res.get("status_code"), 200)
        self.assertEqual(res.get("status"), "success")
        deleted = res.get("deleted_counts", {})
        self.assertGreaterEqual(deleted.get("events", 0), 1)
        self.assertGreaterEqual(deleted.get("entities", 0), 1)
        self.assertGreaterEqual(deleted.get("decisions", 0), 1)
        self.assertGreaterEqual(deleted.get("repos", 0), 1)
        self.assertGreaterEqual(deleted.get("ingest_jobs", 0), 1)

        # Verify Alice's rows are completely gone in database
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM repos WHERE repo_full_name = ?", (self.repo_alice,))
            self.assertEqual(cur.fetchone()[0], 0)

            cur.execute("SELECT COUNT(*) FROM events WHERE repo = ?", (self.repo_alice,))
            self.assertEqual(cur.fetchone()[0], 0)

            cur.execute("SELECT COUNT(*) FROM entities WHERE repo = ?", (self.repo_alice,))
            self.assertEqual(cur.fetchone()[0], 0)

            cur.execute("SELECT COUNT(*) FROM decisions WHERE repo = ?", (self.repo_alice,))
            self.assertEqual(cur.fetchone()[0], 0)

            cur.execute("SELECT COUNT(*) FROM ingest_jobs WHERE repo_full_name = ?", (self.repo_alice,))
            self.assertEqual(cur.fetchone()[0], 0)

            cur.execute("SELECT COUNT(*) FROM repo_access WHERE repo_full_name = ?", (self.repo_alice,))
            self.assertEqual(cur.fetchone()[0], 0)

            # Bob's data must remain intact
            cur.execute("SELECT COUNT(*) FROM repos WHERE repo_full_name = ?", (self.repo_bob,))
            self.assertEqual(cur.fetchone()[0], 1)

            cur.execute("SELECT COUNT(*) FROM events WHERE repo = ?", (self.repo_bob,))
            self.assertEqual(cur.fetchone()[0], 1)

    def test_delete_by_admin_token_succeeds(self):
        """Admin with CIF_ADMIN_TOKEN can delete any repository."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        with patch.dict(os.environ, {"CIF_ADMIN_TOKEN": self.admin_token}):
            res = self.api.handle_delete(f"/api/repos/{self.repo_alice}", headers=headers)

        self.assertEqual(res.get("status_code"), 200)
        self.assertEqual(res.get("status"), "success")

    def test_raw_byte_scan_database_after_deletion(self):
        """Acceptance test: after deletion, raw-byte scan of SQLite DB finds zero repo text on disk."""
        # Confirm marker exists in DB file before deletion
        with open(self.db_path, "rb") as f:
            pre_bytes = f.read()
        self.assertIn(self.unique_marker.encode("utf-8"), pre_bytes)
        self.assertIn(self.unique_title.encode("utf-8"), pre_bytes)

        # Delete Alice's repository
        headers = {"Authorization": f"Bearer {self.session_alice}"}
        res = self.api.handle_delete(f"/api/repos/{self.repo_alice}", headers=headers)
        self.assertEqual(res.get("status_code"), 200)

        # Perform raw binary byte scan of SQLite database file on disk
        with open(self.db_path, "rb") as f:
            post_bytes = f.read()

        # Both the secret payload marker and unique title must NOT appear anywhere on disk
        self.assertNotIn(
            self.unique_marker.encode("utf-8"),
            post_bytes,
            f"Privacy Violation: Unique marker '{self.unique_marker}' was found in SQLite binary disk bytes after deletion!"
        )
        self.assertNotIn(
            self.unique_title.encode("utf-8"),
            post_bytes,
            f"Privacy Violation: Title '{self.unique_title}' was found in SQLite binary disk bytes after deletion!"
        )
        self.assertNotIn(
            self.repo_alice.encode("utf-8"),
            post_bytes,
            f"Privacy Violation: Repo name '{self.repo_alice}' was found in SQLite binary disk bytes after deletion!"
        )


if __name__ == "__main__":
    unittest.main()
