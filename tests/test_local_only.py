"""
Unit and Integration Tests for Local-Only Mode (Step 5.1)
Verifies that when CIF_LOCAL_ONLY=1:
1. LLM client is disabled and returns False/None.
2. Network ingestion calls raise RuntimeError.
3. Ingesting local repository folders still works cleanly.
4. API endpoint /api/ingest-repo rejects remote targets with 403.
"""
import os
import tempfile
import unittest
from backend.db import Database
from backend.engine.llm_client import LLMClient
from backend.ingestion.live_github import LiveGitHubIngestor
from backend.api import APIHandler


class TestLocalOnlyMode(unittest.TestCase):
    def setUp(self):
        self.old_local_only = os.environ.get("CIF_LOCAL_ONLY")
        self.old_llm_key = os.environ.get("CIF_LLM_API_KEY")
        self.old_llm_model = os.environ.get("CIF_LLM_MODEL")

    def tearDown(self):
        if self.old_local_only is not None:
            os.environ["CIF_LOCAL_ONLY"] = self.old_local_only
        else:
            os.environ.pop("CIF_LOCAL_ONLY", None)

        if self.old_llm_key is not None:
            os.environ["CIF_LLM_API_KEY"] = self.old_llm_key
        else:
            os.environ.pop("CIF_LLM_API_KEY", None)

        if self.old_llm_model is not None:
            os.environ["CIF_LLM_MODEL"] = self.old_llm_model
        else:
            os.environ.pop("CIF_LLM_MODEL", None)

    def test_llm_client_disabled_in_local_only_mode(self):
        """Verifies LLMClient is deactivated when CIF_LOCAL_ONLY=1 even with configured keys."""
        os.environ["CIF_LOCAL_ONLY"] = "1"
        os.environ["CIF_LLM_API_KEY"] = "sk-test-key-12345678"
        os.environ["CIF_LLM_MODEL"] = "gpt-4o"

        client = LLMClient()
        self.assertTrue(client.is_local_only())
        self.assertFalse(client.available(), "LLMClient must report available() == False in local-only mode")
        
        # complete_json must return None without making any network attempt
        res = client.complete_json("Extract decisions from this diff")
        self.assertIsNone(res, "complete_json must return None in local-only mode")

    def test_live_github_network_calls_blocked(self):
        """Verifies that network ingestion calls raise RuntimeError when CIF_LOCAL_ONLY=1."""
        os.environ["CIF_LOCAL_ONLY"] = "1"
        temp_dir = tempfile.TemporaryDirectory()
        db = Database(os.path.join(temp_dir.name, "test.db"))
        ingestor = LiveGitHubIngestor(db)

        # Network requests must raise RuntimeError
        with self.assertRaises(RuntimeError) as ctx:
            ingestor._make_request("/repos/octocat/Hello-World")
        self.assertIn("Network ingestion disabled in local-only mode", str(ctx.exception))

        with self.assertRaises(RuntimeError):
            ingestor.fetch_commits("octocat/Hello-World")

        temp_dir.cleanup()

    def test_local_folder_ingestion_works_in_local_only_mode(self):
        """Verifies that ingesting a local repository directory still functions when CIF_LOCAL_ONLY=1."""
        os.environ["CIF_LOCAL_ONLY"] = "1"
        temp_dir = tempfile.TemporaryDirectory()
        db = Database(os.path.join(temp_dir.name, "test.db"))
        ingestor = LiveGitHubIngestor(db)

        # Create a small local repo directory structure
        repo_dir = os.path.join(temp_dir.name, "sample_repo")
        os.makedirs(os.path.join(repo_dir, "docs", "adr"), exist_ok=True)
        adr_path = os.path.join(repo_dir, "docs", "adr", "adr_001.md")
        with open(adr_path, "w", encoding="utf-8") as f:
            f.write("# 1. Use SQLite for Local Storage\n\n## Status\nAccepted\n\n## Context\nOffline storage needed.\n\n## Decision\nUse SQLite.\n\n## Consequences\nZero config.")

        # Ingestion of local folder should succeed completely
        stats = ingestor.ingest_local_repository(repo_dir, clear_existing=True)
        self.assertGreater(stats.get("decisions_extracted", 0), 0)

        # Verify event saved in database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as c FROM events WHERE source_type = 'adr'")
            self.assertEqual(cursor.fetchone()["c"], 1)

        temp_dir.cleanup()

    def test_api_ingest_repo_rejects_remote_in_local_only_mode(self):
        """Verifies POST /api/ingest-repo returns 403 when remote repo requested in local-only mode."""
        os.environ["CIF_LOCAL_ONLY"] = "1"
        temp_dir = tempfile.TemporaryDirectory()
        db = Database(os.path.join(temp_dir.name, "test.db"))
        api = APIHandler(db)

        res = api.handle_post("/api/ingest-repo", {"repo": "owner/remote-repo-does-not-exist-on-disk"})
        self.assertEqual(res.get("status"), "error")
        self.assertEqual(res.get("status_code"), 403)
        self.assertIn("Network ingestion disabled in local-only mode", res.get("message", ""))

        temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
