"""
Unit tests for Context Intelligence Framework (CIF) Diagnostics and Health API
Verifies the /api/diagnostics endpoint, database health metrics, and rate limit statistics.
"""
import unittest
import os
import tempfile
from backend.db import Database
from backend.api import APIHandler
from backend.seed_data import populate_seed_data


class TestDiagnosticsEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "test_diag.db")
        cls.db = Database(cls.db_path)
        populate_seed_data(cls.db)
        cls.api = APIHandler(cls.db)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.tmp_dir.cleanup()
        except Exception:
            pass

    def test_healthz_endpoint(self):
        res = self.api.handle_get("/api/healthz", {})
        self.assertEqual(res.get("status"), "ok")
        self.assertEqual(res.get("db"), "ok")

    def test_diagnostics_endpoint(self):
        res = self.api.handle_get("/api/diagnostics", {})
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("backend_status"), "online")
        self.assertIn("uptime_seconds", res)
        self.assertIn("database", res)
        self.assertEqual(res["database"]["status"], "connected")
        self.assertTrue(res["database"]["authoritative"])
        self.assertIn("tables", res["database"])
        self.assertGreater(res["database"]["tables"].get("decisions", 0), 0)
        self.assertIn("rate_limiter", res)
        self.assertIn("timestamp", res)

    def test_system_status_alias(self):
        res = self.api.handle_get("/api/system/status", {})
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("backend_status"), "online")


if __name__ == "__main__":
    unittest.main()

