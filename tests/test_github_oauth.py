"""
GitHub OAuth sign-in ("Continue with GitHub") — regression tests (2026-11-24).

Before this fix the flow never failed visibly: when credentials were missing, when GitHub rejected
the authorization code (wrong secret, expired code, callback mismatch) or when the token request
failed, a web sign-in silently created a session for the shared "demo-developer" account; when the
profile request failed it invented a user "github-user" (id 999999). Users believed they were signed
in with GitHub while they were not.

Only GitHub's two HTTPS endpoints are mocked (token exchange and GET /user), as in test_auth_flow.py.
"""
import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import reload_config
from backend.db import Database
from backend.auth.github_login import initiate_github_login, handle_github_callback

CONFIGURED = {"GITHUB_APP_CLIENT_ID": "Iv1.testclient", "GITHUB_APP_CLIENT_SECRET": "test-secret-not-real",
              "CIF_BASE_URL": "http://localhost:8080", "GITHUB_CLIENT_ID": "", "GITHUB_CLIENT_SECRET": "",
              "GITHUB_CALLBACK_URL": ""}
NOT_CONFIGURED = {k: "" for k in ("GITHUB_APP_CLIENT_ID", "GITHUB_APP_CLIENT_SECRET", "GITHUB_CLIENT_ID",
                                  "GITHUB_CLIENT_SECRET", "GITHUB_CALLBACK_URL")}


