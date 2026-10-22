"""
Tool to repair missing edge repo_full_name tenancy attributions (Step 1.2).
Finds edges where repo_full_name IS NULL and resolves the repo from its endpoints.

Usage:
    python tools/repair_edge_repo.py [--db PATH] [--apply]
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from backend.db import Database

DEFAULT_DB = PROJECT_ROOT / "context_intelligence.db"


def repair_edge_repos(db_path: str, apply_changes: bool = False):
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"[REPAIR] Error: Database file not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    if apply_changes:
        backups_dir = PROJECT_ROOT / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backups_dir / f"{db_file.name}.bak.{timestamp_str}"
        shutil.copy2(db_file, backup_path)
        print(f"[REPAIR] Created backup at: {backup_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS cnt FROM edges WHERE repo_full_name IS NULL")
    before_count = cursor.fetchone()["cnt"]

    cursor.execute("""
        SELECT edge_id, edge_type, from_id, from_type, to_id, to_type, valid_from, valid_to, repo_full_name
        FROM edges
        WHERE repo_full_name IS NULL
    """)
    null_edges = cursor.fetchall()

    print(f"[REPAIR] Inspected edges in {db_file.name}:")
    print(f"         Found {before_count} edge(s) with NULL repo_full_name.")

    repairs = []
    unresolved = []

    for edge in null_edges:
        edge_id = edge["edge_id"]
        from_id = edge["from_id"]
        from_type = edge["from_type"]
        to_id = edge["to_id"]
        to_type = edge["to_type"]

        resolved = Database.resolve_edge_repo(conn, from_id, from_type, to_id, to_type)
        if resolved:
            repairs.append((edge_id, resolved, edge["edge_type"]))
        else:
            unresolved.append(edge_id)

    print(f"[REPAIR] Determined {len(repairs)} repair candidate(s), {len(unresolved)} unresolved.")

    if not apply_changes:
        print("[REPAIR] DRY-RUN MODE: No changes written to database. Use --apply to execute.")
        if repairs:
            print("\n--- Dry Run Plan ---")
            for eid, repo, etype in repairs:
                print(f"Edge '{eid}' ({etype}): NULL -> '{repo}'")
            print("--------------------\n")
        conn.close()
        return {
            "before_count": before_count,
            "after_count": before_count,
            "repaired_count": len(repairs),
            "unresolved_count": len(unresolved)
        }

    for eid, repo, _ in repairs:
        cursor.execute("UPDATE edges SET repo_full_name = ? WHERE edge_id = ?", (repo, eid))
    conn.commit()

    cursor.execute("SELECT COUNT(*) AS cnt FROM edges WHERE repo_full_name IS NULL")
    after_count = cursor.fetchone()["cnt"]
    conn.close()

    print(f"[REPAIR] Successfully APPLIED {len(repairs)} update(s) to database.")
    print(f"[REPAIR] NULL edges before: {before_count}, after: {after_count}")

    return {
        "before_count": before_count,
        "after_count": after_count,
        "repaired_count": len(repairs),
        "unresolved_count": len(unresolved)
    }


def main():
    parser = argparse.ArgumentParser(description="Repair missing edge repo_full_name attributions")
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB), help="Path to database")
    parser.add_argument("--apply", action="store_true", help="Apply updates (default is dry-run)")
    args = parser.parse_args()

    repair_edge_repos(args.db, apply_changes=args.apply)


if __name__ == "__main__":
    main()
