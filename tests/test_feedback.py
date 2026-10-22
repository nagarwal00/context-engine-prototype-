"""
Tests for Step 3.6: Developer Feedback Loop and Review Routing
Verifies:
1. Authentication boundary on POST /api/findings/feedback (requires reviewer role).
2. Developer action: 'confirm' finding records feedback and resolves review item.
3. Developer action: 'dismiss' finding persists and suppresses subsequent findings on same PR+decision.
4. Developer action: 'reopen' transitions rejected decision -> reopened via lifecycle engine with audit trail.
5. Review queue routing: ambiguous findings ('possible' tier, supersession candidates, weak evidence)
   route to GET /api/review-queue with explicit reasons.
6. Feedback metrics: measured counts exposed via GET /api/findings/feedback, GET /api/stats, and GET /api/benchmark.
"""
import http.server
import json
import os
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path

from backend.db import Database
from backend.models import Decision, Edge
from backend.seed_data import populate_seed_data
from backend.api import APIHandler
from backend.engine.rejected_idea_guard import RejectedIdeaGuard
from server import ContextIntelligenceServer

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestDeveloperFeedbackLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "test_feedback.db")
        cls.db = Database(cls.db_path)
        populate_seed_data(cls.db)

        cls.admin_token = "test_admin_secret_xyz"
        cls.reviewer_token = cls.admin_token

        cls.orig_env = {
            "CIF_ADMIN_TOKEN": os.environ.get("CIF_ADMIN_TOKEN"),
            "CIF_REVIEWER_TOKEN": os.environ.get("CIF_REVIEWER_TOKEN"),
            "CIF_DEV_MODE": os.environ.get("CIF_DEV_MODE"),
        }

        os.environ["CIF_ADMIN_TOKEN"] = cls.admin_token
        os.environ["CIF_REVIEWER_TOKEN"] = cls.reviewer_token
        os.environ["CIF_DEV_MODE"] = "0"

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
        req_headers = {"User-Agent": "CIF-Feedback-Tester/1.0"}
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
                return status, parsed
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            return e.code, parsed

    def test_01_auth_boundary_on_findings_feedback(self):
        """Verifies POST /api/findings/feedback requires reviewer role."""
        payload = {
            "finding_id": "rej_test_auth",
            "action": "confirm",
            "pr_id": "pr_auth_test",
            "decision_id": "dec_thermal_deadband_rejected",
            "reason": "Test confirmation"
        }

        # 1. Unauthenticated request without token fails (401 or 403)
        status, resp = self._request("POST", "/api/findings/feedback", data=payload)
        self.assertIn(status, [401, 403], f"Expected 401/403 without token, got {status}: {resp}")

        # 2. Invalid bearer token fails (403)
        status, resp = self._request(
            "POST",
            "/api/findings/feedback",
            data=payload,
            headers={"Authorization": "Bearer invalid_random_token"}
        )
        self.assertEqual(status, 403, f"Expected 403 with wrong token, got {status}: {resp}")

        # 3. Valid reviewer token succeeds (200)
        status, resp = self._request(
            "POST",
            "/api/findings/feedback",
            data=payload,
            headers={"Authorization": f"Bearer {self.reviewer_token}"}
        )
        self.assertEqual(status, 200, f"Expected 200 with reviewer token, got {status}: {resp}")
        self.assertEqual(resp.get("status"), "success")

    def test_02_confirm_finding_action(self):
        """Verifies confirming a finding records feedback and resolves the finding."""
        finding_id = "rej_confirm_001"
        pr_id = "pr_1001"
        dec_id = "dec_cache_redis_accepted"
        payload = {
            "finding_id": finding_id,
            "action": "confirm",
            "pr_id": pr_id,
            "decision_id": dec_id,
            "reason": "Confirmed local cache reintroduction violates cluster consistency invariant",
            "actor": "sarah_chen"
        }

        status, resp = self._request(
            "POST",
            "/api/findings/feedback",
            data=payload,
            headers={"Authorization": f"Bearer {self.reviewer_token}"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(resp.get("status"), "success")
        self.assertEqual(resp.get("data", {}).get("status"), "confirmed")

        # Verify feedback stored in database
        feedback_rows = self.db.get_finding_feedback(finding_id=finding_id)
        self.assertGreaterEqual(len(feedback_rows), 1)
        row = feedback_rows[0]
        self.assertEqual(row["action"], "confirm")
        self.assertEqual(row["decision_id"], dec_id)
        self.assertEqual(row["pr_id"], pr_id)

    def test_03_dismiss_finding_persists_and_suppresses_subsequent_checks(self):
        """Verifies dismissing a finding persists and suppresses alerts on the same PR+decision."""
        guard = RejectedIdeaGuard(self.db)
        pr_id = "pr_dismiss_300"
        dec_id = "dec_cache_redis_accepted"
        repo = "acme-eng/distributed-cache-service"

        # 1. Initial check triggers finding
        rep1 = guard.evaluate_proposal(
            repo=repo,
            pr_id=pr_id,
            title="Local dict cache optimization",
            body="Emergency in-process dictionary cache.",
            diff_text="+++ b/src/cache/store.py\n@@ -20,2 +20,3 @@\n+    local_cache = {}\n",
            changed_files=["src/cache/store.py"]
        )
        findings1 = [f for f in rep1.get("findings", []) if f["decision_id"] == dec_id]
        self.assertGreaterEqual(len(findings1), 1)
        f_id = findings1[0]["finding_id"]

        # 2. Dismiss via API
        payload = {
            "finding_id": f_id,
            "action": "dismiss",
            "pr_id": pr_id,
            "decision_id": dec_id,
            "reason": "Exempted for localized unit test fixture helper"
        }
        status, resp = self._request(
            "POST",
            "/api/findings/feedback",
            data=payload,
            headers={"Authorization": f"Bearer {self.reviewer_token}"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(resp.get("data", {}).get("status"), "dismissed")

        # 3. Subsequent check on SAME PR produces 0 findings (suppressed)
        rep2 = guard.evaluate_proposal(
            repo=repo,
            pr_id=pr_id,
            title="Local dict cache optimization",
            body="Emergency in-process dictionary cache.",
            diff_text="+++ b/src/cache/store.py\n@@ -20,2 +20,3 @@\n+    local_cache = {}\n",
            changed_files=["src/cache/store.py"]
        )
        findings2 = [f for f in rep2.get("findings", []) if f["decision_id"] == dec_id]
        self.assertEqual(findings2, [], "Dismissed finding must be suppressed for same PR")

        # 4. Check on DIFFERENT PR is NOT suppressed
        rep3 = guard.evaluate_proposal(
            repo=repo,
            pr_id="pr_different_400",
            title="Local dict cache optimization",
            body="Emergency in-process dictionary cache.",
            diff_text="+++ b/src/cache/store.py\n@@ -20,2 +20,3 @@\n+    local_cache = {}\n",
            changed_files=["src/cache/store.py"]
        )
        findings3 = [f for f in rep3.get("findings", []) if f["decision_id"] == dec_id]
        self.assertGreaterEqual(len(findings3), 1, "Dismissal must not suppress finding on other PRs")

    def test_04_reopen_decision_flow_with_lifecycle_engine(self):
        """Verifies reopening transitions decision rejected -> reopened and records audit history."""
        dec_id = "dec_thermal_deadband_rejected"
        pr_id = "pr_reopen_500"

        # Verify initial decision state is rejected
        dec_before = self.db.get_decision(dec_id)
        self.assertIsNotNone(dec_before)
        self.assertEqual(dec_before.state, "rejected")

        # Call reopen action via API
        payload = {
            "finding_id": f"rej_{dec_id[:8]}",
            "action": "reopen",
            "pr_id": pr_id,
            "decision_id": dec_id,
            "reason": "New optical sensor with zero jitter invalidates original rejection rationale"
        }
        status, resp = self._request(
            "POST",
            "/api/findings/feedback",
            data=payload,
            headers={"Authorization": f"Bearer {self.reviewer_token}"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(resp.get("data", {}).get("status"), "reopened")

        # Verify DB state is updated to 'reopened'
        dec_after = self.db.get_decision(dec_id)
        self.assertEqual(dec_after.state, "reopened")

        # Verify state history audit trail row was inserted
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM state_history WHERE decision_id = ? AND state = 'reopened'", (dec_id,))
            hist_row = cur.fetchone()
            self.assertIsNotNone(hist_row)
            self.assertIn("New optical sensor", hist_row["notes"])

    def test_05_review_queue_routing_for_ambiguous_findings(self):
        """
        Verifies Step 3.6: Ambiguous findings ('possible' tier, supersession candidates, weak evidence)
        go to the review queue with the reason.
        """
        guard = RejectedIdeaGuard(self.db)
        repo = "acme-eng/distributed-cache-service"
        pr_id = "pr_ambiguous_600"

        # Trigger a 'possible' tier finding (1 structural signal without entity overlap)
        eval_res = guard.evaluate_proposal(
            repo=repo,
            pr_id=pr_id,
            title="Update memory caps in worker",
            body="Reviewing local cache bounds in worker.",
            diff_text="+++ b/src/worker/helper.py\n@@ -10,2 +10,3 @@\n+    local_cache = {}\n",
            changed_files=["src/worker/helper.py"]
        )
        possible_findings = [f for f in eval_res.get("findings", []) if f["tier"] == "possible"]
        self.assertGreaterEqual(len(possible_findings), 1)

        # Seed a supersession_candidate edge to verify routing of ambiguous supersessions
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO edges (edge_id, edge_type, from_id, from_type, to_id, to_type, valid_from, repo_full_name)
            VALUES ('edge_sup_test_01', 'supersession_candidate', 'dec_thermal_pid_accepted', 'decision', 'dec_thermal_deadband_rejected', 'decision', '2026-01-15T00:00:00Z', 'acme-eng/thermal-control-system')
            """)
            conn.commit()

        # Query GET /api/review-queue
        status, q_data = self._request("GET", "/api/review-queue")
        self.assertEqual(status, 200)
        items = q_data.get("data", [])
        self.assertIsInstance(items, list)

        # 1. Verify 'possible' tier finding is present in review queue
        possible_items = [it for it in items if it.get("item_type") == "possible_rejected_idea"]
        self.assertGreaterEqual(len(possible_items), 1)
        amb_item = possible_items[0]
        self.assertIn("Ambiguous finding", amb_item["queue_reason"])
        self.assertEqual(amb_item["review_status"], "pending_review")

        # 2. Verify 'weak' / 'insufficient' / 'contradicted' evidence decisions are present
        evidence_items = [it for it in items if it.get("item_type") == "decision"]
        self.assertGreaterEqual(len(evidence_items), 1)
        for ev_it in evidence_items:
            self.assertIn("queue_reason", ev_it)

        # 3. Verify 'supersession_candidate' edges are present
        sup_items = [it for it in items if it.get("item_type") == "supersession_candidate"]
        self.assertGreaterEqual(len(sup_items), 1)
        self.assertIn("Ambiguous supersession candidate", sup_items[0]["queue_reason"])

        # 4. Resolving ambiguous item removes it from pending review queue
        f_target = amb_item["finding_id"]
        status_dismiss, _ = self._request(
            "POST",
            "/api/findings/feedback",
            data={
                "finding_id": f_target,
                "action": "dismiss",
                "pr_id": pr_id,
                "decision_id": amb_item["decision_id"],
                "reason": "Dismissed from queue"
            },
            headers={"Authorization": f"Bearer {self.reviewer_token}"}
        )
        self.assertEqual(status_dismiss, 200)

        # Re-fetch queue: resolved finding is no longer in pending review queue
        status2, q_data2 = self._request("GET", "/api/review-queue")
        items2 = q_data2.get("data", [])
        still_pending = [it for it in items2 if it.get("finding_id") == f_target]
        self.assertEqual(still_pending, [], "Resolved ambiguous finding must not remain in pending queue")

    def test_06_measured_feedback_counts_in_metrics_and_stats(self):
        """Verifies feedback counts are reported as measured data across endpoints."""
        # Query GET /api/findings/feedback
        status, fb_resp = self._request("GET", "/api/findings/feedback")
        self.assertEqual(status, 200)
        data = fb_resp.get("data", {})
        counts = data.get("counts", {})
        self.assertIn("total", counts)
        self.assertIn("confirm", counts)
        self.assertIn("dismiss", counts)
        self.assertIn("reopen", counts)
        self.assertGreater(counts["total"], 0, "Expected non-zero measured feedback count")

        # Query GET /api/stats
        status_stats, stats_resp = self._request("GET", "/api/stats")
        self.assertEqual(status_stats, 200)
        stats_data = stats_resp.get("data", {})
        self.assertIn("finding_feedback", stats_data)
        self.assertEqual(stats_data["finding_feedback"]["total"], counts["total"])

        # Query GET /api/benchmark
        status_bm, bm_resp = self._request("GET", "/api/benchmark")
        self.assertEqual(status_bm, 200)
        bm_data = bm_resp.get("data", {})
        self.assertIn("finding_feedback", bm_data)
        self.assertEqual(bm_data["finding_feedback"]["total"], counts["total"])
        self.assertEqual(bm_data["metrics"]["finding_feedback_total"], counts["total"])


if __name__ == "__main__":
    unittest.main()
