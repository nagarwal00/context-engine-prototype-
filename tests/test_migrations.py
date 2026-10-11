import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from backend.db import Database
from backend.migrations import (
    run_migrations,
    get_applied_migrations,
    get_available_migrations,
    ensure_schema_migrations_table,
)


class TestMigrations(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_schema_migrations_table_created_on_new_db(self):
        """Database initialization must create schema_migrations table."""
        db_path = os.path.join(self.tmp_dir.name, "fresh.db")
        db = Database(db_path)

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
            self.assertIsNotNone(cursor.fetchone(), "schema_migrations table must exist on fresh database")

            cursor.execute("PRAGMA table_info(schema_migrations)")
            cols = {row["name"]: row["type"].upper() for row in cursor.fetchall()}
            self.assertIn("version", cols)
            self.assertIn("name", cols)
            self.assertIn("applied_at", cols)

    def test_running_migrations_twice_is_noop(self):
        """Applying migrations twice must be a no-op on the second run."""
        # Create a mock migrations directory
        mock_mig_dir = os.path.join(self.tmp_dir.name, "mock_migrations")
        os.makedirs(mock_mig_dir)

        mig1_content = """
def upgrade(conn):
    conn.execute("CREATE TABLE mock_alpha (id INTEGER PRIMARY KEY, label TEXT);")
"""
        with open(os.path.join(mock_mig_dir, "001_create_alpha.py"), "w", encoding="utf-8") as f:
            f.write(mig1_content)

        db_path = os.path.join(self.tmp_dir.name, "test_noop.db")
        conn = sqlite3.connect(db_path)
        try:
            # First run: applies migration 1
            first_run = run_migrations(conn, migrations_dir=mock_mig_dir, dry_run=False)
            self.assertEqual(len(first_run), 1)
            self.assertEqual(first_run[0]["version"], 1)

            applied = get_applied_migrations(conn)
            self.assertEqual(applied, [1])

            # Second run: should be a no-op
            second_run = run_migrations(conn, migrations_dir=mock_mig_dir, dry_run=False)
            self.assertEqual(len(second_run), 0, "Second run must apply 0 migrations")

            applied_after = get_applied_migrations(conn)
            self.assertEqual(applied_after, [1])
        finally:
            conn.close()

    def test_failed_migration_rolls_back_and_leaves_db_unchanged(self):
        """A failed migration must roll back its transaction and not record in schema_migrations."""
        mock_mig_dir = os.path.join(self.tmp_dir.name, "mock_failing_migrations")
        os.makedirs(mock_mig_dir)

        # Migration 1: good
        with open(os.path.join(mock_mig_dir, "001_good.py"), "w", encoding="utf-8") as f:
            f.write("""
def upgrade(conn):
    conn.execute("CREATE TABLE good_table (id INTEGER PRIMARY KEY);")
""")

        # Migration 2: creates bad_table then raises an exception
        with open(os.path.join(mock_mig_dir, "002_bad.py"), "w", encoding="utf-8") as f:
            f.write("""
def upgrade(conn):
    conn.execute("CREATE TABLE bad_table (id INTEGER PRIMARY KEY);")
    raise ValueError("Deliberate failure inside migration 002")
""")

        db_path = os.path.join(self.tmp_dir.name, "test_fail.db")
        conn = sqlite3.connect(db_path)
        try:
            with self.assertRaises(RuntimeError) as ctx:
                run_migrations(conn, migrations_dir=mock_mig_dir, dry_run=False)

            self.assertIn("Deliberate failure inside migration 002", str(ctx.exception))

            # Migration 1 was committed before migration 2 ran
            applied = get_applied_migrations(conn)
            self.assertEqual(applied, [1], "Only migration 1 should be recorded as applied")

            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='good_table'")
            self.assertIsNotNone(cursor.fetchone(), "good_table should exist")

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bad_table'")
            self.assertIsNone(cursor.fetchone(), "bad_table must not exist due to transaction rollback")
        finally:
            conn.close()

    def test_dry_run_does_not_apply_migrations(self):
        """dry_run=True must report pending migrations without executing them."""
        mock_mig_dir = os.path.join(self.tmp_dir.name, "mock_dry_run")
        os.makedirs(mock_mig_dir)

        with open(os.path.join(mock_mig_dir, "001_dry.py"), "w", encoding="utf-8") as f:
            f.write("""
def upgrade(conn):
    conn.execute("CREATE TABLE dry_table (id INTEGER PRIMARY KEY);")
""")

        db_path = os.path.join(self.tmp_dir.name, "test_dry.db")
        conn = sqlite3.connect(db_path)
        try:
            report = run_migrations(conn, migrations_dir=mock_mig_dir, dry_run=True)
            self.assertEqual(len(report), 1)
            self.assertEqual(report[0]["status"], "pending")

            applied = get_applied_migrations(conn)
            self.assertEqual(len(applied), 0, "No migrations should be marked applied during dry run")

            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dry_table'")
            self.assertIsNone(cursor.fetchone(), "dry_table must not exist after dry run")
        finally:
            conn.close()

    def test_cli_migrate_tool(self):
        """tools/migrate_db.py CLI tool executes properly with --dry-run and apply."""
        db_path = os.path.join(self.tmp_dir.name, "cli_test.db")
        # Initialize basic empty db
        conn = sqlite3.connect(db_path)
        conn.close()

        # Run CLI with --dry-run
        res_dry = subprocess.run(
            [sys.executable, "tools/migrate_db.py", "--db", db_path, "--dry-run"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res_dry.returncode, 0)
        self.assertIn("[MIGRATE] Target database:", res_dry.stdout)

        # Run CLI without --dry-run
        res_apply = subprocess.run(
            [sys.executable, "tools/migrate_db.py", "--db", db_path],
            capture_output=True,
            text=True
        )
        self.assertEqual(res_apply.returncode, 0)

    def test_migrations_on_pre_v2_backup_copy(self):
        """Validates migration runner against an exact copy of backups/context_intelligence.pre_v2.db."""
        backup_path = os.path.join("backups", "context_intelligence.pre_v2.db")
        if not os.path.exists(backup_path):
            self.skipTest(f"Pre-v2 backup not found at {backup_path}; skipping.")

        # Create isolated copy
        copy_path = os.path.join(self.tmp_dir.name, "backup_copy.db")
        shutil.copyfile(backup_path, copy_path)

        # Inspect pre-migration counts
        orig_conn = sqlite3.connect(copy_path)
        orig_conn.row_factory = sqlite3.Row
        cur = orig_conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM decisions")
        orig_decisions_count = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM events")
        orig_events_count = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM entities")
        orig_entities_count = cur.fetchone()["c"]
        orig_conn.close()

        # Run migration runner on the copy
        mig_conn = sqlite3.connect(copy_path)
        mig_conn.row_factory = sqlite3.Row
        try:
            run_migrations(mig_conn, dry_run=False)

            # Check that schema_migrations table was created
            cur = mig_conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
            self.assertIsNotNone(cur.fetchone())

            # Verify no data loss in pre-existing tables
            cur.execute("SELECT COUNT(*) AS c FROM decisions")
            self.assertEqual(cur.fetchone()["c"], orig_decisions_count)
            cur.execute("SELECT COUNT(*) AS c FROM events")
            self.assertEqual(cur.fetchone()["c"], orig_events_count)
            cur.execute("SELECT COUNT(*) AS c FROM entities")
            self.assertEqual(cur.fetchone()["c"], orig_entities_count)

            # Re-running is a no-op
            second_run = run_migrations(mig_conn, dry_run=False)
            self.assertEqual(len(second_run), 0)
        finally:
            mig_conn.close()


if __name__ == "__main__":
    unittest.main()
