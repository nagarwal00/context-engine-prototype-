"""
Unit and Integration Tests for Privacy-First Ingestion Sanitizer (Step 5.1)
Verifies redaction of all secret classes, raw-byte SQLite database scanning,
URL query parameter redaction, logging filter scrub, and repository purge retention.
"""
import os
import io
import json
import logging
import tempfile
import unittest
from backend.models import Event, Decision, Entity, Edge
from backend.db import Database
from backend.ingestion.sanitizer import (
    sanitize_text,
    sanitize_url,
    sanitize_author,
    sanitize_metadata,
    sanitize_event,
    SanitizingLogFilter,
    install_sanitizing_logger
)
from backend.ingestion.identity import IdentityResolver
from backend.ingestion.git_adapter import GitAdapter
from backend.ingestion.github_adapter import GitHubAdapter
from backend.ingestion.adr_adapter import ADRAdapter
from backend.api import APIHandler


class TestSanitizer(unittest.TestCase):
    def setUp(self):
        # Build synthetic secrets strictly at runtime by string concatenation
        # to ensure no realistic secrets exist in source code (scanner-safe).
        self.gh_pat = "gh" + "p_" + "1234567890abcdefghijklmnopqrstuvwxyzABCD"
        self.gh_oauth = "gh" + "o_" + "1234567890abcdefghijklmnopqrstuvwxyzABCD"
        self.gh_server = "gh" + "s_" + "1234567890abcdefghijklmnopqrstuvwxyzABCD"
        self.gh_fine = "github_" + "pat_" + "11ABCD_1234567890abcdefghijklmnopqrstuvwxyz"
        self.aws_key = "AK" + "IA" + "1234567890ABCDEF"
        self.aws_secret_val = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        self.slack_token = "xo" + "xb-" + "1234567890-abcdefghijklmnopqrstuv"
        self.google_key = "AI" + "za" + "SyD1234567890abcdefghijklmnopqrstuv"
        self.jwt_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4ifQ."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        self.bearer_token = "mySuperSecretBearerTokenValue123456789"
        self.password_val = "SuperSecretPassword123!"
        self.api_key_val = "abc123secretAPIKeyPayload987654"
        self.private_key_block = (
            "-----BEGIN RSA " + "PRIVATE KEY-----\n"
            "MIIEowIBAAKCAQEA0syntheticPrivateKeyBlockForTestingOnly1234567890\n"
            "-----END RSA " + "PRIVATE KEY-----"
        )
        self.email_val = "developer" + "@" + "company-internal-domain.com"
        self.phone_val = "555-019-2834"

    def test_sanitize_text_all_secret_categories(self):
        """Verifies that all secret classes are redacted in raw text."""
        # GitHub tokens
        self.assertNotIn(self.gh_pat, sanitize_text(f"Token: {self.gh_pat}"))
        self.assertIn("[REDACTED:GITHUB_TOKEN]", sanitize_text(f"Token: {self.gh_pat}"))
        self.assertNotIn(self.gh_oauth, sanitize_text(f"OAuth: {self.gh_oauth}"))
        self.assertNotIn(self.gh_fine, sanitize_text(f"PAT: {self.gh_fine}"))

        # AWS keys and secrets
        s_aws = sanitize_text(f"AWS ID is {self.aws_key} and aws_secret_access_key = '{self.aws_secret_val}'")
        self.assertNotIn(self.aws_key, s_aws)
        self.assertNotIn(self.aws_secret_val, s_aws)
        self.assertIn("[REDACTED:AWS_KEY]", s_aws)

        # Slack token
        s_slack = sanitize_text(f"Slack bot token is {self.slack_token}")
        self.assertNotIn(self.slack_token, s_slack)
        self.assertIn("[REDACTED:SLACK_TOKEN]", s_slack)

        # Google API key
        s_google = sanitize_text(f"Key is {self.google_key}")
        self.assertNotIn(self.google_key, s_google)
        self.assertIn("[REDACTED:GOOGLE_KEY]", s_google)

        # Private Key
        s_pk = sanitize_text(f"Certificate key:\n{self.private_key_block}\nFinished")
        self.assertNotIn("syntheticPrivateKeyBlock", s_pk)
        self.assertIn("[REDACTED:PRIVATE_KEY]", s_pk)

        # JWT
        s_jwt = sanitize_text(f"User JWT: {self.jwt_token}")
        self.assertNotIn(self.jwt_token, s_jwt)
        self.assertIn("[REDACTED:JWT]", s_jwt)

        # Bearer
        s_bearer = sanitize_text(f"Authorization: Bearer {self.bearer_token}")
        self.assertNotIn(self.bearer_token, s_bearer)
        self.assertIn("[REDACTED:BEARER_TOKEN]", s_bearer)

        # Password and API key assignments
        s_pass = sanitize_text(f"DB password = '{self.password_val}' and api_key: \"{self.api_key_val}\"")
        self.assertNotIn(self.password_val, s_pass)
        self.assertNotIn(self.api_key_val, s_pass)
        self.assertIn("[REDACTED:SECRET_ASSIGNMENT]", s_pass)

    def test_optional_pii_redaction(self):
        """Verifies that email and phone are preserved by default, but redacted when CIF_REDACT_PII=1."""
        text = f"Contact developer at {self.email_val} or call {self.phone_val}."
        
        # Default: PII not redacted
        os.environ.pop("CIF_REDACT_PII", None)
        s_default = sanitize_text(text)
        self.assertIn(self.email_val, s_default)

        # With CIF_REDACT_PII=1
        os.environ["CIF_REDACT_PII"] = "1"
        try:
            s_pii = sanitize_text(text)
            self.assertNotIn(self.email_val, s_pii)
            self.assertNotIn(self.phone_val, s_pii)
            self.assertIn("[REDACTED:EMAIL]", s_pii)
            self.assertIn("[REDACTED:PHONE]", s_pii)
        finally:
            os.environ.pop("CIF_REDACT_PII", None)

    def test_sanitize_url_query_parameters(self):
        """Verifies that query parameters and basic auth credentials in URLs are sanitized."""
        url = f"https://admin:{self.password_val}@github.com/org/repo/pull/42?token={self.gh_pat}&session_id=98765"
        sanitized = sanitize_url(url)
        self.assertNotIn(self.password_val, sanitized)
        self.assertNotIn(self.gh_pat, sanitized)
        self.assertNotIn("98765", sanitized)
        self.assertIn("[REDACTED:CREDENTIALS]", sanitized)
        self.assertIn("[REDACTED:QUERY_PARAM]", sanitized)

    def test_sanitize_metadata_recursive(self):
        """Verifies nested dictionaries and lists are thoroughly sanitized."""
        meta = {
            "author": "Alice",
            "nested": {
                "token": self.gh_pat,
                "config": [f"key={self.api_key_val}", "normal_value"]
            },
            "secret_field": self.password_val
        }
        sanitized = sanitize_metadata(meta)
        self.assertNotIn(self.gh_pat, json.dumps(sanitized))
        self.assertNotIn(self.api_key_val, json.dumps(sanitized))
        self.assertNotIn(self.password_val, json.dumps(sanitized))
        self.assertEqual(sanitized["author"], "Alice")
        self.assertEqual(sanitized["nested"]["config"][1], "normal_value")

    def test_raw_byte_scan_sqlite_database(self):
        """
        Critical Acceptance Test (Step 5.1):
        Ingests events containing every secret type into an SQLite DB,
        then performs a raw byte scan of the database file on disk.
        Asserts that ZERO secret strings appear in the raw bytes.
        """
        temp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(temp_dir.name, "privacy_test.db")
        db = Database(db_path)
        id_res = IdentityResolver(db)

        git_adapter = GitAdapter(db, id_res)
        gh_adapter = GitHubAdapter(db, id_res)
        adr_adapter = ADRAdapter(db, id_res)

        # 1. Ingest commit with secrets in message and diff
        git_adapter.ingest_commit_record(
            repo="org/repo",
            commit_sha="a" * 40,
            author_raw="Alice <alice@example.com>",
            timestamp="2026-03-01T10:00:00Z",
            message=f"Fix bug with token {self.gh_pat}\n\npassword = '{self.password_val}'",
            files_changed=["src/auth.py"],
            diff_summary=f"+ api_key = '{self.api_key_val}'"
        )

        # 2. Ingest issue with secrets in title and body
        gh_adapter.ingest_issue(
            repo="org/repo",
            issue_number=101,
            title=f"Setup AWS key {self.aws_key}",
            body=f"Credentials:\naws_secret_access_key = '{self.aws_secret_val}'\nSlack: {self.slack_token}",
            author_raw="Bob",
            created_at="2026-03-02T11:00:00Z"
        )

        # 3. Ingest review comment with private key and bearer header
        gh_adapter.ingest_review_comment(
            repo="org/repo",
            pr_number=202,
            comment_id="comm_99",
            author_raw="Charlie",
            timestamp="2026-03-03T12:00:00Z",
            body=f"Here is the certificate:\n{self.private_key_block}\nHeader: Authorization: Bearer {self.bearer_token}"
        )

        # 4. Ingest ADR with Google key and JWT in URL query
        adr_adapter.ingest_doc_file(
            repo="org/repo",
            file_path="docs/architecture.md",
            title=f"Google Integration Key {self.google_key}",
            content=f"Using token: {self.jwt_token}",
            author_raw="Dave",
            timestamp="2026-03-04T14:00:00Z"
        )

        # Read the SQLite database file in binary mode for raw-byte scanning
        with open(db_path, "rb") as f:
            raw_bytes = f.read()

        all_secrets = [
            self.gh_pat,
            self.aws_key,
            self.aws_secret_val,
            self.slack_token,
            self.google_key,
            self.bearer_token,
            self.password_val,
            self.api_key_val,
            "syntheticPrivateKeyBlockForTestingOnly",
            self.jwt_token
        ]

        # Assert NONE of the secrets exist in raw database bytes
        for sec in all_secrets:
            self.assertNotIn(
                sec.encode("utf-8"),
                raw_bytes,
                f"Privacy Violation: Raw secret '{sec}' was persisted in SQLite database bytes!"
            )

        # Assert replacement tokens ARE present
        self.assertIn(b"[REDACTED:GITHUB_TOKEN]", raw_bytes)
        self.assertIn(b"[REDACTED:AWS_KEY]", raw_bytes)
        self.assertIn(b"[REDACTED:SLACK_TOKEN]", raw_bytes)
        self.assertIn(b"[REDACTED:PRIVATE_KEY]", raw_bytes)

        temp_dir.cleanup()

    def test_sanitizing_log_filter(self):
        """Verifies that SanitizingLogFilter scrubs secrets from logger output."""
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.addFilter(SanitizingLogFilter())
        
        logger = logging.getLogger("test_privacy_logger")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        logger.info(f"Failed with token {self.gh_pat} and secret {self.password_val}")
        output = stream.getvalue()

        self.assertNotIn(self.gh_pat, output)
        self.assertNotIn(self.password_val, output)
        self.assertIn("[REDACTED:GITHUB_TOKEN]", output)

    def test_purge_repo_endpoint_retention(self):
        """Verifies that POST /api/purge-repo deletes all records for a repository."""
        temp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(temp_dir.name, "purge_test.db")
        db = Database(db_path)
        api = APIHandler(db)

        # Seed data for repoA and repoB
        ev_a = Event(
            event_id="evt_a1",
            source_type="git_commit",
            source_id="c1",
            source_url="https://github.com/org/repoA/commit/1",
            repo="org/repoA",
            author="Alice",
            timestamp="2026-03-01T10:00:00Z",
            title="Repo A Commit",
            body="Commit on Repo A"
        )
        ev_b = Event(
            event_id="evt_b1",
            source_type="git_commit",
            source_id="c2",
            source_url="https://github.com/org/repoB/commit/2",
            repo="org/repoB",
            author="Bob",
            timestamp="2026-03-01T10:00:00Z",
            title="Repo B Commit",
            body="Commit on Repo B"
        )
        db.upsert_event(ev_a)
        db.upsert_event(ev_b)

        dec_a = Decision(
            decision_id="dec_a1",
            title="Architecture Decision A1",
            state="accepted",
            repo="org/repoA",
            confidence=0.9,
            evidence_event_ids=["evt_a1"]
        )
        dec_b = Decision(
            decision_id="dec_b1",
            title="Architecture Decision B1",
            state="accepted",
            repo="org/repoB",
            confidence=0.9,
            evidence_event_ids=["evt_b1"]
        )
        db.save_decision(dec_a)
        db.save_decision(dec_b)

        # 1. Attempt purge with mismatching confirm
        bad_res = api.handle_post("/api/purge-repo", {"repo": "org/repoA", "confirm": "wrong_repo"})
        self.assertEqual(bad_res["status"], "error")
        self.assertEqual(bad_res["status_code"], 400)

        # 2. Successfully purge repoA
        ok_res = api.handle_post("/api/purge-repo", {"repo": "org/repoA", "confirm": "org/repoA"})
        self.assertEqual(ok_res["status"], "success")
        self.assertEqual(ok_res["deleted_counts"]["events"], 1)
        self.assertEqual(ok_res["deleted_counts"]["decisions"], 1)

        # 3. Verify repoA records are gone while repoB records remain
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as c FROM events WHERE repo = 'org/repoA'")
            self.assertEqual(cursor.fetchone()["c"], 0)

            cursor.execute("SELECT COUNT(*) as c FROM decisions WHERE repo = 'org/repoA'")
            self.assertEqual(cursor.fetchone()["c"], 0)

            cursor.execute("SELECT COUNT(*) as c FROM events WHERE repo = 'org/repoB'")
            self.assertEqual(cursor.fetchone()["c"], 1)

            cursor.execute("SELECT COUNT(*) as c FROM decisions WHERE repo = 'org/repoB'")
            self.assertEqual(cursor.fetchone()["c"], 1)

        temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
