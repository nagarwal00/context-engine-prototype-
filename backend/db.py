"""
Context Intelligence Framework - Database Layer
Implements concrete DDL schema from Section 13 and invariants from Section 5.2.
"""
import sqlite3
import json
import os
import time
import uuid
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from backend.models import Event, Decision, Entity, Edge, Identity, GuardRule, DecisionClaim, ClaimEvidence
from backend.migrations import run_migrations

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
                state TEXT NOT NULL CHECK (state IN ('proposed','tested','accepted','rejected','superseded','reopened')),
                made_by TEXT,
                made_at TEXT,
                rationale TEXT,
                confidence REAL NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'pending_review',
                supersedes_decision_id TEXT,
                superseded_by_decision_id TEXT,
                alternatives_json TEXT DEFAULT '[]',
                repo TEXT NOT NULL,
                evidence_assessment TEXT NOT NULL DEFAULT 'insufficient' CHECK (evidence_assessment IN ('strong','moderate','weak','insufficient','contradicted')),
                freshness TEXT NOT NULL DEFAULT 'fresh' CHECK (freshness IN ('fresh','stale','under_review','revalidated')),
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
                from_state TEXT,
                state TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                changed_by TEXT NOT NULL,
                notes TEXT,
                reconstructed INTEGER DEFAULT 0,
                FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
            );
            """)

            # 9. Decision Guard Rules Table (Section 5.1 Novelty & Step 3.4 Constraints)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS guard_rules (
                rule_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                rule_type TEXT NOT NULL CHECK (rule_type IN ('forbid_import', 'require_import', 'forbid_pattern', 'config_value')),
                params_json TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('proposed', 'active', 'disabled')),
                created_by TEXT,
                created_at TEXT,
                approved_by TEXT,
                approved_at TEXT,
                polarity TEXT NOT NULL DEFAULT 'must_not' CHECK (polarity IN ('must', 'must_not')),
                applies_to TEXT NOT NULL DEFAULT '[]',
                source TEXT NOT NULL DEFAULT 'proposed' CHECK (source IN ('human', 'proposed')),
                FOREIGN KEY (decision_id) REFERENCES decisions(decision_id) ON DELETE CASCADE
            );
            """)
            cursor.execute("""
            CREATE VIEW IF NOT EXISTS decision_constraints AS
            SELECT rule_id AS constraint_id, decision_id, rule_type, params_json, status, polarity, applies_to, source, created_by, created_at, approved_by, approved_at
            FROM guard_rules;
            """)
            conn.commit()

            # 10. Schema Migrations (Step 2.0)
            run_migrations(conn)

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

            # Check if decision already exists to validate transitions
            cursor.execute("SELECT state FROM decisions WHERE decision_id = ?", (decision.decision_id,))
            existing_row = cursor.fetchone()
            existing_state = existing_row["state"] if existing_row else None

            if existing_state is not None and existing_state != decision.state:
                from backend.engine.lifecycle import ALLOWED_TRANSITIONS, InvalidTransition
                allowed_targets = ALLOWED_TRANSITIONS.get(existing_state, set())
                if decision.state not in allowed_targets:
                    conn.rollback()
                    raise InvalidTransition(
                        f"Cannot save decision '{decision.decision_id}': illegal transition from '{existing_state}' to '{decision.state}'. "
                        f"Allowed transitions: {sorted(allowed_targets)}"
                    )

            cursor.execute("""
            INSERT INTO decisions (
                decision_id, title, state, made_by, made_at, rationale, confidence,
                review_status, supersedes_decision_id, superseded_by_decision_id,
                alternatives_json, repo, evidence_assessment, freshness
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                repo=excluded.repo,
                evidence_assessment=excluded.evidence_assessment,
                freshness=excluded.freshness;
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
                decision.repo,
                decision.evidence_assessment,
                decision.freshness
            ))

            # Update decision_evidence links
            cursor.execute("DELETE FROM decision_evidence WHERE decision_id = ?", (decision.decision_id,))
            for eid in decision.evidence_event_ids:
                cursor.execute("""
                INSERT OR IGNORE INTO decision_evidence (decision_id, event_id) VALUES (?, ?)
                """, (decision.decision_id, eid))

            # Invariant check at DB level (Section 13 / Step 2.1)
            cursor.execute("SELECT COUNT(*) as cnt FROM decision_evidence WHERE decision_id = ?", (decision.decision_id,))
            evidence_count = cursor.fetchone()["cnt"]
            if decision.state in ("tested", "accepted", "rejected", "superseded") and evidence_count == 0:
                conn.rollback()
                raise ValueError(
                    f"Mechanical Invariant Failure: Decision '{decision.title}' ({decision.decision_id}) has state='{decision.state}' persisted with 0 valid evidence records!"
                )
            elif decision.state in ("proposed", "reopened") and evidence_count == 0 and decision.evidence_assessment != "insufficient":
                conn.rollback()
                raise ValueError(
                    f"Mechanical Invariant Failure: Decision '{decision.title}' has state='{decision.state}' with 0 evidence records but evidence_assessment '{decision.evidence_assessment}' != 'insufficient'!"
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

            # Record state history
            cursor.execute("PRAGMA table_info(state_history)")
            sh_cols = {r["name"] for r in cursor.fetchall()}
            has_from = "from_state" in sh_cols
            has_rec = "reconstructed" in sh_cols

            if decision.state_history:
                for sh in decision.state_history:
                    sh_from = sh.get("from_state")
                    sh_to = sh.get("state", decision.state)
                    sh_at = sh.get("changed_at", decision.made_at)
                    sh_by = sh.get("changed_by", decision.made_by or "system")
                    sh_notes = sh.get("notes", "")
                    sh_id = sh.get("history_id", f"sh_{decision.decision_id}_{sh_at}")

                    if has_from and has_rec:
                        cursor.execute("""
                        INSERT OR REPLACE INTO state_history (history_id, decision_id, from_state, state, changed_at, changed_by, notes, reconstructed)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                        """, (sh_id, decision.decision_id, sh_from, sh_to, sh_at, sh_by, sh_notes))
                    elif has_from:
                        cursor.execute("""
                        INSERT OR REPLACE INTO state_history (history_id, decision_id, from_state, state, changed_at, changed_by, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (sh_id, decision.decision_id, sh_from, sh_to, sh_at, sh_by, sh_notes))
                    elif has_rec:
                        cursor.execute("""
                        INSERT OR REPLACE INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes, reconstructed)
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                        """, (sh_id, decision.decision_id, sh_to, sh_at, sh_by, sh_notes))
                    else:
                        cursor.execute("""
                        INSERT OR REPLACE INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (sh_id, decision.decision_id, sh_to, sh_at, sh_by, sh_notes))
            else:
                cursor.execute("SELECT COUNT(*) AS c FROM state_history WHERE decision_id = ?", (decision.decision_id,))
                prior_hist_count = cursor.fetchone()["c"]
                if existing_state is not None and existing_state != decision.state:
                    hist_id = f"hist_{decision.decision_id}_{time.time_ns()}_{uuid.uuid4().hex[:6]}"
                    notes_text = f"Transition: {existing_state} -> {decision.state}. Reason: {decision.rationale or 'State updated'}"
                    if has_from and has_rec:
                        cursor.execute("""
                        INSERT INTO state_history (history_id, decision_id, from_state, state, changed_at, changed_by, notes, reconstructed)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                        """, (hist_id, decision.decision_id, existing_state, decision.state, decision.made_at, decision.made_by or "system", notes_text))
                    elif has_from:
                        cursor.execute("""
                        INSERT INTO state_history (history_id, decision_id, from_state, state, changed_at, changed_by, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (hist_id, decision.decision_id, existing_state, decision.state, decision.made_at, decision.made_by or "system", notes_text))
                    elif has_rec:
                        cursor.execute("""
                        INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes, reconstructed)
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                        """, (hist_id, decision.decision_id, decision.state, decision.made_at, decision.made_by or "system", notes_text))
                    else:
                        cursor.execute("""
                        INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (hist_id, decision.decision_id, decision.state, decision.made_at, decision.made_by or "system", notes_text))
                elif prior_hist_count == 0:
                    hist_id = f"hist_init_{decision.decision_id}_{time.time_ns()}_{uuid.uuid4().hex[:6]}"
                    notes_text = f"Initial state: {decision.state}. Reason: {decision.rationale or 'Initial state recorded'}"
                    if has_from and has_rec:
                        cursor.execute("""
                        INSERT INTO state_history (history_id, decision_id, from_state, state, changed_at, changed_by, notes, reconstructed)
                        VALUES (?, ?, NULL, ?, ?, ?, ?, 0)
                        """, (hist_id, decision.decision_id, decision.state, decision.made_at, decision.made_by or "system:ingestion", notes_text))
                    elif has_from:
                        cursor.execute("""
                        INSERT INTO state_history (history_id, decision_id, from_state, state, changed_at, changed_by, notes)
                        VALUES (?, ?, NULL, ?, ?, ?, ?)
                        """, (hist_id, decision.decision_id, decision.state, decision.made_at, decision.made_by or "system:ingestion", notes_text))
                    elif has_rec:
                        cursor.execute("""
                        INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes, reconstructed)
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                        """, (hist_id, decision.decision_id, decision.state, decision.made_at, decision.made_by or "system:ingestion", notes_text))
                    else:
                        cursor.execute("""
                        INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (hist_id, decision.decision_id, decision.state, decision.made_at, decision.made_by or "system:ingestion", notes_text))

            # Step 3.1: Automatically sync decision claims and evidence links
            self._sync_decision_claims(cursor, decision)

            conn.commit()
            return decision.decision_id

    def _sync_decision_claims(self, cursor: sqlite3.Cursor, decision: Decision) -> None:
        """Helper to extract and sync claims and evidence for a decision inside an active cursor."""
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='decision_claims'")
            if not cursor.fetchone():
                return
            from backend.engine.independence import extract_claims_from_decision, extract_best_passage, independence_key

            claims = extract_claims_from_decision(decision)
            for clm in claims:
                cursor.execute("""
                INSERT OR REPLACE INTO decision_claims (claim_id, decision_id, claim_type, text)
                VALUES (?, ?, ?, ?)
                """, (clm.claim_id, clm.decision_id, clm.claim_type, clm.text))

                cursor.execute("""
                SELECT e.event_id, e.source_type, e.source_id, e.source_url, e.repo, e.title, e.body, e.raw_metadata, e.parent_event_ids
                FROM decision_evidence de
                JOIN events e ON de.event_id = e.event_id
                WHERE de.decision_id = ?
                """, (decision.decision_id,))
                ev_rows = cursor.fetchall()
                ev_dicts = []
                for er in ev_rows:
                    rm = {}
                    if er["raw_metadata"]:
                        try:
                            rm = json.loads(er["raw_metadata"])
                        except Exception:
                            pass
                    pe = []
                    if er["parent_event_ids"]:
                        try:
                            pe = json.loads(er["parent_event_ids"])
                        except Exception:
                            pass
                    ev_dicts.append({
                        "event_id": er["event_id"],
                        "source_type": er["source_type"],
                        "source_id": er["source_id"],
                        "source_url": er["source_url"],
                        "repo": er["repo"],
                        "title": er["title"],
                        "body": er["body"],
                        "raw_metadata": rm,
                        "parent_event_ids": pe
                    })

                for ev in ev_dicts:
                    sg = independence_key(ev, all_events=ev_dicts)
                    full_text = f"{ev.get('title') or ''}\n{ev.get('body') or ''}".strip()
                    p_text, p_start, p_end, rel = extract_best_passage(clm.text, full_text)
                    cursor.execute("""
                    INSERT OR REPLACE INTO claim_evidence (
                        claim_id, event_id, relation, passage_text, passage_start, passage_end, source_group
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (clm.claim_id, ev["event_id"], rel, p_text, p_start, p_end, sg))

            # Step 3.2: Recompute assessment label and store in decisions.evidence_assessment
            from backend.engine.evidence import assess
            assessment = assess(decision, db=self)
            new_label = assessment.get("label", "insufficient")
            cursor.execute("UPDATE decisions SET evidence_assessment = ? WHERE decision_id = ?", (new_label, decision.decision_id))
            decision.evidence_assessment = new_label
        except Exception:
            pass

    def recompute_evidence_assessment(self, decision_id: str) -> str:
        """Recomputes deterministic evidence assessment label for a decision and updates database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,))
            row = cursor.fetchone()
            if not row:
                return "insufficient"
            from backend.engine.evidence import assess
            assessment = assess(dict(row), db=self)
            label = assessment.get("label", "insufficient")
            cursor.execute("UPDATE decisions SET evidence_assessment = ? WHERE decision_id = ?", (label, decision_id))
            conn.commit()
            return label

    def upsert_decision(self, decision: Decision) -> str:
        """Alias for save_decision."""
        return self.save_decision(decision)

    def save_claim(self, claim: DecisionClaim) -> str:
        claim.validate()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO decision_claims (claim_id, decision_id, claim_type, text)
            VALUES (?, ?, ?, ?)
            """, (claim.claim_id, claim.decision_id, claim.claim_type, claim.text))
            conn.commit()
            return claim.claim_id

    def get_claims_for_decision(self, decision_id: str) -> List[DecisionClaim]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT claim_id, decision_id, claim_type, text
            FROM decision_claims
            WHERE decision_id = ?
            ORDER BY claim_id ASC
            """, (decision_id,))
            rows = cursor.fetchall()
            return [
                DecisionClaim(
                    claim_id=r["claim_id"],
                    decision_id=r["decision_id"],
                    claim_type=r["claim_type"],
                    text=r["text"]
                )
                for r in rows
            ]

    def save_claim_evidence(self, ce: ClaimEvidence) -> None:
        ce.validate()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO claim_evidence (
                claim_id, event_id, relation, passage_text, passage_start, passage_end, source_group
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ce.claim_id, ce.event_id, ce.relation, ce.passage_text, ce.passage_start, ce.passage_end, ce.source_group))
            conn.commit()

    def get_claim_evidence(self, claim_id: str) -> List[ClaimEvidence]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT claim_id, event_id, relation, passage_text, passage_start, passage_end, source_group
            FROM claim_evidence
            WHERE claim_id = ?
            ORDER BY event_id ASC
            """, (claim_id,))
            rows = cursor.fetchall()
            return [
                ClaimEvidence(
                    claim_id=r["claim_id"],
                    event_id=r["event_id"],
                    relation=r["relation"],
                    passage_text=r["passage_text"],
                    passage_start=r["passage_start"],
                    passage_end=r["passage_end"],
                    source_group=r["source_group"]
                )
                for r in rows
            ]

    def get_all_claim_evidence_for_decision(self, decision_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT dc.claim_id, dc.decision_id, dc.claim_type, dc.text AS claim_text,
                   ce.event_id, ce.relation, ce.passage_text, ce.passage_start, ce.passage_end, ce.source_group,
                   e.source_type, e.source_url, e.author, e.ts, e.title AS event_title
            FROM decision_claims dc
            JOIN claim_evidence ce ON dc.claim_id = ce.claim_id
            JOIN events e ON ce.event_id = e.event_id
            WHERE dc.decision_id = ?
            ORDER BY dc.claim_id ASC, ce.event_id ASC
            """, (decision_id,))
            return [dict(r) for r in cursor.fetchall()]

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

            # State transitions history (Section 5.2 / Section 4.1)
            cursor.execute("""
            SELECT * FROM state_history WHERE decision_id = ? ORDER BY changed_at ASC
            """, (decision_id,))
            state_history = [dict(r) for r in cursor.fetchall()]

            return {
                "decision": decision,
                "evidence_events": evidence_events,
                "discussion_events": discussion_events,
                "state_history": state_history
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

    # --- Guard Rules & Decision Constraints Methods (Section 5.1 & Step 3.4) ---

    def upsert_guard_rule(self, rule: GuardRule) -> str:
        """Upserts a decision guard rule / decision constraint (Step 3.4)."""
        applies_val = rule.applies_to if isinstance(rule.applies_to, list) else (rule.params.get("paths", []) if rule.params else [])
        polarity_val = rule.polarity or ("must" if rule.rule_type == "require_import" else "must_not")
        source_val = rule.source or "proposed"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO guard_rules (
                rule_id, decision_id, rule_type, params_json, status,
                created_by, created_at, approved_by, approved_at,
                polarity, applies_to, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(rule_id) DO UPDATE SET
                rule_type=excluded.rule_type,
                params_json=excluded.params_json,
                status=excluded.status,
                approved_by=excluded.approved_by,
                approved_at=excluded.approved_at,
                polarity=excluded.polarity,
                applies_to=excluded.applies_to,
                source=excluded.source;
            """, (
                rule.rule_id,
                rule.decision_id,
                rule.rule_type,
                json.dumps(rule.params),
                rule.status,
                rule.created_by,
                rule.created_at,
                rule.approved_by,
                rule.approved_at,
                polarity_val,
                json.dumps(applies_val),
                source_val
            ))
            conn.commit()
            return rule.rule_id

    def get_guard_rules(self, decision_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries guard rules with optional filtering by decision_id or status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT gr.*, d.title as decision_title, d.repo as repo FROM guard_rules gr JOIN decisions d ON gr.decision_id = d.decision_id WHERE 1=1"
            params = []
            if decision_id:
                query += " AND gr.decision_id = ?"
                params.append(decision_id)
            if status:
                query += " AND gr.status = ?"
                params.append(status)

            query += " ORDER BY gr.created_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            rules = []
            for r in rows:
                item = dict(r)
                try:
                    item["params"] = json.loads(item["params_json"]) if item["params_json"] else {}
                except Exception as e:
                    item["params"] = None
                    item["_parse_error"] = str(e)
                try:
                    item["applies_to"] = json.loads(item["applies_to"]) if item.get("applies_to") else []
                except Exception:
                    item["applies_to"] = []
                rules.append(item)
            return rules

    def get_decision_evidence_passages(self, decision_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves evidence passages and clickable source URLs for a decision (Step 3.4).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT ce.passage_text, ce.relation, e.source_url, e.author, e.title, e.ts
            FROM claim_evidence ce
            JOIN decision_claims dc ON ce.claim_id = dc.claim_id
            JOIN events e ON ce.event_id = e.event_id
            WHERE dc.decision_id = ?
            ORDER BY ce.passage_text DESC
            """, (decision_id,))
            rows = [dict(r) for r in cursor.fetchall()]
            if not rows:
                # Fallback to decision_evidence direct events
                cursor.execute("""
                SELECT ev.body as passage_text, 'direct' as relation, ev.source_url, ev.author, ev.title, ev.ts
                FROM decision_evidence de
                JOIN events ev ON de.event_id = ev.event_id
                WHERE de.decision_id = ?
                """, (decision_id,))
                rows = [dict(r) for r in cursor.fetchall()]
            return rows

    def update_guard_rule_status(self, rule_id: str, status: str, approved_by: Optional[str] = None) -> bool:
        """Updates the status of a guard rule (e.g. approve -> active, disable -> disabled)."""
        if status not in ("proposed", "active", "disabled"):
            raise ValueError(f"Invalid guard rule status: '{status}'")

        approved_at = datetime.now().isoformat() + "Z" if status == "active" else None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE guard_rules SET
                status = ?,
                approved_by = COALESCE(?, approved_by),
                approved_at = COALESCE(?, approved_at)
            WHERE rule_id = ?
            """, (status, approved_by, approved_at, rule_id))
            conn.commit()
            return cursor.rowcount > 0

