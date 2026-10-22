"""
Integration Tests for Step 7.5: Add-Repository Flow & Installation Discovery
Verifies:
- Unauthenticated requests to /api/github/repos, /api/repos, /api/repos/status are rejected (401).
- Tokens in request body are rejected with HTTP 400 (Rule R4 / Step 7.5).
- Missing or malformed repository slugs return HTTP 400.
- GET /api/github/repos discovers repositories where the App is installed.
- POST /api/repos for uninstalled repositories returns HTTP 409 with app_not_installed and install_url.
- POST /api/repos for installed repositories creates a repos row, a repo_access row, and an ingest_jobs row.
- Duplicate POST /api/repos reuses the existing active ingest job.
- GET /api/repos/status returns accurate sync and active job status.
"""
import http.server
import json
import os
import shutil
import ssl
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional

from backend.config import reload_config
from backend.db import Database
from backend.api import APIHandler
from backend.auth.sessions import create_session, store_user_github_tokens
from server import ContextIntelligenceServer


class MockGitHubAPIHandler(http.server.BaseHTTPRequestHandler):
    """Mock GitHub API server simulating user installations and repository endpoints."""
    def log_message(self, format, *args):
        pass  # Suppress console logging during tests

    def do_GET(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"message": "Bad credentials"}')
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/user/installations":
            resp = {
                "total_count": 1,
                "installations": [
                    {
                        "id": 501,
                        "account": {"login": "testorg", "type": "Organization"},
                        "app_slug": "context-intelligence-framework"
                    }
                ]
            }
            self._send_json(resp, 200)

        elif path == "/user/installations/501/repositories":
            resp = {
                "total_count": 2,
                "repositories": [
                    {
                        "id": 9001,
                        "name": "installed-repo",
                        "full_name": "testorg/installed-repo",
                        "private": False,
                        "visibility": "public"
                    },
                    {
                        "id": 9002,
                        "name": "private-installed",
                        "full_name": "testorg/private-installed",
                        "private": True,
                        "visibility": "private"
                    }
                ]
            }
            self._send_json(resp, 200)

        elif path == "/repos/testorg/installed-repo":
            self._send_json({"id": 9001, "full_name": "testorg/installed-repo", "private": False}, 200)

        elif path == "/repos/testorg/uninstalled-repo":
            # Repo exists on GitHub, but App is not installed on it
            self._send_json({"id": 9999, "full_name": "testorg/uninstalled-repo", "private": False}, 200)

        elif path == "/repos/testorg/nonexistent":
            self._send_json({"message": "Not Found"}, 404)

        else:
            self._send_json({"message": "Not Found"}, 404)

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class TestAddRepoFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Start mock GitHub API server
        cls.mock_gh_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), MockGitHubAPIHandler)
        cls.gh_port = cls.mock_gh_server.server_address[1]
        cls.gh_thread = threading.Thread(target=cls.mock_gh_server.serve_forever, daemon=True)
        cls.gh_thread.start()

        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, "test_add_repo.db")
        cls.db = Database(cls.db_path)

        cls.orig_env = dict(os.environ)
        cls.admin_token = "adm_test_secret_token_12345"
        os.environ["CIF_ADMIN_TOKEN"] = cls.admin_token
        os.environ["CIF_BASE_URL"] = "http://127.0.0.1:8080"
        os.environ["CIF_DEV_MODE"] = "0"
        os.environ["GITHUB_APP_SLUG"] = "context-intelligence-framework"
        reload_config()

        # Build test user in DB
        with cls.db.get_connection() as conn:
            conn.execute("""
            INSERT INTO users (user_id, github_id, login, avatar_url, created_at, last_login_at)
            VALUES (10, 10001, 'octotester', 'https://avatars.example.com/u/10001', datetime('now'), datetime('now'));
            """)

        # Store test user's GitHub access token
        cls.user_id = 10
        cls.gh_access_token = "ghu_synthetic_test_token_for_user_10"
        store_user_github_tokens(cls.db, cls.user_id, cls.gh_access_token)

        # Create CIF session
        cls.raw_session_token, _ = create_session(cls.db, user_id=cls.user_id, client="web")

        # Start ContextIntelligenceServer
        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ContextIntelligenceServer)
        cls.httpd.api_handler = APIHandler(cls.db)
        cls.cif_port = cls.httpd.server_address[1]
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()

        # Monkey-patch _github_get_json in repo_add to point to our mock GitHub server
        import backend.auth.repo_add as ra
        cls._orig_github_get_json = ra._github_get_json

        def mock_github_get_json(url, token, ssl_ctx=None):
            # Rewrite https://api.github.com to mock server URL
            mock_url = url.replace("https://api.github.com", f"http://127.0.0.1:{cls.gh_port}")
            req = urllib.request.Request(
                mock_url,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                method="GET"
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    body = resp.read().decode("utf-8")
                    return resp.getcode(), json.loads(body) if body else {}, dict(resp.headers)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8")
                try:
                    parsed = json.loads(body)
                except Exception:
                    parsed = {}
                return e.code, parsed, dict(e.headers)

        ra._github_get_json = mock_github_get_json

    @classmethod
    def tearDownClass(cls):
        import backend.auth.repo_add as ra
        ra._github_get_json = cls._orig_github_get_json

        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.server_thread.join(timeout=2)

        cls.mock_gh_server.shutdown()
        cls.mock_gh_server.server_close()
        cls.gh_thread.join(timeout=2)

        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        os.environ.clear()
        os.environ.update(cls.orig_env)
        reload_config()

    def _request(self, method: str, path: str, data: Optional[Dict[str, Any]] = None, token: Optional[str] = None):
        url = f"http://127.0.0.1:{self.cif_port}{path}"
        headers = {"User-Agent": "CIF-Test/1.0"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req_body = json.dumps(data).encode("utf-8") if data is not None else None
        if req_body is not None:
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=req_body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read().decode("utf-8")
                return resp.getcode(), json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            return e.code, parsed

    # 1. Unauthenticated Requests Blocked (401)
    def test_01_unauthenticated_requests_blocked(self):
        status, _ = self._request("GET", "/api/github/repos")
        self.assertEqual(status, 401)

        status, _ = self._request("POST", "/api/repos", data={"repo": "testorg/installed-repo"})
        self.assertEqual(status, 401)

        status, _ = self._request("GET", "/api/repos/status?repo=testorg/installed-repo")
        self.assertEqual(status, 401)

    # 2. Token in Request Body Rejected (Rule R4 / Step 7.5 -> 400)
    def test_02_token_in_body_rejected(self):
        status1, res1 = self._request(
            "POST", "/api/repos",
            data={"repo": "testorg/installed-repo", "token": "ghp_forbidden"},
            token=self.raw_session_token
        )
        self.assertEqual(status1, 400)
        self.assertIn("Tokens or secrets must never be sent", res1.get("message", ""))

        status2, res2 = self._request(
            "POST", "/api/repos",
            data={"repo": "testorg/installed-repo", "access_token": "ghp_forbidden"},
            token=self.raw_session_token
        )
        self.assertEqual(status2, 400)

        status3, res3 = self._request(
            "POST", "/api/repos",
            data={"repo": "testorg/installed-repo", "github_token": "ghp_forbidden"},
            token=self.raw_session_token
        )
        self.assertEqual(status3, 400)

    # 3. Missing or Malformed Repository Format (400)
    def test_03_missing_or_malformed_repo_slug(self):
        status1, _ = self._request("POST", "/api/repos", data={}, token=self.raw_session_token)
        self.assertEqual(status1, 400)

        status2, _ = self._request("POST", "/api/repos", data={"repo": "not-a-valid-slug"}, token=self.raw_session_token)
        self.assertEqual(status2, 400)

    # 4. List User Installable Repositories (GET /api/github/repos)
    def test_04_list_installable_repos(self):
        status, data = self._request("GET", "/api/github/repos", token=self.raw_session_token)
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "success")
        self.assertIn("https://github.com/apps/context-intelligence-framework/installations/new", data.get("install_url"))

        repos = data.get("repos", [])
        self.assertEqual(len(repos), 2)
        full_names = [r["full_name"] for r in repos]
        self.assertIn("testorg/installed-repo", full_names)
        self.assertIn("testorg/private-installed", full_names)

        installed_repo = next(r for r in repos if r["full_name"] == "testorg/installed-repo")
        self.assertFalse(installed_repo["private"])
        self.assertFalse(installed_repo["added"])

        private_repo = next(r for r in repos if r["full_name"] == "testorg/private-installed")
        self.assertTrue(private_repo["private"])

    # 5. Add Uninstalled Repository Fails with 409 and install_url
    def test_05_add_uninstalled_repo_returns_409(self):
        status, data = self._request(
            "POST", "/api/repos",
            data={"repo": "testorg/uninstalled-repo"},
            token=self.raw_session_token
        )
        self.assertEqual(status, 409)
        self.assertEqual(data.get("error"), "app_not_installed")
        self.assertIn("install_url", data)
        self.assertIn("context-intelligence-framework/installations/new", data["install_url"])

    # 6. Add Installed Repository Succeeds and Creates Job
    def test_06_add_installed_repo_succeeds(self):
        status, data = self._request(
            "POST", "/api/repos",
            data={"repo": "testorg/installed-repo"},
            token=self.raw_session_token
        )
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("repo"), "testorg/installed-repo")
        self.assertEqual(data.get("visibility"), "public")
        self.assertTrue(data.get("job_id", "").startswith("job_"))

        job_id = data["job_id"]

        # Verify DB records created
        with self.db.get_connection() as conn:
            repo_row = conn.execute("SELECT * FROM repos WHERE repo_full_name = 'testorg/installed-repo'").fetchone()
            self.assertIsNotNone(repo_row)
            self.assertEqual(repo_row["added_by_user_id"], self.user_id)
            self.assertEqual(repo_row["visibility"], "public")

            access_row = conn.execute("SELECT * FROM repo_access WHERE repo_full_name = 'testorg/installed-repo' AND user_id = ?", (self.user_id,)).fetchone()
            self.assertIsNotNone(access_row)
            self.assertEqual(access_row["level"], "review")

            job_row = conn.execute("SELECT * FROM ingest_jobs WHERE job_id = ?", (job_id,)).fetchone()
            self.assertIsNotNone(job_row)
            self.assertEqual(job_row["status"], "queued")
            self.assertEqual(job_row["phase"], "metadata")

    # 7. Duplicate Add Reuses Active Job
    def test_07_duplicate_add_reuses_active_job(self):
        status, data = self._request(
            "POST", "/api/repos",
            data={"repo": "testorg/installed-repo"},
            token=self.raw_session_token
        )
        self.assertEqual(status, 200)
        first_job_id = data.get("job_id")

        # Second add call
        status2, data2 = self._request(
            "POST", "/api/repos",
            data={"repo": "testorg/installed-repo"},
            token=self.raw_session_token
        )
        self.assertEqual(status2, 200)
        self.assertEqual(data2.get("job_id"), first_job_id, "Duplicate add must reuse existing active ingest job")

    # 8. Repo Sync Status (GET /api/repos/status)
    def test_08_repo_status_endpoint(self):
        # Non-added repo
        s1, res1 = self._request("GET", "/api/repos/status?repo=testorg/nonexistent", token=self.raw_session_token)
        self.assertEqual(s1, 200)
        self.assertFalse(res1.get("added"))
        self.assertIsNone(res1.get("active_job"))

        # Added repo
        s2, res2 = self._request("GET", "/api/repos/status?repo=testorg/installed-repo", token=self.raw_session_token)
        self.assertEqual(s2, 200)
        self.assertTrue(res2.get("added"))
        self.assertEqual(res2.get("visibility"), "public")
        self.assertIsNotNone(res2.get("active_job"))
        self.assertEqual(res2["active_job"]["status"], "queued")
        self.assertEqual(res2["active_job"]["phase"], "metadata")


if __name__ == "__main__":
    unittest.main()
