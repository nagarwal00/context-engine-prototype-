"""
HTTP-level security and reliability regression tests.

Unlike most tests in this suite (which call APIHandler directly), these start the real
`server.py` in a subprocess against a temporary database and send real HTTP requests.
That is the layer where the 2026-11-21 audit found its critical defects
(see audit/KNOWN_ISSUES.md: SEC-01..SEC-12, APP-01, APP-02).
"""
import http.client
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.parse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

DEMO_REPO = "acme-eng/thermal-control-system"
PRIVATE_REPO = "victim/private-repo"
SECRET_DECISION = "dec_secret_http_01"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _build_db(path: str) -> None:
    """Fresh DB with the demo seed plus one private repository owned by nobody."""
    from backend.db import Database
    from backend.seed_data import populate_seed_data
    db = Database(path)
    populate_seed_data(db)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        "INSERT INTO repos (repo_full_name, visibility, added_at, partial) "
        "VALUES (?, 'private', datetime('now'), 0)", (PRIVATE_REPO,))
    cols = [r[1] for r in conn.execute("PRAGMA table_info(decisions)")]
    row = dict(zip(cols, conn.execute(
        "SELECT * FROM decisions WHERE decision_id = 'dec_cache_redis_01'").fetchone()))
    row.update(decision_id=SECRET_DECISION, title="SECRET private decision",
               repo=PRIVATE_REPO, repo_full_name=PRIVATE_REPO)
    conn.execute(f"INSERT INTO decisions ({','.join(row)}) VALUES ({','.join('?' * len(row))})",
                 list(row.values()))
    conn.execute("INSERT INTO decision_evidence (decision_id, event_id) "
                 "SELECT ?, event_id FROM decision_evidence WHERE decision_id = 'dec_cache_redis_01'",
                 (SECRET_DECISION,))
    conn.commit()
    conn.close()


