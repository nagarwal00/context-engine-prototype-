"""
Context Intelligence Framework - State History Backfill Tool
Implements Step 2.3 of docs/process/ANTIGRAVITY_HANDOFF_V2.md:
Backfills one history row per existing decision with:
  notes = 'reconstructed from current state at backfill'
  changed_by = 'system:backfill'
  changed_at = decision.made_at
  reconstructed = 1

Usage:
  python tools/backfill_state_history.py [--db PATH] [--dry-run]
"""
import argparse
import os
import sqlite3
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def backfill_state_history(db_path: str, dry_run: bool = False) -> dict:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='decisions'")
        if not cursor.fetchone():
            print(f"[WARN] No 'decisions' table found in {db_path}")
            return {"decisions": 0, "before": 0, "after": 0, "backfilled": 0}

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='state_history'")
        has_sh = bool(cursor.fetchone())

        cursor.execute("SELECT COUNT(*) AS c FROM decisions")
        total_decisions = cursor.fetchone()["c"]

        if has_sh:
            cursor.execute("SELECT COUNT(*) AS c FROM state_history")
            sh_count_before = cursor.fetchone()["c"]

            cursor.execute("""
            SELECT d.decision_id, d.state, d.made_at, d.made_by
            FROM decisions d
            LEFT JOIN state_history sh ON d.decision_id = sh.decision_id
            WHERE sh.decision_id IS NULL
            """)
            missing = [dict(r) for r in cursor.fetchall()]
        else:
            sh_count_before = 0
            cursor.execute("SELECT decision_id, state, made_at, made_by FROM decisions")
            missing = [dict(r) for r in cursor.fetchall()]

        print("=" * 65)
        print("  DECISION STATE HISTORY BACKFILL TOOL")
        print("=" * 65)
        print(f"  Target Database   : {db_path}")
        print(f"  Dry Run Mode      : {dry_run}")
        print("-----------------------------------------------------------------")
        print(f"  Total Decisions                 : {total_decisions}")
        print(f"  State History Rows (Before)     : {sh_count_before}")
        print(f"  Decisions Lacking History Rows  : {len(missing)}")
        print("-----------------------------------------------------------------")

        if dry_run:
            print(f"  [DRY-RUN] Would insert {len(missing)} reconstructed history row(s):")
            for m in missing:
                print(f"    - Decision: {m['decision_id']} ({m['state']}) at {m.get('made_at')}")
            return {
                "decisions": total_decisions,
                "before": sh_count_before,
                "after": sh_count_before,
                "backfilled": 0,
                "planned": len(missing)
            }

        # Real run: Ensure state_history table exists with proper columns
        if not has_sh:
            cursor.execute("""
            CREATE TABLE state_history (
                history_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                from_state TEXT,
                state TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                changed_by TEXT NOT NULL,
                notes TEXT,
                reconstructed INTEGER DEFAULT 0,
                FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
            );
            """)
        else:
            cursor.execute("PRAGMA table_info(state_history)")
            cols = {r["name"] for r in cursor.fetchall()}
            if "from_state" not in cols:
                cursor.execute("ALTER TABLE state_history ADD COLUMN from_state TEXT;")
            if "reconstructed" not in cols:
                cursor.execute("ALTER TABLE state_history ADD COLUMN reconstructed INTEGER DEFAULT 0;")

        inserted = 0
        for m in missing:
            dec_id = m["decision_id"]
            state = m["state"]
            made_at = m.get("made_at") or "1970-01-01T00:00:00Z"
            hist_id = f"hist_backfill_{dec_id}"
            notes = "reconstructed from current state at backfill"
            changed_by = "system:backfill"

            cursor.execute("""
            INSERT INTO state_history (
                history_id, decision_id, from_state, state, changed_at, changed_by, notes, reconstructed
            ) VALUES (?, ?, NULL, ?, ?, ?, ?, 1)
            """, (hist_id, dec_id, state, made_at, changed_by, notes))
            inserted += 1

        conn.commit()

        cursor.execute("SELECT COUNT(*) AS c FROM state_history")
        sh_count_after = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) AS c FROM state_history WHERE reconstructed = 1 OR changed_by = 'system:backfill'")
        reconstructed_count = cursor.fetchone()["c"]

        print(f"  Backfill Applied Successfully!")
        print(f"  Rows Inserted                   : {inserted}")
        print(f"  State History Rows (After)      : {sh_count_after}")
        print(f"  Total Reconstructed Rows        : {reconstructed_count}")
        print("=" * 65)

        return {
            "decisions": total_decisions,
            "before": sh_count_before,
            "after": sh_count_after,
            "backfilled": inserted,
            "reconstructed_total": reconstructed_count
        }
    finally:
        conn.close()


def main():
    default_db = os.path.join(PROJECT_ROOT, "context_intelligence.db")
    parser = argparse.ArgumentParser(description="Backfill state_history for decisions lacking audit rows.")
    parser.add_argument("--db", default=default_db, help="Path to SQLite database file")
    parser.add_argument("--dry-run", action="store_true", help="Report planned actions without modifying DB")
    args = parser.parse_args()

    backfill_state_history(args.db, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
