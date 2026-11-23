"""
Regression tests for leaked SQLite connections (Windows test-suite failure, 2026-11-23).

Symptom on Windows: 6 errors in tests/test_db_integrity.py, raised from tearDown:
    NotADirectoryError: [WinError 267] The directory name is invalid: ...\\integrity.db
Root cause: a helper returned a bare sqlite3 connection used as `with self._conn() as conn:`.
sqlite3's `with conn:` commits/rolls back but never closes, so the file stayed open; Windows
cannot delete an open file, so TemporaryDirectory.cleanup() failed (PermissionError, which
tempfile's retry logic then reported as WinError 267). Linux allows deleting open files, so the
bug was invisible there. These tests detect it on every platform.
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Modules that leaked connections before the fix.
PREVIOUSLY_LEAKING = [
    "tests.test_db_integrity",
    "tests.test_history_recorded",
    "tests.test_migration_auth_tables",
    "tests.test_precision_sampling",  # exercises tools/make_precision_sample.py
]


class NoLeakedConnectionsTests(unittest.TestCase):
    def test_previously_leaking_modules_close_every_connection(self):
        """Python reports a ResourceWarning for each connection garbage-collected while open."""
        proc = subprocess.run(
            [sys.executable, "-X", "dev", "-W", "always::ResourceWarning",
             "-m", "unittest", *PREVIOUSLY_LEAKING],
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=600)
        self.assertEqual(proc.returncode, 0, proc.stderr[-3000:])
        leaks = proc.stderr.count("unclosed database")
        self.assertEqual(leaks, 0, f"{leaks} SQLite connection(s) left open:\n{proc.stderr[-3000:]}")


class ConnHelperClosesTests(unittest.TestCase):
    def setUp(self):
        from tests.test_db_integrity import EvidenceInvariantTests
        self.case = EvidenceInvariantTests("test_seed_data_is_fully_grounded")
        self.case.setUp()  # creates a seeded temp DB; its cleanup is registered via addCleanup
        self.addCleanup(self.case.doCleanups)

    def test_connection_is_closed_after_normal_exit(self):
        with self.case._conn() as conn:
            conn.execute("SELECT 1")
        with self.assertRaises(sqlite3.ProgrammingError):  # "Cannot operate on a closed database"
            conn.execute("SELECT 1")

    def test_connection_is_closed_when_the_block_raises(self):
        with self.assertRaises(RuntimeError):
            with self.case._conn() as conn:
                raise RuntimeError("simulated assertion failure inside the block")
        with self.assertRaises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")


class WindowsStyleCleanupTests(unittest.TestCase):
    def test_database_file_and_folder_can_be_deleted_without_ignoring_errors(self):
        """On Windows this is exactly what failed: deleting a DB file that is still open."""
        from tests.test_db_integrity import EvidenceInvariantTests
        case = EvidenceInvariantTests("test_cannot_promote_a_decision_without_evidence")
        case.setUp()
        try:
            case.test_cannot_promote_a_decision_without_evidence()  # opens, writes, raises inside
            folder = case.tmp.name
            os.remove(case.path)   # raises PermissionError on Windows if a handle is still open
            os.rmdir(folder)       # folder must now be empty and removable
            self.assertFalse(os.path.exists(folder))
        finally:
            case.doCleanups()      # TemporaryDirectory.cleanup tolerates the already-removed folder

    def test_temporary_directory_cleanup_succeeds(self):
        tmp = tempfile.TemporaryDirectory()
        path = os.path.join(tmp.name, "x.db")
        from contextlib import closing
        with closing(sqlite3.connect(path)) as conn, conn:
            conn.execute("CREATE TABLE t (x)")
        tmp.cleanup()  # must not raise (no ignore_cleanup_errors)
        self.assertFalse(os.path.exists(tmp.name))


if __name__ == "__main__":
    unittest.main()