class _Resp(io.BytesIO):
    def __init__(self, payload, status=200):
        super().__init__(json.dumps(payload).encode())
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def fake_github(token_payload=None, token_exc=None, user_payload=None, user_exc=None):
    def _open(req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if url.startswith("https://github.com/login/oauth/access_token"):
            if token_exc:
                raise token_exc
            return _Resp(token_payload or {"access_token": "gho_testtoken", "token_type": "bearer"})
        if url.startswith("https://api.github.com/user"):
            if user_exc:
                raise user_exc
            return _Resp(user_payload or {"id": 4242, "login": "octo-student", "avatar_url": "https://x/a.png"})
        raise AssertionError(f"unexpected request {url}")
    return _open


class GitHubOAuthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "oauth.db")
        self.db = Database(self.path)
        self.env = mock.patch.dict(os.environ, CONFIGURED)
        self.env.start()
        self.addCleanup(self.env.stop)
        reload_config()
        self.addCleanup(reload_config)

    def q(self, sql, *args):
        with contextlib.closing(sqlite3.connect(self.path)) as c:
            return c.execute(sql, args).fetchall()

    def start(self, next_path="/dashboard.html"):
        status, location, headers = initiate_github_login(self.db, next_path=next_path, client="web")
        self.assertEqual(status, 302, location)
        return urllib.parse.parse_qs(urllib.parse.urlparse(location).query)["state"][0], location

    def callback(self, state, code="good-code", **fake):
        params = {"state": [state], "code": [code]}
        with mock.patch("urllib.request.urlopen", side_effect=fake_github(**fake)):
            return handle_github_callback(self.db, params)

    def assert_no_session(self):
        self.assertEqual(self.q("SELECT COUNT(*) FROM sessions")[0][0], 0)
        self.assertEqual(self.q("SELECT COUNT(*) FROM users WHERE login IN ('demo-developer','github-user')")[0][0], 0)

    # ---- configuration --------------------------------------------------------------------
    def test_missing_credentials_is_a_configuration_error_not_a_demo_login(self):
        with mock.patch.dict(os.environ, NOT_CONFIGURED):
            reload_config()
            status, message, headers = initiate_github_login(self.db, next_path="/dashboard.html", client="web")
        self.assertEqual(status, 503)
        self.assertEqual(headers.get("X-CIF-Auth-Error"), "GITHUB_NOT_CONFIGURED")
        self.assertNotIn("Set-Cookie", headers)
        self.assert_no_session()

    def test_redirects_to_github_with_state_and_exact_callback_url(self):
        state, location = self.start()
        q = urllib.parse.parse_qs(urllib.parse.urlparse(location).query)
        self.assertTrue(location.startswith("https://github.com/login/oauth/authorize?"))
        self.assertEqual(q["client_id"], ["Iv1.testclient"])
        self.assertEqual(q["redirect_uri"], ["http://localhost:8080/auth/github/callback"])
        self.assertGreaterEqual(len(state), 40)
        self.assertEqual(self.q("SELECT COUNT(*) FROM oauth_states")[0][0], 1)
        self.assertFalse(self.q("SELECT 1 FROM oauth_states WHERE state_hash = ?", state))  # stored hashed

    def test_requested_variable_names_are_accepted(self):
        with mock.patch.dict(os.environ, {"GITHUB_APP_CLIENT_ID": "", "GITHUB_APP_CLIENT_SECRET": "",
                                          "GITHUB_CLIENT_ID": "Ov23.alias", "GITHUB_CLIENT_SECRET": "alias-secret",
                                          "GITHUB_CALLBACK_URL": "http://localhost:9000/auth/github/callback"}):
            reload_config()
            status, location, _ = initiate_github_login(self.db, next_path="/dashboard.html", client="web")
        q = urllib.parse.parse_qs(urllib.parse.urlparse(location).query)
        self.assertEqual((status, q["client_id"], q["redirect_uri"]),
                         (302, ["Ov23.alias"], ["http://localhost:9000/auth/github/callback"]))

    # ---- successful login -----------------------------------------------------------------
    def test_successful_callback_creates_github_user_and_session(self):
        state, _ = self.start()
        status, target, headers = self.callback(state)
        self.assertEqual(status, 302, target)
        self.assertTrue(target.endswith("/dashboard.html"))
        self.assertIn("cif_session=", headers.get("Set-Cookie", ""))
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertEqual(self.q("SELECT github_id, login, password_hash FROM users"), [(4242, "octo-student", None)])
        self.assertEqual(self.q("SELECT COUNT(*) FROM sessions")[0][0], 1)
        self.assertEqual(self.q("SELECT COUNT(*) FROM oauth_states")[0][0], 0)  # single use

    def test_second_login_reuses_the_same_account(self):
        for _ in range(2):
            state, _ = self.start()
            self.assertEqual(self.callback(state)[0], 302)
        self.assertEqual(self.q("SELECT COUNT(*) FROM users WHERE github_id = 4242")[0][0], 1)

    # ---- failures never produce a session ---------------------------------------------------
    def _assert_refused(self, result, status, code):
        self.assertEqual((result[0], result[2].get("X-CIF-Auth-Error")), (status, code), result)
        self.assertNotIn("Set-Cookie", result[2])
        self.assert_no_session()

    def test_user_denies_authorization(self):
        state, _ = self.start()
        res = handle_github_callback(self.db, {"state": [state], "error": ["access_denied"],
                                               "error_description": ["The user has denied your application access."]})
        self._assert_refused(res, 403, "ACCESS_DENIED")
        self.assertEqual(self.q("SELECT COUNT(*) FROM oauth_states")[0][0], 0)  # state consumed

    def test_invalid_state_is_rejected(self):
        self._assert_refused(self.callback("forged-state"), 400, "INVALID_STATE")

    def test_invalid_or_expired_code(self):
        state, _ = self.start()
        res = self.callback(state, token_payload={"error": "bad_verification_code",
                                                  "error_description": "The code passed is incorrect or expired."})
        self._assert_refused(res, 400, "INVALID_CODE")

    def test_callback_url_mismatch(self):
        state, _ = self.start()
        res = self.callback(state, token_payload={"error": "redirect_uri_mismatch"})
        self._assert_refused(res, 400, "CALLBACK_MISMATCH")
        self.assertIn("http://localhost:8080/auth/github/callback", res[1])

    def test_wrong_client_secret(self):
        state, _ = self.start()
        res = self.callback(state, token_payload={"error": "incorrect_client_credentials"})
        self._assert_refused(res, 502, "INVALID_APP_CREDENTIALS")
        self.assertNotIn("test-secret-not-real", res[1])

    def test_github_unavailable_during_token_exchange(self):
        state, _ = self.start()
        res = self.callback(state, token_exc=urllib.error.URLError("connection refused"))
        self._assert_refused(res, 503, "GITHUB_UNAVAILABLE")

    def test_profile_request_failure_does_not_invent_a_user(self):
        state, _ = self.start()
        res = self.callback(state, user_exc=urllib.error.URLError("timeout"))
        self._assert_refused(res, 502, "PROFILE_FAILED")

    def test_access_token_is_never_returned_to_the_browser(self):
        state, _ = self.start()
        status, target, headers = self.callback(state)
        self.assertNotIn("gho_testtoken", target + json.dumps(headers))


class GitHubOAuthBrowserTests(unittest.TestCase):
    """Through the real server: browsers are sent back to the login page with an error code."""

    def test_browser_errors_redirect_to_login_page_json_clients_get_status(self):
        from tests.test_http_security import _Server, _build_db
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "b.db")
        _build_db(path)
        srv = _Server(path)  # no GitHub credentials configured
        self.addCleanup(srv.stop)
        html = {"Accept": "text/html,application/xhtml+xml"}
        st, _, h = srv.request("GET", "/auth/github/login?next=/dashboard.html", headers=html)
        self.assertEqual((st, h.get("Location")), (302, "/login.html?auth_error=GITHUB_NOT_CONFIGURED"))
        self.assertNotIn("Set-Cookie", h)
        st, body, _ = srv.request("GET", "/auth/github/login?next=/dashboard.html")
        self.assertEqual((st, body.get("error_code")), (503, "GITHUB_NOT_CONFIGURED"))
        st, _, h = srv.request("GET", "/auth/github/callback?code=x&state=forged", headers=html)
        self.assertEqual((st, h.get("Location")), (302, "/login.html?auth_error=INVALID_STATE"))


if __name__ == "__main__":
    unittest.main()