class _Server:
    """Runs server.py in a subprocess with an explicit, isolated environment."""

    def __init__(self, db_path: str, **env_overrides):
        self.port = _free_port()
        env = dict(os.environ)
        # Override everything the developer's real .env might set (server.py never
        # overrides variables that are already present in the environment).
        env.update({
            "PORT": str(self.port),
            "CIF_BIND": "127.0.0.1",
            "CIF_DB_PATH": db_path,
            "CIF_DEV_MODE": "0",
            "CIF_ADMIN_TOKEN": "",
            "CIF_BASE_URL": f"http://127.0.0.1:{self.port}",
            "CIF_SESSION_SECRET": "test-session-secret-not-real",
            "GITHUB_APP_CLIENT_ID": "",
            "GITHUB_APP_CLIENT_SECRET": "",
            "GITHUB_TOKEN": "",
            "GH_TOKEN": "",
            "CIF_CA_BUNDLE": "",
            "CIF_RATE_LIMIT_API_MAX": "5000",
            "CIF_RATE_LIMIT_AUTH_MAX": "1000",
            "CIF_LOCAL_ONLY": "1",
            "PYTHONUNBUFFERED": "1",
        })
        env.update({k: str(v) for k, v in env_overrides.items()})
        self.origin = f"http://127.0.0.1:{self.port}"
        self.proc = subprocess.Popen(
            [sys.executable, os.path.join(PROJECT_ROOT, "server.py")],
            cwd=PROJECT_ROOT, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                if self.request("GET", "/healthz")[0] == 200:
                    return
            except OSError:
                time.sleep(0.1)
        self.stop()
        raise RuntimeError("server.py did not start")

    def request(self, method, path, body=None, headers=None, raw_body=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        hdrs = dict(headers or {})
        data = raw_body
        if body is not None:
            data = json.dumps(body).encode()
            hdrs.setdefault("Content-Type", "application/json")
        conn.request(method, path, body=data, headers=hdrs)
        resp = conn.getresponse()
        payload = resp.read()
        conn.close()
        try:
            parsed = json.loads(payload) if payload else None
        except ValueError:
            parsed = payload.decode(errors="replace")
        return resp.status, parsed, dict(resp.getheaders())

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def _cookie(headers):
    raw = headers.get("Set-Cookie", "")
    return raw.split(";", 1)[0] if raw else ""


class HTTPSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp.name, "http_test.db")
        _build_db(cls.db_path)
        cls.srv = _Server(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()
        cls.tmp.cleanup()

    def _same_origin(self, extra=None):
        h = {"Origin": self.srv.origin}
        h.update(extra or {})
        return h

    def _register(self, username, password="correct horse battery"):
        return self.srv.request("POST", "/auth/register",
                                {"username": username, "password": password},
                                headers=self._same_origin())

    def _decision_state(self, decision_id):
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute("SELECT state FROM decisions WHERE decision_id = ?",
                                (decision_id,)).fetchone()[0]
        finally:
            conn.close()

    # --- SEC-01: password-less login ---------------------------------------------------
    def test_register_then_login_requires_correct_password(self):
        st, body, _ = self._register("alice_http")
        self.assertEqual(st, 200, body)
        st, body, h = self.srv.request("POST", "/auth/login",
                                       {"username": "alice_http", "password": "correct horse battery"},
                                       headers=self._same_origin())
        self.assertEqual(st, 200, body)
        self.assertIn("cif_session=", h.get("Set-Cookie", ""))
        st, body, h = self.srv.request("POST", "/auth/login",
                                       {"username": "alice_http", "password": "wrong password!!"},
                                       headers=self._same_origin())
        self.assertEqual(st, 401, body)
        self.assertNotIn("cif_session=", h.get("Set-Cookie", ""))

    def test_login_without_password_is_rejected(self):
        self._register("bob_http")
        st, body, h = self.srv.request("POST", "/auth/login", {"username": "bob_http"},
                                       headers=self._same_origin())
        self.assertIn(st, (400, 401), body)
        self.assertNotIn("cif_session=", h.get("Set-Cookie", ""))

    def test_login_as_unknown_or_oauth_user_is_rejected(self):
        # An account without a local password (e.g. created by GitHub OAuth) cannot be
        # taken over by typing its login name.
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO users (github_id, login, avatar_url, created_at, last_login_at) "
                     "VALUES (4242, 'oauth_only_user', '', datetime('now'), datetime('now'))")
        conn.commit()
        conn.close()
        for name in ("oauth_only_user", "never_registered"):
            st, body, h = self.srv.request("POST", "/auth/login",
                                           {"username": name, "password": "anything at all"},
                                           headers=self._same_origin())
            self.assertEqual(st, 401, (name, body))
            self.assertNotIn("cif_session=", h.get("Set-Cookie", ""))

    def test_register_existing_username_conflicts(self):
        self._register("carol_http")
        st, body, _ = self._register("carol_http", password="another password 1")
        self.assertEqual(st, 409, body)

    def test_register_rejects_short_password(self):
        st, body, _ = self._register("dave_http", password="short")
        self.assertEqual(st, 400, body)

    # --- SEC-03 / SEC-12: cross-repository access --------------------------------------
    def test_object_id_cannot_be_read_through_another_repo(self):
        for path in (f"/api/evidence?repo={DEMO_REPO}&decision_id={SECRET_DECISION}",
                     f"/api/explain?repo={DEMO_REPO}&decision_id={SECRET_DECISION}",
                     f"/api/evidence?decision_id={SECRET_DECISION}"):
            st, body, _ = self.srv.request("GET", path)
            # 404 is deliberate: it does not confirm that the private object exists.
            self.assertIn(st, (400, 401, 403, 404), (path, body))
            self.assertNotIn("SECRET", json.dumps(body), path)

    def test_object_id_cannot_be_modified_through_another_repo(self):
        _, _, h = self._register("mallory_http")
        cookie = _cookie(h)
        st, body, _ = self.srv.request(
            "POST", "/api/review-action",
            {"repo": DEMO_REPO, "target_id": SECRET_DECISION, "action": "reopen", "reason": "attack"},
            headers=self._same_origin({"Cookie": cookie}))
        self.assertIn(st, (400, 403, 404), body)
        self.assertEqual(self._decision_state(SECRET_DECISION), "accepted")

    def test_list_endpoints_without_repo_do_not_leak_private_repos(self):
        for path in ("/api/decisions", "/api/timeline", "/api/graph",
                     "/api/decision-history", "/api/artifacts"):
            st, body, _ = self.srv.request("GET", path)
            text = json.dumps(body)
            self.assertNotIn(PRIVATE_REPO, text, path)
            self.assertNotIn(SECRET_DECISION, text, path)

    # --- APP-01: DELETE crashed with NameError -----------------------------------------
    def test_delete_returns_json_instead_of_crashing(self):
        st, body, _ = self.srv.request("DELETE", "/api/repos/" + urllib.parse.quote(PRIVATE_REPO, safe=""))
        self.assertIn(st, (401, 403), body)
        self.assertIsInstance(body, dict)

    def test_cross_origin_delete_with_cookie_is_rejected(self):
        _, _, h = self._register("erin_http")
        st, body, _ = self.srv.request(
            "DELETE", "/api/repos/" + urllib.parse.quote(DEMO_REPO, safe=""),
            headers={"Cookie": _cookie(h), "Origin": "https://evil.example"})
        self.assertEqual(st, 403, body)

    # --- SEC-04: demo login open redirect ----------------------------------------------
    def test_demo_login_does_not_redirect_off_site(self):
        st, _, h = self.srv.request("GET", "/auth/demo/login?next=https://evil.example/phish")
        self.assertIn(st, (302, 403, 404))
        loc = h.get("Location", "")
        self.assertFalse(loc.startswith("http") and "evil.example" in loc, loc)
        self.assertNotIn("//evil.example", loc)

    # --- SEC-07: GitHub proxy endpoints ------------------------------------------------
    def test_github_proxy_requires_sign_in(self):
        st, body, _ = self.srv.request("GET", "/api/github-commits?repo=octocat/Hello-World")
        self.assertEqual(st, 401, body)

    def test_github_proxy_rejects_malformed_repo(self):
        _, _, h = self._register("frank_http")
        st, body, _ = self.srv.request("GET", "/api/github-commits?repo=../../user/repos",
                                       headers={"Cookie": _cookie(h)})
        self.assertEqual(st, 400, body)

    # --- SEC-11: diagnostics information disclosure ------------------------------------
    def test_public_diagnostics_do_not_disclose_paths_or_user_counts(self):
        st, body, _ = self.srv.request("GET", "/api/diagnostics")
        self.assertEqual(st, 200)
        text = json.dumps(body)
        self.assertNotIn(self.db_path, text)
        self.assertNotIn("sessions", text)

    # --- Content-type and JSON error shape ---------------------------------------------
    def test_api_post_requires_json_content_type(self):
        st, body, _ = self.srv.request("POST", "/api/drift-check", raw_body=b'{"repo":"x"}',
                                       headers={"Content-Type": "text/plain"})
        self.assertEqual(st, 415, body)

    def test_error_responses_are_json_with_request_id(self):
        st, body, h = self.srv.request("GET", "/api/does-not-exist")
        self.assertEqual(st, 404)
        self.assertEqual(body.get("status"), "error")
        self.assertIn("request_id", body)
        self.assertIn("X-Request-ID", h)


class HTTPDevModeTests(unittest.TestCase):
    """SEC-02: dev mode must not turn a malicious web page into a local admin."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp.name, "dev_test.db")
        _build_db(cls.db_path)
        cls.srv = _Server(cls.db_path, CIF_DEV_MODE="1")

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()
        cls.tmp.cleanup()

    def _decision_count(self):
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        finally:
            conn.close()

    def test_cross_site_simple_post_cannot_clear_database(self):
        before = self._decision_count()
        st, body, _ = self.srv.request(
            "POST", "/api/clear-db", raw_body=b'{"confirm":"dev_test.db"}',
            headers={"Origin": "https://evil.example", "Content-Type": "text/plain"})
        self.assertIn(st, (403, 415), body)
        st, body, _ = self.srv.request(
            "POST", "/api/clear-db", {"confirm": "dev_test.db"},
            headers={"Origin": "https://evil.example"})
        self.assertEqual(st, 403, body)
        self.assertEqual(self._decision_count(), before)

    def test_dns_rebinding_host_is_rejected_in_dev_mode(self):
        st, body, _ = self.srv.request("GET", "/api/decisions",
                                       headers={"Host": f"attacker.example:{self.srv.port}"})
        self.assertEqual(st, 403, body)

    def test_same_origin_dev_request_still_works(self):
        st, body, _ = self.srv.request(
            "POST", "/api/drift-check",
            {"repo": DEMO_REPO, "diff_text": "", "files": ["src/thermal/control.py"]},
            headers={"Origin": self.srv.origin})
        self.assertEqual(st, 200, body)

    def test_invalid_numeric_input_returns_400_not_empty_reply(self):
        st, body, _ = self.srv.request(
            "POST", "/api/ingest-repo", {"repo": "a/b", "max_commits": "abc"},
            headers={"Origin": self.srv.origin})
        self.assertEqual(st, 400, body)
        self.assertEqual(body.get("status"), "error")


class HTTPRateLimitTests(unittest.TestCase):
    """SEC-05: rotating fake bearer tokens must not reset the rate-limit bucket."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp.name, "rl_test.db")
        _build_db(cls.db_path)
        cls.srv = _Server(cls.db_path, CIF_RATE_LIMIT_AUTH_MAX="3")

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()
        cls.tmp.cleanup()

    def test_fake_tokens_share_the_ip_bucket(self):
        body = {"username": "nobody", "password": "irrelevant pw"}
        hdrs = {"Origin": self.srv.origin}
        codes = [self.srv.request("POST", "/auth/login", body, headers=hdrs)[0] for _ in range(4)]
        self.assertEqual(codes[-1], 429, codes)
        for i in range(3):
            st, _, h = self.srv.request("POST", "/auth/login", body,
                                        headers={**hdrs, "Authorization": f"Bearer fake{i}xyz"})
            self.assertEqual(st, 429)
            self.assertIn("Retry-After", h)


class BindSafetyTests(unittest.TestCase):
    """SEC-06: the enforcing bind check must not be shadowed by a print-only duplicate."""

    def test_public_bind_with_dev_mode_is_refused(self):
        import importlib
        old = dict(os.environ)
        try:
            os.environ["CIF_DEV_MODE"] = "1"
            import server
            importlib.reload(server)
            with self.assertRaises(SystemExit):
                server.check_bind_safety("0.0.0.0")
            server.check_bind_safety("127.0.0.1")  # loopback is always fine
        finally:
            os.environ.clear()
            os.environ.update(old)


if __name__ == "__main__":
    unittest.main()
