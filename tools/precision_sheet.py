"""
tools/precision_sheet.py
Export and import precision labelling sheets bound to DB snapshot hash (Step 4.3).

Commands:
  python tools/precision_sheet.py --export
    Exports backend/evaluation/whybench/precision_labels.json to results/precision_sheet.csv
    with decision details and cited events, leaving 'correct' and 'reason' blank.

  python tools/precision_sheet.py --import
    Imports results/precision_sheet.csv into precision_labels.json, validating that
    the database snapshot SHA-256 matches and only binary (true/false) labels are accepted.
"""
import argparse
import csv
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def compute_db_sha256(db_path: Path) -> str:
    if not db_path.exists():
        return ""
    hasher = hashlib.sha256()
    with open(db_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_cited_events_text(conn: sqlite3.Connection, decision_id: str) -> str:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.event_id, e.source_type, e.source_id, e.title
        FROM edges ed
        JOIN events e ON ed.to_id = e.event_id
        WHERE ed.from_id = ? AND ed.edge_type = 'evidenced_by'
        ORDER BY e.ts ASC, e.event_id ASC
    """, (decision_id,))
    events = cursor.fetchall()
    if not events:
        return "None"
    parts = []
    for ev in events:
        eid, stype, sid, title = ev[0], ev[1], ev[2], ev[3] or ""
        parts.append(f"[{eid}] ({stype}:{sid}) {title}")
    return " | ".join(parts)


def export_precision_sheet(labels_path: Path, csv_path: Path, db_path: Path) -> None:
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with open(labels_path, "r", encoding="utf-8") as f:
        labels_data = json.load(f)

    conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    rows = []
    try:
        for item in labels_data:
            did = item.get("decision_id")
            title = item.get("title") or ""
            rationale = item.get("rationale") or ""
            cited_text = get_cited_events_text(conn, did)
            rows.append({
                "id": did,
                "decision_title": title,
                "rationale": rationale,
                "cited_events": cited_text,
                "correct": "" if item.get("correct") is None else str(item["correct"]).lower(),
                "reason": item.get("note") or ""
            })
    finally:
        conn.close()

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="\n") as f:
        fieldnames = ["id", "decision_title", "rationale", "cited_events", "correct", "reason"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} decisions to {csv_path}")


def import_precision_sheet(csv_path: Path, labels_path: Path, db_path: Path) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    current_db_hash = compute_db_sha256(db_path)
    with open(labels_path, "r", encoding="utf-8") as f:
        labels_data = json.load(f)

    # Validate snapshot hash bound to DB
    for item in labels_data:
        item_hash = item.get("db_snapshot_sha256")
        if item_hash and item_hash != current_db_hash:
            raise ValueError(
                f"Snapshot hash mismatch: DB has '{current_db_hash}', "
                f"but labels file records '{item_hash}' for decision '{item.get('decision_id')}'"
            )

    labels_by_id = {item.get("decision_id"): item for item in labels_data if item.get("decision_id")}

    csv_rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if any(v.strip() for v in r.values() if v):
                csv_rows.append(r)

    updated_count = 0
    for r in csv_rows:
        did = (r.get("id") or r.get("decision_id") or "").strip()
        if not did:
            raise ValueError("Encountered row missing decision ID in CSV")
        if did not in labels_by_id:
            raise ValueError(f"Unknown decision ID '{did}' in CSV (not found in {labels_path.name})")

        raw_correct = (r.get("correct") or "").strip().lower()
        if raw_correct in ("true", "1", "yes"):
            val = True
        elif raw_correct in ("false", "0", "no"):
            val = False
        elif raw_correct in ("", "null", "none"):
            val = None
        else:
            raise ValueError(f"Invalid label '{raw_correct}' for decision '{did}': must be true, false, 1, 0, or blank")

        reason = (r.get("reason") or r.get("note") or "").strip()

        item = labels_by_id[did]
        item["correct"] = val
        if reason:
            item["note"] = reason
        if val is not None:
            updated_count += 1

    with open(labels_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(labels_data, f, indent=2)
        f.write("\n")

    print(f"Imported {len(csv_rows)} rows ({updated_count} labelled) into {labels_path}")
    return updated_count


def main():
    parser = argparse.ArgumentParser(description="Export and import precision evaluation sheets.")
    parser.add_argument("--export", action="store_true", help="Export precision labels to CSV sheet")
    parser.add_argument("--import", dest="do_import", action="store_true", help="Import CSV sheet back into precision labels")
    parser.add_argument("--csv", default=str(PROJECT_ROOT / "results/precision_sheet.csv"), help="Path to CSV sheet")
    parser.add_argument("--labels", default=str(PROJECT_ROOT / "backend/evaluation/whybench/precision_labels.json"), help="Path to precision_labels.json")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "whybench.db"), help="Path to SQLite DB snapshot")
    args = parser.parse_args()

    labels_path = Path(args.labels)
    csv_path = Path(args.csv)
    db_path = Path(args.db)

    if args.do_import:
        import_precision_sheet(csv_path, labels_path, db_path)
    else:
        # Default action is export
        export_precision_sheet(labels_path, csv_path, db_path)


if __name__ == "__main__":
    main()
