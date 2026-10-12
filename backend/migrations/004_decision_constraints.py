"""
Migration 004: Decision-specific constraints and guard rules schema update
Implements Step 3.4 of ANTIGRAVITY_HANDOFF_V2.md:
- Adds polarity ('must' | 'must_not'), applies_to (JSON array of entity IDs / path globs),
  and source ('human' | 'proposed') to guard_rules.
- Creates decision_constraints view referencing guard_rules.
- Backfills applies_to and polarity from existing rule params.
"""
import sqlite3
import json

VERSION = 4
NAME = "decision_constraints"


def upgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    # 1. Ensure guard_rules table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guard_rules (
        rule_id TEXT PRIMARY KEY,
        decision_id TEXT NOT NULL,
        rule_type TEXT NOT NULL,
        params_json TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'proposed',
        polarity TEXT NOT NULL DEFAULT 'must_not',
        applies_to TEXT NOT NULL DEFAULT '[]',
        source TEXT NOT NULL DEFAULT 'proposed',
        created_by TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        approved_by TEXT,
        approved_at TEXT,
        FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
    );
    """)

    # 2. Add columns to guard_rules if missing from an existing pre-v2 schema
    cursor.execute("PRAGMA table_info(guard_rules)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    if "polarity" not in existing_cols:
        cursor.execute("ALTER TABLE guard_rules ADD COLUMN polarity TEXT NOT NULL DEFAULT 'must_not'")
    if "applies_to" not in existing_cols:
        cursor.execute("ALTER TABLE guard_rules ADD COLUMN applies_to TEXT NOT NULL DEFAULT '[]'")
    if "source" not in existing_cols:
        cursor.execute("ALTER TABLE guard_rules ADD COLUMN source TEXT NOT NULL DEFAULT 'proposed'")

    # 2. Create decision_constraints view
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS decision_constraints AS
    SELECT rule_id AS constraint_id, decision_id, rule_type, params_json, status, polarity, applies_to, source, created_by, created_at, approved_by, approved_at
    FROM guard_rules;
    """)

    # 3. Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guard_rules_status ON guard_rules(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guard_rules_decision ON guard_rules(decision_id);")

    # 4. Backfill applies_to and polarity for existing rows
    cursor.execute("SELECT rule_id, rule_type, params_json, polarity, applies_to FROM guard_rules")
    rows = cursor.fetchall()

    for r in rows:
        rule_id = r[0]
        rule_type = r[1]
        params_raw = r[2]
        cur_pol = r[3]
        cur_applies = r[4]

        try:
            params = json.loads(params_raw) if params_raw else {}
        except Exception:
            params = {}

        updates = []
        vals = []

        # Populate applies_to from paths if applies_to is empty or '[]'
        if not cur_applies or cur_applies == "[]":
            paths = params.get("paths")
            if not paths and params.get("file"):
                paths = [params["file"]]
            if paths:
                updates.append("applies_to = ?")
                vals.append(json.dumps(paths))

        # Infer polarity: require_import -> 'must', forbid_* -> 'must_not'
        if not cur_pol or cur_pol == "must_not":
            if rule_type == "require_import":
                updates.append("polarity = ?")
                vals.append("must")

        if updates:
            vals.append(rule_id)
            cursor.execute(f"UPDATE guard_rules SET {', '.join(updates)} WHERE rule_id = ?", vals)
