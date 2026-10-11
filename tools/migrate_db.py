#!/usr/bin/env python3
"""
tools/migrate_db.py -- CLI for running schema migrations against a database.
Usage:
    python tools/migrate_db.py --db PATH [--dry-run]
"""
import argparse
import os
import sys
import sqlite3

# Ensure project root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.migrations import run_migrations, get_applied_migrations, get_available_migrations


def main() -> int:
    parser = argparse.ArgumentParser(description="Context Intelligence Framework - Database Migration Tool")
    parser.add_argument("--db", required=True, help="Path to SQLite database file")
    parser.add_argument("--dry-run", action="store_true", help="Report pending migrations without applying them")
    args = parser.parse_args()

    db_path = os.path.abspath(args.db)
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found at: {db_path}", file=sys.stderr)
        return 1

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        applied = get_applied_migrations(conn)
        available = get_available_migrations()
        pending = [m for m in available if m[0] not in set(applied)]

        print(f"[MIGRATE] Target database: {db_path}")
        print(f"[MIGRATE] Currently applied: {len(applied)} migration(s)")
        print(f"[MIGRATE] Available total:   {len(available)} migration(s)")
        print(f"[MIGRATE] Pending:           {len(pending)} migration(s)")

        if args.dry_run:
            print("\n--- Dry Run Report ---")
            if not pending:
                print("Database is up to date. No pending migrations.")
            else:
                for v, name, _ in pending:
                    print(f"  [PENDING] {v:03d}_{name}")
            return 0

        if not pending:
            print("[MIGRATE] No pending migrations. Database is up to date.")
            return 0

        print("\n--- Applying Migrations ---")
        results = run_migrations(conn, dry_run=False)
        for res in results:
            print(f"  [APPLIED] {res['version']:03d}_{res['name']} at {res['applied_at']}")
        print(f"[SUCCESS] Successfully applied {len(results)} migration(s).")
        return 0

    except Exception as exc:
        print(f"[ERROR] Migration failed: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
