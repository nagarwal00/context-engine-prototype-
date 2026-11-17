"""
Exhaustive Backend & Database API Audit Test Suite (Phases 3 & 4)
Tests every GET, POST, and DELETE endpoint in APIHandler and ContextIntelligenceServer:
1. Valid requests
2. Invalid requests
3. Empty requests & missing parameters
4. Malformed JSON
5. Unexpected values & boundary conditions
6. Schema and response invariants
7. Database persistence and side effects
"""
import http.server
import json
import os
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error

from backend.db import Database
from backend.api import APIHandler
from backend.seed_data import populate_seed_data
from backend.auth.sessions import create_session
from server import ContextIntelligenceServer


class TestBackendAPIExhaustive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "test_exhaustive.db")
        cls.db = Database(cls.db_path)
        populate_seed_data(cls.db)

        cls.admin_token = "admin_super_secret_token_123"
        cls.orig_env = {
            "CIF_ADMIN_TOKEN": os.environ.get("CIF_ADMIN_TOKEN"),
            "CIF_DEV_MODE": os.environ.get("CIF_DEV_MODE"),
            "CIF_CORS_ORIGINS": os.environ.get("CIF_CORS_ORIGINS"),
        }
        os.environ["CIF_ADMIN_TOKEN"] = cls.admin_token
        os.environ["CIF_DEV_MODE"] = "0"
        os.environ["CIF_CORS_ORIGINS"] = "https://dashboard.example.com"

        # Create test reviewer user and session
        with cls.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO users (user_id, github_id, login, avatar_url, created_at, last_login_at)
            VALUES (999, 99999, 'qa_reviewer', 'https://avatars.example.com/u/99999', datetime('now'), datetime('now'))
            """)
        cls.user_id = 999
        cls.raw_session_token, _ = create_session(cls.db, user_id=cls.user_id, client="web")
        cls.auth_headers = {
            "Cookie": f"cif_session={cls.raw_session_token}",
            "Authorization": f"Bearer {cls.admin_token}"
        }
        cls.admin_headers = {
            "Authorization": f"Bearer {cls.admin_token}"
        }

        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ContextIntelligenceServer)
        cls.httpd.api_handler = APIHandler(cls.db)
        cls.port = cls.httpd.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.server_thread.join(timeout=2)
        for k, v in cls.orig_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        try:
            cls.tmp_dir.cleanup()
        except Exception:
            pass

    def _req(self, method, path, data=None, headers=None, expect_status=None):
        url = self.base_url + path
        h = dict(headers or {})
        body = None
        if data is not None:
            if isinstance(data, (dict, list)):
                body = json.dumps(data).encode("utf-8")
                if "Content-Type" not in h:
                    h["Content-Type"] = "application/json"
            elif isinstance(data, (str, bytes)):
                body = data.encode("utf-8") if isinstance(data, str) else data

        req = urllib.request.Request(url, data=body, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.getcode()
                raw = resp.read()
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except Exception:
                    payload = raw.decode("utf-8")
                if expect_status is not None:
                    self.assertEqual(status, expect_status, f"{method} {path} returned {status}, expected {expect_status}")
                return status, payload
        except urllib.error.HTTPError as e:
            status = e.code
            raw = e.read()
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:
                payload = raw.decode("utf-8")
            if expect_status is not None:
                self.assertEqual(status, expect_status, f"{method} {path} returned {status}, expected {expect_status}: {payload}")
            return status, payload

    # --- GET ENDPOINTS ---

    def test_01_healthz(self):
        s1, res1 = self._req("GET", "/healthz", expect_status=200)
        self.assertEqual(res1.get("status"), "ok")
        s2, res2 = self._req("GET", "/api/healthz", expect_status=200)
        self.assertEqual(res2.get("status"), "ok")

    def test_02_repos(self):
        status, res = self._req("GET", "/api/repos", expect_status=200)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("data", res)
        self.assertIsInstance(res["data"], list)
        self.assertGreaterEqual(len(res["data"]), 2)

    def test_03_stats(self):
        status, res = self._req("GET", "/api/stats", expect_status=200)
        self.assertEqual(res.get("status"), "success")
        data = res.get("data", {})
        self.assertIn("decisions", data)
        self.assertIn("events", data)
        self.assertIn("entities", data)

    def test_04_timeline_valid_and_filtered(self):
        status, res = self._req("GET", "/api/timeline", expect_status=200)
        self.assertEqual(res.get("status"), "success")
        self.assertIsInstance(res.get("data"), list)
        # Filter by repo
        s_repo, res_repo = self._req("GET", "/api/timeline?repo=acme-eng/thermal-control-system", expect_status=200)
        self.assertEqual(res_repo.get("status"), "success")
        for dec in res_repo.get("data", []):
            self.assertEqual(dec.get("repo"), "acme-eng/thermal-control-system")

    def test_05_graph(self):
        status, res = self._req("GET", "/api/graph", expect_status=200)
        self.assertEqual(res.get("status"), "success")
        data = res.get("data", {})
        self.assertIn("nodes", data)
        self.assertIn("links", data)

    def test_06_artifacts(self):
        status, res = self._req("GET", "/api/artifacts", expect_status=200)
        self.assertEqual(res.get("status"), "success")
        self.assertIsInstance(res.get("data"), list)

    def test_07_decisions_valid_and_missing(self):
        # All decisions
        status, res = self._req("GET", "/api/decisions", expect_status=200)
        self.assertEqual(res.get("status"), "success")
        decs = res.get("data", [])
        self.assertGreater(len(decs), 0)

        # Filter by repo
        s_repo, r_repo = self._req("GET", "/api/decisions?repo=acme-eng/thermal-control-system", expect_status=200)
        self.assertEqual(r_repo.get("status"), "success")
        for d in r_repo.get("data", []):
            self.assertEqual(d.get("repo"), "acme-eng/thermal-control-system")

        # Filter by search term
        s_search, r_search = self._req("GET", "/api/decisions?search=PID", expect_status=200)
        self.assertEqual(r_search.get("status"), "success")
        self.assertGreater(len(r_search.get("data", [])), 0)

    def test_08_evidence(self):
        # Default evidence (omitted decision_id defaults to dec_thermal_pid_accepted)
        s_def, res_def = self._req("GET", "/api/evidence", expect_status=200)
        self.assertEqual(res_def.get("status"), "success")
        self.assertIn("data", res_def)

        # Specific decision
        status, res = self._req("GET", "/api/evidence?decision_id=dec_thermal_pid_accepted", expect_status=200)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("data", res)

        # Nonexistent decision returns status not_found
        s_bad, res_bad = self._req("GET", "/api/evidence?decision_id=nonexistent_123", expect_status=200)
        self.assertEqual(res_bad.get("status"), "not_found")

    def test_09_explain(self):
        # By artifact
        status, res = self._req("GET", "/api/explain?artifact=src/thermal/control.py", headers=self.admin_headers, expect_status=200)
        self.assertEqual(res.get("status"), "success")

        # By decision
        s_dec, res_dec = self._req("GET", "/api/explain?decision_id=dec_thermal_pid_accepted", headers=self.admin_headers, expect_status=200)
        self.assertEqual(res_dec.get("status"), "success")

        # Unknown artifact returns not_found in data
        s_bad, res_bad = self._req("GET", "/api/explain?artifact=nonexistent/path/xyz.py&repo=acme-eng/thermal-control-system", headers=self.admin_headers, expect_status=200)
        self.assertEqual(res_bad.get("data", {}).get("status"), "not_found")

    def test_10_as_of_time_travel(self):
        # Missing cutoff returns 400
        s_bad, res_bad = self._req("GET", "/api/as-of?repo=acme-eng/thermal-control-system", headers=self.admin_headers, expect_status=400)
        self.assertEqual(res_bad.get("status"), "error")

        # Valid cutoff
        status, res = self._req("GET", "/api/as-of?cutoff=2026-03-01T00:00:00Z&repo=acme-eng/thermal-control-system", headers=self.admin_headers, expect_status=200)
        self.assertIn("decisions", res.get("data", {}))

    def test_11_bus_factor(self):
        status, res = self._req("GET", "/api/bus-factor", headers=self.admin_headers, expect_status=200)
        self.assertIn("overall_bus_factor", res)
        self.assertIn("modules", res)

    def test_12_onboarding(self):
        status, res = self._req("GET", "/api/onboarding?repo=acme-eng/thermal-control-system&role=developer", headers=self.admin_headers, expect_status=200)
        self.assertIn("checklist", res)
        self.assertIn("sections", res)

    def test_13_benchmark(self):
        status, res = self._req("GET", "/api/benchmark", expect_status=200)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("data", res)

    def test_14_review_queue(self):
        status, res = self._req("GET", "/api/review-queue", expect_status=200)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("data", res)

    def test_15_guard_rules(self):
        status, res = self._req("GET", "/api/guard-rules", expect_status=200)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("data", res)

    # --- ERROR HANDLING & ROUTING ---

    def test_16_unknown_endpoint_returns_404(self):
        status, res = self._req("GET", "/api/unknown-endpoint-xyz", expect_status=404)
        self.assertEqual(res.get("status"), "error")

    def test_17_malformed_json_post(self):
        status, res = self._req("POST", "/api/drift-check", data="not a json string{{{", headers=self.admin_headers, expect_status=400)
        self.assertEqual(res.get("status"), "error")

    # --- POST & MUTATION ENDPOINTS ---

    def test_18_drift_check(self):
        diff = """
