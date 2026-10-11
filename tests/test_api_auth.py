"""
Tests for API Authorization Boundary and Security (P0-b / Step 1.2)
"""
import http.server
import json
import os
import tempfile
import threading
import unittest
import urllib.request
import urllib.error

from backend.db import Database
from backend.api import APIHandler
from backend.seed_data import populate_seed_data
from server import ContextIntelligenceServer


class TestAPIAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "test_auth.db")
        cls.db = Database(cls.db_path)
        populate_seed_data(cls.db)

        cls.admin_token = "test_admin_token_xyz"
        cls.reviewer_token = "test_reviewer_token_abc"
        cls.allowed_origin = "https://allowed.example.com"

        cls.orig_env = {
            "CIF_ADMIN_TOKEN": os.environ.get("CIF_ADMIN_TOKEN"),
            "CIF_REVIEWER_TOKEN": os.environ.get("CIF_REVIEWER_TOKEN"),
            "CIF_DEV_MODE": os.environ.get("CIF_DEV_MODE"),
            "CIF_CORS_ORIGINS": os.environ.get("CIF_CORS_ORIGINS"),
        }

        os.environ["CIF_ADMIN_TOKEN"] = cls.admin_token
        os.environ["CIF_REVIEWER_TOKEN"] = cls.reviewer_token
        os.environ["CIF_DEV_MODE"] = "0"
        os.environ["CIF_CORS_ORIGINS"] = cls.allowed_origin

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
        cls.tmp_dir.cleanup()

        for k, v in cls.orig_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _request(self, method: str, endpoint: str, data=None, headers=None):
        url = f"http://127.0.0.1:{self.port}{endpoint}"
        req_headers = {"User-Agent": "CIF-Auth-Tester/1.0"}
        if headers:
            req_headers.update(headers)

        req_body = None
        if data is not None:
            if isinstance(data, (dict, list)):
                req_body = json.dumps(data).encode("utf-8")
                req_headers["Content-Type"] = "application/json"
            elif isinstance(data, bytes):
                req_body = data
            elif isinstance(data, str):
                req_body = data.encode("utf-8")

        req = urllib.request.Request(url, data=req_body, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.getcode()
                body = response.read().decode("utf-8")
                try:
                    parsed = json.loads(body)
                except Exception:
                    parsed = body
                resp_headers = dict(response.headers)
                return status, parsed, resp_headers
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            resp_headers = dict(e.headers)
            return e.code, parsed, resp_headers

    def test_viewer_routes_allowed_without_token(self):
        viewer_endpoints = [
            "/api/timeline",
            "/api/graph",
            "/api/artifacts",
            "/api/decisions",
            "/api/stats",
            "/api/repos",
            "/api/guard-rules",
            "/api/auth-status",
        ]
        for ep in viewer_endpoints:
            status, data, _ = self._request("GET", ep)
            self.assertEqual(status, 200, f"Expected 200 for viewer endpoint {ep}, got {status}: {data}")
            self.assertEqual(data.get("status"), "success")

    def test_write_routes_fail_without_token(self):
        write_endpoints = [
            ("/api/review-action", {"action": "confirm", "target_id": "dec_thermal_pid_accepted"}),
            ("/api/guard-rules/approve", {"rule_id": "rule_test"}),
            ("/api/guard-rules/disable", {"rule_id": "rule_test"}),
            ("/api/drift-check", {"diff_text": "sample"}),
            ("/api/reseed", {"confirm": "test_auth.db"}),
            ("/api/clear-db", {"confirm": "test_auth.db"}),
            ("/api/ingest-repo", {"repo": "owner/repo"}),
        ]
        for ep, payload in write_endpoints:
            status, data, _ = self._request("POST", ep, data=payload)
            self.assertIn(
                status,
                [401, 403],
                f"Write endpoint {ep} should fail without token, got status {status}: {data}"
            )

    def test_write_routes_fail_with_wrong_token(self):
        bad_headers = {"Authorization": "Bearer wrong_token_12345"}
        status, data, _ = self._request(
            "POST",
            "/api/review-action",
            data={"action": "confirm", "target_id": "dec_thermal_pid_accepted"},
            headers=bad_headers
        )
        self.assertEqual(status, 403, f"Expected 403 for invalid token, got {status}: {data}")

    def test_write_routes_succeed_with_correct_token(self):
        # Reviewer token on reviewer endpoint
        rev_headers = {"Authorization": f"Bearer {self.reviewer_token}"}
        status, data, _ = self._request(
            "POST",
            "/api/review-action",
            data={"action": "confirm", "target_id": "dec_thermal_pid_accepted"},
            headers=rev_headers
        )
        self.assertEqual(status, 200, f"Expected 200 with reviewer token, got {status}: {data}")

        # Admin token on admin endpoint with confirm
        adm_headers = {"Authorization": f"Bearer {self.admin_token}"}
        status, data, _ = self._request(
            "POST",
            "/api/reseed",
            data={"confirm": "test_auth.db"},
            headers=adm_headers
        )
        self.assertEqual(status, 200, f"Expected 200 with admin token, got {status}: {data}")

    def test_unknown_routes_denied(self):
        status, data, _ = self._request("GET", "/api/unknown-route")
        self.assertEqual(status, 404, f"Expected 404 for unknown GET route, got {status}")

        status, data, _ = self._request("POST", "/api/dangerous-unknown", data={"foo": "bar"})
        self.assertEqual(status, 404, f"Expected 404 for unknown POST route, got {status}")

    def test_oversized_body_rejected(self):
        adm_headers = {"Authorization": f"Bearer {self.admin_token}"}
        large_body = b"x" * (1024 * 1024 + 100)  # > 1 MB
        status, data, _ = self._request(
            "POST",
            "/api/review-action",
            data=large_body,
            headers=adm_headers
        )
        self.assertIn(status, [400, 413], f"Expected 413 or 400 for oversized payload, got {status}: {data}")

    def test_clear_db_without_confirm_fails(self):
        adm_headers = {"Authorization": f"Bearer {self.admin_token}"}
        # Call clear-db without confirmation
        status, data, _ = self._request(
            "POST",
            "/api/clear-db",
            data={},
            headers=adm_headers
        )
        self.assertEqual(status, 400, f"Expected 400 when confirm is omitted, got {status}: {data}")

        # Call with incorrect confirmation name
        status, data, _ = self._request(
            "POST",
            "/api/clear-db",
            data={"confirm": "wrong_filename.db"},
            headers=adm_headers
        )
        self.assertEqual(status, 400, f"Expected 400 when confirm filename does not match, got {status}: {data}")

    def test_cors_origin_filtering(self):
        # Disallowed origin receives no Access-Control-Allow-Origin header
        status, _, headers = self._request(
            "GET",
            "/api/stats",
            headers={"Origin": "https://unauthorized-origin.com"}
        )
        self.assertEqual(status, 200)
        self.assertNotIn("Access-Control-Allow-Origin", headers)

        # Allowed origin receives echoed Access-Control-Allow-Origin header
        status, _, headers = self._request(
            "GET",
            "/api/stats",
            headers={"Origin": self.allowed_origin}
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), self.allowed_origin)


if __name__ == "__main__":
    unittest.main()
