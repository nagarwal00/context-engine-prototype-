"""
Tool to repair temporal edge validity defaults (P1-c / Step 1.5)
Finds stored edges whose valid_from equals the old placeholder (2026-01-01T00:00:00Z)
and sets it to the earliest relevant timestamp (decision made_at or its earliest evidence event).

Usage:
    python tools/repair_edge_validity.py [--db PATH] [--apply]
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = PROJECT_ROOT / "context_intelligence.db"
OLD_PLACEHOLDER_PREFIX = "2026-01-01T00:00:00"


def _parse_iso(ts: str) -> datetime:
    clean = ts.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def repair_edges(db_path: str, apply_changes: bool = False):
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"[REPAIR] Error: Database file not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    backup_path = None
    if apply_changes:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_file.parent / f"{db_file.name}.bak.{timestamp_str}"
        shutil.copy2(db_file, backup_path)
        print(f"[REPAIR] Created backup at: {backup_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find edges with placeholder timestamp
    cursor.execute("""
        SELECT edge_id, edge_type, from_id, from_type, to_id, to_type, valid_from, valid_to
        FROM edges
        WHERE valid_from LIKE ? OR valid_from = '2026-01-01'
    """, (f"{OLD_PLACEHOLDER_PREFIX}%",))
    placeholder_edges = cursor.fetchall()

    print(f"[REPAIR] Inspected edges in {db_file.name}:")
    print(f"         Found {len(placeholder_edges)} edge(s) with placeholder valid_from.")

    repairs = []

    for edge in placeholder_edges:
        edge_id = edge["edge_id"]
        from_id = edge["from_id"]
        to_id = edge["to_id"]
        old_vf = edge["valid_from"]

        candidates = []

        # 1. Search for decision timestamps
        for dec_candidate_id in [from_id, to_id]:
            cursor.execute("SELECT made_at FROM decisions WHERE decision_id = ?", (dec_candidate_id,))
            d_row = cursor.fetchone()
            if d_row and d_row["made_at"]:
                candidates.append(d_row["made_at"])

            # 2. Search for linked evidence events
            cursor.execute("""
                SELECT e.ts FROM events e
                JOIN decision_evidence de ON e.event_id = de.event_id
                WHERE de.decision_id = ?
            """, (dec_candidate_id,))
            for ev_row in cursor.fetchall():
                if ev_row["ts"]:
                    candidates.append(ev_row["ts"])

        # 3. Direct event lookup if from_id or to_id is an event
        for ev_candidate_id in [from_id, to_id]:
            cursor.execute("SELECT ts FROM events WHERE event_id = ?", (ev_candidate_id,))
            e_row = cursor.fetchone()
            if e_row and e_row["ts"]:
                candidates.append(e_row["ts"])

        # Pick earliest valid candidate timestamp
        parsed_candidates = []
        for c in candidates:
            try:
                parsed_candidates.append((_parse_iso(c), c))
            except Exception:
                pass

        if parsed_candidates:
            parsed_candidates.sort(key=lambda x: x[0])
            earliest_iso = parsed_candidates[0][1]
            repairs.append({
                "edge_id": edge_id,
                "edge_type": edge["edge_type"],
                "from_id": from_id,
                "to_id": to_id,
                "old_valid_from": old_vf,
                "new_valid_from": earliest_iso
            })

    print(f"[REPAIR] Determined {len(repairs)} repair candidate(s).")

    if apply_changes and repairs:
        for r in repairs:
            cursor.execute(
                "UPDATE edges SET valid_from = ? WHERE edge_id = ?",
                (r["new_valid_from"], r["edge_id"])
            )
        conn.commit()
        print(f"[REPAIR] Successfully APPLIED {len(repairs)} update(s) to database.")
    elif not apply_changes and repairs:
        print("[REPAIR] DRY-RUN MODE: No changes written to database. Use --apply to execute.")

    conn.close()

    # Print summary report
    print("\n--- Repair Report ---")
    for r in repairs:
        print(f"Edge '{r['edge_id']}' ({r['edge_type']}):")
        print(f"  {r['old_valid_from']} -> {r['new_valid_from']}")
    print("---------------------\n")

    return {
        "edges_scanned": len(placeholder_edges),
        "edges_repaired": len(repairs),
        "backup_path": str(backup_path) if backup_path else None,
        "repairs": repairs
    }


def main():
    parser = argparse.ArgumentParser(
        description="Repairs placeholder valid_from timestamps in SQLite temporal edges."
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB),
        help=f"Path to SQLite database (default: {DEFAULT_DB})"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to database (creates backup first). Default is dry-run."
    )
    args = parser.parse_args()

    repair_edges(args.db, apply_changes=args.apply)


if __name__ == "__main__":
    main()
