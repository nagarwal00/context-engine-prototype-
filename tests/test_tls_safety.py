"""
Tests for TLS Safety and Certificate Verification (P0-a / Step 1.1)
"""
import os
import re
import ssl
import tempfile
import unittest
import urllib.error
from unittest.mock import patch, MagicMock

from backend.db import Database
from backend.ingestion.live_github import LiveGitHubIngestor, GitHubTLSError


class TestTLSSafety(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_tls.db")
        self.db = Database(self.db_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    @patch("urllib.request.urlopen")
    def test_cert_verification_error_raises_github_tls_error_once(self, mock_urlopen):
        secret_token = "ghp_super_secret_test_token_xyz987"
        ingestor = LiveGitHubIngestor(self.db, token=secret_token)

        # Mock urlopen to raise ssl.SSLCertVerificationError
        mock_urlopen.side_effect = ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED")

        with self.assertRaises(GitHubTLSError) as ctx:
            ingestor._make_request("/repos/owner/repo/commits")

        # Verify urlopen was called exactly once (no insecure fallback retry)
        self.assertEqual(mock_urlopen.call_count, 1)

        # Verify secret token is NOT leaked in the error message
        err_msg = str(ctx.exception)
        self.assertNotIn(secret_token, err_msg)
        self.assertIn("CIF_CA_BUNDLE", err_msg)

    @patch("urllib.request.urlopen")
    def test_urlerror_wrapping_cert_error_raises_github_tls_error_once(self, mock_urlopen):
        secret_token = "ghp_super_secret_test_token_xyz987"
        ingestor = LiveGitHubIngestor(self.db, token=secret_token)

        ssl_inner = ssl.SSLCertVerificationError("certificate verify failed")
        mock_urlopen.side_effect = urllib.error.URLError(ssl_inner)

        with self.assertRaises(GitHubTLSError) as ctx:
            ingestor._make_request("/repos/owner/repo/commits")

        self.assertEqual(mock_urlopen.call_count, 1)
        err_msg = str(ctx.exception)
        self.assertNotIn(secret_token, err_msg)
        self.assertIn("CIF_CA_BUNDLE", err_msg)

    def test_no_banned_ssl_strings_in_backend_or_tools(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        banned_patterns = [
            (re.compile(r"_create_unverified_context"), "_create_unverified_context"),
            (re.compile(r"CERT_NONE"), "CERT_NONE"),
            (re.compile(r"check_hostname\s*=\s*False"), "check_hostname = False"),
        ]

        found_violations = []
        for target_folder in ["backend", "tools"]:
            scan_path = os.path.join(root_dir, target_folder)
            if not os.path.isdir(scan_path):
                continue
            for cur_root, _, files in os.walk(scan_path):
                if "__pycache__" in cur_root:
                    continue
                for f in files:
                    if f.endswith(".py"):
                        full_path = os.path.join(cur_root, f)
                        with open(full_path, "r", encoding="utf-8") as file:
                            content = file.read()
                            for pat, name in banned_patterns:
                                if pat.search(content):
                                    rel = os.path.relpath(full_path, root_dir)
                                    found_violations.append(f"{rel}: banned string '{name}' found")

        self.assertEqual(found_violations, [], f"Banned insecure SSL patterns found:\n" + "\n".join(found_violations))


if __name__ == "__main__":
    unittest.main()
