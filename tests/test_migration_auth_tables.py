"""
Test Migration 007: Auth, Sessions, Repositories, Jobs, and Repo Attribution (Step 7.2)
Verifies:
- Migration works on a fresh database.
- Migration works on a copy of the real database without data loss.
- All new tables and columns exist with appropriate constraints.
- Repo attribution is backfilled on existing data tables.
- Demo repos are seeded with visibility='demo'.
- PRAGMA foreign_key_check reports 0 violations.
- Migration runner is idempotent on second execution.
"""
import os
import shutil
import sqlite3
import tempfile
import unittest

from backend.db import Database
from backend.migrations.runner import run_migrations, get_applied_migrations


class TestMigrationAuthTables(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.real_db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "context_intelligence.db"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_migration_on_fresh_db(self):
        """Verifies migration 007 applies cleanly on a brand new Database instance."""
        fresh_db_path = os.path.join(self.temp_dir, "fresh.db")
        db = Database(fresh_db_path)

        with db.get_connection() as conn:
            cur = conn.cursor()

            # Verify migration version 7 is registered
            applied = get_applied_migrations(conn)
            self.assertIn(7, applied)

            # Check new tables exist
            tables = [
                "users",
                "sessions",
                "oauth_states",
                "ext_codes",
                "repos",
                "repo_access",
                "repo_reviewers",
                "ingest_jobs",
                "user_tokens"
            ]
            for t in tables:
                cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (t,))
                self.assertIsNotNone(cur.fetchone(), f"Table {t} should exist")

            # Check demo repos seeded
            cur.execute("SELECT repo_full_name, visibility FROM repos")
            repos = dict(cur.fetchall())
            self.assertIn("acme-eng/thermal-control-system", repos)
            self.assertIn("acme-eng/distributed-cache-service", repos)
            self.assertEqual(repos["acme-eng/thermal-control-system"], "demo")
            self.assertEqual(repos["acme-eng/distributed-cache-service"], "demo")

            # Check PRAGMA foreign_key_check passes
            cur.execute("PRAGMA foreign_key_check;")
            violations = cur.fetchall()
            self.assertEqual(len(violations), 0, f"Foreign key violations found: {violations}")

    def test_migration_on_real_db_copy_without_data_loss(self):
        """Copies the real database and applies migration 007, ensuring data counts and attribution."""
        self.assertTrue(os.path.exists(self.real_db_path), "Real database file must exist")

        copy_path = os.path.join(self.temp_dir, "real_copy.db")
        shutil.copyfile(self.real_db_path, copy_path)

        # Record counts before running migrations
        before_counts = {}
        with sqlite3.connect(copy_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            for tbl in ["decisions", "events", "entities", "edges"]:
                cnt = c.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                before_counts[tbl] = cnt

        # Run migration runner on the copy
        with sqlite3.connect(copy_path) as conn:
            conn.row_factory = sqlite3.Row
            results = run_migrations(conn)
            cur = conn.cursor()

            # Foreign key check must pass
            cur.execute("PRAGMA foreign_key_check;")
            violations = cur.fetchall()
            self.assertEqual(len(violations), 0, f"Foreign key violations: {violations}")

            # Verify no data loss in core tables
            for tbl, expected_count in before_counts.items():
                actual_count = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                self.assertEqual(
                    actual_count,
                    expected_count,
                    f"Table {tbl} lost rows during migration! before={expected_count}, after={actual_count}"
                )

            # Verify repo_full_name is populated on data tables
            tables_to_verify = [
                "events",
                "entities",
                "decisions",
                "edges",
                "decision_claims",
                "claim_evidence",
                "decision_evidence",
                "decision_artifacts",
                "state_history",
                "guard_rules"
            ]
            for tbl in tables_to_verify:
                # Column exists
                cur.execute(f"PRAGMA table_info({tbl});")
                cols = [r["name"] for r in cur.fetchall()]
                self.assertIn("repo_full_name", cols, f"Table {tbl} must have repo_full_name")

                # Verify all rows have non-null repo_full_name
                cur.execute(f"SELECT COUNT(*) as unres FROM {tbl} WHERE repo_full_name IS NULL OR repo_full_name = ''")
                unresolved = cur.fetchone()["unres"]
                self.assertEqual(
                    unresolved, 0, f"Table {tbl} has {unresolved} rows with unresolved repo_full_name"
                )

            # Check demo repos
            cur.execute("SELECT repo_full_name, visibility FROM repos WHERE visibility = 'demo'")
            demo_repos = [r["repo_full_name"] for r in cur.fetchall()]
            self.assertIn("acme-eng/thermal-control-system", demo_repos)
            self.assertIn("acme-eng/distributed-cache-service", demo_repos)

    def test_running_twice_is_noop(self):
        """Applying migrations on an already migrated DB produces empty applied results."""
        db_path = os.path.join(self.temp_dir, "idempotent.db")
        db = Database(db_path)

        with db.get_connection() as conn:
            results = run_migrations(conn)
            self.assertEqual(len(results), 0)

    def test_constraints_enforced(self):
        """Verifies check and unique constraints on the newly created tables."""
        db_path = os.path.join(self.temp_dir, "constraints.db")
        db = Database(db_path)

        with db.get_connection() as conn:
            cur = conn.cursor()

            # Unique github_id on users
            cur.execute(
                "INSERT INTO users (github_id, login, created_at, last_login_at) VALUES (101, 'user1', 'ts', 'ts')"
            )
            with self.assertRaises(sqlite3.IntegrityError):
                cur.execute(
                    "INSERT INTO users (github_id, login, created_at, last_login_at) VALUES (101, 'user2', 'ts', 'ts')"
                )

            # Check constraint on repos.visibility ('demo', 'public', 'private')
            with self.assertRaises(sqlite3.IntegrityError):
                cur.execute(
                    "INSERT INTO repos (repo_full_name, visibility) VALUES ('org/repo', 'invalid_vis')"
                )

            # Check constraint on ingest_jobs.status
            with self.assertRaises(sqlite3.IntegrityError):
                cur.execute(
                    "INSERT INTO ingest_jobs (job_id, repo_full_name, status, created_at) VALUES ('j1', 'acme-eng/thermal-control-system', 'invalid_status', 'ts')"
                )


if __name__ == "__main__":
    unittest.main()
