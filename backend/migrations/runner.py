"""
Context Intelligence Framework - Database Migration Runner
Implements Step 2.0 of docs/process/ANTIGRAVITY_HANDOFF_V2.md
"""
import os
import re
import datetime
import importlib.util
import sqlite3
from typing import List, Tuple, Callable, Dict, Any, Optional

MIGRATIONS_DIR_DEFAULT = os.path.dirname(os.path.abspath(__file__))


def ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    """Ensures the schema_migrations tracking table exists."""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        applied_at TEXT NOT NULL
    );
    """)


def get_applied_migrations(conn: sqlite3.Connection) -> List[int]:
    """Returns list of already applied migration version numbers in ascending order."""
    ensure_schema_migrations_table(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM schema_migrations ORDER BY version ASC")
    return [row[0] for row in cursor.fetchall()]


def get_available_migrations(
    migrations_dir: Optional[str] = None
) -> List[Tuple[int, str, Callable[[sqlite3.Connection], None]]]:
    """
    Discovers all migration modules in the migrations directory.
    Matches files named like: 001_reconcile_state_definitions.py
    Returns sorted by version integer.
    """
    target_dir = migrations_dir or MIGRATIONS_DIR_DEFAULT
    if not os.path.isdir(target_dir):
        return []

    migrations: List[Tuple[int, str, Callable[[sqlite3.Connection], None]]] = []
    pattern = re.compile(r"^(\d+)_(.+)\.py$")

    for fname in sorted(os.listdir(target_dir)):
        match = pattern.match(fname)
        if not match:
            continue
        version_num = int(match.group(1))
        migration_name = match.group(2)
        fpath = os.path.join(target_dir, fname)

        # Dynamic import
        spec = importlib.util.spec_from_file_location(f"migration_{version_num}", fpath)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        upgrade_fn = getattr(mod, "upgrade", None)
        if upgrade_fn is None or not callable(upgrade_fn):
            raise AttributeError(f"Migration module '{fname}' must define a callable 'upgrade(conn)' function.")

        migrations.append((version_num, migration_name, upgrade_fn))

    migrations.sort(key=lambda m: m[0])
    return migrations


def run_migrations(
    conn: sqlite3.Connection,
    migrations_dir: Optional[str] = None,
    dry_run: bool = False
) -> List[Dict[str, Any]]:
    """
    Applies all pending migrations in order, inside one transaction each.
    - If dry_run is True, returns pending migrations without executing.
    - If migration fails, rolls back transaction and re-raises.
    - Re-running with no pending migrations is a no-op.
    """
    ensure_schema_migrations_table(conn)
    applied_versions = set(get_applied_migrations(conn))
    available = get_available_migrations(migrations_dir)

    pending = [m for m in available if m[0] not in applied_versions]

    if dry_run:
        return [
            {
                "version": v,
                "name": n,
                "status": "pending"
            }
            for v, n, _ in pending
        ]

    applied_results: List[Dict[str, Any]] = []
    old_isolation = conn.isolation_level
    try:
        # Flush any open statements before managing explicit transactions
        conn.commit()
        conn.isolation_level = None  # Autocommit mode for manual BEGIN / COMMIT control

        cursor = conn.cursor()
        for version_num, name, upgrade_fn in pending:
            applied_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cursor.execute("PRAGMA foreign_keys = OFF;")
            conn.execute("BEGIN;")
            try:
                upgrade_fn(conn)
                cursor.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                    (version_num, name, applied_at)
                )
                conn.execute("COMMIT;")
            except Exception as exc:
                try:
                    conn.execute("ROLLBACK;")
                except Exception:
                    pass
                raise RuntimeError(f"Migration {version_num:03d}_{name} failed: {exc}") from exc
            finally:
                try:
                    cursor.execute("PRAGMA foreign_keys = ON;")
                except Exception:
                    pass

            # Foreign key check after each migration
            cursor.execute("PRAGMA foreign_key_check;")
            violations = cursor.fetchall()
            if violations:
                raise RuntimeError(
                    f"Mechanical Integrity Error: PRAGMA foreign_key_check reported violations after migration {version_num:03d}_{name}: {violations}"
                )

            applied_results.append({
                "version": version_num,
                "name": name,
                "status": "applied",
                "applied_at": applied_at
            })

    finally:
        conn.isolation_level = old_isolation

    return applied_results
