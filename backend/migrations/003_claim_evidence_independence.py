"""
Migration 003: Claim-level evidence and source independence tables
Implements Step 3.1 of ANTIGRAVITY_HANDOFF_V2.md:
- Creates decision_claims table:
    claim_id TEXT PRIMARY KEY
    decision_id TEXT NOT NULL
    claim_type TEXT NOT NULL CHECK (claim_type IN ('rationale', 'alternative_rejected', 'outcome', 'constraint'))
    text TEXT NOT NULL
- Creates claim_evidence table:
    claim_id TEXT NOT NULL
    event_id TEXT NOT NULL
    relation TEXT NOT NULL CHECK (relation IN ('direct', 'indirect', 'contradicting'))
    passage_text TEXT
    passage_start INTEGER
    passage_end INTEGER
    source_group TEXT NOT NULL
    PRIMARY KEY (claim_id, event_id)
- Backfills claims and claim_evidence for existing decisions
"""
import sqlite3
import json

VERSION = 3
NAME = "claim_evidence_independence"


def upgrade(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS decision_claims (
        claim_id TEXT PRIMARY KEY,
        decision_id TEXT NOT NULL,
        claim_type TEXT NOT NULL CHECK (claim_type IN ('rationale', 'alternative_rejected', 'outcome', 'constraint')),
        text TEXT NOT NULL,
        FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision_claims_dec ON decision_claims(decision_id);")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claim_evidence (
        claim_id TEXT NOT NULL,
        event_id TEXT NOT NULL,
        relation TEXT NOT NULL CHECK (relation IN ('direct', 'indirect', 'contradicting')),
        passage_text TEXT,
        passage_start INTEGER,
        passage_end INTEGER,
        source_group TEXT NOT NULL,
        PRIMARY KEY (claim_id, event_id),
        FOREIGN KEY (claim_id) REFERENCES decision_claims(claim_id) ON DELETE CASCADE,
        FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claim_evidence_event ON claim_evidence(event_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claim_evidence_group ON claim_evidence(source_group);")

    # Backfill claims and claim_evidence for existing decisions
    cursor.execute("SELECT decision_id, title, rationale, alternatives_json, repo FROM decisions")
    dec_rows = cursor.fetchall()
    if dec_rows:
        from backend.engine.independence import (
            extract_claims_from_decision,
            extract_best_passage,
            independence_key
        )

        for d_row in dec_rows:
            d_id = d_row[0]
            title = d_row[1]
            rationale = d_row[2]
            alts_json = d_row[3]
            repo = d_row[4]
            alts = []
            if alts_json:
                try:
                    alts = json.loads(alts_json)
                except Exception:
                    pass

            mock_dec = {
                "decision_id": d_id,
                "title": title,
                "rationale": rationale,
                "alternatives_considered": alts,
                "repo": repo
            }
            claims = extract_claims_from_decision(mock_dec)
            for clm in claims:
                cursor.execute("""
                INSERT OR IGNORE INTO decision_claims (claim_id, decision_id, claim_type, text)
                VALUES (?, ?, ?, ?)
                """, (clm.claim_id, clm.decision_id, clm.claim_type, clm.text))

                cursor.execute("""
                SELECT e.event_id, e.source_type, e.source_id, e.source_url, e.repo, e.title, e.body, e.raw_metadata, e.parent_event_ids
                FROM decision_evidence de
                JOIN events e ON de.event_id = e.event_id
                WHERE de.decision_id = ?
                """, (d_id,))
                ev_rows = cursor.fetchall()
                ev_dicts = []
                for er in ev_rows:
                    rm = {}
                    if er[7]:
                        try:
                            rm = json.loads(er[7])
                        except Exception:
                            pass
                    pe = []
                    if er[8]:
                        try:
                            pe = json.loads(er[8])
                        except Exception:
                            pass
                    ev_dicts.append({
                        "event_id": er[0],
                        "source_type": er[1],
                        "source_id": er[2],
                        "source_url": er[3],
                        "repo": er[4],
                        "title": er[5],
                        "body": er[6],
                        "raw_metadata": rm,
                        "parent_event_ids": pe
                    })

                for ev in ev_dicts:
                    sg = independence_key(ev, all_events=ev_dicts)
                    full_text = f"{ev.get('title') or ''}\n{ev.get('body') or ''}".strip()
                    p_text, p_start, p_end, rel = extract_best_passage(clm.text, full_text)
                    cursor.execute("""
                    INSERT OR IGNORE INTO claim_evidence (
                        claim_id, event_id, relation, passage_text, passage_start, passage_end, source_group
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (clm.claim_id, ev["event_id"], rel, p_text, p_start, p_end, sg))
