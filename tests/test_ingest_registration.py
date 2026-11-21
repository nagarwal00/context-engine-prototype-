"""
Regression test: repositories ingested through POST /api/ingest-repo must be
registered in the repos table. Repo listing (/api/repos), repo filtering and
per-repo access checks all read that table, so an unregistered repository was
invisible in the dashboard even though its decisions had been stored.
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.api import APIHandler
from backend.db import Database

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_REPO = PROJECT_ROOT / "demo_sample_repo"


class IngestRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = Database(os.path.join(self.tmp, "ingest_reg.db"))
        self.api = APIHandler(self.db)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def repo_row(self, name):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM repos WHERE repo_full_name = ?", (name,)).fetchone()
        return dict(row) if row else None

    @unittest.skipUnless(SAMPLE_REPO.is_dir(), "demo_sample_repo not present")
    def test_ingested_repo_is_registered_and_listed(self):
        res = self.api.handle_post("/api/ingest-repo", {"repo": str(SAMPLE_REPO)})
        self.assertEqual(res["status"], "success", res)
        repo = res["data"]["repo"]
        self.assertEqual(repo, "local/demo_sample_repo")

        row = self.repo_row(repo)
        self.assertIsNotNone(row, "ingested repository must be registered in repos")
        self.assertEqual(row["visibility"], "private")
        self.assertIsNotNone(row["last_synced_at"])

        listed = self.api.handle_get("/api/repos", {}, headers={"X-CIF-Role": "admin"})
        self.assertEqual(listed["status"], "success")

    @unittest.skipUnless(SAMPLE_REPO.is_dir(), "demo_sample_repo not present")
    def test_reingest_updates_sync_time_without_duplicating(self):
        self.api.handle_post("/api/ingest-repo", {"repo": str(SAMPLE_REPO)})
        first = self.repo_row("local/demo_sample_repo")["last_synced_at"]
        self.api.handle_post("/api/ingest-repo", {"repo": str(SAMPLE_REPO)})
        with self.db.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM repos WHERE repo_full_name = ?",
                                 ("local/demo_sample_repo",)).fetchone()[0]
        self.assertEqual(count, 1)
        self.assertGreaterEqual(self.repo_row("local/demo_sample_repo")["last_synced_at"], first)


class IngestingUserAccessTests(unittest.TestCase):
    """The signed-in user who ingests a repository can read and review it."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = Database(os.path.join(self.tmp, "ingest_access.db"))
        self.api = APIHandler(self.db)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @unittest.skipUnless(SAMPLE_REPO.is_dir(), "demo_sample_repo not present")
    def test_ingesting_user_becomes_owner_and_reviewer(self):
        from backend.auth.repo_access import authorize_repo
        from backend.auth.sessions import create_session
        with self.db.get_connection() as conn:
            conn.execute("INSERT INTO users (github_id, login, created_at, last_login_at) "
                         "VALUES (424242, 'ingest-tester', '2026-11-21T00:00:00Z', '2026-11-21T00:00:00Z')")
            user_id = conn.execute("SELECT user_id FROM users WHERE login = 'ingest-tester'").fetchone()[0]
        token, _ = create_session(self.db, user_id)

        res = self.api.handle_post("/api/ingest-repo", {"repo": str(SAMPLE_REPO)},
                                   headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res["status"], "success", res)

        with self.db.get_connection() as conn:
            row = conn.execute("SELECT added_by_user_id FROM repos WHERE repo_full_name = ?",
                               ("local/demo_sample_repo",)).fetchone()
        self.assertEqual(row["added_by_user_id"], user_id)
        user = {"user_id": user_id, "login": "ingest-tester", "is_admin": False}
        for need in ("repo_read", "repo_review"):
            ok, status, msg = authorize_repo(self.db, user, "local/demo_sample_repo", need)
            self.assertTrue(ok, f"{need}: {status} {msg}")

        stranger = {"user_id": user_id + 1, "login": "someone-else", "is_admin": False}
        ok, status, _ = authorize_repo(self.db, stranger, "local/demo_sample_repo", "repo_review")
        self.assertFalse(ok, "other users must not gain access")


class RateLimitTests(unittest.TestCase):
    """A GitHub 403 must produce a clear error, never synthesized commits."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = Database(os.path.join(self.tmp, "rate_limit.db"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_403_raises_and_stores_nothing(self):
        from unittest import mock
        from backend.ingestion.live_github import LiveGitHubIngestor
        ingestor = LiveGitHubIngestor(self.db)
        with mock.patch.object(LiveGitHubIngestor, "fetch_commits",
                               return_value=(403, [], "API rate limit exceeded")):
            with self.assertRaises(ValueError) as ctx:
                ingestor.ingest_custom_repository("example-owner/example-repo")
        self.assertIn("GITHUB_TOKEN", str(ctx.exception))
        with self.db.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM events WHERE repo = ?",
                                 ("example-owner/example-repo",)).fetchone()[0]
        self.assertEqual(count, 0, "no commits may be fabricated on a rate-limit error")


if __name__ == "__main__":
    unittest.main()