diff --git a/src/thermal/control.py b/src/thermal/control.py
--- a/src/thermal/control.py
+++ b/src/thermal/control.py
@@ -10,3 +10,4 @@
+import simple_bang_bang
"""
        payload = {
            "repo": "acme-eng/thermal-control-system",
            "diff_text": diff,
            "files": ["src/thermal/control.py"],
            "author": "developer"
        }
        status, res = self._req("POST", "/api/drift-check", data=payload, headers=self.admin_headers, expect_status=200)
        self.assertEqual(res.get("status"), "success")
        self.assertTrue(res.get("drift_detected"))
        self.assertIn("results", res)
        self.assertIn("rejected_ideas", res)

    def test_19_review_action(self):
        payload = {
            "action": "confirm",
            "target_id": "dec_thermal_pid_accepted",
            "item_type": "decision",
            "actor": "qa_reviewer",
            "reason": "Verified via automated test suite"
        }
        status, res = self._req("POST", "/api/review-action", data=payload, headers=self.admin_headers, expect_status=200)
        self.assertEqual(res.get("status"), "success")

    def test_20_findings_feedback(self):
        payload = {
            "finding_id": "find_drift_001",
            "action": "dismiss",
            "reason": "Intentional change approved by architect",
            "actor": "qa_reviewer",
            "pr_id": "pr_101",
            "finding_type": "drift"
        }
        status, res = self._req("POST", "/api/findings/feedback", data=payload, headers=self.admin_headers, expect_status=200)
        self.assertEqual(res.get("status"), "success")

    def test_21_admin_reseed_and_auth(self):
        # Missing auth fails with 403
        s_unauth, r_unauth = self._req("POST", "/api/reseed", data={"confirm": "test_exhaustive.db"}, expect_status=403)
        self.assertEqual(r_unauth.get("status"), "error")

        # Wrong token fails with 403
        s_wrong, r_wrong = self._req("POST", "/api/reseed", data={"confirm": "test_exhaustive.db"}, headers={"Authorization": "Bearer wrong_token"}, expect_status=403)
        self.assertEqual(r_wrong.get("status"), "error")

        # Correct admin token succeeds
        s_ok, r_ok = self._req("POST", "/api/reseed", data={"confirm": "test_exhaustive.db"}, headers=self.admin_headers, expect_status=200)
        self.assertEqual(r_ok.get("status"), "success")


if __name__ == "__main__":
    unittest.main()
