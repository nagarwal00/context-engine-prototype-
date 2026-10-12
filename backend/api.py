"""
Context Intelligence Framework - REST API Handler
Provides clean JSON REST endpoints for all 6 UI surfaces, review actions, and evaluation.
"""
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import hmac
import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime
import urllib.parse
from backend.db import Database
from backend.engine.graph import TemporalGraph
from backend.engine.explanation import ExplanationGenerator
from backend.engine.reconciliation import ReconciliationEngine
from backend.engine.drift_detector import DriftDetector
import uuid
from backend.evaluation.benchmark import BenchmarkRunner
from backend.seed_data import populate_seed_data
from backend.security import (
    ROLE_VIEWER,
    ROLE_REVIEWER,
    ROLE_ADMIN,
    ROLE_EXEMPT,
    authorize,
    is_dev_mode,
    get_authenticated_role
)

# Route-to-role authorization mapping (Step 1.2 / P0-b)
# Default deny: any route not explicitly listed here is rejected.
ROUTE_ROLES: Dict[Tuple[str, str], str] = {
    # GET routes (viewer)
    ("GET", "/api/timeline"): ROLE_VIEWER,
    ("GET", "/api/graph"): ROLE_VIEWER,
    ("GET", "/api/artifacts"): ROLE_VIEWER,
    ("GET", "/api/explain"): ROLE_VIEWER,
    ("GET", "/api/decisions"): ROLE_VIEWER,
    ("GET", "/api/evidence"): ROLE_VIEWER,
    ("GET", "/api/review-queue"): ROLE_VIEWER,
    ("GET", "/api/benchmark"): ROLE_VIEWER,
    ("GET", "/api/stats"): ROLE_VIEWER,
    ("GET", "/api/repos"): ROLE_VIEWER,
    ("GET", "/api/guard-rules"): ROLE_VIEWER,
    ("GET", "/api/auth-status"): ROLE_VIEWER,
    ("GET", "/api/decision-history"): ROLE_VIEWER,
    ("GET", "/api/as-of"): ROLE_VIEWER,

    # POST routes (reviewer)
    ("POST", "/api/review-action"): ROLE_REVIEWER,
    ("POST", "/api/guard-rules/approve"): ROLE_REVIEWER,
    ("POST", "/api/guard-rules/disable"): ROLE_REVIEWER,
    ("POST", "/api/drift-check"): ROLE_REVIEWER,

    # POST routes (admin)
    ("POST", "/api/reseed"): ROLE_ADMIN,
    ("POST", "/api/clear-db"): ROLE_ADMIN,
    ("POST", "/api/ingest-repo"): ROLE_ADMIN,

    # Webhook (exempt from Bearer token - uses GitHub HMAC signature)
    ("POST", "/api/webhook/github"): ROLE_EXEMPT,
}

