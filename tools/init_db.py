"""
Database Initializer and Seed Runner (Step 6.3)
Usage:
    python tools/init_db.py [--db PATH] [--seed] [--fresh]

Initializes a fresh or existing SQLite database, applies all schema migrations
in backend/migrations/ in strict order, and optionally populates deterministic seed data.
"""
import os
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.db import Database
from backend.seed_data import populate_seed_data


def init_database(db_path: Path, seed: bool = False, fresh: bool = False) -> None:
    if fresh and db_path.exists():
        print(f"[INIT] Removing existing database at {db_path} (--fresh requested)...")
        os.remove(db_path)

    print(f"[INIT] Connecting to database at {db_path}...")
    db = Database(str(db_path))

    # Verify migrations applied
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT version, name, applied_at FROM schema_migrations ORDER BY version")
        applied = cursor.fetchall()
        print(f"[OK] Applied {len(applied)} schema migration(s):")
        for m in applied:
            print(f"     - v{m[0]:03d}: {m[1]} ({m[2]})")

    if seed:
        print("[INIT] Populating deterministic seed data for pilot repositories...")
        populate_seed_data(db)
        print("[OK] Seed data populated successfully.")

    # Print summary statistics
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        ev_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM decisions")
        dec_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM entities")
        ent_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM edges")
        edge_count = cursor.fetchone()[0]

    print(f"[STATUS] Database initialized: {ev_count} events, {dec_count} decisions, {ent_count} entities, {edge_count} edges.")


def main():
    parser = argparse.ArgumentParser(description="Database Initializer & Migration Runner")
    parser.add_argument("--db", type=str, default=str(PROJECT_ROOT / "context_intelligence.db"), help="Database file path")
    parser.add_argument("--seed", action="store_true", help="Populate pilot repository seed data")
    parser.add_argument("--fresh", action="store_true", help="Delete existing database before initializing")
    args = parser.parse_args()

    init_database(Path(args.db), seed=args.seed, fresh=args.fresh)


if __name__ == "__main__":
    main()
