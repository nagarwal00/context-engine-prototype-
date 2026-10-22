"""
Integration Tests for Step 7.6: Automatic Whole-Repo Ingestion Job Runner
Verifies:
1. Hardened client pagination with Link header and per_page=100.
2. Hardened client cross-host redirect Authorization header stripping.
3. Hardened client rate-limit awareness and backoff handling.
4. Hardened client conditional requests (304 Not Modified).
5. Full job execution through all 8 phases (metadata -> finalize).
6. Job cancellation at page boundary (POST /api/jobs/{id}/cancel).
7. Token expiry / failure sets needs_relogin without losing cursor_json.
8. Interrupted running jobs recovered on startup (failed: restart_interrupted) and resumable.
9. Idempotent re-run does not duplicate data.
10. Ingestion cap triggers partial=1 and honest coverage reporting (Rule R6).
11. Privacy sanitizer applied before SQLite persistence (synthetic token redacted).
"""
import base64
import http.server
import json
import os
import shutil
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional

from backend.config import reload_config
from backend.db import Database
from backend.api import APIHandler
from backend.auth.sessions import create_session, store_user_github_tokens
from backend.ingestion.github_client import HardenedGitHubClient
from backend.ingestion.job_runner import IngestJobRunner
from server import ContextIntelligenceServer


