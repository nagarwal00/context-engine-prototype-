"""
Integration Tests for Repository Scoping and Two-User Isolation (Step 7.4)
Verifies:
- User A cannot read User B's private repository data across ANY GET or POST route.
- ID-guessing attacks on decision_id, entity canonical_path, rule_id, finding_id are blocked with 403/404.
- Anonymous callers see ONLY demo repositories; private repositories are never listed or readable.
- List endpoint /api/repos returns only repositories the caller has access to.
- Private repository data (titles, text, tokens) never leaks in error responses or unauthorized requests.
"""
import datetime
import http.server
import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request

from backend.config import reload_config
from backend.db import Database
from backend.api import APIHandler
from backend.auth.sessions import create_session
from server import ContextIntelligenceServer


class TestRepoIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, "test_isolation.db")
        cls.db = Database(cls.db_path)

        cls.orig_env = dict(os.environ)
        cls.admin_token = "adm_secret_token_12345678"
        os.environ["CIF_ADMIN_TOKEN"] = cls.admin_token
        os.environ["CIF_BASE_URL"] = "http://127.0.0.1:8080"
        os.environ["CIF_DEV_MODE"] = "0"
        reload_config()

        # Build two users in DB
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with cls.db.get_connection() as conn:
            conn.execute("""
            INSERT INTO users (user_id, github_id, login, avatar_url, created_at, last_login_at)
            VALUES (101, 10101, 'alice', 'https://avatars.example.com/u/101', ?, ?),
                   (202, 20202, 'bob', 'https://avatars.example.com/u/202', ?, ?);
            """, (now_iso, now_iso, now_iso, now_iso))

            # Build private repo A and private repo B
            cls.repo_a = "alice-org/private-repo-a"
            cls.repo_b = "bob-org/private-repo-b"

            conn.execute("""
            INSERT INTO repos (repo_full_name, visibility, added_by_user_id, added_at, partial)
            VALUES (?, 'private', 101, ?, 0),
                   (?, 'private', 202, ?, 0);
            """, (cls.repo_a, now_iso, cls.repo_b, now_iso))

            # Grant Alice review access on Repo A, Bob review access on Repo B
            conn.execute("""
            INSERT INTO repo_access (user_id, repo_full_name, level, verified_at)
            VALUES (101, ?, 'review', ?),
                   (202, ?, 'review', ?);
            """, (cls.repo_a, now_iso, cls.repo_b, now_iso))

            # Seed secret data in Repo A
            conn.execute("""
            INSERT INTO decisions (decision_id, title, state, confidence, review_status, repo, repo_full_name)
            VALUES ('dec_alice_secret', 'Alice Secret Algorithm V1', 'accepted', 0.95, 'approved', ?, ?);
            """, (cls.repo_a, cls.repo_a))
            conn.execute("""
            INSERT INTO entities (entity_id, entity_type, canonical_path, repo, repo_full_name)
            VALUES ('ent_alice_secret', 'file', 'src/alice/secret.py', ?, ?);
            """, (cls.repo_a, cls.repo_a))

            # Seed secret data in Repo B
            cls.bob_secret_payload = "BOB_HIGHLY_CONFIDENTIAL_PAYLOAD_XYZ"
            conn.execute("""
            INSERT INTO decisions (decision_id, title, rationale, state, confidence, review_status, repo, repo_full_name)
            VALUES ('dec_bob_secret', 'Bob Secret Architecture', ?, 'accepted', 0.98, 'approved', ?, ?);
            """, (cls.bob_secret_payload, cls.repo_b, cls.repo_b))
            conn.execute("""
            INSERT INTO events (event_id, source_type, source_id, source_url, repo, title, body, ts, repo_full_name)
            VALUES ('evt_bob_secret', 'git_commit', 'c_bob_1', 'https://github.com/bob/c1', ?, 'Bob Commit', ?, ?, ?);
            """, (cls.repo_b, cls.bob_secret_payload, now_iso, cls.repo_b))
            conn.execute("""
            INSERT INTO entities (entity_id, entity_type, canonical_path, repo, repo_full_name)
            VALUES ('ent_bob_secret', 'file', 'src/bob/secret_module.py', ?, ?);
            """, (cls.repo_b, cls.repo_b))
            conn.execute("""
            INSERT INTO guard_rules (rule_id, decision_id, rule_type, params_json, status, polarity, repo_full_name)
            VALUES ('rule_bob_secret', 'dec_bob_secret', 'forbid_import', '{"import_name":"secret_pkg"}', 'active', 'must_not', ?);
            """, (cls.repo_b,))
            conn.execute("""
            INSERT INTO ambiguous_findings (finding_id, pr_id, repo, decision_id, decision_title, tier, signals_matched, status, created_at, repo_full_name)
            VALUES ('find_bob_secret', 'pr_99', ?, 'dec_bob_secret', 'Bob Secret Architecture', 'advisory', '["sig"]', 'pending_review', ?, ?);
            """, (cls.repo_b, now_iso, cls.repo_b))

        # Create sessions
        cls.token_alice, _ = create_session(cls.db, user_id=101, client="web")
        cls.token_bob, _ = create_session(cls.db, user_id=202, client="web")

        cls.api_handler = APIHandler(cls.db)
        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ContextIntelligenceServer)
        cls.httpd.api_handler = cls.api_handler
        cls.port = cls.httpd.server_address[1]

        cls.base_url = f"http://127.0.0.1:{cls.port}"
        os.environ["CIF_BASE_URL"] = cls.base_url
        reload_config()

        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        os.environ.clear()
        os.environ.update(cls.orig_env)
        reload_config()

    def _request(self, method: str, path: str, token: str = None, data: dict = None):
        """Helper to send authenticated HTTP requests."""
        url = f"{self.base_url}{path}"
        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"Origin": self.base_url}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["Cookie"] = f"cif_session={token}"

        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = raw
                return resp.status, parsed, raw
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8")
            try:
                parsed = json.loads(err_body)
            except Exception:
                parsed = err_body
            return err.code, parsed, err_body

    # 1. Anonymous Access Restrictions
    def test_anonymous_access_restricted_to_demo_repos_only(self):
        """Anonymous callers can only access demo repositories; private repos return 401."""
        # Querying demo repo works for anonymous
        status, data, _ = self._request("GET", "/api/timeline?repo=acme-eng/thermal-control-system")
        self.assertEqual(status, 200)

        # Querying Bob's private repo fails for anonymous
        status_anon, data_anon, raw_anon = self._request("GET", f"/api/decisions?repo={self.repo_b}")
        self.assertEqual(status_anon, 401)
        self.assertNotIn(self.bob_secret_payload, raw_anon)

        # Listing repos returns only demo repositories
        status_list, repos_list, _ = self._request("GET", "/api/repos")
        self.assertEqual(status_list, 200)
        self.assertIn("acme-eng/thermal-control-system", repos_list["data"])
        self.assertNotIn(self.repo_a, repos_list["data"])
        self.assertNotIn(self.repo_b, repos_list["data"])

    # 2. Scoped Repository Listing
    def test_repo_list_scoped_to_authorized_user(self):
        """User A sees only demo repos + Repo A. User B sees only demo repos + Repo B."""
        # Alice
        status_a, repos_a, _ = self._request("GET", "/api/repos", token=self.token_alice)
        self.assertEqual(status_a, 200)
        self.assertIn(self.repo_a, repos_a["data"])
        self.assertNotIn(self.repo_b, repos_a["data"])

        # Bob
        status_b, repos_b, _ = self._request("GET", "/api/repos", token=self.token_bob)
        self.assertEqual(status_b, 200)
        self.assertIn(self.repo_b, repos_b["data"])
        self.assertNotIn(self.repo_a, repos_b["data"])

    # 3. Cross-User Access Blocked on EVERY GET Route
    def test_cross_user_get_routes_denied(self):
        """User A attempting to query User B's private repository across all GET endpoints returns 403."""
        get_routes = [
            f"/api/timeline?repo={self.repo_b}",
            f"/api/graph?repo={self.repo_b}",
            f"/api/artifacts?repo={self.repo_b}",
            f"/api/explain?repo={self.repo_b}",
            f"/api/decisions?repo={self.repo_b}",
            f"/api/evidence?repo={self.repo_b}",
            f"/api/review-queue?repo={self.repo_b}",
            f"/api/benchmark?repo={self.repo_b}",
            f"/api/stats?repo={self.repo_b}",
            f"/api/guard-rules?repo={self.repo_b}",
            f"/api/decision-history?repo={self.repo_b}",
            f"/api/as-of?repo={self.repo_b}",
            f"/api/findings/feedback?repo={self.repo_b}",
            f"/api/bus-factor?repo={self.repo_b}",
            f"/api/onboarding?repo={self.repo_b}",
        ]
        for route in get_routes:
            status, data, raw = self._request("GET", route, token=self.token_alice)
            self.assertEqual(
                status, 403, f"Expected 403 Forbidden for User A accessing User B's route {route}, got {status}: {data}"
            )
            # Ensure no secret content is ever leaked
            self.assertNotIn(self.bob_secret_payload, raw)

    # 4. ID-Guessing Attacks Blocked
    def test_id_guessing_attacks_blocked(self):
        """User A attempting to resolve or inspect Bob's decisions/entities by ID alone is blocked."""
        # 1. Guessing decision_id in /api/explain without repo param
        status, data, raw = self._request("GET", "/api/explain?decision_id=dec_bob_secret", token=self.token_alice)
        self.assertEqual(status, 403, f"Expected 403 on ID guess, got {status}: {data}")
        self.assertNotIn(self.bob_secret_payload, raw)

        # 2. Guessing artifact path in /api/explain
        status, data, raw = self._request("GET", "/api/explain?artifact=src/bob/secret_module.py", token=self.token_alice)
        self.assertEqual(status, 403, f"Expected 403 on artifact guess, got {status}: {data}")
        self.assertNotIn(self.bob_secret_payload, raw)

        # 3. Guessing decision_id in /api/decision-history
        status, data, raw = self._request("GET", "/api/decision-history?decision_id=dec_bob_secret", token=self.token_alice)
        self.assertEqual(status, 403, f"Expected 403 on decision-history guess, got {status}: {data}")
        self.assertNotIn(self.bob_secret_payload, raw)

        # 4. Guessing non-existent ID yields 404 (not error or leak)
        status, data, _ = self._request("GET", "/api/explain?decision_id=dec_nonexistent_random_id", token=self.token_alice)
        self.assertEqual(status, 404)

    # 5. Cross-User Writes Blocked on POST Routes
    def test_cross_user_post_routes_denied(self):
        """User A cannot perform review actions, rule changes, or reviewer updates on User B's repo."""
        # 1. Review action targeting Bob's decision
        s1, b1, _ = self._request(
            "POST",
            "/api/review-action",
            token=self.token_alice,
            data={"action": "confirm", "target_id": "dec_bob_secret"}
        )
        self.assertEqual(s1, 403)

        # 2. Approve guard rule on Bob's decision
        s2, b2, _ = self._request(
            "POST",
            "/api/guard-rules/approve",
            token=self.token_alice,
            data={"rule_id": "rule_bob_secret"}
        )
        self.assertEqual(s2, 403)

        # 3. Disable guard rule on Bob's decision
        s3, b3, _ = self._request(
            "POST",
            "/api/guard-rules/disable",
            token=self.token_alice,
            data={"rule_id": "rule_bob_secret"}
        )
        self.assertEqual(s3, 403)

        # 4. Drift check on Bob's repo
        s4, b4, _ = self._request(
            "POST",
            "/api/drift-check",
            token=self.token_alice,
            data={"repo": self.repo_b, "diff_text": "sample diff"}
        )
        self.assertEqual(s4, 403)

        # 5. Finding feedback on Bob's finding
        s5, b5, _ = self._request(
            "POST",
            "/api/findings/feedback",
            token=self.token_alice,
            data={"finding_id": "find_bob_secret", "action": "confirm"}
        )
        self.assertEqual(s5, 403)

        # 6. Adding reviewer to Bob's repo without being owner
        s6, b6, _ = self._request(
            "POST",
            "/api/repos/reviewers",
            token=self.token_alice,
            data={"repo": self.repo_b, "user_id": 101}
        )
        self.assertEqual(s6, 403)

    # 6. Legitimate User Access Succeeded
    def test_user_can_access_own_repo(self):
        """Bob can successfully access and review his own private repository."""
        status, data, raw = self._request("GET", f"/api/decisions?repo={self.repo_b}", token=self.token_bob)
        self.assertEqual(status, 200)
        self.assertIn("dec_bob_secret", [d["decision_id"] for d in data.get("data", [])])


if __name__ == "__main__":
    unittest.main()
