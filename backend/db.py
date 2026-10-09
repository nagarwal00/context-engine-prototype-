"""
Context Intelligence Framework - Database Layer
Implements concrete DDL schema from Section 13 and invariants from Section 5.2.
"""
import sqlite3
import json
import os
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from backend.models import Event, Decision, Entity, Edge, Identity

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "context_intelligence.db")

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_schema()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_schema(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Events Table (Section 13)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_url TEXT NOT NULL,
                repo TEXT NOT NULL,
                author TEXT,
                ts TEXT NOT NULL,
                title TEXT,
                body TEXT,
                artifacts_touched TEXT, -- JSON array
                parent_event_ids TEXT,  -- JSON array
                raw_metadata TEXT,      -- JSON dict
                UNIQUE (source_type, source_id, repo)
            );
            """)

            # 2. Entities Table (Section 13)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                canonical_path TEXT NOT NULL,
                aliases TEXT DEFAULT '[]', -- JSON array
                repo TEXT NOT NULL,
                current_state_summary TEXT,
                UNIQUE (canonical_path, repo)
            );
            """)

            # 3. Decisions Table (Section 13)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                decision_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('proposed','accepted','rejected','superseded','unresolved')),
                made_by TEXT,
                made_at TEXT,
                rationale TEXT,
                confidence REAL NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'pending_review',
                supersedes_decision_id TEXT,
                superseded_by_decision_id TEXT,
                alternatives_json TEXT DEFAULT '[]',
                repo TEXT NOT NULL,
                FOREIGN KEY (supersedes_decision_id) REFERENCES decisions(decision_id)
            );
            """)

            # 4. Decision Evidence Table (Section 13)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_evidence (
                decision_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                PRIMARY KEY (decision_id, event_id),
                FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE,
                FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
            );
            """)

            # 5. Decision Artifacts Table (Section 13)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_artifacts (
                decision_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                PRIMARY KEY (decision_id, entity_id),
                FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE,
                FOREIGN KEY (entity_id) REFERENCES entities(entity_id) ON DELETE CASCADE
            );
            """)

            # 6. Edges Table (Section 13)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                edge_id TEXT PRIMARY KEY,
                edge_type TEXT NOT NULL,
                from_id TEXT NOT NULL,
                from_type TEXT NOT NULL,
                to_id TEXT NOT NULL,
                to_type TEXT NOT NULL,
                valid_from TEXT NOT NULL,
                valid_to TEXT
            );
            """)

            # 7. Contributor Identity Resolution Table (Section 6.5)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS identities (
                canonical_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                git_emails TEXT DEFAULT '[]',
                github_logins TEXT DEFAULT '[]'
            );
            """)

            # 8. Decision State History Table (Section 5.2 audit trail)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS state_history (
                history_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                state TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                changed_by TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
            );
            """)
            conn.commit()

    # --- Upsert & Query Methods ---

    def upsert_event(self, event: Event) -> str:
        """Idempotent upsert on (source_type, source_id, repo) per Section 6."""
        if not event.source_url:
            raise ValueError(f"Section 5.1 Violation: Event {event.source_id} has empty source_url!")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO events (
                event_id, source_type, source_id, source_url, repo, author, ts, title, body,
                artifacts_touched, parent_event_ids, raw_metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_type, source_id, repo) DO UPDATE SET
                source_url=excluded.source_url,
                author=excluded.author,
                ts=excluded.ts,
                title=excluded.title,
                body=excluded.body,
                artifacts_touched=excluded.artifacts_touched,
                parent_event_ids=excluded.parent_event_ids,
                raw_metadata=excluded.raw_metadata
            RETURNING event_id;
            """, (
                event.event_id,
                event.source_type,
                event.source_id,
                event.source_url,
                event.repo,
                event.author,
                event.timestamp,
                event.title,
                event.body,
                json.dumps(event.artifacts_touched),
                json.dumps(event.parent_event_ids),
                json.dumps(event.raw_metadata)
            ))
            row = cursor.fetchone()
            conn.commit()
            return row["event_id"] if row else event.event_id

    def upsert_entity(self, entity: Entity) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO entities (
                entity_id, entity_type, canonical_path, aliases, repo, current_state_summary
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(canonical_path, repo) DO UPDATE SET
                entity_type=excluded.entity_type,
                aliases=excluded.aliases,
                current_state_summary=excluded.current_state_summary
            RETURNING entity_id;
            """, (
                entity.entity_id,
                entity.entity_type,
                entity.canonical_path,
                json.dumps(entity.aliases),
                entity.repo,
                entity.current_state_summary
            ))
            row = cursor.fetchone()
            conn.commit()
            return row["entity_id"] if row else entity.entity_id

    def save_decision(self, decision: Decision) -> str:
        """
        Saves a decision and mechanically enforces Section 5.2 & Section 13 invariant:
        evidence_event_ids can never be empty unless state == 'unresolved'.
        """
        decision.validate_invariants()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO decisions (
                decision_id, title, state, made_by, made_at, rationale, confidence,
                review_status, supersedes_decision_id, superseded_by_decision_id,
                alternatives_json, repo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(decision_id) DO UPDATE SET
                title=excluded.title,
                state=excluded.state,
                made_by=excluded.made_by,
                made_at=excluded.made_at,
                rationale=excluded.rationale,
                confidence=excluded.confidence,
                review_status=excluded.review_status,
                supersedes_decision_id=excluded.supersedes_decision_id,
                superseded_by_decision_id=excluded.superseded_by_decision_id,
                alternatives_json=excluded.alternatives_json,
                repo=excluded.repo;
            """, (
                decision.decision_id,
                decision.title,
                decision.state,
                decision.made_by,
                decision.made_at,
                decision.rationale,
                decision.confidence,
                decision.review_status,
                decision.supersedes_decision_id,
                decision.superseded_by_decision_id,
                json.dumps(decision.alternatives_considered),
                decision.repo
            ))

            # Update decision_evidence links
            cursor.execute("DELETE FROM decision_evidence WHERE decision_id = ?", (decision.decision_id,))
            for eid in decision.evidence_event_ids:
                cursor.execute("""
                INSERT OR IGNORE INTO decision_evidence (decision_id, event_id) VALUES (?, ?)
                """, (decision.decision_id, eid))

            # Invariant check at DB level (Section 13)
            cursor.execute("SELECT COUNT(*) as cnt FROM decision_evidence WHERE decision_id = ?", (decision.decision_id,))
            evidence_count = cursor.fetchone()["cnt"]
            if decision.state != "unresolved" and evidence_count == 0:
                conn.rollback()
                raise ValueError(
                    f"Mechanical Invariant Failure: Decision '{decision.title}' persisted with 0 valid evidence records!"
                )

            # Update decision_artifacts links
            cursor.execute("DELETE FROM decision_artifacts WHERE decision_id = ?", (decision.decision_id,))
            for ent_ref in decision.artifacts_affected:
                # Check if ent_ref is already an entity_id or a canonical_path
                cursor.execute(
                    "SELECT entity_id FROM entities WHERE entity_id = ? OR (canonical_path = ? AND repo = ?)",
                    (ent_ref, ent_ref, decision.repo)
                )
                row = cursor.fetchone()
                if row:
                    actual_entity_id = row["entity_id"]
                    cursor.execute("""
                    INSERT OR IGNORE INTO decision_artifacts (decision_id, entity_id) VALUES (?, ?)
                    """, (decision.decision_id, actual_entity_id))
                else:
                    # Auto-create entity for referenced path if not already registered
                    auto_id = f"ent_file_{decision.repo.replace('/', '_')}_{ent_ref.replace('/', '_').replace('.', '_').replace(':', '_')}"
                    cursor.execute("""
                    INSERT OR IGNORE INTO entities (entity_id, entity_type, canonical_path, aliases, repo, current_state_summary)
                    VALUES (?, ?, ?, '[]', ?, ?)
                    """, (auto_id, 'file' if '::' not in ent_ref else 'function', ent_ref, decision.repo, f"Referenced artifact {ent_ref}"))
                    cursor.execute("""
                    INSERT OR IGNORE INTO decision_artifacts (decision_id, entity_id) VALUES (?, ?)
                    """, (decision.decision_id, auto_id))

            # Record state history if provided or new
            for sh in decision.state_history:
                cursor.execute("""
                INSERT OR IGNORE INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    sh.get("history_id", f"sh_{decision.decision_id}_{sh.get('changed_at')}"),
                    decision.decision_id,
                    sh.get("state", decision.state),
                    sh.get("changed_at", decision.made_at),
                    sh.get("changed_by", "system"),
                    sh.get("notes", "")
                ))

            conn.commit()
            return decision.decision_id

    def upsert_decision(self, decision: Decision) -> str:
        """Alias for save_decision."""
        return self.save_decision(decision)

    def upsert_edge(self, edge: Edge) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO edges (
                edge_id, edge_type, from_id, from_type, to_id, to_type, valid_from, valid_to
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                edge.edge_id,
                edge.edge_type,
                edge.from_id,
                edge.from_type,
                edge.to_id,
                edge.to_type,
                edge.valid_from,
                edge.valid_to
            ))
            conn.commit()
            return edge.edge_id

    def upsert_identity(self, identity: Identity):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO identities (canonical_id, display_name, git_emails, github_logins)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(canonical_id) DO UPDATE SET
                display_name=excluded.display_name,
                git_emails=excluded.git_emails,
                github_logins=excluded.github_logins;
            """, (
                identity.canonical_id,
                identity.display_name,
                json.dumps(identity.git_emails),
                json.dumps(identity.github_logins)
            ))
            conn.commit()

    # --- Canonical Queries (Section 7.3) ---

    def query_decision_chain_for_artifact(self, canonical_path_or_entity_id: str) -> List[Dict[str, Any]]:
        """
        Query 1 (Section 7.3.1): Decision chain for an artifact.
        Given an Entity, return all Decisions affecting it, ordered by time, with superseded ones clearly marked.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT e.entity_id, e.canonical_path, e.entity_type, e.repo
            FROM entities e
            WHERE e.entity_id = ? OR e.canonical_path = ?
            """, (canonical_path_or_entity_id, canonical_path_or_entity_id))
            entity_row = cursor.fetchone()
            if not entity_row:
                return []

            entity_id = entity_row["entity_id"]

            cursor.execute("""
            SELECT d.*, 
                   (SELECT json_group_array(de.event_id) FROM decision_evidence de WHERE de.decision_id = d.decision_id) as evidence_ids,
                   (SELECT json_group_array(da.entity_id) FROM decision_artifacts da WHERE da.decision_id = d.decision_id) as artifact_ids
            FROM decisions d
            JOIN decision_artifacts da ON d.decision_id = da.decision_id
            WHERE da.entity_id = ? AND d.review_status != 'human_rejected'
            ORDER BY d.made_at ASC
            """, (entity_id,))

            rows = cursor.fetchall()
            chain = []
            for r in rows:
                item = dict(r)
                item["evidence_ids"] = json.loads(item["evidence_ids"]) if item["evidence_ids"] else []
                item["artifact_ids"] = json.loads(item["artifact_ids"]) if item["artifact_ids"] else []
                item["alternatives_considered"] = json.loads(item["alternatives_json"]) if item["alternatives_json"] else []
                item["entity_canonical_path"] = entity_row["canonical_path"]
                chain.append(item)
            return chain

    def query_full_evidence_trail(self, decision_id: str) -> Dict[str, Any]:
        """
        Query 2 (Section 7.3.2): Full evidence trail for a decision.
        Given a Decision, return all evidenced_by and discussed_in events with clickable source_urls.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,))
            dec_row = cursor.fetchone()
            if not dec_row:
                return {"decision": None, "evidence_events": [], "discussion_events": []}

            decision = dict(dec_row)
            decision["alternatives_considered"] = json.loads(decision["alternatives_json"]) if decision["alternatives_json"] else []

            # Direct evidence events
            cursor.execute("""
            SELECT ev.* FROM events ev
            JOIN decision_evidence de ON ev.event_id = de.event_id
            WHERE de.decision_id = ?
            ORDER BY ev.ts ASC
            """, (decision_id,))
            evidence_events = [dict(r) for r in cursor.fetchall()]
            for ev in evidence_events:
                ev["artifacts_touched"] = json.loads(ev["artifacts_touched"]) if ev["artifacts_touched"] else []
                ev["parent_event_ids"] = json.loads(ev["parent_event_ids"]) if ev["parent_event_ids"] else []
                ev["raw_metadata"] = json.loads(ev["raw_metadata"]) if ev["raw_metadata"] else {}

            # Broader discussion events linked via discussed_in edges
            cursor.execute("""
            SELECT ev.* FROM events ev
            JOIN edges ed ON ed.to_id = ev.event_id
            WHERE ed.from_id = ? AND ed.edge_type = 'discussed_in'
            ORDER BY ev.ts ASC
            """, (decision_id,))
            discussion_events = [dict(r) for r in cursor.fetchall()]
            for ev in discussion_events:
                ev["artifacts_touched"] = json.loads(ev["artifacts_touched"]) if ev["artifacts_touched"] else []
                ev["parent_event_ids"] = json.loads(ev["parent_event_ids"]) if ev["parent_event_ids"] else []
                ev["raw_metadata"] = json.loads(ev["raw_metadata"]) if ev["raw_metadata"] else {}

            return {
                "decision": decision,
                "evidence_events": evidence_events,
                "discussion_events": discussion_events
            }

    def query_timeline_slice(self, repo: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query 3 (Section 7.3.3): Timeline slice.
        Given a repo and time range, return all decisions with state transitions in that window.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT d.* FROM decisions d WHERE d.review_status != 'human_rejected'"
            params = []
            if repo:
                query += " AND d.repo = ?"
                params.append(repo)
            if start_time:
                query += " AND d.made_at >= ?"
                params.append(start_time)
            if end_time:
                query += " AND d.made_at <= ?"
                params.append(end_time)
            
            query += " ORDER BY d.made_at ASC"
            cursor.execute(query, params)
            decisions = []
            for r in cursor.fetchall():
                d = dict(r)
                d["alternatives_considered"] = json.loads(d["alternatives_json"]) if d["alternatives_json"] else []
                
                # Fetch affected artifacts canonical paths
                cursor.execute("""
                SELECT e.canonical_path, e.entity_type FROM entities e
                JOIN decision_artifacts da ON e.entity_id = da.entity_id
                WHERE da.decision_id = ?
                """, (d["decision_id"],))
                d["affected_artifacts"] = [dict(a) for a in cursor.fetchall()]

                # Fetch evidence count
                cursor.execute("SELECT COUNT(*) as cnt FROM decision_evidence WHERE decision_id = ?", (d["decision_id"],))
                d["evidence_count"] = cursor.fetchone()["cnt"]

                decisions.append(d)
            return decisions