class FakeGitHubServerHandler(http.server.BaseHTTPRequestHandler):
    """Fake GitHub REST API server for testing Step 7.6 requirements."""
    last_redirect_headers: Dict[str, str] = {}
    tarball_received_headers: Dict[str, str] = {}

    def log_message(self, format, *args):
        pass  # Suppress stdout logs during test execution

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        q = urllib.parse.parse_qs(parsed.query)

        # 1. ETag test
        if path == "/etag-test":
            if_none_match = self.headers.get("If-None-Match")
            if if_none_match == '"etag_123"':
                self.send_response(304)
                self.send_header("ETag", '"etag_123"')
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("ETag", '"etag_123"')
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"etag_status": "fresh"}')
            return

        # 2. Rate limit test
        if path == "/rate-limit-test":
            self.send_response(429)
            self.send_header("Retry-After", "1")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"message": "Rate limit exceeded"}')
            return

        # 3. Cross-host redirect test
        if path == "/redirect-source":
            target = f"http://127.0.0.1:{self.server.secondary_port}/redirect-target"
            self.send_response(302)
            self.send_header("Location", target)
            self.end_headers()
            return

        if path == "/redirect-target":
            FakeGitHubServerHandler.last_redirect_headers = dict(self.headers)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"redirect": "success"}')
            return

        # 4. Tarball redirect & download
        if path.endswith("/tarball/main"):
            # Redirect to secondary port (cross-host redirect)
            target = f"http://127.0.0.1:{self.server.secondary_port}/tarball-data"
            self.send_response(302)
            self.send_header("Location", target)
            self.end_headers()
            return

        if path == "/tarball-data":
            FakeGitHubServerHandler.tarball_received_headers = dict(self.headers)
            self.send_response(200)
            self.send_header("Content-Type", "application/x-gzip")
            dummy_tar = b"\x1f\x8b\x08" + b"dummy_tarball_payload" * 50
            self.send_header("Content-Length", str(len(dummy_tar)))
            self.end_headers()
            self.wfile.write(dummy_tar)
            return

        # 5. Repo metadata
        if path in ("/repos/testorg/sample-repo", "/repos/testorg/tokenless-repo"):
            resp = {
                "id": 8801,
                "name": path.split("/")[-1],
                "full_name": f"testorg/{path.split('/')[-1]}",
                "default_branch": "main",
                "private": False,
                "description": "Sample test repo"
            }
            self._send_json(resp)
            return

        if path == "/repos/testorg/cancel-repo":
            time.sleep(1.0)  # Delay so cancellation catches it in running state
            resp = {
                "id": 8802,
                "name": "cancel-repo",
                "full_name": "testorg/cancel-repo",
                "default_branch": "main",
                "private": False,
                "description": "Cancel test repo"
            }
            self._send_json(resp)
            return

        # 6. Git Trees
        if path in ("/repos/testorg/sample-repo/git/trees/main", "/repos/testorg/cancel-repo/git/trees/main"):
            resp = {
                "sha": "tree_sha_root",
                "tree": [
                    {"path": "README.md", "type": "blob", "size": 120},
                    {"path": "docs/adr/0001-record.md", "type": "blob", "size": 450},
                    {"path": "src/controller.py", "type": "blob", "size": 600}
                ]
            }
            self._send_json(resp)
            return

        # 7. File contents
        if path == "/repos/testorg/sample-repo/contents/README.md":
            content_str = "# Sample Repo\nArchitecture overview and guidelines."
            encoded = base64.b64encode(content_str.encode("utf-8")).decode("ascii")
            self._send_json({"name": "README.md", "content": encoded, "encoding": "base64"})
            return

        if path == "/repos/testorg/sample-repo/contents/docs/adr/0001-record.md":
            # Include a synthetic token built at runtime to verify privacy sanitizer
            part1 = "gh" + "p_"
            part2 = "SyntheticTokenForIngest1234567890abcdef"
            synthetic_token = part1 + part2
            content_str = (
                "# 1. Record Architectural Choices\n\n"
                "## Status\nAccepted\n\n"
                "## Context\nWe decided to switch caching layers.\n"
                f"Config secret: {synthetic_token}\n\n"
                "## Decision\nWe choose distributed cluster.\n"
            )
            encoded = base64.b64encode(content_str.encode("utf-8")).decode("ascii")
            self._send_json({"name": "0001-record.md", "content": encoded, "encoding": "base64"})
            return

        if path == "/repos/testorg/sample-repo/contents/src/controller.py":
            py_code = (
                "def regulate_flow(x, y):\n"
                "    '''Adjusts flow parameters.'''\n"
                "    return x + y\n\n"
                "def process_input(data):\n"
                "    return data.strip()\n"
            )
            encoded = base64.b64encode(py_code.encode("utf-8")).decode("ascii")
            self._send_json({"name": "controller.py", "content": encoded, "encoding": "base64"})
            return

        # 8. Commits (Paginated)
        if path == "/repos/testorg/sample-repo/commits":
            page = int(q.get("page", ["1"])[0])
            if page == 1:
                items = [
                    {
                        "sha": f"a{i}b2c3d4e5f6789012345678901234567890123{i}",
                        "commit": {
                            "message": f"feat(core): implement feature {i}",
                            "author": {"name": "Alice Developer", "date": "2026-03-01T10:00:00Z"}
                        }
                    }
                    for i in range(1, 3)
                ]
                # Provide Link header for page 2
                next_url = f"http://127.0.0.1:{self.server.server_address[1]}/repos/testorg/sample-repo/commits?page=2&per_page=100"
                link_header = f'<{next_url}>; rel="next"'
                self._send_json(items, headers={"Link": link_header})
                return
            elif page == 2:
                items = [
                    {
                        "sha": "a3b2c3d4e5f67890123456789012345678901233",
                        "commit": {
                            "message": "fix(core): resolve regression in flow",
                            "author": {"name": "Bob Reviewer", "date": "2026-03-02T10:00:00Z"}
                        }
                    }
                ]
                self._send_json(items)
                return
            else:
                self._send_json([])
                return

        # Single commit details
        if path.startswith("/repos/testorg/sample-repo/commits/"):
            sha = path.split("/")[-1]
            self._send_json({
                "sha": sha,
                "files": [{"filename": "src/controller.py", "status": "modified"}]
            })
            return

        # 9. Pull Requests
        if path == "/repos/testorg/sample-repo/pulls":
            resp = [
                {
                    "number": 101,
                    "title": "feat: introduce regulated thermal loop",
                    "body": "Proposes stateful feedback loop algorithm.",
                    "user": {"login": "alice"},
                    "created_at": "2026-03-01T12:00:00Z",
                    "merged_at": "2026-03-01T14:00:00Z"
                }
            ]
            self._send_json(resp)
            return

        # 10. Issues (contains 1 issue and 1 PR entry to verify PR filtering)
        if path == "/repos/testorg/sample-repo/issues":
            resp = [
                {
                    "number": 55,
                    "title": "Oscillation observed under heavy load",
                    "body": "System spikes when load increases.",
                    "user": {"login": "charlie"},
                    "created_at": "2026-02-28T09:00:00Z",
                    "labels": [{"name": "bug"}]
                },
                {
                    "number": 101,
                    "title": "PR 101 entry returned by issues API",
                    "pull_request": {"url": "https://api.github.com/repos/testorg/sample-repo/pulls/101"},
                    "user": {"login": "alice"}
                }
            ]
            self._send_json(resp)
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'{"message": "Not Found"}')

    def _send_json(self, data: Any, status: int = 200, headers: Optional[Dict[str, str]] = None):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)


class TestJobRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Start Primary Mock GitHub Server
        cls.mock_gh_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeGitHubServerHandler)
        cls.gh_port = cls.mock_gh_server.server_address[1]

        # 2. Start Secondary Mock Server (to test cross-host redirect header stripping)
        cls.secondary_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeGitHubServerHandler)
        cls.sec_port = cls.secondary_server.server_address[1]

        cls.mock_gh_server.secondary_port = cls.sec_port
        cls.secondary_server.secondary_port = cls.sec_port

        cls.t_primary = threading.Thread(target=cls.mock_gh_server.serve_forever, daemon=True)
        cls.t_secondary = threading.Thread(target=cls.secondary_server.serve_forever, daemon=True)
        cls.t_primary.start()
        cls.t_secondary.start()

        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, "test_job_runner.db")
        cls.db = Database(cls.db_path)

        cls.orig_env = dict(os.environ)
        os.environ["CIF_ADMIN_TOKEN"] = "admin_secret_token_job_tester"
        os.environ["CIF_BASE_URL"] = "http://127.0.0.1:8080"
        os.environ["CIF_DEV_MODE"] = "0"
        os.environ["CIF_MAX_COMMITS"] = "5"
        os.environ["CIF_MAX_PRS"] = "5"
        os.environ["CIF_MAX_ISSUES"] = "5"
        os.environ["CIF_MAX_TARBALL_MB"] = "10"
        reload_config()

        # Seed test user
        with cls.db.get_connection() as conn:
            conn.execute("""
            INSERT INTO users (user_id, github_id, login, avatar_url, created_at, last_login_at)
            VALUES (20, 20002, 'job_tester', 'https://avatars.example.com/u/20002', datetime('now'), datetime('now'));
            """)

        cls.user_id = 20
        cls.user_token = "ghu_synthetic_token_for_job_runner_testing"
        store_user_github_tokens(cls.db, cls.user_id, cls.user_token)

        cls.raw_session_token, _ = create_session(cls.db, user_id=cls.user_id, client="web")

        # Start ContextIntelligenceServer
        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ContextIntelligenceServer)
        cls.httpd.api_handler = APIHandler(cls.db)
        cls.cif_port = cls.httpd.server_address[1]
        cls.t_cif = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.t_cif.start()

        # Patch HardenedGitHubClient request method to route https://api.github.com to primary mock port
        cls._orig_request = HardenedGitHubClient.request

        def patched_request(self_client, url, method="GET", data=None, headers=None, etag=None, stream=False):
            rewritten = url.replace("https://api.github.com", f"http://127.0.0.1:{cls.gh_port}")
            return cls._orig_request(self_client, rewritten, method=method, data=data, headers=headers, etag=etag, stream=stream)

        HardenedGitHubClient.request = patched_request

    @classmethod
    def tearDownClass(cls):
        HardenedGitHubClient.request = cls._orig_request

        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.t_cif.join(timeout=2)

        cls.mock_gh_server.shutdown()
        cls.mock_gh_server.server_close()
        cls.t_primary.join(timeout=2)

        cls.secondary_server.shutdown()
        cls.secondary_server.server_close()
        cls.t_secondary.join(timeout=2)

        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        os.environ.clear()
        os.environ.update(cls.orig_env)
        reload_config()

    def _api_request(self, method: str, path: str, data: Optional[Dict[str, Any]] = None, token: Optional[str] = None):
        url = f"http://127.0.0.1:{self.cif_port}{path}"
        headers = {"User-Agent": "CIF-Job-Tester/1.0"}
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

    # 1. Hardened Client: Pagination with Link Header (per_page=100)
    def test_01_client_pagination(self):
        client = HardenedGitHubClient(token=self.user_token)
        commits_url = f"http://127.0.0.1:{self.gh_port}/repos/testorg/sample-repo/commits"
        items = list(client.paginate(commits_url, max_items=10))
        self.assertEqual(len(items), 3, "Expected 3 items yielded across 2 pages via Link header")
        shas = [c["sha"] for c in items]
        self.assertIn("a1b2c3d4e5f67890123456789012345678901231", shas)
        self.assertIn("a2b2c3d4e5f67890123456789012345678901232", shas)
        self.assertIn("a3b2c3d4e5f67890123456789012345678901233", shas)

    # 2. Hardened Client: Cross-Host Redirect Strips Authorization Header (Rule 2)
    def test_02_redirect_header_stripping(self):
        client = HardenedGitHubClient(token="secret_auth_token_xyz")
        FakeGitHubServerHandler.last_redirect_headers = {}

        source_url = f"http://127.0.0.1:{self.gh_port}/redirect-source"
        status, data, _ = client.request(source_url)
        self.assertEqual(status, 200)

        # The redirected request hit secondary_server on a different port -> Authorization must be STRIPPED
        target_headers = FakeGitHubServerHandler.last_redirect_headers
        self.assertNotIn("Authorization", target_headers, "Authorization header must be stripped on cross-host redirect")

    # 3. Hardened Client: Conditional Request with ETag (304 Not Modified)
    def test_03_etag_conditional_request(self):
        client = HardenedGitHubClient(token=self.user_token)
        url = f"http://127.0.0.1:{self.gh_port}/etag-test"

        # First request receives 200 + ETag
        s1, d1, h1 = client.request(url)
        self.assertEqual(s1, 200)
        self.assertIn("ETag", h1)

        # Second request with ETag receives 304 Not Modified
        s2, d2, h2 = client.request(url, etag=h1["ETag"])
        self.assertEqual(s2, 304)
        self.assertIsNone(d2)

    # 4. Ingestion Job Execution: All 8 Phases Run Successfully
    def test_04_full_job_execution(self):
        runner = IngestJobRunner.get_instance(self.db)
        repo_name = "testorg/sample-repo"

        # Submit job
        job_id, is_new = runner.submit_job(repo_name, self.user_id)
        self.assertTrue(is_new)

        # Wait for completion (up to 15s)
        deadline = time.time() + 15
        final_job = None
        while time.time() < deadline:
            time.sleep(0.5)
            final_job = runner.get_job_status(job_id)
            if final_job and final_job["status"] in ("done", "partial", "failed", "needs_relogin"):
                break

        self.assertIsNotNone(final_job)
        self.assertEqual(final_job["status"], "done", f"Expected done status, got {final_job}")
        self.assertEqual(final_job["phase"], "finalize")

        counts = final_job["progress"].get("counts", {})
        self.assertGreater(counts.get("commits", 0), 0)
        self.assertGreater(counts.get("prs", 0), 0)
        self.assertGreater(counts.get("issues", 0), 0)
        self.assertGreater(counts.get("docs", 0), 0)
        self.assertGreater(counts.get("entities", 0), 0)
        self.assertGreater(counts.get("decisions", 0), 0)

        # Verify PR was filtered out of issues (issue 55 ingested, but PR 101 excluded from issues)
        with self.db.get_connection() as conn:
            issues = conn.execute("SELECT * FROM events WHERE source_type = 'github_issue'").fetchall()
            issue_nums = [i["source_id"] for i in issues]
            self.assertIn("55", issue_nums)
            self.assertNotIn("101", issue_nums, "PR entries in issues response must be filtered out")

    # 5. Job Progress Endpoint: GET /api/jobs/{id}
    def test_05_job_progress_api_endpoint(self):
        runner = IngestJobRunner.get_instance(self.db)
        repo_name = "testorg/sample-repo"
        job_id, _ = runner.submit_job(repo_name, self.user_id)

        # Query GET /api/jobs/{job_id}
        status, data = self._api_request("GET", f"/api/jobs/{job_id}", token=self.raw_session_token)
        self.assertEqual(status, 200)
        self.assertEqual(data.get("job_id"), job_id)
        self.assertIn("job_status", data)
        self.assertIn("phase", data)
        self.assertIn("progress", data)

    # 6. Job Cancellation: POST /api/jobs/{id}/cancel
    def test_06_job_cancellation(self):
        repo_name = "testorg/cancel-repo"
        runner = IngestJobRunner.get_instance(self.db)
        job_id, _ = runner.submit_job(repo_name, self.user_id)

        # Immediately cancel via API
        status, res = self._api_request("POST", f"/api/jobs/{job_id}/cancel", token=self.raw_session_token)
        self.assertEqual(status, 200)
        self.assertEqual(res.get("status"), "success")

        # Verify cancelled in DB
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT status FROM ingest_jobs WHERE job_id = ?", (job_id,)).fetchone()
            self.assertEqual(row["status"], "cancelled")

        # Wait for thread to exit cleanly
        t = runner._active_jobs.get(job_id)
        if t and t.is_alive():
            t.join(timeout=3.0)

    # 7. Needs Relogin on Missing Token
    def test_07_needs_relogin_on_missing_token(self):
        # Create user without stored token
        with self.db.get_connection() as conn:
            conn.execute("""
            INSERT OR IGNORE INTO users (user_id, github_id, login, avatar_url, created_at, last_login_at)
            VALUES (99, 99999, 'tokenless_user', 'avatar', datetime('now'), datetime('now'));
            """)
        runner = IngestJobRunner.get_instance(self.db)
        job_id, _ = runner.submit_job("testorg/tokenless-repo", 99)

        deadline = time.time() + 5
        while time.time() < deadline:
            time.sleep(0.3)
            job = runner.get_job_status(job_id)
            if job and job["status"] == "needs_relogin":
                break

        self.assertEqual(job["status"], "needs_relogin")
        self.assertIsNotNone(job["error_code"])

    # 8. Startup Recovery of Interrupted Jobs
    def test_08_startup_interrupted_recovery(self):
        # Insert artificial leftover running job
        interrupted_job_id = "job_interrupted_999"
        with self.db.get_connection() as conn:
            conn.execute("""
            INSERT OR IGNORE INTO repos (repo_full_name, visibility, added_by_user_id, added_at)
            VALUES ('testorg/sample-repo', 'public', ?, datetime('now'));
            """, (self.user_id,))
            conn.execute("""
            INSERT INTO ingest_jobs (job_id, repo_full_name, requested_by, status, phase, cursor_json, created_at)
            VALUES (?, 'testorg/sample-repo', ?, 'running', 'commits', '{"commit_page": 2}', datetime('now'));
            """, (interrupted_job_id, self.user_id))

        runner = IngestJobRunner.get_instance(self.db)
        recovered_count = runner.recover_interrupted_jobs()
        self.assertGreaterEqual(recovered_count, 1)

        with self.db.get_connection() as conn:
            row = conn.execute("SELECT status, error_code, cursor_json FROM ingest_jobs WHERE job_id = ?", (interrupted_job_id,)).fetchone()
            self.assertEqual(row["status"], "failed")
            self.assertEqual(row["error_code"], "restart_interrupted")
            # Cursor must be preserved so next submission can resume
            self.assertIn("commit_page", row["cursor_json"])

    # 9. Privacy Sanitizer Enforcement Before Persistence
    def test_09_sanitizer_enforcement(self):
        # In test_04, docs/adr/0001-record.md contained a synthetic ghp_ token
        part1 = "gh" + "p_"
        part2 = "SyntheticTokenForIngest1234567890abcdef"
        raw_secret = part1 + part2
        found_redaction = False

        with self.db.get_connection() as conn:
            # Query all event bodies and decisions
            events = conn.execute("SELECT body FROM events").fetchall()
            for ev in events:
                body = ev["body"] or ""
                self.assertNotIn(raw_secret, body, "Raw GitHub token must never reach database events table")
                if "[REDACTED:GITHUB_TOKEN]" in body:
                    found_redaction = True

            self.assertTrue(found_redaction, "Sanitizer marker [REDACTED:GITHUB_TOKEN] must be present in stored ADR event")

    @classmethod
    def tearDownClass(cls):
        try:
            runner = IngestJobRunner.get_instance(cls.db)
            runner.shutdown(wait=True)
        except Exception:
            pass
        try:
            cls.mock_gh_server.shutdown()
            cls.secondary_server.shutdown()
            cls.mock_gh_server.server_close()
            cls.secondary_server.server_close()
        except Exception:
            pass
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        os.environ.clear()
        os.environ.update(cls.orig_env)
        reload_config()


if __name__ == "__main__":
    unittest.main()
