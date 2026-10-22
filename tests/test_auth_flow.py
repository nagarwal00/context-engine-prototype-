"""
Unit and Integration Tests for GitHub Login, Sessions, and Extension Auth (Step 7.3)
Verifies with a mocked HTTP layer for GitHub (no network calls):
1. Happy path (web client login -> callback -> cookie set -> /api/me).
2. Happy path (extension client login -> chromiumapp redirect -> exchange code -> /api/me).
3. Wrong, missing, reused, and expired OAuth state.
4. Bad next_path redirect rejection (open redirect defense).
5. Bad or unlisted ext_id rejection.
6. One-time extension code reuse rejection.
7. One-time extension code expiry (> 60s).
8. Cookie security flags (HttpOnly, SameSite=Lax, Secure on https).
9. CSRF Origin check on cookie-authenticated POSTs vs Bearer exemption.
10. Session expiration (7-day absolute and 24-hour idle timeout) and logout.
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
from unittest.mock import patch, MagicMock
from io import BytesIO

from backend.config import Config, reload_config
from backend.db import Database
from backend.api import APIHandler
from backend.auth.sessions import (
    create_session,
    get_session,
    delete_session,
    create_extension_code,
    exchange_extension_code,
    hash_token,
    build_session_cookie,
    build_logout_cookie,
)
from server import ContextIntelligenceServer


class TestAuthFlow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_auth.db")
        self.db = Database(self.db_path)

        # Configure environment for auth
        self.orig_env = dict(os.environ)
        os.environ["CIF_BASE_URL"] = "http://127.0.0.1:8080"
        os.environ["CIF_SESSION_SECRET"] = "test_session_secret_32_bytes_long!!"
        os.environ["GITHUB_APP_SLUG"] = "cif-test-app"
        os.environ["GITHUB_APP_CLIENT_ID"] = "Iv1.test_client_id"
        os.environ["GITHUB_APP_CLIENT_SECRET"] = "test_client_secret_xyz"
        os.environ["CIF_EXTENSION_IDS"] = "ext_chrome_valid_id_1,ext_chrome_valid_id_2"
        os.environ["CIF_DEV_MODE"] = "0"
        reload_config()

        self.api_handler = APIHandler(self.db)
        self.server_address = ("127.0.0.1", 0)
        self.httpd = http.server.ThreadingHTTPServer(self.server_address, ContextIntelligenceServer)
        self.httpd.api_handler = self.api_handler
        self.port = self.httpd.server_address[1]

        # Update CIF_BASE_URL to match ephemeral server port
        self.base_url = f"http://127.0.0.1:{self.port}"
        os.environ["CIF_BASE_URL"] = self.base_url
        reload_config()

        self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.server_thread.start()

        # Seed default test user in users table for foreign key constraints
        with self.db.get_connection() as conn:
            conn.execute("""
            INSERT OR IGNORE INTO users (user_id, github_id, login, avatar_url, created_at, last_login_at)
            VALUES (1, 99991, 'testuser', 'https://avatar.example.com', 'ts', 'ts');
            """)

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.environ.clear()
        os.environ.update(self.orig_env)
        reload_config()

    def _http_request(
        self,
        method: str,
        path: str,
        headers: dict = None,
        data: dict = None,
        follow_redirects: bool = False
    ):
        """Helper to make HTTP requests against the running test server."""
        url = f"{self.base_url}{path}"
        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body_bytes, method=method)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)

        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers):
                infourl = urllib.response.addinfourl(fp, headers, req.get_full_url())
                infourl.code = code
                return infourl
            http_error_301 = http_error_302
            http_error_303 = http_error_302
            http_error_307 = http_error_302

        opener = urllib.request.build_opener() if follow_redirects else urllib.request.build_opener(NoRedirectHandler)

        try:
            with opener.open(req) as resp:
                resp_body = resp.read().decode("utf-8")
                try:
                    parsed = json.loads(resp_body)
                except Exception:
                    parsed = resp_body
                status_code = getattr(resp, "status", getattr(resp, "code", 200))
                return status_code, parsed, dict(resp.headers)
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8")
            try:
                parsed = json.loads(err_body)
            except Exception:
                parsed = err_body
            return err.code, parsed, dict(err.headers)

    def _mock_github_responses(self, access_token="gh_token_abc", login="octocat", github_id=99901):
        """Builds a mock urlopen context for GitHub OAuth token exchange and user API."""
        def fake_urlopen(req, *args, **kwargs):
            url = req.full_url if hasattr(req, "full_url") else req
            if "login/oauth/access_token" in url:
                payload = json.dumps({
                    "access_token": access_token,
                    "refresh_token": f"gh_refresh_{access_token}",
                    "expires_in": 28800,
                }).encode("utf-8")
                resp = MagicMock()
                resp.read.return_value = payload
                resp.__enter__.return_value = resp
                return resp
            elif "api.github.com/user" in url:
                payload = json.dumps({
                    "id": github_id,
                    "login": login,
                    "avatar_url": f"https://avatars.githubusercontent.com/u/{github_id}",
                }).encode("utf-8")
                resp = MagicMock()
                resp.read.return_value = payload
                resp.__enter__.return_value = resp
                return resp
            raise ValueError(f"Unexpected urlopen call in test: {url}")
        return fake_urlopen

    # 1. Happy Path: Web Flow
    def test_happy_path_web_flow(self):
        """Full web login: login redirect -> callback -> set cookie -> /api/me profile."""
        # 1. Initiate login
        status, _, headers = self._http_request("GET", "/auth/github/login?next=/dashboard")
        self.assertEqual(status, 302)
        loc = headers.get("Location")
        self.assertIn("https://github.com/login/oauth/authorize", loc)
        parsed_loc = urllib.parse.urlparse(loc)
        qs = urllib.parse.parse_qs(parsed_loc.query)
        self.assertEqual(qs["client_id"][0], "Iv1.test_client_id")
        raw_state = qs["state"][0]

        # 2. Mock GitHub token exchange and user fetch
        fake_urlopen = self._mock_github_responses()
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            cb_status, _, cb_headers = self._http_request(
                "GET", f"/auth/github/callback?code=fake_gh_code_123&state={raw_state}"
            )

        self.assertEqual(cb_status, 302)
        self.assertEqual(cb_headers.get("Location"), f"{self.base_url}/dashboard")
        set_cookie = cb_headers.get("Set-Cookie")
        self.assertIsNotNone(set_cookie)
        self.assertIn("cif_session=", set_cookie)
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("SameSite=Lax", set_cookie)

        # Extract cookie value
        cookie_val = set_cookie.split(";")[0]

        # 3. Call /api/me with session cookie
        me_status, me_body, _ = self._http_request("GET", "/api/me", headers={"Cookie": cookie_val})
        self.assertEqual(me_status, 200)
        self.assertEqual(me_body.get("status"), "success")
        self.assertEqual(me_body.get("login"), "octocat")
        self.assertTrue(me_body.get("avatar_url").startswith("https://avatars.githubusercontent.com/"))
        self.assertTrue(len(me_body.get("csrf", "")) > 10)

    # 2. Happy Path: Extension Client Flow
    def test_happy_path_extension_flow(self):
        """Extension login: client=extension -> chromiumapp redirect -> exchange -> Bearer auth /api/me."""
        ext_id = "ext_chrome_valid_id_1"
        status, _, headers = self._http_request(
            "GET", f"/auth/github/login?client=extension&ext_id={ext_id}"
        )
        self.assertEqual(status, 302)
        loc = headers.get("Location")
        raw_state = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query)["state"][0]

        fake_urlopen = self._mock_github_responses(login="ext_user", github_id=55501)
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            cb_status, _, cb_headers = self._http_request(
                "GET", f"/auth/github/callback?code=ext_code_abc&state={raw_state}"
            )

        self.assertEqual(cb_status, 302)
        target_loc = cb_headers.get("Location")
        self.assertTrue(target_loc.startswith(f"https://{ext_id}.chromiumapp.org/cb?code="))
        one_time_code = urllib.parse.parse_qs(urllib.parse.urlparse(target_loc).query)["code"][0]

        # Swap code for session token via POST /auth/extension/exchange
        ex_status, ex_body, _ = self._http_request(
            "POST", "/auth/extension/exchange", data={"code": one_time_code}
        )
        self.assertEqual(ex_status, 200)
        session_token = ex_body.get("token")
        self.assertIsNotNone(session_token)

        # Access /api/me with Bearer token
        me_status, me_body, _ = self._http_request(
            "GET", "/api/me", headers={"Authorization": f"Bearer {session_token}"}
        )
        self.assertEqual(me_status, 200)
        self.assertEqual(me_body.get("login"), "ext_user")

    # 3. State Validation: Wrong, Missing, Reused, Expired
    def test_state_validation(self):
        """Rejects missing, wrong, reused, or expired states fail-closed."""
        fake_urlopen = self._mock_github_responses()

        # Missing state
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            status, body, _ = self._http_request("GET", "/auth/github/callback?code=test_code")
            self.assertEqual(status, 400)

        # Wrong/Unrecognized state
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            status, body, _ = self._http_request("GET", "/auth/github/callback?code=test_code&state=nonexistent_state")
            self.assertEqual(status, 400)

        # Generate a valid state
        status, _, headers = self._http_request("GET", "/auth/github/login?next=/repos")
        raw_state = urllib.parse.parse_qs(urllib.parse.urlparse(headers["Location"]).query)["state"][0]

        # Use once -> succeeds
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            s1, _, _ = self._http_request("GET", f"/auth/github/callback?code=c1&state={raw_state}")
            self.assertEqual(s1, 302)

        # Reusing the state -> fails closed (already deleted)
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            s2, body2, _ = self._http_request("GET", f"/auth/github/callback?code=c2&state={raw_state}")
            self.assertEqual(s2, 400)

        # Expired state (> 10 minutes old)
        status, _, headers = self._http_request("GET", "/auth/github/login?next=/repos")
        raw_state2 = urllib.parse.parse_qs(urllib.parse.urlparse(headers["Location"]).query)["state"][0]
        state_hash2 = hash_token(raw_state2)

        # Backdate state in DB to 15 minutes ago
        old_ts = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=15)).isoformat()
        with self.db.get_connection() as conn:
            conn.execute("UPDATE oauth_states SET created_at = ? WHERE state_hash = ?", (old_ts, state_hash2))

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            s_exp, _, _ = self._http_request("GET", f"/auth/github/callback?code=c3&state={raw_state2}")
            self.assertEqual(s_exp, 400)

    # 4. Open Redirect Defense: bad next_path
    def test_bad_next_path_rejected(self):
        """Ensures next_path must start with '/' and not '//'."""
        bad_paths = [
            "//evil.example.com/exploit",
            "https://evil.example.com",
            "http://attacker.com",
            "javascript:alert(1)",
            "\\evil.com",
        ]
        for bad in bad_paths:
            status, body, _ = self._http_request("GET", f"/auth/github/login?next={urllib.parse.quote(bad)}")
            self.assertEqual(status, 400, f"Expected 400 for next={bad}")

        # Valid paths
        status, _, headers = self._http_request("GET", "/auth/github/login?next=/valid/app/page")
        self.assertEqual(status, 302)

    # 5. Extension ID allowlist check
    def test_extension_id_allowlist(self):
        """Only extension IDs configured in CIF_EXTENSION_IDS may initiate extension login."""
        # Unlisted extension ID
        status, body, _ = self._http_request("GET", "/auth/github/login?client=extension&ext_id=unauthorized_ext_999")
        self.assertEqual(status, 400)

        # Missing ext_id
        status, body, _ = self._http_request("GET", "/auth/github/login?client=extension")
        self.assertEqual(status, 400)

        # Allowed extension ID
        status, _, headers = self._http_request("GET", "/auth/github/login?client=extension&ext_id=ext_chrome_valid_id_2")
        self.assertEqual(status, 302)

    # 6. One-time code reuse rejected
    def test_extension_code_cannot_be_reused(self):
        """A one-time extension exchange code can only be swapped once."""
        raw_token, _ = create_session(self.db, user_id=1, client="extension")
        code = create_extension_code(self.db, raw_token)

        # First exchange succeeds
        s1, b1, _ = self._http_request("POST", "/auth/extension/exchange", data={"code": code})
        self.assertEqual(s1, 200)
        self.assertEqual(b1.get("token"), raw_token)

        # Second exchange fails
        s2, b2, _ = self._http_request("POST", "/auth/extension/exchange", data={"code": code})
        self.assertEqual(s2, 400)

    # 7. One-time code expiry
    def test_extension_code_expiry(self):
        """One-time extension code expires after 60 seconds."""
        raw_token, _ = create_session(self.db, user_id=1, client="extension")
        code = create_extension_code(self.db, raw_token)
        code_h = hash_token(code)

        # Backdate in database to 65 seconds ago
        old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=65)).isoformat()
        with self.db.get_connection() as conn:
            conn.execute("UPDATE ext_codes SET created_at = ? WHERE code_hash = ?", (old_time, code_h))

        s, _, _ = self._http_request("POST", "/auth/extension/exchange", data={"code": code})
        self.assertEqual(s, 400)

    # 8. Cookie Security Flags
    def test_cookie_flags(self):
        """HTTP base URL produces HttpOnly; SameSite=Lax without Secure. HTTPS adds Secure."""
        # 1. HTTP base URL
        cookie_http = build_session_cookie("tok123", "http://127.0.0.1:8080")
        self.assertIn("HttpOnly", cookie_http)
        self.assertIn("SameSite=Lax", cookie_http)
        self.assertNotIn("Secure", cookie_http)

        # 2. HTTPS base URL
        cookie_https = build_session_cookie("tok123", "https://cif.company.com")
        self.assertIn("HttpOnly", cookie_https)
        self.assertIn("SameSite=Lax", cookie_https)
        self.assertIn("Secure", cookie_https)

    # 9. CSRF Origin Check
    def test_csrf_origin_check(self):
        """Cookie-authenticated state-changing calls require matching Origin. Bearer calls are exempt."""
        raw_token, _ = create_session(self.db, user_id=1, client="web")
        cookie_header = f"cif_session={raw_token}"

        # 1. Cookie auth with matching Origin -> allowed
        status, resp, _ = self._http_request(
            "POST",
            "/auth/logout",
            headers={"Cookie": cookie_header, "Origin": self.base_url}
        )
        self.assertEqual(status, 200)

        # Re-create session for attack tests
        raw_token2, _ = create_session(self.db, user_id=1, client="web")
        cookie_header2 = f"cif_session={raw_token2}"

        # 2. Cookie auth with mismatched Origin -> 403 Forbidden
        status, resp, _ = self._http_request(
            "POST",
            "/auth/logout",
            headers={"Cookie": cookie_header2, "Origin": "http://malicious-site.example.com"}
        )
        self.assertEqual(status, 403)

        # 3. Cookie auth with missing Origin -> 403 Forbidden
        status, resp, _ = self._http_request(
            "POST",
            "/auth/logout",
            headers={"Cookie": cookie_header2}
        )
        self.assertEqual(status, 403)

        # 4. Bearer auth (Extension) with missing Origin -> exempt from CSRF check
        raw_token3, _ = create_session(self.db, user_id=1, client="extension")
        status, resp, _ = self._http_request(
            "POST",
            "/auth/logout",
            headers={"Authorization": f"Bearer {raw_token3}"}
        )
        self.assertEqual(status, 200)

    # 10. Session Expiration & Logout
    def test_session_expiration_and_logout(self):
        """Absolute expiry (7 days) and idle timeout (24 hours) invalidate session; logout clears session."""
        # Populate user row so join succeeds
        with self.db.get_connection() as conn:
            conn.execute("""
            INSERT OR IGNORE INTO users (user_id, github_id, login, avatar_url, created_at, last_login_at)
            VALUES (10, 10001, 'session_tester', 'avatar_url', 'ts', 'ts');
            """)

        raw_token, _ = create_session(self.db, user_id=10, client="web")
        sess_hash = hash_token(raw_token)

        # Normal active session works
        s, body, _ = self._http_request("GET", "/api/me", headers={"Cookie": f"cif_session={raw_token}"})
        self.assertEqual(s, 200)
        self.assertEqual(body.get("login"), "session_tester")

        # Expired absolute (8 days old)
        old_expiry = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat()
        with self.db.get_connection() as conn:
            conn.execute("UPDATE sessions SET expires_at = ? WHERE session_hash = ?", (old_expiry, sess_hash))

        s_exp, _, _ = self._http_request("GET", "/api/me", headers={"Cookie": f"cif_session={raw_token}"})
        self.assertEqual(s_exp, 401)

        # Idle timeout (last seen 25 hours ago)
        raw_token2, _ = create_session(self.db, user_id=10, client="web")
        sess_hash2 = hash_token(raw_token2)
        idle_last_seen = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=25)).isoformat()
        with self.db.get_connection() as conn:
            conn.execute("UPDATE sessions SET last_seen_at = ? WHERE session_hash = ?", (idle_last_seen, sess_hash2))

        s_idle, _, _ = self._http_request("GET", "/api/me", headers={"Cookie": f"cif_session={raw_token2}"})
        self.assertEqual(s_idle, 401)

        # Logout explicitly invalidates session and sends clearance cookie
        raw_token3, _ = create_session(self.db, user_id=10, client="web")
        out_status, _, out_headers = self._http_request(
            "POST",
            "/auth/logout",
            headers={"Cookie": f"cif_session={raw_token3}", "Origin": self.base_url}
        )
        self.assertEqual(out_status, 200)
        self.assertIn("Max-Age=0", out_headers.get("Set-Cookie", ""))

        # Subsequent query is unauthorized
        s_after, _, _ = self._http_request("GET", "/api/me", headers={"Cookie": f"cif_session={raw_token3}"})
        self.assertEqual(s_after, 401)

    # 11. VS Code Client Auth Flow (Phase 9)
    def test_vscode_client_login_and_callback(self):
        """Validates client=vscode generates vscode:// URI redirect and exchanges code for token."""
        # Initiate login for VS Code client
        status, _, headers = self._http_request("GET", "/auth/github/login?client=vscode&ext_id=cif.cif-vscode")
        self.assertEqual(status, 302)
        loc = headers["Location"]
        self.assertIn("github.com/login/oauth/authorize", loc)
        parsed_q = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query)
        raw_state = parsed_q["state"][0]

        # Callback from GitHub
        fake_urlopen = self._mock_github_responses(access_token="gh_vscode_token_xyz", login="vscoder", github_id=88881)
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            s_cb, _, cb_headers = self._http_request("GET", f"/auth/github/callback?code=gh_oauth_code_123&state={raw_state}")
            self.assertEqual(s_cb, 302)
            cb_loc = cb_headers["Location"]
            self.assertTrue(cb_loc.startswith("vscode://cif.cif-vscode/auth?code="))
            one_time_code = urllib.parse.parse_qs(urllib.parse.urlparse(cb_loc).query)["code"][0]

        # Exchange code via /auth/token/exchange
        s_exch, exch_data, _ = self._http_request("POST", "/auth/token/exchange", data={"code": one_time_code})
        self.assertEqual(s_exch, 200)
        self.assertIn("token", exch_data)
        self.assertEqual(exch_data.get("login"), "vscoder")

        # Verify bearer token works
        raw_token = exch_data["token"]
        s_me, me_data, _ = self._http_request("GET", "/api/me", headers={"Authorization": f"Bearer {raw_token}"})
        self.assertEqual(s_me, 200)
        self.assertEqual(me_data.get("login"), "vscoder")


if __name__ == "__main__":
    unittest.main()
