"""
Unit tests for Context Intelligence Framework (CIF) Logging System
Verifies structured log files, rotating handlers, correlation IDs, and secret redaction.
"""
import unittest
import os
import logging
from backend.logging_config import (
    setup_logging,
    get_logger,
    set_request_id,
    get_request_id,
    SecretRedactionFilter,
    RequestIdFilter,
    LOGS_DIR
)


class TestLoggingSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_logging()

    def test_logs_directory_and_files_exist(self):
        self.assertTrue(os.path.isdir(LOGS_DIR), f"Logs directory not found at: {LOGS_DIR}")
        expected_logs = [
            "application.log",
            "api.log",
            "error.log",
            "database.log",
            "security.log",
            "rate_limit.log"
        ]
        for log_file in expected_logs:
            path = os.path.join(LOGS_DIR, log_file)
            self.assertTrue(
                os.path.isfile(path),
                f"Expected log file '{log_file}' was not created in {LOGS_DIR}"
            )

    def test_secret_redaction_filter(self):
        f = SecretRedactionFilter()

        # GitHub token
        rec1 = logging.LogRecord("cif.test", logging.INFO, "test.py", 10, "Using token ghp_ABC1234567890123456789012345678901234567", (), None)
        f.filter(rec1)
        self.assertNotIn("ghp_ABC", rec1.msg)
        self.assertIn("[REDACTED_GH_TOKEN]", rec1.msg)

        # Bearer token
        rec2 = logging.LogRecord("cif.test", logging.INFO, "test.py", 11, "Header: Bearer secret_session_token_123456", (), None)
        f.filter(rec2)
        self.assertNotIn("secret_session_token_123456", rec2.msg)
        self.assertIn("[REDACTED_TOKEN]", rec2.msg)

    def test_request_id_filter(self):
        rf = RequestIdFilter()
        set_request_id("req-uuid-test-999")
        rec = logging.LogRecord("cif.test", logging.INFO, "test.py", 12, "Processing request", (), None)
        rf.filter(rec)
        self.assertEqual(getattr(rec, "request_id", None), "req-uuid-test-999")


if __name__ == "__main__":
    unittest.main()