class APIHandler:
    def __init__(self, db: Database):
        self.db = db
        self.graph = TemporalGraph(db)
        self.explanation_gen = ExplanationGenerator(db)
        self.reconciliation = ReconciliationEngine(db)
        self.drift_detector = DriftDetector(db)
        self.benchmark_runner = BenchmarkRunner(db)

    def check_authorization(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        client_ip: str = "127.0.0.1"
    ) -> Tuple[bool, int, str]:
        """Validates route existence and credentials against required role (default deny)."""
        required_role = ROUTE_ROLES.get((method.upper(), path))
        if required_role is None:
            return False, 404, f"Endpoint not found: {method.upper()} {path}"
        return authorize(headers, required_role, client_ip)

    def handle_get(self, path: str, query_params: Dict[str, List[str]]) -> Dict[str, Any]:
        # 1. Timeline Slice
        if path == "/api/timeline":
            repo = query_params.get("repo", [None])[0]
            start = query_params.get("start", [None])[0]
            end = query_params.get("end", [None])[0]
            return {"status": "success", "data": self.db.query_timeline_slice(repo, start, end)}

        # 2. Context Graph
        elif path == "/api/graph":
            repo = query_params.get("repo", [None])[0]
            return {"status": "success", "data": self.graph.get_full_graph_visualization_data(repo)}

        # 3. Artifacts / Code-Context Entities
        elif path == "/api/artifacts":
            repo = query_params.get("repo", [None])[0]
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM entities"
                params = []
                if repo:
                    query += " WHERE repo = ?"
                    params.append(repo)
                query += " ORDER BY entity_type, canonical_path"
                cursor.execute(query, params)
                entities = [dict(r) for r in cursor.fetchall()]
                for e in entities:
                    e["aliases"] = json.loads(e["aliases"]) if e["aliases"] else []
                    # Get decision count
                    cursor.execute("SELECT COUNT(*) as cnt FROM decision_artifacts WHERE entity_id = ?", (e["entity_id"],))
                    e["decision_count"] = cursor.fetchone()["cnt"]
            return {"status": "success", "data": entities}

        # 4. Code-Context View / Explain Artifact
        elif path == "/api/explain":
            decision_id = query_params.get("decision_id", [None])[0]
            artifact = query_params.get("artifact", [None])[0]
            if decision_id:
                res = self.explanation_gen.explain_decision(decision_id)
            elif artifact:
                res = self.explanation_gen.explain_artifact(artifact)
            else:
                res = self.explanation_gen.explain_artifact("src/thermal/control.py::regulate_temperature")

            if res.get("status") == "insufficient_evidence":
                return {
                    "status": "insufficient_evidence",
                    "message": res.get("message") or res.get("explanation"),
                    "data": res
                }
            return {"status": "success", "data": res}

        # 5. Decision Explorer
        elif path == "/api/decisions":
            repo = query_params.get("repo", [None])[0]
            state = query_params.get("state", [None])[0]
            search = query_params.get("search", [None])[0]

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM decisions WHERE review_status != 'human_rejected'"
                params = []
                if repo:
                    query += " AND repo = ?"
                    params.append(repo)
                if state:
                    query += " AND state = ?"
                    params.append(state)
                if search:
                    query += " AND (title LIKE ? OR rationale LIKE ?)"
                    params.extend([f"%{search}%", f"%{search}%"])
                query += " ORDER BY made_at DESC"
                cursor.execute(query, params)
                decisions = []
                for r in cursor.fetchall():
                    d = dict(r)
                    d["alternatives_considered"] = json.loads(d["alternatives_json"]) if d["alternatives_json"] else []
                    cursor.execute("SELECT COUNT(*) as cnt FROM decision_evidence WHERE decision_id = ?", (d["decision_id"],))
                    d["evidence_count"] = cursor.fetchone()["cnt"]
                    decisions.append(d)
            return {"status": "success", "data": decisions}

        # 6. Evidence Panel
        elif path == "/api/evidence":
            decision_id = query_params.get("decision_id", ["dec_thermal_pid_accepted"])[0]
            return {"status": "success", "data": self.db.query_full_evidence_trail(decision_id)}

        # 7. Review Queue
        elif path == "/api/review-queue":
            queue = []
            seen_decision_ids = set()
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Low confidence decisions (< 0.90) or pending_review
                # OR evidence quality labels 'weak', 'insufficient', 'contradicted' (Step 3.2 review routing)
                cursor.execute("""
                SELECT * FROM decisions
                WHERE (confidence < 0.90 OR review_status = 'pending_review' OR evidence_assessment IN ('weak', 'insufficient', 'contradicted'))
                  AND review_status NOT IN ('human_rejected', 'human_confirmed')
                ORDER BY confidence ASC
                """)
                for r in cursor.fetchall():
                    d = dict(r)
                    ea = d.get("evidence_assessment", "insufficient")
                    if ea == "contradicted":
                        d["queue_reason"] = "Evidence quality assessed as 'contradicted': active contradictory findings detected"
                    elif ea == "insufficient":
                        d["queue_reason"] = "Evidence quality assessed as 'insufficient': missing evidence links or corroboration"
                    elif ea == "weak":
                        d["queue_reason"] = "Evidence quality assessed as 'weak': single source group without independent corroboration"
                    else:
                        d["queue_reason"] = f"Low extraction confidence ({round(d['confidence']*100)}%) or pending review"
                    d["item_type"] = "decision"
                    seen_decision_ids.add(d["decision_id"])
                    queue.append(d)

                # Conflicts
                cursor.execute("SELECT * FROM edges WHERE edge_type = 'conflicts_with'")
                for r in cursor.fetchall():
                    ed = dict(r)
                    cursor.execute("SELECT title, made_by FROM decisions WHERE decision_id = ?", (ed["from_id"],))
                    d1 = cursor.fetchone()
                    cursor.execute("SELECT title, made_by FROM decisions WHERE decision_id = ?", (ed["to_id"],))
                    d2 = cursor.fetchone()
                    queue.append({
                        "item_type": "conflict",
                        "edge_id": ed["edge_id"],
                        "from_id": ed["from_id"],
                        "to_id": ed["to_id"],
                        "title": f"Conflict: '{d1['title'] if d1 else ed['from_id']}' vs '{d2['title'] if d2 else ed['to_id']}'",
                        "queue_reason": "Contributor/Architectural Disagreement Detected",
                        "confidence": 0.88,
                        "review_status": "pending_review",
                        "made_at": ed["valid_from"]
                    })

                # Drifts
                cursor.execute("SELECT * FROM edges WHERE edge_type = 'drifts_from'")
                for r in cursor.fetchall():
                    ed = dict(r)
                    cursor.execute("SELECT canonical_path FROM entities WHERE entity_id = ?", (ed["from_id"],))
                    ent = cursor.fetchone()
                    cursor.execute("SELECT title FROM decisions WHERE decision_id = ?", (ed["to_id"],))
                    dec = cursor.fetchone()
                    queue.append({
                        "item_type": "drift",
                        "edge_id": ed["edge_id"],
                        "entity_id": ed["from_id"],
                        "decision_id": ed["to_id"],
                        "title": f"Drift on {ent['canonical_path'] if ent else 'artifact'}",
                        "queue_reason": f"Code diff contradicts accepted decision '{dec['title'] if dec else 'unknown'}'",
                        "confidence": 0.93,
                        "review_status": "pending_review",
                        "made_at": ed["valid_from"]
                    })

                # Supersession candidates (P1-d / Step 1.6)
                cursor.execute("SELECT * FROM edges WHERE edge_type = 'supersession_candidate'")
                for r in cursor.fetchall():
                    ed = dict(r)
                    cursor.execute("SELECT title FROM decisions WHERE decision_id = ?", (ed["from_id"],))
                    d1 = cursor.fetchone()
                    cursor.execute("SELECT title FROM decisions WHERE decision_id = ?", (ed["to_id"],))
                    d2 = cursor.fetchone()
                    queue.append({
                        "item_type": "supersession_candidate",
                        "edge_id": ed["edge_id"],
                        "from_id": ed["from_id"],
                        "to_id": ed["to_id"],
                        "title": f"Candidate Supersession: '{d1['title'] if d1 else ed['from_id']}' -> '{d2['title'] if d2 else ed['to_id']}'",
                        "queue_reason": "Ambiguous supersession candidate flagged for human arbitration per Section 10",
                        "confidence": 0.70,
                        "review_status": "pending_review",
                        "made_at": ed["valid_from"]
                    })

            return {"status": "success", "data": queue}

        # 8. Evaluation & Benchmark
        elif path == "/api/benchmark":
            return {"status": "success", "data": self.benchmark_runner.run_full_evaluation()}

        # 9. Summary stats
        elif path == "/api/stats":
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as c FROM decisions")
                dec_cnt = cursor.fetchone()["c"]
                cursor.execute("SELECT COUNT(*) as c FROM events")
                evt_cnt = cursor.fetchone()["c"]
                cursor.execute("SELECT COUNT(*) as c FROM entities")
                ent_cnt = cursor.fetchone()["c"]
                cursor.execute("SELECT COUNT(*) as c FROM edges")
                edg_cnt = cursor.fetchone()["c"]
                cursor.execute("SELECT COUNT(*) as c FROM edges WHERE edge_type = 'drifts_from'")
                drf_cnt = cursor.fetchone()["c"]
                cursor.execute("SELECT COUNT(*) as c FROM edges WHERE edge_type = 'conflicts_with'")
                cnf_cnt = cursor.fetchone()["c"]

            return {
                "status": "success",
                "data": {
                    "decisions": dec_cnt,
                    "events": evt_cnt,
                    "entities": ent_cnt,
                    "edges": edg_cnt,
                    "drifts": drf_cnt,
                    "conflicts": cnf_cnt
                }
            }

        # 10. Distinct Repositories
        elif path == "/api/repos":
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT repo FROM (
                        SELECT repo FROM decisions WHERE repo IS NOT NULL AND repo != ''
                        UNION
                        SELECT repo FROM events WHERE repo IS NOT NULL AND repo != ''
                        UNION
                        SELECT repo FROM entities WHERE repo IS NOT NULL AND repo != ''
                    ) ORDER BY repo ASC
                """)
                repos = [r["repo"] for r in cursor.fetchall()]
            return {"status": "success", "data": repos}

        # 11. Decision Guard Rules (Section 5.4)
        elif path == "/api/guard-rules":
            status_filter = query_params.get("status", [None])[0]
            rules = self.db.get_guard_rules(status=status_filter)
            return {"status": "success", "data": rules}

        # 12. Auth Status (Step 1.2 / P0-b)
        elif path == "/api/auth-status":
            return {
                "status": "success",
                "data": {
                    "role_required_for_writes": True,
                    "dev_mode": is_dev_mode()
                }
            }

        # 13. Decision Lifecycle History and Audit Log (Step 2.5)
        elif path == "/api/decision-history":
            decision_id = query_params.get("decision_id", [None])[0]
            actor_filter = query_params.get("actor", [None])[0]
            date_filter = query_params.get("date", [None])[0]

            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                if decision_id:
                    cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,))
                    d_row = cursor.fetchone()
                    if not d_row:
                        return {"status": "error", "message": f"Decision '{decision_id}' not found", "status_code": 404}

                    dec = dict(d_row)

                    cursor.execute("PRAGMA table_info(state_history)")
                    cols = {r["name"] for r in cursor.fetchall()}
                    has_from = "from_state" in cols
                    has_rec = "reconstructed" in cols

                    cursor.execute("""
                    SELECT * FROM state_history
                    WHERE decision_id = ?
                    ORDER BY changed_at ASC
                    """, (decision_id,))
                    history_rows = [dict(r) for r in cursor.fetchall()]

                    transitions = []
                    for h in history_rows:
                        is_reconstructed = bool(h.get("reconstructed", 0)) if has_rec else (
                            h.get("changed_by") == "system:backfill" or "reconstructed" in (h.get("notes") or "").lower()
                        )
                        transitions.append({
                            "history_id": h.get("history_id"),
                            "decision_id": h.get("decision_id"),
                            "from_state": h.get("from_state") if has_from else None,
                            "to_state": h.get("state"),
                            "state": h.get("state"),
                            "changed_at": h.get("changed_at"),
                            "changed_by": h.get("changed_by"),
                            "notes": h.get("notes") or "",
                            "reconstructed": is_reconstructed
                        })

                    # Supersession chain traversal:
                    # Preceding decisions (what this decision supersedes)
                    preceding = []
                    curr_prev = dec.get("supersedes_decision_id")
                    seen_prev = {decision_id}
                    while curr_prev and curr_prev not in seen_prev:
                        seen_prev.add(curr_prev)
                        cursor.execute("SELECT decision_id, title, state, made_at, made_by, supersedes_decision_id FROM decisions WHERE decision_id = ?", (curr_prev,))
                        p_row = cursor.fetchone()
                        if p_row:
                            p_dict = dict(p_row)
                            preceding.append(p_dict)
                            curr_prev = p_dict.get("supersedes_decision_id")
                        else:
                            break

                    # Succeeding decisions (what supersedes this decision)
                    succeeding = []
                    curr_next = dec.get("superseded_by_decision_id")
                    seen_next = {decision_id}
                    while curr_next and curr_next not in seen_next:
                        seen_next.add(curr_next)
                        cursor.execute("SELECT decision_id, title, state, made_at, made_by, superseded_by_decision_id FROM decisions WHERE decision_id = ?", (curr_next,))
                        n_row = cursor.fetchone()
                        if n_row:
                            n_dict = dict(n_row)
                            succeeding.append(n_dict)
                            curr_next = n_dict.get("superseded_by_decision_id")
                        else:
                            break

                    return {
                        "status": "success",
                        "data": {
                            "decision": {
                                "decision_id": dec["decision_id"],
                                "title": dec["title"],
                                "state": dec["state"],
                                "made_by": dec.get("made_by"),
                                "made_at": dec.get("made_at"),
                                "rationale": dec.get("rationale"),
                                "repo": dec.get("repo"),
                                "evidence_assessment": dec.get("evidence_assessment", "insufficient"),
                                "freshness": dec.get("freshness", "fresh"),
                                "supersedes_decision_id": dec.get("supersedes_decision_id"),
                                "superseded_by_decision_id": dec.get("superseded_by_decision_id")
                            },
                            "transitions": transitions,
                            "supersession_chain": {
                                "preceding": preceding,
                                "current": {
                                    "decision_id": dec["decision_id"],
                                    "title": dec["title"],
                                    "state": dec["state"]
                                },
                                "succeeding": succeeding
                            }
                        }
                    }

                else:
                    # Global audit log (filterable by actor or date)
                    cursor.execute("PRAGMA table_info(state_history)")
                    cols = {r["name"] for r in cursor.fetchall()}
                    has_from = "from_state" in cols
                    has_rec = "reconstructed" in cols

                    query = """
                    SELECT sh.*, d.title as decision_title, d.repo as decision_repo
                    FROM state_history sh
                    LEFT JOIN decisions d ON sh.decision_id = d.decision_id
                    WHERE 1=1
                    """
                    params = []
                    if actor_filter:
                        query += " AND sh.changed_by LIKE ?"
                        params.append(f"%{actor_filter}%")
                    if date_filter:
                        query += " AND sh.changed_at LIKE ?"
                        params.append(f"{date_filter}%")

                    query += " ORDER BY sh.changed_at DESC"
                    cursor.execute(query, params)
                    rows = [dict(r) for r in cursor.fetchall()]

                    audit_log = []
                    for h in rows:
                        is_reconstructed = bool(h.get("reconstructed", 0)) if has_rec else (
                            h.get("changed_by") == "system:backfill" or "reconstructed" in (h.get("notes") or "").lower()
                        )
                        audit_log.append({
                            "history_id": h.get("history_id"),
                            "decision_id": h.get("decision_id"),
                            "decision_title": h.get("decision_title"),
                            "decision_repo": h.get("decision_repo"),
                            "from_state": h.get("from_state") if has_from else None,
                            "to_state": h.get("state"),
                            "state": h.get("state"),
                            "changed_at": h.get("changed_at"),
                            "changed_by": h.get("changed_by"),
                            "notes": h.get("notes") or "",
                            "reconstructed": is_reconstructed
                        })

                    return {
                        "status": "success",
                        "data": {
                            "audit_log": audit_log,
                            "total_count": len(audit_log)
                        }
                    }

        if path == "/api/as-of":
            repo = query_params.get("repo", [None])[0]
            date_param = query_params.get("date", [None])[0]
            cutoff_param = query_params.get("cutoff", [None])[0]
            cutoff_val = date_param or cutoff_param
            artifact = query_params.get("artifact", [None])[0]

            if not cutoff_val:
                return {
                    "status": "error",
                    "message": "Missing required parameter 'date' (e.g. YYYY-MM-DD or ISO-8601 timestamp)",
                    "status_code": 400
                }

            from backend.engine.as_of import as_of
            try:
                result = as_of(self.db, repo=repo, cutoff=cutoff_val, artifact=artifact)
                return result
            except ValueError as ve:
                return {"status": "error", "message": str(ve), "status_code": 400}
            except Exception as e:
                return {"status": "error", "message": f"Error executing as_of query: {e}", "status_code": 500}

        return {"status": "error", "message": f"Unknown endpoint {path}"}

    def handle_post(
        self,
        path: str,
        body: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        client_ip: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        # 1. Review Actions (confirm | reject | merge | correct | reopen | mark_tested per Step 2.4)
        if path == "/api/review-action":
            action = body.get("action")
            target_id = body.get("target_id")
            item_type = body.get("item_type", "decision")
            reason = (body.get("reason") or body.get("notes") or "").strip()

            if not action or not target_id:
                return {
                    "status": "error",
                    "status_code": 400,
                    "message": "Missing 'action' or 'target_id' in review request"
                }

            if not reason:
                if action in ("reopen", "mark_tested"):
                    return {
                        "status": "error",
                        "status_code": 400,
                        "message": f"Review action '{action}' requires a non-empty reason"
                    }
                else:
                    reason = f"Human triage action: {action}"

            # Record reviewer identity: token role + optional display name (Step 2.4)
            token_role = get_authenticated_role(headers, client_ip)
            display_name = (body.get("reviewer") or body.get("reviewer_name") or body.get("display_name") or "").strip()
            if display_name:
                actor = f"{token_role}:{display_name}"
            else:
                actor = body.get("actor") or token_role

            now_iso = datetime.utcnow().isoformat() + "Z"

            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                if item_type == "decision":
                    cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (target_id,))
                    d_row = cursor.fetchone()
                    if not d_row:
                        return {
                            "status": "error",
                            "status_code": 404,
                            "message": f"Decision '{target_id}' not found"
                        }

                    cur_state = d_row["state"]
                    from backend.engine.lifecycle import transition, InvalidTransition

                    try:
                        if action == "mark_tested":
                            transition(conn, target_id, "tested", actor=actor, reason=reason, at=now_iso)
                            cursor.execute("""
                            UPDATE decisions SET review_status = 'human_tested' WHERE decision_id = ?
                            """, (target_id,))

                        elif action == "confirm":
                            if cur_state in ("proposed", "tested"):
                                transition(conn, target_id, "accepted", actor=actor, reason=reason, at=now_iso)
                            elif cur_state == "accepted":
                                # Already accepted: record triage confirmation history row
                                hist_id = f"hist_rev_{target_id}_{time.time_ns()}_{uuid.uuid4().hex[:6]}"
                                cursor.execute("PRAGMA table_info(state_history)")
                                sh_cols = {r["name"] for r in cursor.fetchall()}
                                notes_entry = f"Review confirmed: {reason}"
                                if "reconstructed" in sh_cols:
                                    cursor.execute("""
                                    INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes, reconstructed)
                                    VALUES (?, ?, 'accepted', ?, ?, ?, 0)
                                    """, (hist_id, target_id, now_iso, actor, notes_entry))
                                else:
                                    cursor.execute("""
                                    INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                                    VALUES (?, ?, 'accepted', ?, ?, ?)
                                    """, (hist_id, target_id, now_iso, actor, notes_entry))
                            else:
                                raise InvalidTransition(f"Cannot confirm decision currently in '{cur_state}' state")

                            cursor.execute("""
                            UPDATE decisions SET review_status = 'human_confirmed', confidence = 1.0
                            WHERE decision_id = ?
                            """, (target_id,))

                        elif action == "reject":
                            if cur_state in ("proposed", "tested"):
                                transition(conn, target_id, "rejected", actor=actor, reason=reason, at=now_iso)
                            elif cur_state == "rejected":
                                hist_id = f"hist_rev_{target_id}_{time.time_ns()}_{uuid.uuid4().hex[:6]}"
                                cursor.execute("PRAGMA table_info(state_history)")
                                sh_cols = {r["name"] for r in cursor.fetchall()}
                                notes_entry = f"Review rejected: {reason}"
                                if "reconstructed" in sh_cols:
                                    cursor.execute("""
                                    INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes, reconstructed)
                                    VALUES (?, ?, 'rejected', ?, ?, ?, 0)
                                    """, (hist_id, target_id, now_iso, actor, notes_entry))
                                else:
                                    cursor.execute("""
                                    INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                                    VALUES (?, ?, 'rejected', ?, ?, ?)
                                    """, (hist_id, target_id, now_iso, actor, notes_entry))
                            else:
                                raise InvalidTransition(f"Cannot reject decision currently in '{cur_state}' state. Must be reopened or superseded.")

                            cursor.execute("""
                            UPDATE decisions SET review_status = 'human_rejected' WHERE decision_id = ?
                            """, (target_id,))

                        elif action == "reopen":
                            transition(conn, target_id, "reopened", actor=actor, reason=reason, at=now_iso)
                            cursor.execute("""
                            UPDATE decisions SET review_status = 'human_reopened' WHERE decision_id = ?
                            """, (target_id,))

                        elif action == "merge":
                            into_id = body.get("into_decision_id") or body.get("canonical_decision_id")
                            if not into_id:
                                return {
                                    "status": "error",
                                    "status_code": 400,
                                    "message": "Action 'merge' requires 'into_decision_id'"
                                }
                            cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (into_id,))
                            if not cursor.fetchone():
                                return {
                                    "status": "error",
                                    "status_code": 404,
                                    "message": f"Target decision to merge into '{into_id}' not found"
                                }
                            if cur_state in ("proposed", "tested"):
                                transition(conn, target_id, "accepted", actor=actor, reason=f"Accepted for merge: {reason}", at=now_iso)
                            transition(conn, target_id, "superseded", actor=actor, reason=f"Merged into {into_id}: {reason}", at=now_iso, superseded_by_id=into_id)
                            cursor.execute("""
                            UPDATE decisions SET review_status = 'human_merged' WHERE decision_id = ?
                            """, (target_id,))

                        elif action == "correct":
                            new_state = body.get("state")
                            new_title = body.get("title")
                            new_rationale = body.get("rationale")
                            if new_state and new_state != cur_state:
                                transition(conn, target_id, new_state, actor=actor, reason=reason, at=now_iso)
                            else:
                                hist_id = f"hist_rev_{target_id}_{time.time_ns()}_{uuid.uuid4().hex[:6]}"
                                cursor.execute("PRAGMA table_info(state_history)")
                                sh_cols = {r["name"] for r in cursor.fetchall()}
                                notes_entry = f"Correction applied: {reason}"
                                if "reconstructed" in sh_cols:
                                    cursor.execute("""
                                    INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes, reconstructed)
                                    VALUES (?, ?, ?, ?, ?, ?, 0)
                                    """, (hist_id, target_id, cur_state, now_iso, actor, notes_entry))
                                else:
                                    cursor.execute("""
                                    INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                    """, (hist_id, target_id, cur_state, now_iso, actor, notes_entry))

                            cursor.execute("""
                            UPDATE decisions SET
                                title = COALESCE(?, title),
                                rationale = COALESCE(?, rationale),
                                review_status = 'human_corrected'
                            WHERE decision_id = ?
                            """, (new_title, new_rationale, target_id))

                        else:
                            return {
                                "status": "error",
                                "status_code": 400,
                                "message": f"Unknown review action '{action}' for decision"
                            }

                        conn.commit()

                    except InvalidTransition as e:
                        conn.rollback()
                        return {
                            "status": "error",
                            "status_code": 409,
                            "message": f"Conflict: {str(e)}"
                        }
                    except ValueError as e:
                        conn.rollback()
                        return {
                            "status": "error",
                            "status_code": 409,
                            "message": f"Conflict: {str(e)}"
                        }

                elif item_type in ("conflict", "drift"):
                    if action in ("confirm", "reject"):
                        cursor.execute("DELETE FROM edges WHERE edge_id = ?", (target_id,))
                        conn.commit()

                elif item_type == "supersession_candidate":
                    cursor.execute("""
                        SELECT * FROM edges
                        WHERE edge_id = ? OR (from_id = ? AND edge_type = 'supersession_candidate')
                    """, (target_id, target_id))
                    edge_row = cursor.fetchone()
                    if edge_row:
                        edge = dict(edge_row)
                        newer_id = edge["from_id"]
                        older_id = edge["to_id"]
                        if action == "confirm":
                            cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (newer_id,))
                            new_dec = cursor.fetchone()
                            d_time = new_dec["made_at"] if new_dec else now_iso

                            from backend.engine.lifecycle import transition, InvalidTransition
                            try:
                                transition(
                                    conn,
                                    older_id,
                                    "superseded",
                                    actor=actor,
                                    reason=reason,
                                    at=d_time,
                                    superseded_by_id=newer_id
                                )
                                cursor.execute("DELETE FROM edges WHERE edge_id = ?", (edge["edge_id"],))
                                conn.commit()
                            except (InvalidTransition, ValueError) as e:
                                conn.rollback()
                                return {
                                    "status": "error",
                                    "status_code": 409,
                                    "message": f"Conflict: {str(e)}"
                                }
                        elif action == "reject":
                            cursor.execute("DELETE FROM edges WHERE edge_id = ?", (edge["edge_id"],))
                            conn.commit()
                    else:
                        return {
                            "status": "error",
                            "status_code": 404,
                            "message": f"Supersession candidate edge '{target_id}' not found"
                        }

            return {
                "status": "success",
                "message": f"Action '{action}' executed successfully on {target_id}",
                "actor": actor,
                "reason": reason
            }

        # 2. Guard Rule Actions (Section 5.4: approve | disable)
        elif path == "/api/guard-rules/approve":
            rule_id = body.get("rule_id")
            if not rule_id:
                return {"status": "error", "message": "Missing 'rule_id'"}
            success = self.db.update_guard_rule_status(rule_id, "active", approved_by="human_reviewer")
            return {"status": "success", "rule_id": rule_id, "active": success}

        elif path == "/api/guard-rules/disable":
            rule_id = body.get("rule_id")
            if not rule_id:
                return {"status": "error", "message": "Missing 'rule_id'"}
            success = self.db.update_guard_rule_status(rule_id, "disabled", approved_by="human_reviewer")
            return {"status": "success", "rule_id": rule_id, "disabled": success}


        # 2. Live Drift Check (Section 8.3)
        elif path == "/api/drift-check":
            repo = body.get("repo", "acme-eng/thermal-control-system")
            diff_text = body.get("diff_text", "")
            files = body.get("files", ["src/thermal/control.py"])
            author = body.get("author", "developer")
            report = self.drift_detector.analyze_diff_for_drift(
                repo=repo,
                commit_or_pr_id="live_ci_check",
                author=author,
                changed_files=files,
                diff_text=diff_text
            )
            findings = report.get("findings", [])
            return {
                "status": "success",
                "drift_detected": len(findings) > 0,
                "results": findings,
                "check_status": report.get("status", "complete"),
                "errors": report.get("errors", []),
                "report": report
            }

        # 3. Reseed Pilot Database
        elif path == "/api/reseed":
            expected_db = os.path.basename(self.db.db_path)
            if body.get("confirm") != expected_db:
                return {
                    "status": "error",
                    "status_code": 400,
                    "message": f"Confirmation required: body must contain 'confirm': '{expected_db}'"
                }
            stats = populate_seed_data(self.db)
            return {"status": "success", "message": "Pilot database reseeded successfully", "stats": stats}

        # 4. Ingest Custom Live GitHub Repository
        elif path == "/api/ingest-repo":
            repo_input = body.get("repo", "")
            token = body.get("token")
            clear_first = body.get("clear_existing", False)
            max_commits = int(body.get("max_commits", 25))
            max_issues = int(body.get("max_issues", 15))

            try:
                from backend.ingestion.live_github import LiveGitHubIngestor
                ingestor = LiveGitHubIngestor(self.db, token=token)
                stats = ingestor.ingest_custom_repository(
                    raw_repo_input=repo_input,
                    clear_existing=clear_first,
                    max_commits=max_commits,
                    max_issues=max_issues
                )
                return {"status": "success", "message": f"Successfully ingested {stats['repo']}!", "data": stats}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        # 5. Clear Database (Empty Canvas)
        elif path == "/api/clear-db":
            expected_db = os.path.basename(self.db.db_path)
            if body.get("confirm") != expected_db:
                return {
                    "status": "error",
                    "status_code": 400,
                    "message": f"Confirmation required: body must contain 'confirm': '{expected_db}'"
                }
            from backend.ingestion.live_github import LiveGitHubIngestor
            LiveGitHubIngestor(self.db).clear_database()
            return {"status": "success", "message": "Dashboard database cleared successfully. Ready for custom repository."}

        return {"status": "error", "message": f"Unknown POST endpoint {path}"}

    def handle_webhook(
        self,
        path: str,
        headers: Dict[str, str],
        raw_body: bytes,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 7.1/7.2 — GitHub Webhook Receiver.
        Verifies HMAC-SHA256 signature, handles pull_request events only,
        runs drift analysis and optionally posts a PR comment.
        Returns (response_dict, http_status_code).
        """
        if path != "/api/webhook/github":
            return ({"status": "error", "message": "Not found"}, 404)

        secret = os.environ.get("CIF_WEBHOOK_SECRET", "")
        if not secret:
            return ({"status": "error", "message": "Webhook secret not configured"}, 401)

        sig_header = headers.get("X-Hub-Signature-256", "") or headers.get("x-hub-signature-256", "")
        if not sig_header:
            return ({"status": "error", "message": "Missing X-Hub-Signature-256"}, 401)

        expected = "sha256=" + hmac.new(
            secret.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, sig_header):
            return ({"status": "error", "message": "Signature mismatch"}, 401)

        event_type = headers.get("X-GitHub-Event", "") or headers.get("x-github-event", "")
        if event_type != "pull_request":
            return ({"status": "ok", "message": f"Ignored event type: {event_type}"}, 200)

        action = body.get("action", "")
        if action not in ("opened", "synchronize", "reopened"):
            return ({"status": "ok", "message": f"Ignored PR action: {action}"}, 200)

        pr = body.get("pull_request", {})
        repo_full = body.get("repository", {}).get("full_name", "unknown")
        pr_number = pr.get("number", 0)
        diff_url = pr.get("diff_url", "")
        comments_url = pr.get("comments_url", "")
        head_sha = pr.get("head", {}).get("sha", "")

        # Fetch diff via GitHub API if GITHUB_TOKEN is set
        token = os.environ.get("GITHUB_TOKEN", "")
        diff_text = ""
        fetch_error = None
        if token and diff_url:
            try:
                req = urllib.request.Request(
                    diff_url,
                    headers={
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github.v3.diff",
                        "User-Agent": "CIF-Bot/1.0"
                    }
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    diff_text = resp.read().decode("utf-8", errors="replace")
            except urllib.error.URLError as e:
                fetch_error = str(e)

        # Extract changed files from diff headers
        changed_files = []
        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                changed_files.append(line[6:].strip())
        if not changed_files:
            changed_files = ["unknown"]

        # Run drift analysis
        report = self.drift_detector.analyze_diff_for_drift(
            repo=repo_full,
            commit_or_pr_id=f"pr_{pr_number}",
            author=pr.get("user", {}).get("login", "unknown"),
            changed_files=changed_files,
            diff_text=diff_text
        )
        findings = report.get("findings", [])

        # Post PR comment if violations and token available
        comment_posted = False
        if findings and token and comments_url:
            lines = ["**⚠️ Context Intelligence Framework — Decision Guard Violations**", ""]
            for f in findings[:5]:
                lines.append(f"- **{f.get('violation_type','drift')}**: {f.get('message', '')[:200]}")
                if f.get("decision_url"):
                    lines.append(f"  📋 [Evidence]({f['decision_url']})")
            lines.append("")
            lines.append("*Posted by CIF Decision Guard. See [full evidence].*")
            comment_body = "\n".join(lines)
            try:
                req = urllib.request.Request(
                    comments_url,
                    data=json.dumps({"body": comment_body}).encode("utf-8"),
                    headers={
                        "Authorization": f"token {token}",
                        "Content-Type": "application/json",
                        "User-Agent": "CIF-Bot/1.0"
                    },
                    method="POST"
                )
                urllib.request.urlopen(req, timeout=15)
                comment_posted = True
            except urllib.error.URLError:
                pass
        elif findings and not token:
            print(f"[CIF] {len(findings)} drift finding(s) for PR#{pr_number} stored. "
                  "Set GITHUB_TOKEN to enable PR comment posting.")

        return ({
            "status": "ok",
            "repo": repo_full,
            "pr": pr_number,
            "findings_count": len(findings),
            "check_status": report.get("status", "complete"),
            "errors": report.get("errors", []),
            "comment_posted": comment_posted,
            "diff_fetch_error": fetch_error
        }, 200)
