"""
Unit tests for Context Intelligence Framework (CIF) Rate Limiter
Tests sliding window enforcement, category limits, IP/user isolation, and HTTP 429 response.
"""
import unittest
import time
import os
import http.server
import threading
import urllib.request
import urllib.error
import json
import tempfile
from backend.rate_limiter import RateLimiter, get_rate_limiter, reset_rate_limiter
from backend.db import Database
from backend.api import APIHandler
from backend.seed_data import populate_seed_data
from server import ContextIntelligenceServer


class TestRateLimiter(unittest.TestCase):
    def setUp(self):
        reset_rate_limiter()

    def test_category_limits(self):
        env = {
            "CIF_RATE_LIMIT_ENABLED": "true",
            "CIF_RATE_LIMIT_WINDOW": "60",
            "CIF_RATE_LIMIT_AUTH_MAX": "3",
            "CIF_RATE_LIMIT_INGEST_MAX": "2",
            "CIF_RATE_LIMIT_EXPENSIVE_MAX": "2",
            "CIF_RATE_LIMIT_API_MAX": "5",
        }
        limiter = RateLimiter(env)

        # Ingest: max 2
        allowed1, retry1, rem1, lim1 = limiter.check_rate_limit("ip:127.0.0.1", category="ingest")
        self.assertTrue(allowed1)
        self.assertEqual(rem1, 1)

        allowed2, retry2, rem2, lim2 = limiter.check_rate_limit("ip:127.0.0.1", category="ingest")
        self.assertTrue(allowed2)
        self.assertEqual(rem2, 0)

        # 3rd request must be blocked
        allowed3, retry3, rem3, lim3 = limiter.check_rate_limit("ip:127.0.0.1", category="ingest")
        self.assertFalse(allowed3)
        self.assertGreaterEqual(retry3, 1)
        self.assertEqual(rem3, 0)

    def test_ip_and_user_isolation(self):
        env = {
            "CIF_RATE_LIMIT_ENABLED": "true",
            "CIF_RATE_LIMIT_WINDOW": "60",
            "CIF_RATE_LIMIT_API_MAX": "2",
        }
        limiter = RateLimiter(env)

        # IP 1 uses up quota
        self.assertTrue(limiter.check_rate_limit("ip:10.0.0.1", category="api")[0])
        self.assertTrue(limiter.check_rate_limit("ip:10.0.0.1", category="api")[0])
        self.assertFalse(limiter.check_rate_limit("ip:10.0.0.1", category="api")[0])

        # IP 2 should still be allowed
        self.assertTrue(limiter.check_rate_limit("ip:10.0.0.2", category="api")[0])

        # User key should also be independent
        self.assertTrue(limiter.check_rate_limit("user:alice", category="api")[0])

    def test_bypass_when_disabled(self):
        env = {
            "CIF_RATE_LIMIT_ENABLED": "false",
            "CIF_RATE_LIMIT_API_MAX": "1",
        }
        limiter = RateLimiter(env)
        for _ in range(10):
            allowed, retry, rem, lim = limiter.check_rate_limit("ip:1.2.3.4", category="api")
            self.assertTrue(allowed)
            self.assertEqual(retry, 0)

    def test_path_categorization(self):
        self.assertEqual(RateLimiter.get_category_for_path("/auth/login"), "auth")
        self.assertEqual(RateLimiter.get_category_for_path("/api/auth/register"), "auth")
        self.assertEqual(RateLimiter.get_category_for_path("/api/ingest"), "ingest")
        self.assertEqual(RateLimiter.get_category_for_path("/api/webhook/github"), "ingest")
        self.assertEqual(RateLimiter.get_category_for_path("/api/reseed"), "expensive")
        self.assertEqual(RateLimiter.get_category_for_path("/api/benchmark"), "expensive")
        self.assertEqual(RateLimiter.get_category_for_path("/api/repos"), "api")
        self.assertEqual(RateLimiter.get_category_for_path("/api/timeline"), "api")

    def test_get_stats(self):
        limiter = RateLimiter()
        limiter.check_rate_limit("ip:1.1.1.1", category="api")
        stats = limiter.get_stats()
        self.assertIn("enabled", stats)
        self.assertIn("total_requests_checked", stats)
        self.assertEqual(stats["total_requests_checked"], 1)


class TestRateLimiterHTTPIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "test_rl.db")
        cls.db = Database(cls.db_path)
        populate_seed_data(cls.db)

        # Force very small limit for testing HTTP 429
        os.environ["CIF_RATE_LIMIT_ENABLED"] = "true"
        os.environ["CIF_RATE_LIMIT_WINDOW"] = "60"
        os.environ["CIF_RATE_LIMIT_API_MAX"] = "2"
        reset_rate_limiter()

        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ContextIntelligenceServer)
        cls.httpd.api_handler = APIHandler(cls.db)
        cls.port = cls.httpd.server_address[1]

        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.server_thread.join(timeout=2)
        try:
            cls.tmp_dir.cleanup()
        except Exception:
            pass
        os.environ["CIF_RATE_LIMIT_API_MAX"] = "60"
        reset_rate_limiter()

    def test_http_429_on_exceeded_quota(self):
        url = f"http://127.0.0.1:{self.port}/api/repos"

        # Request 1: 200 OK
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.getcode(), 200)
            self.assertIn("X-Request-ID", resp.headers)

        # Request 2: 200 OK
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.getcode(), 200)

        # Request 3: HTTP 429
        try:
            with urllib.request.urlopen(url) as resp:
                self.fail(f"Expected HTTP 429 but got {resp.getcode()}")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 429)
            self.assertIn("Retry-After", e.headers)
            body = json.loads(e.read().decode("utf-8"))
            self.assertEqual(body.get("status"), "error")
            self.assertEqual(body.get("error_code"), "RATE_LIMIT_EXCEEDED")
            self.assertIn("retry_after", body)
            self.assertIn("request_id", body)


if __name__ == "__main__":
    unittest.main()

