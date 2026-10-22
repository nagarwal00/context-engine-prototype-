"""
Tests for Configuration and Auth Config Endpoint (Step 7.1)
Verifies:
- Missing vars -> login disabled, safe defaults for caps.
- Configured vars -> login enabled, values parsed.
- Secrets NEVER appear in repr, str, or safe dictionary output.
- /api/auth-config returns only { login_enabled, app_slug }.
- Server starts and serves /api/auth-config without credentials.
"""
import json
import logging
import os
import unittest
from io import StringIO
import urllib.request
import threading
import http.server

from backend.config import Config, get_config, reload_config
from backend.db import Database
from backend.api import APIHandler
from server import ContextIntelligenceServer


class TestConfig(unittest.TestCase):
    def setUp(self):
        # Save original environ
        self._orig_env = dict(os.environ)

    def tearDown(self):
        # Restore environ
        os.environ.clear()
        os.environ.update(self._orig_env)
        reload_config()

    def test_missing_vars_reports_disabled_and_defaults(self):
        """When GitHub vars are missing, login is disabled and caps use defaults."""
        cfg = Config(env={})
        self.assertFalse(cfg.is_login_enabled())
        self.assertEqual(cfg.get_github_app_slug(), "")
        self.assertIsNone(cfg.get_github_app_id())
        self.assertEqual(cfg.get_github_client_id(), "")
        self.assertEqual(cfg.get_github_client_secret(), "")
        self.assertIsNone(cfg.get_github_private_key_path())
        self.assertIsNone(cfg.get_token_enc_key())
        self.assertEqual(cfg.get_extension_ids(), [])
        self.assertEqual(cfg.get_base_url(), "http://127.0.0.1:8080")

        # Ingestion limits defaults
        self.assertEqual(cfg.get_max_commits(), 5000)
        self.assertEqual(cfg.get_max_prs(), 1500)
        self.assertEqual(cfg.get_max_issues(), 1500)
        self.assertEqual(cfg.get_max_tarball_mb(), 100)

        # Public config contains only login_enabled and app_slug
        pub = cfg.get_public_auth_config()
        self.assertEqual(pub, {"login_enabled": False, "app_slug": ""})
        self.assertEqual(set(pub.keys()), {"login_enabled", "app_slug"})

    def test_configured_vars_reports_enabled_and_parses_values(self):
        """When credentials are provided, login is enabled and fields parse correctly."""
        env = {
            "CIF_BASE_URL": "https://cif.internal.company.com/",
            "CIF_SESSION_SECRET": "ultra_secret_session_key_999",
            "GITHUB_APP_SLUG": "cif-decision-intelligence",
            "GITHUB_APP_ID": "123456",
            "GITHUB_APP_CLIENT_ID": "Iv1.client_id_abc",
            "GITHUB_APP_CLIENT_SECRET": "secret_app_token_xyz_888",
            "GITHUB_APP_PRIVATE_KEY_PATH": "/path/to/key.pem",
            "CIF_TOKEN_ENC_KEY": "enc_key_secret_333",
            "CIF_EXTENSION_IDS": "ext_chrome_id_1, ext_chrome_id_2 , ",
            "CIF_MAX_COMMITS": "2500",
            "CIF_MAX_PRS": "800",
            "CIF_MAX_ISSUES": "900",
            "CIF_MAX_TARBALL_MB": "50",
        }
        cfg = Config(env=env)
        self.assertTrue(cfg.is_login_enabled())
        self.assertEqual(cfg.get_base_url(), "https://cif.internal.company.com")
        self.assertEqual(cfg.get_github_app_slug(), "cif-decision-intelligence")
        self.assertEqual(cfg.get_github_app_id(), 123456)
        self.assertEqual(cfg.get_github_client_id(), "Iv1.client_id_abc")
        self.assertEqual(cfg.get_github_client_secret(), "secret_app_token_xyz_888")
        self.assertEqual(cfg.get_github_private_key_path(), "/path/to/key.pem")
        self.assertEqual(cfg.get_token_enc_key(), "enc_key_secret_333")
        self.assertEqual(cfg.get_extension_ids(), ["ext_chrome_id_1", "ext_chrome_id_2"])
        self.assertTrue(cfg.is_extension_id_allowed("ext_chrome_id_1"))
        self.assertTrue(cfg.is_extension_id_allowed("ext_chrome_id_2"))
        self.assertFalse(cfg.is_extension_id_allowed("unknown_ext"))

        self.assertEqual(cfg.get_max_commits(), 2500)
        self.assertEqual(cfg.get_max_prs(), 800)
        self.assertEqual(cfg.get_max_issues(), 900)
        self.assertEqual(cfg.get_max_tarball_mb(), 50)

        pub = cfg.get_public_auth_config()
        self.assertEqual(pub, {
            "login_enabled": True,
            "app_slug": "cif-decision-intelligence",
        })
        self.assertEqual(set(pub.keys()), {"login_enabled", "app_slug"})

    def test_secrets_never_in_repr_str_or_logs(self):
        """Strict check: sensitive secrets must never appear in repr, str, or log output."""
        sensitive_session = "SECRET_SESSION_TOKEN_NEVER_LEAK"
        sensitive_client_sec = "SECRET_GITHUB_CLIENT_SECRET_NEVER_LEAK"
        sensitive_enc = "SECRET_ENC_KEY_NEVER_LEAK"

        env = {
            "CIF_SESSION_SECRET": sensitive_session,
            "GITHUB_APP_CLIENT_SECRET": sensitive_client_sec,
            "CIF_TOKEN_ENC_KEY": sensitive_enc,
            "GITHUB_APP_CLIENT_ID": "client_id_123",
            "GITHUB_APP_SLUG": "test-slug",
        }
        cfg = Config(env=env)

        # repr & str checks
        repr_str = repr(cfg)
        str_str = str(cfg)
        safe_dict = str(cfg.to_dict_safe())

        for text in (repr_str, str_str, safe_dict):
            self.assertNotIn(sensitive_session, text)
            self.assertNotIn(sensitive_client_sec, text)
            self.assertNotIn(sensitive_enc, text)
            self.assertIn("[REDACTED]", text)

        # Logging check
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger("test_config_logger")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        logger.info("Configuration state: %s", cfg)
        logger.debug("Config dict: %r", cfg.to_dict_safe())

        log_output = log_stream.getvalue()
        self.assertNotIn(sensitive_session, log_output)
        self.assertNotIn(sensitive_client_sec, log_output)
        self.assertNotIn(sensitive_enc, log_output)

    def test_invalid_integer_caps_fallback_to_defaults(self):
        """Non-numeric or non-positive caps must safely fall back to positive defaults."""
        env = {
            "CIF_MAX_COMMITS": "-10",
            "CIF_MAX_PRS": "invalid_number",
            "CIF_MAX_ISSUES": "0",
            "CIF_MAX_TARBALL_MB": "abc",
        }
        cfg = Config(env=env)
        self.assertEqual(cfg.get_max_commits(), 5000)
        self.assertEqual(cfg.get_max_prs(), 1500)
        self.assertEqual(cfg.get_max_issues(), 1500)
        self.assertEqual(cfg.get_max_tarball_mb(), 100)

    def test_public_auth_config_via_http_server(self):
        """GET /api/auth-config works over real HTTP and returns only login_enabled and app_slug."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            temp_db_path = tf.name

        try:
            db = Database(temp_db_path)
            api_handler = APIHandler(db)

            # Clean environment without GitHub credentials
            clean_env = {k: v for k, v in os.environ.items() if not k.startswith("GITHUB_") and not k.startswith("CIF_")}
            clean_env["CIF_DEV_MODE"] = "1"
            reload_config(env=clean_env)

            server_address = ("127.0.0.1", 0)
            httpd = http.server.ThreadingHTTPServer(server_address, ContextIntelligenceServer)
            httpd.api_handler = api_handler
            port = httpd.server_address[1]

            t = threading.Thread(target=httpd.serve_forever, daemon=True)
            t.start()

            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/auth-config")
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
                body = json.loads(resp.read().decode("utf-8"))

            self.assertEqual(body, {"login_enabled": False, "app_slug": ""})
            self.assertEqual(set(body.keys()), {"login_enabled", "app_slug"})

            httpd.shutdown()
            httpd.server_close()
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)


if __name__ == "__main__":
    unittest.main()
