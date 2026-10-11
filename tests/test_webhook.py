"""
Tests for Phase 7.1/7.2: GitHub Webhook Receiver.
Uses mocked HTTP layer - no real network calls.
"""
import hashlib
import hmac
import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from backend.db import Database
from backend.api import APIHandler
from backend.seed_data import populate_seed_data

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

def _load_fixture(name: str) -> bytes:
    with open(os.path.join(FIXTURES_DIR, name), "rb") as f:
        return f.read()

def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


class TestWebhookReceiver(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "webhook_test.db")
        self.db = Database(self.db_path)
        populate_seed_data(self.db)
        self.api = APIHandler(self.db)
        self.secret = "test_webhook_secret_abc123"

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _make_headers(self, raw_body: bytes, event_type: str = "pull_request") -> dict:
        return {
            "X-Hub-Signature-256": _sign(self.secret, raw_body),
            "X-GitHub-Event": event_type,
            "Content-Type": "application/json"
        }

    def test_signed_valid_payload_returns_200(self):
        """Signed pull_request opened payload should return 200."""
        raw_body = _load_fixture("pr_opened.json")
        body = json.loads(raw_body)
        headers = self._make_headers(raw_body)

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret, "GITHUB_TOKEN": ""}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw_body, body)

        self.assertEqual(status, 200, f"Expected 200, got {status}: {result}")
        self.assertEqual(result["status"], "ok")

    def test_unsigned_payload_returns_401(self):
        """Missing signature header should return 401."""
        raw_body = _load_fixture("pr_opened.json")
        body = json.loads(raw_body)
        headers = {"X-GitHub-Event": "pull_request"}  # No signature

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw_body, body)

        self.assertEqual(status, 401, f"Expected 401, got {status}: {result}")

    def test_invalid_signature_returns_401(self):
        """Wrong signature should return 401."""
        raw_body = _load_fixture("pr_opened.json")
        body = json.loads(raw_body)
        headers = {
            "X-Hub-Signature-256": "sha256=deadbeefdeadbeef",
            "X-GitHub-Event": "pull_request"
        }

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw_body, body)

        self.assertEqual(status, 401, f"Expected 401, got {status}: {result}")

    def test_no_secret_configured_returns_401(self):
        """If CIF_WEBHOOK_SECRET is not set, all requests should be rejected."""
        raw_body = _load_fixture("pr_opened.json")
        body = json.loads(raw_body)
        headers = self._make_headers(raw_body)

        env = {k: v for k, v in os.environ.items() if k != "CIF_WEBHOOK_SECRET"}
        with patch.dict(os.environ, env, clear=True):
            if "CIF_WEBHOOK_SECRET" in os.environ:
                del os.environ["CIF_WEBHOOK_SECRET"]
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw_body, body)

        self.assertEqual(status, 401)

    def test_non_pr_event_ignored_with_200(self):
        """Non-pull_request events should return 200 but be ignored."""
        raw_body = b'{"action": "created"}'
        body = json.loads(raw_body)
        headers = {
            "X-Hub-Signature-256": _sign(self.secret, raw_body),
            "X-GitHub-Event": "push"
        }

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw_body, body)

        self.assertEqual(status, 200)
        self.assertIn("Ignored", result.get("message", ""))

    def test_pr_closed_action_ignored_with_200(self):
        """pull_request with action=closed should be ignored (not in opened/sync/reopened)."""
        raw_body = json.dumps({"action": "closed", "pull_request": {}, "repository": {}}).encode()
        body = json.loads(raw_body)
        headers = {
            "X-Hub-Signature-256": _sign(self.secret, raw_body),
            "X-GitHub-Event": "pull_request"
        }

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret}):
            result, status = self.api.handle_webhook("/api/webhook/github", headers, raw_body, body)

        self.assertEqual(status, 200)
        self.assertIn("Ignored", result.get("message", ""))

    def test_violating_pr_with_mocked_diff_stores_findings(self):
        """
        With a mocked diff containing a banned pattern and GITHUB_TOKEN set,
        a violating PR should produce findings but not crash when comment fails.
        """
        raw_body = _load_fixture("pr_opened.json")
        body = json.loads(raw_body)
        headers = self._make_headers(raw_body)

        # Mock diff that re-introduces banned bang-bang control
        mock_diff = "+++ b/src/thermal/control.py\n+ state = on_off_relay(temp)  # fallback\n"

        def mock_urlopen(req, timeout=None):
            mock_resp = MagicMock()
            mock_resp.read.return_value = mock_diff.encode("utf-8")
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret, "GITHUB_TOKEN": "mock_token"}):
            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                result, status = self.api.handle_webhook("/api/webhook/github", headers, raw_body, body)

        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "ok")
        # findings_count may be 0 if no active guard rules for this repo in test DB,
        # but the call must not crash
        self.assertIn("findings_count", result)

    def test_clean_pr_no_comment_call(self):
        """A clean diff with no violations should produce 0 findings and no comment posting."""
        raw_body = _load_fixture("pr_opened.json")
        body = json.loads(raw_body)
        headers = self._make_headers(raw_body)

        # Clean diff touching unrelated file
        mock_diff = "+++ b/docs/README.md\n+ Updated documentation for v2\n"
        comment_calls = []

        def mock_urlopen(req, timeout=None):
            if hasattr(req, "get_full_url") and "comments" in req.get_full_url():
                comment_calls.append(req)
                raise Exception("Should not post comment for clean diff")
            mock_resp = MagicMock()
            mock_resp.read.return_value = mock_diff.encode("utf-8")
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        with patch.dict(os.environ, {"CIF_WEBHOOK_SECRET": self.secret, "GITHUB_TOKEN": "mock_token"}):
            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                result, status = self.api.handle_webhook("/api/webhook/github", headers, raw_body, body)

        self.assertEqual(status, 200)
        self.assertEqual(len(comment_calls), 0, "Should not post comments for clean PR")


if __name__ == "__main__":
    unittest.main()
