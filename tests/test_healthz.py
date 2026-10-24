"""
Unit tests for the /healthz endpoint (Step 6.1).
Verifies:
1. Public accessibility (no auth required).
2. Returns {"status": "ok", "mode": "live|static", "db": "ok"}.
3. Reports db: "error" if database connection fails.
4. Never performs database mutations.
"""
import os
import tempfile
import unittest
from unittest.mock import patch

from backend.db import Database
from backend.api import APIHandler


class TestHealthzEndpoint(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_health.db")
        self.db = Database(self.db_path)
        self.handler = APIHandler(self.db)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass
        if os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
            except OSError:
                pass

    def test_healthz_returns_ok_and_live_mode(self):
        with patch.dict(os.environ, {"CIF_MODE": "live"}):
            res = self.handler.handle_get("/healthz", {})
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["mode"], "live")
            self.assertEqual(res["db"], "ok")

    def test_api_healthz_returns_ok(self):
        res = self.handler.handle_get("/api/healthz", {})
        self.assertEqual(res["status"], "ok")
        self.assertIn(res["mode"], ("live", "static"))
        self.assertEqual(res["db"], "ok")

    def test_healthz_static_mode_configured(self):
        with patch.dict(os.environ, {"CIF_MODE": "static"}):
            res = self.handler.handle_get("/healthz", {})
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["mode"], "static")
            self.assertEqual(res["db"], "ok")

    def test_healthz_public_authorization(self):
        # Route must be public (allowed without headers or tokens)
        ok, code, msg = self.handler.check_authorization("GET", "/healthz", {})
        self.assertTrue(ok)
        self.assertEqual(code, 200)

        ok_api, code_api, _ = self.handler.check_authorization("GET", "/api/healthz", {})
        self.assertTrue(ok_api)
        self.assertEqual(code_api, 200)

    def test_healthz_db_failure_reported(self):
        # When DB connection raises an exception, healthz reports db="error"
        broken_db = Database(self.db_path)
        broken_handler = APIHandler(broken_db)
        with patch.object(broken_db, "get_connection", side_effect=RuntimeError("DB disconnected")):
            res = broken_handler.handle_get("/healthz", {})
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["db"], "error")


if __name__ == "__main__":
    unittest.main()
