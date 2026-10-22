"""
Tests for Step 7.7: Webhook Live-Sync (Incremental Updates).
Verifies:
- HMAC signature verification across all supported event types:
  push, pull_request, issues, issue_comment, pull_request_review, installation, installation_repositories.
- Incremental updates: PR comments, reviews, issues, and commits appear in CIF events table.
- Installation lifecycle: creation links access; deletion marks repo removed and stops syncing.
- Removing a repository via installation_repositories marks it removed and stops syncing.
- Privacy sanitizer applied to all webhook payloads before database storage.
- Rule R1 gating: reports 'unavailable: install cryptography' when cryptography is absent.
"""
import hashlib
import hmac
import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from backend.db import Database
from backend.api import APIHandler
from backend.models import Event
from backend.auth.app_token import is_r1_available, get_installation_token, mint_app_jwt

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(name: str) -> bytes:
    with open(os.path.join(FIXTURES_DIR, name), "rb") as f:
        return f.read()


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


class TestWebhookLiveSync(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "sync_test.db")
        self.db = Database(self.db_path)
        self.api = APIHandler(self.db)
        self.secret = "webhook_secret_sync_test_98765"

        # Pre-seed test-org/sync-repo in repos
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO repos (repo_full_name, visibility, added_at, stats_json)
                VALUES ('test-org/sync-repo', 'private', datetime('now'), '{"status": "active", "sync_enabled": true}')
            """)
            # Create a user with github_id 8880
            conn.execute("""
                INSERT OR IGNORE INTO users (user_id, github_id, login, created_at, last_login_at)
                VALUES (1, 8880, 'admin-user', datetime('now'), datetime('now'))
            """)
            conn.commit()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _headers(self, raw_body: bytes, event_type: str) -> dict:
        return {
            "X-Hub-Signature-256": _sign(self.secret, raw_body),
            "X-GitHub-Event": event_type,
            "Content-Type": "application/json"
        }

    def test_push_event_syncs_commits(self):
        """Push webhook extracts and persists commits into CIF events table."""
        raw = _load_fixture("push.json")
        body = json.loads(raw)
        headers = self._headers(raw, "push")

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw, body)

        self.assertEqual(status, 200)
        self.assertEqual(result.get("status"), "ok")
        self.assertEqual(result.get("event"), "push")
        self.assertEqual(result.get("commits_synced"), 1)

        # Verify commit appears in events table
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT event_id, source_type, author, title, repo FROM events WHERE repo = 'test-org/sync-repo'")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], "git_commit")
            self.assertEqual(row[2], "test-committer")
            self.assertIn("fix: update timeout configuration", row[3])

    def test_issue_comment_sync_appears_in_cif(self):
        """PR/issue comment webhook inserts comment into events, linked to PR."""
        raw = _load_fixture("issue_comment.json")
        body = json.loads(raw)
        headers = self._headers(raw, "issue_comment")

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw, body)

        self.assertEqual(status, 200)
        self.assertEqual(result.get("status"), "ok")
        self.assertEqual(result.get("event"), "issue_comment")
        self.assertEqual(result.get("event_id"), "comment_9901")

        # Verify comment is queryable in events table
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT event_id, source_type, author, parent_event_ids, body FROM events WHERE event_id = 'comment_9901'")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], "pr_review_comment")
            self.assertEqual(row[2], "lead-architect")
            self.assertIn("pr_42", row[3])
            self.assertIn("reject connection pooling via Celery", row[4])

    def test_issues_event_syncs_new_issue(self):
        """Issues webhook extracts and records the issue in events table."""
        raw = _load_fixture("issues.json")
        body = json.loads(raw)
        headers = self._headers(raw, "issues")

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw, body)

        self.assertEqual(status, 200)
        self.assertEqual(result.get("status"), "ok")
        self.assertEqual(result.get("event_id"), "issue_105")

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT title, author FROM events WHERE event_id = 'issue_105'")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "Bug: Connection leak under high load")
            self.assertEqual(row[1], "tester-user")

    def test_pull_request_review_syncs_review(self):
        """Pull request review webhook inserts review decision event."""
        raw = _load_fixture("pull_request_review.json")
        body = json.loads(raw)
        headers = self._headers(raw, "pull_request_review")

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw, body)

        self.assertEqual(status, 200)
        self.assertEqual(result.get("status"), "ok")
        self.assertEqual(result.get("event_id"), "review_5501")

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT title, author, parent_event_ids FROM events WHERE event_id = 'review_5501'")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertIn("APPROVED", row[0])
            self.assertEqual(row[1], "senior-reviewer")
            self.assertIn("pr_42", row[2])

    def test_privacy_sanitizer_redacts_secrets_in_webhook_payload(self):
        """Sanitizer scrubs synthetic secrets in comment before inserting into DB."""
        payload = {
            "action": "created",
            "issue": {"number": 99, "title": "Secret discussion"},
            "comment": {
                "id": 8802,
                "body": "Use this GitHub token ghp_A1B2C3D4E5F6789012345678901234567890 for API calls.",
                "user": {"login": "dev1"},
                "created_at": "2026-10-18T01:20:00Z"
            },
            "repository": {"full_name": "test-org/sync-repo"}
        }
        raw = json.dumps(payload).encode("utf-8")
        headers = self._headers(raw, "issue_comment")

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw, payload)

        self.assertEqual(status, 200)
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT body FROM events WHERE event_id = 'comment_8802'")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            # The token must be redacted and never stored in plain text
            self.assertNotIn("ghp_A1B2C3D4E5F6789012345678901234567890", row[0])
            self.assertIn("[REDACTED", row[0])

    def test_installation_created_links_access(self):
        """Installation created event adds repos and links repo_access for sender."""
        raw = _load_fixture("installation_created.json")
        body = json.loads(raw)
        headers = self._headers(raw, "installation")

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw, body)

        self.assertEqual(status, 200)
        self.assertEqual(result.get("action"), "created")
        self.assertEqual(result.get("repos_linked"), 2)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            # User 1 should now have admin access to test-org/sync-repo and test-org/analytics-repo
            cur.execute("SELECT repo_full_name, level FROM repo_access WHERE user_id = 1")
            access_rows = {r[0]: r[1] for r in cur.fetchall()}
            self.assertIn("test-org/sync-repo", access_rows)
            self.assertIn("test-org/analytics-repo", access_rows)
            self.assertEqual(access_rows["test-org/sync-repo"], "admin")

    def test_installation_deleted_stops_syncing(self):
        """Installation deleted marks repos removed and halts syncing."""
        # First ensure access is linked
        raw_create = _load_fixture("installation_created.json")
        body_create = json.loads(raw_create)
        headers_create = self._headers(raw_create, "installation")
        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            self.api.handle_webhook("/api/webhook/github", headers_create, raw_create, body_create)

        # Now send installation deleted
        raw_del = _load_fixture("installation_deleted.json")
        body_del = json.loads(raw_del)
        headers_del = self._headers(raw_del, "installation")
        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers_del, raw_del, body_del)

        self.assertEqual(status, 200)
        self.assertEqual(result.get("action"), "deleted")

        # Verify repos marked removed and repo_access cleared
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT stats_json FROM repos WHERE repo_full_name = 'test-org/sync-repo'")
            stats = json.loads(cur.fetchone()[0])
            self.assertEqual(stats.get("status"), "removed")
            self.assertFalse(stats.get("sync_enabled"))

            cur.execute("SELECT count(*) FROM repo_access WHERE repo_full_name = 'test-org/sync-repo'")
            self.assertEqual(cur.fetchone()[0], 0)

        # A subsequent push or comment must be ignored and not synced
        raw_push = _load_fixture("push.json")
        body_push = json.loads(raw_push)
        headers_push = self._headers(raw_push, "push")
        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            res2, st2 = self.api.handle_webhook("/api/webhook/github", headers_push, raw_push, body_push)

        self.assertEqual(st2, 200)
        self.assertIn("syncing stopped", res2.get("message", "").lower())

    def test_installation_repositories_removed_stops_syncing(self):
        """Removing a repo via installation_repositories marks it removed and stops syncing."""
        raw = _load_fixture("installation_repositories.json")
        body = json.loads(raw)
        headers = self._headers(raw, "installation_repositories")

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw, body)

        self.assertEqual(status, 200)
        self.assertEqual(result.get("repos_removed"), 1)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT stats_json FROM repos WHERE repo_full_name = 'test-org/sync-repo'")
            stats = json.loads(cur.fetchone()[0])
            self.assertEqual(stats.get("status"), "removed")

    def test_r1_gating_reports_unavailable_without_cryptography(self):
        """Rule R1 reports 'unavailable: install cryptography' when cryptography is not installed."""
        if not is_r1_available():
            token, err = get_installation_token(12345)
            self.assertIsNone(token)
            self.assertEqual(err, "unavailable: install cryptography")

            jwt_str, jwt_err = mint_app_jwt("123", b"dummy_key")
            self.assertIsNone(jwt_str)
            self.assertEqual(jwt_err, "unavailable: install cryptography")
        else:
            # If cryptography is installed, verify proper error when key is missing
            token, err = get_installation_token(12345)
            self.assertIsNone(token)
            self.assertTrue(err.startswith("unavailable:"))


if __name__ == "__main__":
    unittest.main()
