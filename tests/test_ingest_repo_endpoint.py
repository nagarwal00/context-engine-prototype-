"""
POST /api/ingest-repo: real pipeline against a local server that answers like the GitHub REST API.

Regression tests for the 2026-11-24 report ("Endpoint not found: GET /api/ingest-repo" and
"400 Bad Request"): the route only accepts POST (a browser address bar sends GET, which must be
405, not 404), and every ingestion failure used to be HTTP 400 regardless of its cause.

The fake GitHub serves realistic JSON and headers only; all CIF code (HTTP client, error
classification, extraction, storage, API, server) runs unmodified. It does NOT prove that the real
github.com works — that is verified manually (see audit/INGEST_FIX_REPORT.md).
"""
import base64
import contextlib
import http.server
import json
import os
import sqlite3
import sys
import tempfile
import threading
import unittest
import urllib.parse
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import APIHandler
from backend.db import Database

PY_SOURCE = "def get_cached(key):\n    return redis_client.get(key)\n"
ADR = ("# ADR 0001: Use Redis for caching\n\n## Status\nAccepted\n\n## Context\nThe in-process cache in "
       "src/cache.py loses data on restart.\n\n## Decision\nWe decided to migrate caching to Redis.\n")


class FakeGitHub(http.server.BaseHTTPRequestHandler):
    """Answers like api.github.com for a handful of repositories."""
    remaining = "4999"

    def log_message(self, *args):
        pass

    def _send(self, status, payload, headers=None):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-RateLimit-Remaining", (headers or {}).get("X-RateLimit-Remaining", FakeGitHub.remaining))
        for k, v in (headers or {}).items():
            if k != "X-RateLimit-Remaining":
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path, query = url.path, urllib.parse.parse_qs(url.query)
        parts = path.strip("/").split("/")
        if len(parts) < 3 or parts[0] != "repos":
            return self._send(404, {"message": "Not Found"})
        owner, rest = parts[1], parts[3:]
        if owner == "missing":
            return self._send(404, {"message": "Not Found"})
        if owner == "limited":
            return self._send(403, {"message": "API rate limit exceeded for 127.0.0.1."},
                              {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "9999999999"})
        if owner == "empty" and rest == ["commits"]:
            return self._send(409, {"message": "Git Repository is empty."})
        if owner == "broken":
            return self._send(500, {"message": "Server Error"})
        if owner == "private":
            return self._send(404, {"message": "Not Found"})  # GitHub hides private repos without a token
        if owner == "lowbudget":
            FakeGitHub.remaining = "3"
        # ----- a healthy repository (owners "good" and "lowbudget") -----
        if not rest:
            return self._send(200, {"full_name": f"{owner}/{parts[2]}", "default_branch": "main"})
        if rest == ["commits"] and "path" in query:
            return self._send(200, [{"sha": "c" * 40, "commit": {"author": {"name": "Ada Architect",
                                                                            "date": "2025-02-01T10:00:00Z"}}}])
        if rest == ["commits"]:
            return self._send(200, [
                {"sha": "a" * 40, "commit": {"message": "We decided to migrate the cache to Redis instead of memcached",
                                             "author": {"name": "Ada Architect", "date": "2025-02-02T10:00:00Z"}}},
                {"sha": "b" * 40, "commit": {"message": "docs: fix typo in README",
                                             "author": {"name": "Bo Writer", "date": "2025-02-03T10:00:00Z"}}},
            ])
        if len(rest) == 2 and rest[0] == "commits":
            return self._send(200, {"files": [{"filename": "src/cache.py"}]})
        if rest[:3] == ["git", "trees", "main"]:
            return self._send(200, {"tree": [{"path": "src/cache.py", "type": "blob"},
                                             {"path": "docs/adr/0001-use-redis.md", "type": "blob"},
                                             {"path": "README.md", "type": "blob"}, {"path": "src", "type": "tree"}]})
        if rest == ["issues"]:
            return self._send(200, [{"number": 7, "title": "Cache misses after deploy",
                                     "body": "cache.py drops entries on restart", "user": {"login": "carol"},
                                     "created_at": "2025-01-20T09:00:00Z", "labels": []}])
        if rest and rest[0] == "contents":
            file_path = "/".join(rest[1:])
            text = PY_SOURCE if file_path.endswith(".py") else ADR
            return self._send(200, {"encoding": "base64", "content": base64.b64encode(text.encode()).decode()})
        return self._send(404, {"message": "Not Found"})


class IngestRepoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.github = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeGitHub)
        threading.Thread(target=cls.github.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.github.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.github.shutdown()
        cls.github.server_close()

    def setUp(self):
        FakeGitHub.remaining = "4999"
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "ingest.db")
        self.api = APIHandler(Database(self.path))
        patcher = mock.patch.dict(os.environ, {"CIF_GITHUB_API_BASE": self.base, "CIF_LOCAL_ONLY": "0",
                                               "GITHUB_TOKEN": "", "GH_TOKEN": ""})
        patcher.start()
        self.addCleanup(patcher.stop)

    def ingest(self, repo):
        return self.api.handle_post("/api/ingest-repo", {"repo": repo})

    def rows(self, sql, *args):
        with contextlib.closing(sqlite3.connect(self.path)) as c:
            return c.execute(sql, args).fetchall()

    # ---- success ------------------------------------------------------------------------
    def test_valid_repository_is_ingested_from_real_responses_only(self):
        res = self.ingest("https://github.com/good/repo")
        self.assertEqual(res["status"], "success", res)
        data = res["data"]
        self.assertEqual((data["repo"], data["commits_ingested"], data["issues_ingested"]), ("good/repo", 2, 1))
        self.assertFalse(data["partial"], data)
        self.assertGreaterEqual(data["decisions_extracted"], 2)   # Redis commit + ADR
        authors = {r[0] for r in self.rows("SELECT author FROM events WHERE repo = 'good/repo'")}
        self.assertTrue(authors <= {"ada_architect", "bo_writer", "carol", "Ada Architect", "Bo Writer"}, authors)
        self.assertFalse(self.rows("SELECT 1 FROM decisions WHERE title LIKE 'Initial Architecture%'"))
        self.assertFalse(self.rows("SELECT 1 FROM entities WHERE repo='good/repo' AND canonical_path='src/main.py'"))
        self.assertTrue(self.rows("SELECT 1 FROM entities WHERE canonical_path = 'src/cache.py::get_cached'"))
        adr = self.rows("SELECT author, substr(ts,1,10) FROM events WHERE source_type = 'adr'")
        self.assertEqual(len(adr), 1)
        self.assertEqual(adr[0][1], "2025-02-01")                # from the file's commit, not invented
        self.assertEqual(self.rows("SELECT COUNT(*) FROM v_ungrounded_decisions")[0][0], 0)
        self.assertTrue(self.rows("SELECT 1 FROM repos WHERE repo_full_name = 'good/repo'"))

    def test_reingest_is_idempotent(self):
        self.ingest("good/repo")
        first = self.rows("SELECT COUNT(*) FROM decisions WHERE repo='good/repo'")[0][0]
        self.assertEqual(self.ingest("good/repo")["status"], "success")
        self.assertEqual(self.rows("SELECT COUNT(*) FROM decisions WHERE repo='good/repo'")[0][0], first)

    def test_low_rate_limit_budget_marks_result_partial(self):
        res = self.ingest("lowbudget/repo")
        self.assertEqual(res["status"], "success", res)
        self.assertTrue(res["data"]["partial"])
        self.assertTrue(any("rate limit" in w for w in res["data"]["warnings"]), res["data"]["warnings"])

    # ---- failures carry their real status ------------------------------------------------
    def _assert_error(self, repo, status, code, contains=None):
        res = self.ingest(repo)
        self.assertEqual((res.get("status"), res.get("status_code"), res.get("error_code")), ("error", status, code), res)
        if contains:
            self.assertIn(contains, res["message"])
        return res

    def test_missing_repository_field(self):
        res = self.api.handle_post("/api/ingest-repo", {"repo": ""})
        self.assertEqual(res.get("status_code"), 400)

    def test_invalid_url(self):
        self._assert_error("not a repo", 400, "INVALID_REPOSITORY")

    def test_local_path_that_does_not_exist(self):
        self._assert_error(os.path.join(self.tmp.name, "nope"), 400, "LOCAL_PATH_NOT_FOUND")

    def test_repository_not_found(self):
        self._assert_error("missing/repo", 404, "REPOSITORY_NOT_FOUND", "was not found")

    def test_private_repository_without_token_is_reported_as_not_found(self):
        self._assert_error("private/repo", 404, "REPOSITORY_NOT_FOUND", "Personal Access Token")

    def test_github_rate_limit(self):
        res = self._assert_error("limited/repo", 429, "GITHUB_RATE_LIMIT",
                                 "GitHub API rate limit exceeded. Please try again later.")
        self.assertGreater(res.get("retry_after", 0), 0)
        self.assertLessEqual(res["retry_after"], 3600)  # a bogus reset header must not produce absurd waits
        self.assertEqual(self.rows("SELECT COUNT(*) FROM events WHERE repo='limited/repo'")[0][0], 0)

    def test_empty_repository(self):
        self._assert_error("empty/repo", 422, "EMPTY_REPOSITORY")

    def test_github_server_error(self):
        self._assert_error("broken/repo", 502, "GITHUB_ERROR")

    def test_network_failure(self):
        with mock.patch.dict(os.environ, {"CIF_GITHUB_API_BASE": "http://127.0.0.1:9"}):  # closed port
            self._assert_error("good/repo", 503, "GITHUB_UNREACHABLE")

    def test_processing_failure_is_500_without_internal_details(self):
        with mock.patch("backend.ingestion.live_github.LiveGitHubIngestor.ingest_custom_repository",
                        side_effect=KeyError("secret_internal_detail")):
            res = self.ingest("good/repo")
        self.assertEqual((res.get("status_code"), res.get("error_code")), (500, "INGESTION_FAILED"))
        self.assertNotIn("secret_internal_detail", res["message"])


class IngestRepoHTTPMethodTests(unittest.TestCase):
    def test_get_on_post_only_route_is_405_with_allow_header(self):
        from tests.test_http_security import _Server, _build_db
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "m.db")
        _build_db(path)
        srv = _Server(path)
        self.addCleanup(srv.stop)
        status, body, headers = srv.request("GET", "/api/ingest-repo")
        self.assertEqual(status, 405, body)
        self.assertEqual(headers.get("Allow"), "POST")
        self.assertEqual(body.get("error_code"), "METHOD_NOT_ALLOWED")
        status, body, _ = srv.request("GET", "/api/definitely-not-a-route")
        self.assertEqual(status, 404, body)


if __name__ == "__main__":
    unittest.main()
