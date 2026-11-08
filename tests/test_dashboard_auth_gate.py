"""
Tests for Dashboard Access Control (Auth Guard)
Verifies:
1. Unauthenticated requests to /dashboard.html are redirected (302) to /login.html
2. Unauthenticated requests to /dashboard are redirected (302) to /login.html
3. Authenticated requests with valid session cookie are permitted through to /dashboard.html (200)
"""
import http.server
import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.request
import urllib.parse
import urllib.error

from backend.config import Config, reload_config
from backend.db import Database
from backend.api import APIHandler
from backend.auth.sessions import create_session, build_session_cookie
from server import ContextIntelligenceServer


class TestDashboardAuthGate(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_gate.db")
        self.db = Database(self.db_path)

        self.orig_env = dict(os.environ)
        os.environ["CIF_BASE_URL"] = "http://127.0.0.1:8080"
        os.environ["CIF_SESSION_SECRET"] = "test_secret_32_bytes_long_guard!!"
        os.environ["CIF_DEV_MODE"] = "0"
        reload_config()

        self.api_handler = APIHandler(self.db)
        self.server_address = ("127.0.0.1", 0)
        self.httpd = http.server.ThreadingHTTPServer(self.server_address, ContextIntelligenceServer)
        self.httpd.api_handler = self.api_handler
        self.port = self.httpd.server_address[1]
        self.base_url = f"http://127.0.0.1:{self.port}"
        os.environ["CIF_BASE_URL"] = self.base_url

        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.environ.clear()
        os.environ.update(self.orig_env)
        reload_config()

    def test_unauthenticated_dashboard_redirects_to_login(self):
        # Don't follow redirects automatically so we can inspect status code and Location
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(NoRedirectHandler)

        for path in ("/dashboard.html", "/dashboard", "/repos"):
            url = f"{self.base_url}{path}"
            req = urllib.request.Request(url)
            try:
                res = opener.open(req)
                self.assertEqual(res.status, 302)
                loc = res.headers.get("Location")
                self.assertTrue(loc.startswith("/login.html"), f"Expected redirect to login, got {loc}")
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, 302)
                loc = e.headers.get("Location")
                self.assertTrue(loc.startswith("/login.html"), f"Expected redirect to login, got {loc}")

    def test_authenticated_dashboard_allows_access(self):
        # Create a test user and session
        with self.db.get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO users (github_id, login, avatar_url, created_at, last_login_at) VALUES (?, ?, ?, ?, ?)",
                (12345, "authorized-user", "https://avatar.url", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z")
            )
            user_id = cur.lastrowid

        raw_token, _ = create_session(self.db, user_id=user_id, client="web")
        cookie_header = build_session_cookie(raw_token, self.base_url)

        # Extract only the key=value part for Request headers
        cookie_val = cookie_header.split(";")[0]

        req = urllib.request.Request(f"{self.base_url}/dashboard.html")
        req.add_header("Cookie", cookie_val)

        res = urllib.request.urlopen(req)
        self.assertEqual(res.status, 200)
        body = res.read().decode("utf-8")
        self.assertIn("Context Intelligence", body)


if __name__ == "__main__":
    unittest.main()

