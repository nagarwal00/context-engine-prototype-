"""
Context Intelligence Framework - REST API Handler
Provides clean JSON REST endpoints for all 6 UI surfaces, review actions, and evaluation.
"""
from typing import Dict, Any, List, Optional, Tuple, Set
import hashlib
import hmac
import json
import os
import time
import urllib.request
import urllib.error
import datetime
from datetime import datetime as dt_class, timezone
import urllib.parse
from backend.models import Event
from backend.db import Database
from backend.engine.graph import TemporalGraph
from backend.engine.explanation import ExplanationGenerator
from backend.engine.reconciliation import ReconciliationEngine
from backend.engine.drift_detector import DriftDetector
import uuid
from backend.evaluation.benchmark import BenchmarkRunner
from backend.seed_data import populate_seed_data
from backend.security import (
    ROLE_PUBLIC,
    ROLE_USER,
    ROLE_REPO_READ,
    ROLE_REPO_REVIEW,
    ROLE_ADMIN,
    ROLE_VIEWER,
    ROLE_REVIEWER,
    ROLE_EXEMPT,
    authorize,
    is_dev_mode,
    get_authenticated_role,
    authenticate_caller
)

# Route-to-role authorization mapping (Step 7.4 / R2)
# Default deny: any route not explicitly listed here is rejected.
ROUTE_ROLES: Dict[Tuple[str, str], str] = {
    # Public routes
    ("GET", "/api/auth-status"): ROLE_PUBLIC,
    ("GET", "/api/auth-config"): ROLE_PUBLIC,
    ("GET", "/api/repos"): ROLE_PUBLIC,

    # User routes
    ("GET", "/api/me"): ROLE_USER,
    ("GET", "/api/github/repos"): ROLE_USER,
    ("GET", "/api/repos/status"): ROLE_USER,
    ("POST", "/api/repos"): ROLE_USER,

    # Repo Read & Extension routes
    ("GET", "/api/pr-analysis"): ROLE_PUBLIC,
    ("GET", "/api/file-context"): ROLE_PUBLIC,
    ("GET", "/api/timeline"): ROLE_REPO_READ,
    ("GET", "/api/graph"): ROLE_REPO_READ,
    ("GET", "/api/artifacts"): ROLE_REPO_READ,
    ("GET", "/api/explain"): ROLE_REPO_READ,
    ("GET", "/api/decisions"): ROLE_REPO_READ,
    ("GET", "/api/evidence"): ROLE_REPO_READ,
    ("GET", "/api/review-queue"): ROLE_REPO_READ,
    ("GET", "/api/benchmark"): ROLE_REPO_READ,
    ("GET", "/api/stats"): ROLE_REPO_READ,
    ("GET", "/api/guard-rules"): ROLE_REPO_READ,
    ("GET", "/api/decision-history"): ROLE_REPO_READ,
    ("GET", "/api/as-of"): ROLE_REPO_READ,
    ("GET", "/api/findings/feedback"): ROLE_REPO_READ,
    ("GET", "/api/bus-factor"): ROLE_REPO_READ,
    ("GET", "/api/onboarding"): ROLE_REPO_READ,
    ("POST", "/api/onboarding"): ROLE_REPO_READ,

    # Repo Review routes
    ("POST", "/api/review-action"): ROLE_REPO_REVIEW,
    ("POST", "/api/guard-rules/approve"): ROLE_REPO_REVIEW,
    ("POST", "/api/guard-rules/disable"): ROLE_REPO_REVIEW,
    ("POST", "/api/drift-check"): ROLE_REPO_REVIEW,
    ("POST", "/api/findings/feedback"): ROLE_REPO_REVIEW,
    ("POST", "/api/repos/reviewers"): ROLE_REPO_REVIEW,

    # Admin routes
    ("POST", "/api/reseed"): ROLE_ADMIN,
    ("POST", "/api/clear-db"): ROLE_ADMIN,
    ("POST", "/api/ingest-repo"): ROLE_ADMIN,
    ("POST", "/api/purge-repo"): ROLE_ADMIN,

    # Webhook (exempt from Bearer token - uses GitHub HMAC signature)
    ("POST", "/api/webhook/github"): ROLE_PUBLIC,
}

class APIHandler:
    def __init__(self, db: Database):
        self.db = db
        self.graph = TemporalGraph(db)
        self.explanation_gen = ExplanationGenerator(db)
        self.reconciliation = ReconciliationEngine(db)
        self.drift_detector = DriftDetector(db)
        self.benchmark_runner = BenchmarkRunner(db)
        from backend.engine.rejected_idea_guard import RejectedIdeaGuard
        self.rejected_idea_guard = RejectedIdeaGuard(db)
        self._pr_analysis_cache: Dict[Tuple[str, int, str], Dict[str, Any]] = {}

    def _get_accessible_repo_names(self, headers: Optional[Dict[str, str]] = None) -> Optional[Set[str]]:
        from backend.security import authenticate_caller
        from backend.auth.repo_access import list_accessible_repos
        user, is_admin = authenticate_caller(self.db, headers or {})
        if is_admin:
            return None
        accessible = list_accessible_repos(self.db, user)
        return {r["repo_full_name"] for r in accessible}

    def check_authorization(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        client_ip: str = "127.0.0.1",
        query_params: Optional[Dict[str, List[str]]] = None,
        body_json: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, int, str]:
        """Validates route existence and credentials against required role (default deny)."""
        required_role = ROUTE_ROLES.get((method.upper(), path))
        if required_role is None:
            if method.upper() == "GET" and path.startswith("/api/jobs/"):
                required_role = ROLE_USER
            elif method.upper() == "POST" and path.startswith("/api/jobs/") and path.endswith("/cancel"):
                required_role = ROLE_USER
            elif method.upper() == "DELETE" and path.startswith("/api/repos/"):
                required_role = ROLE_USER
            else:
                return False, 404, f"Endpoint not found: {method.upper()} {path}"
        return authorize(
            headers,
            required_role,
            client_ip,
            db=self.db,
            path=path,
            query_params=query_params,
            body_json=body_json
        )

    def handle_get(
        self,
        path: str,
        query_params: Dict[str, List[str]],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
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
            trail = self.db.query_full_evidence_trail(decision_id)
            if not trail.get("decision"):
                return {"status": "not_found", "message": f"Decision '{decision_id}' not found", "data": None}
            from backend.engine.explanation import build_decision_evidence_block
            evidence_block = build_decision_evidence_block(self.db, trail["decision"])
            trail.update({
                "lifecycle_state": evidence_block["lifecycle_state"],
                "needs_review": evidence_block["needs_review"],
                "evidence_assessment": evidence_block["evidence_assessment"],
                "direct_support": evidence_block["direct_support"],
                "indirect_support": evidence_block["indirect_support"],
                "missing_corroboration": evidence_block["missing_corroboration"],
                "conflicting_evidence": evidence_block["conflicting_evidence"],
            })
            return {"status": "success", "data": trail}

        # 7. Review Queue
        elif path == "/api/review-queue":
            queue = []
            seen_decision_ids = set()
            allowed_repos = self._get_accessible_repo_names(headers)
            repo_filter = query_params.get("repo", [None])[0]
            if repo_filter:
                if allowed_repos is not None and repo_filter not in allowed_repos:
                    return {"status": "error", "message": f"Access denied to repository {repo_filter}"}
                target_repos = {repo_filter}
            else:
                target_repos = allowed_repos

            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Low confidence decisions (< 0.90) or pending_review
                # OR evidence quality labels 'weak', 'insufficient', 'contradicted' (Step 3.2 review routing)
                if target_repos is not None:
                    placeholders = ",".join("?" for _ in target_repos)
                    cursor.execute(f"""
                    SELECT * FROM decisions
                    WHERE (confidence < 0.90 OR review_status = 'pending_review' OR evidence_assessment IN ('weak', 'insufficient', 'contradicted'))
                      AND review_status NOT IN ('human_rejected', 'human_confirmed')
                      AND (repo_full_name IN ({placeholders}) OR (repo_full_name IS NULL AND repo IN ({placeholders})))
                    ORDER BY confidence ASC
                    """, list(target_repos) + list(target_repos))
                else:
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
                if target_repos is not None:
                    placeholders = ",".join("?" for _ in target_repos)
                    cursor.execute(f"SELECT * FROM edges WHERE edge_type = 'conflicts_with' AND (repo_full_name IN ({placeholders}) OR (repo_full_name IS NULL AND from_id IN (SELECT decision_id FROM decisions WHERE repo_full_name IN ({placeholders}))))", list(target_repos) + list(target_repos))
                else:
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
                if target_repos is not None:
                    placeholders = ",".join("?" for _ in target_repos)
                    cursor.execute(f"SELECT * FROM edges WHERE edge_type = 'drifts_from' AND repo_full_name IN ({placeholders})", list(target_repos))
                else:
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
                if target_repos is not None:
                    placeholders = ",".join("?" for _ in target_repos)
                    cursor.execute(f"SELECT * FROM edges WHERE edge_type = 'supersession_candidate' AND repo_full_name IN ({placeholders})", list(target_repos))
                else:
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

                # Ambiguous findings ('possible' tier from rejected-idea guard, Step 3.6)
                pending_ambiguous = self.db.get_pending_ambiguous_findings()
                if target_repos is not None:
                    pending_ambiguous = [af for af in pending_ambiguous if af.get("repo") in target_repos or af.get("repo_full_name") in target_repos]
                for af in pending_ambiguous:
                    queue.append({
                        "item_type": "possible_rejected_idea",
                        "finding_id": af["finding_id"],
                        "decision_id": af["decision_id"],
                        "pr_id": af["pr_id"],
                        "title": f"Possible Rejected Idea: '{af['decision_title']}' ({af['pr_id']})",
                        "queue_reason": f"Ambiguous finding ('possible' tier): {af['rejection_reason']}",
                        "confidence": 0.70,
                        "review_status": "pending_review",
                        "rationale": af["message"],
                        "pr_comment": af["pr_comment"],
                        "made_at": af["created_at"]
                    })

                # Stale decisions (Step 5.2 Decision Half-Life)
                from backend.engine.staleness import StalenessEngine
                stale_items = StalenessEngine(self.db).get_stale_review_items()
                if target_repos is not None:
                    stale_items = [si for si in stale_items if si.get("repo") in target_repos or si.get("repo_full_name") in target_repos]
                for si in stale_items:
                    queue.append(si)

            return {"status": "success", "data": queue}

        # 8. Evaluation & Benchmark
        elif path == "/api/benchmark":
            data = self.benchmark_runner.run_full_evaluation()
            manifest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "latest_manifest.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        data["whybench_manifest"] = json.load(f)
                except Exception:
                    pass
            return {"status": "success", "data": data}

        # 9. Summary stats
        elif path == "/api/stats":
            allowed_repos = self._get_accessible_repo_names(headers)
            repo_filter = query_params.get("repo", [None])[0]
            if repo_filter:
                if allowed_repos is not None and repo_filter not in allowed_repos:
                    return {"status": "error", "message": f"Access denied to repository {repo_filter}"}
                target_repos = {repo_filter}
            else:
                target_repos = allowed_repos

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                if target_repos is not None:
                    placeholders = ",".join("?" for _ in target_repos)
                    repo_list = list(target_repos)
                    cursor.execute(f"SELECT COUNT(*) as c FROM decisions WHERE repo_full_name IN ({placeholders}) OR (repo_full_name IS NULL AND repo IN ({placeholders}))", repo_list + repo_list)
                    dec_cnt = cursor.fetchone()["c"]
                    cursor.execute(f"SELECT COUNT(*) as c FROM events WHERE repo_full_name IN ({placeholders}) OR (repo_full_name IS NULL AND repo IN ({placeholders}))", repo_list + repo_list)
                    evt_cnt = cursor.fetchone()["c"]
                    cursor.execute(f"SELECT COUNT(*) as c FROM entities WHERE repo_full_name IN ({placeholders}) OR (repo_full_name IS NULL AND repo IN ({placeholders}))", repo_list + repo_list)
                    ent_cnt = cursor.fetchone()["c"]
                    cursor.execute(f"SELECT COUNT(*) as c FROM edges WHERE repo_full_name IN ({placeholders})", repo_list)
                    edg_cnt = cursor.fetchone()["c"]
                    cursor.execute(f"SELECT COUNT(*) as c FROM edges WHERE edge_type = 'drifts_from' AND repo_full_name IN ({placeholders})", repo_list)
                    drf_cnt = cursor.fetchone()["c"]
                    cursor.execute(f"SELECT COUNT(*) as c FROM edges WHERE edge_type = 'conflicts_with' AND repo_full_name IN ({placeholders})", repo_list)
                    cnf_cnt = cursor.fetchone()["c"]
                else:
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
                    "conflicts": cnf_cnt,
                    "finding_feedback": self.db.get_finding_feedback_counts()
                }
            }

        # 10. Distinct Repositories (Step 7.4 scoped)
        elif path == "/api/repos":
            from backend.auth.repo_access import list_accessible_repos
            from backend.security import authenticate_caller
            user, is_admin = authenticate_caller(self.db, headers or {})
            accessible = list_accessible_repos(self.db, user)
            repo_names = [r["repo_full_name"] for r in accessible]
            return {"status": "success", "data": repo_names}

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

        # 12b. Auth Config (Step 7.1)
        elif path == "/api/auth-config":
            from backend.config import get_config
            return get_config().get_public_auth_config()

        # 12c. Current User Profile (Step 7.3)
        elif path == "/api/me":
            from backend.auth.sessions import extract_session_token, get_session, generate_csrf_token
            token, _ = extract_session_token(headers or {})
            session = get_session(self.db, token) if token else None
            if not session:
                return {
                    "status_code": 401,
                    "status": "error",
                    "message": "Unauthorized: No valid session"
                }
            csrf = generate_csrf_token(session["session_hash"])
            return {
                "status_code": 200,
                "status": "success",
                "login": session["login"],
                "avatar_url": session["avatar_url"],
                "csrf": csrf
            }

        # 12d. GitHub App Installable Repos (Step 7.5)
        elif path == "/api/github/repos":
            from backend.security import authenticate_caller
            from backend.auth.repo_add import list_user_installable_repos
            user, is_admin = authenticate_caller(self.db, headers or {})
            if not user and not is_admin:
                return {"status_code": 401, "status": "error", "message": "Sign-in required"}
            user_id = user["user_id"] if user else 0
            code, res = list_user_installable_repos(self.db, user_id)
            res["status_code"] = code
            return res

        # 12e. Repo Sync and Active Job Status (Step 7.5)
        elif path == "/api/repos/status":
            from backend.auth.repo_add import get_repo_sync_status
            repo = query_params.get("repo", [None])[0]
            if not repo:
                return {"status_code": 400, "status": "error", "message": "Query parameter 'repo' required"}
            res = get_repo_sync_status(self.db, repo)
            return res

        # 12f. Ingestion Job Progress (Step 7.6)
        elif path.startswith("/api/jobs/"):
            job_id = path.replace("/api/jobs/", "").strip("/")
            from backend.ingestion.job_runner import IngestJobRunner
            runner = IngestJobRunner.get_instance(self.db)
            job = runner.get_job_status(job_id)
            if not job:
                return {"status_code": 404, "status": "error", "message": f"Job '{job_id}' not found"}
            return {
                "status_code": 200,
                "status": "success",
                "job_id": job["job_id"],
                "job_status": job["status"],
                "phase": job["phase"],
                "progress": job["progress"],
                "error_code": job["error_code"],
                "repo_full_name": job["repo_full_name"],
                "created_at": job["created_at"],
                "started_at": job["started_at"],
                "finished_at": job["finished_at"]
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

        elif path == "/api/findings/feedback":
            finding_id = query_params.get("finding_id", [None])[0]
            pr_id = query_params.get("pr_id", [None])[0]
            items = self.db.get_finding_feedback(finding_id=finding_id, pr_id=pr_id)
            counts = self.db.get_finding_feedback_counts()
            return {
                "status": "success",
                "data": {
                    "counts": counts,
                    "items": items
                }
            }

        elif path == "/api/bus-factor":
            repo = query_params.get("repo", [None])[0]
            if not repo:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT DISTINCT repo FROM decisions LIMIT 1")
                    r = cursor.fetchone()
                    repo = r["repo"] if r else "acme-ecommerce/payment-core"
            from backend.engine.bus_factor import BusFactorEngine
            engine = BusFactorEngine(self.db)
            return engine.analyze_repository(repo)

        elif path == "/api/onboarding":
            repo = query_params.get("repo", [None])[0]
            role = query_params.get("role", [None])[0]
            module = query_params.get("module", [None])[0]
            files_raw = query_params.get("files", [None])[0]
            files = [f.strip() for f in files_raw.split(",") if f.strip()] if files_raw else []
            task = query_params.get("task", [None])[0]

            from backend.engine.onboarding import OnboardingEngine
            engine = OnboardingEngine(self.db)
            return engine.generate_learning_path(
                repo=repo,
                role=role,
                module=module,
                files=files,
                task=task
            )

        # 14. Extension API: Pull Request Analysis (Step 8.0)
        elif path == "/api/pr-analysis":
            repo = query_params.get("repo", [None])[0]
            number_val = query_params.get("number", [None])[0] or query_params.get("pr", [None])[0]
            head_sha_param = query_params.get("head_sha", [None])[0]

            if not repo or not number_val:
                return {
                    "schema_version": "1.0",
                    "status": "error",
                    "status_code": 400,
                    "message": "Missing required query parameters: 'repo' and 'number'"
                }

            try:
                pr_num = int(number_val)
            except ValueError:
                return {
                    "schema_version": "1.0",
                    "status": "error",
                    "status_code": 400,
                    "message": f"Invalid PR number: {number_val}"
                }

            # Verify repository exists in repos table
            with self.db.get_connection() as conn:
                r_row = conn.execute("SELECT visibility FROM repos WHERE repo_full_name = ?", (repo,)).fetchone()

            if not r_row:
                # Normal JSON state per Step 8.0
                return {
                    "schema_version": "1.0",
                    "status": "not_added",
                    "repo": repo,
                    "number": pr_num,
                    "message": f"Repository '{repo}' has not been added to CIF yet."
                }

            # Enforce Rule R3 repo isolation for non-demo repositories
            visibility = r_row["visibility"]
            from backend.security import authenticate_caller
            user, is_admin = authenticate_caller(self.db, headers or {})

            if visibility != "demo" and not is_admin:
                if not user:
                    return {
                        "schema_version": "1.0",
                        "status": "needs_relogin",
                        "status_code": 401,
                        "message": "Authentication required to access repository analysis"
                    }
                from backend.auth.repo_access import authorize_repo
                auth_ok, auth_code, auth_msg = authorize_repo(self.db, user, repo, "repo_read")
                if not auth_ok:
                    if auth_code == 401 or "needs_relogin" in str(auth_msg):
                        return {
                            "schema_version": "1.0",
                            "status": "needs_relogin",
                            "status_code": 401,
                            "message": "GitHub authorization expired. Please sign in again."
                        }
                    return {
                        "schema_version": "1.0",
                        "status": "error",
                        "status_code": auth_code,
                        "message": auth_msg
                    }

            # Resolve PR metadata from events or parameters
            head_sha = head_sha_param
            pr_title = ""
            pr_body = ""
            pr_author = "contributor"
            changed_files: List[str] = []
            diff_text = ""

            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                SELECT * FROM events
                WHERE (repo = ? OR repo_full_name = ?)
                  AND (source_id = ? OR source_id = ? OR source_id LIKE ?)
                ORDER BY ts DESC LIMIT 1
                """, (repo, repo, str(pr_num), f"{repo}#{pr_num}", f"%#{pr_num}"))
                ev_row = cur.fetchone()
                if ev_row:
                    payload = {}
                    try:
                        payload = json.loads(ev_row["raw_metadata"] or "{}")
                    except Exception:
                        pass
                    pr_title = ev_row["title"] or payload.get("title", "")
                    pr_body = ev_row["body"] or payload.get("body", "")
                    pr_author = ev_row["author"] or "contributor"
                    if not head_sha:
                        head_sha = payload.get("head_sha") or payload.get("head", {}).get("sha") or payload.get("commit_hash")

            head_sha = head_sha or f"pr_{pr_num}_head"

            # Check head SHA cache (Step 8.0 requirement: cache by head SHA)
            cache_key = (repo, pr_num, head_sha)
            if cache_key in self._pr_analysis_cache:
                cached = dict(self._pr_analysis_cache[cache_key])
                cached["cached"] = True
                return cached

            # Gather affected entities or default files
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                SELECT canonical_path FROM entities
                WHERE repo = ? LIMIT 50
                """, (repo,))
                all_ent_paths = [r["canonical_path"] for r in cur.fetchall()]

            if not changed_files and all_ent_paths:
                changed_files = [p for p in all_ent_paths if "::" not in p][:10]

            # Run Drift Detection
            drift_res = self.drift_detector.analyze_diff_for_drift(
                repo=repo,
                commit_or_pr_id=str(pr_num),
                author=pr_author,
                changed_files=changed_files,
                diff_text=diff_text
            )

            # Run Rejected-Idea Guard
            idea_res = self.rejected_idea_guard.evaluate_proposal(
                repo=repo,
                pr_id=str(pr_num),
                title=pr_title or f"Pull Request #{pr_num}",
                body=pr_body or "",
                diff_text=diff_text,
                changed_files=changed_files,
                author=pr_author
            )

            findings: List[Dict[str, Any]] = []

            # 1. Rejected idea warnings (advisory)
            for rf in idea_res.get("potential_reintroductions", []):
                findings.append({
                    "finding_id": rf.get("finding_id") or str(uuid.uuid4()),
                    "type": "rejected_idea",
                    "decision_id": rf.get("decision_id"),
                    "title": rf.get("decision_title"),
                    "original_reason": rf.get("rejection_reason"),
                    "source_url": rf.get("source_url") or "",
                    "evidence_passages": rf.get("evidence_passages", []),
                    "changed_circumstances": rf.get("changed_circumstances", []),
                    "signal_strength": "advisory",
                    "state": rf.get("decision_state", "rejected")
                })

            # 2. Drift findings (potential_violation)
            for df in drift_res.get("findings", []):
                findings.append({
                    "finding_id": df.get("finding_id") or str(uuid.uuid4()),
                    "type": "potential_violation",
                    "file": df.get("file"),
                    "line": df.get("line_number"),
                    "offending_line": df.get("offending_code") or df.get("raw") or "",
                    "rule_id": df.get("rule_id"),
                    "decision_id": df.get("decision_id"),
                    "title": df.get("rule_name") or "Decision constraint violation",
                    "original_reason": df.get("reason") or "",
                    "source_url": df.get("source_url") or "",
                    "signal_strength": "heuristic",
                    "state": "accepted"
                })

            # 3. Related decisions
            related_decisions: List[Dict[str, Any]] = []
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                SELECT DISTINCT d.decision_id, d.title, d.state, d.made_at, d.rationale
                FROM decisions d
                WHERE d.repo = ?
                ORDER BY d.made_at DESC LIMIT 10
                """, (repo,))
                for row in cur.fetchall():
                    related_decisions.append({
                        "decision_id": row["decision_id"],
                        "title": row["title"],
                        "state": row["state"],
                        "made_at": row["made_at"],
                        "rationale": row["rationale"] or ""
                    })

            result = {
                "schema_version": "1.0",
                "status": "ready",
                "repo": repo,
                "number": pr_num,
                "head_sha": head_sha,
                "findings": findings,
                "related_decisions": related_decisions,
                "detector_status": "complete" if drift_res.get("status") != "incomplete" else "incomplete"
            }

            self._pr_analysis_cache[cache_key] = result
            return result

        # 15. Extension API: File & Entity Context (Step 8.0)
        elif path == "/api/file-context":
            repo = query_params.get("repo", [None])[0]
            file_path = query_params.get("path", [None])[0] or query_params.get("file", [None])[0]
            ref_val = query_params.get("ref", [None])[0] or "HEAD"
            line_str = query_params.get("line", [None])[0]

            if not repo or not file_path:
                return {
                    "schema_version": "1.0",
                    "status": "error",
                    "status_code": 400,
                    "message": "Missing required query parameters: 'repo' and 'path'"
                }

            with self.db.get_connection() as conn:
                r_row = conn.execute("SELECT visibility FROM repos WHERE repo_full_name = ?", (repo,)).fetchone()

            if not r_row:
                return {
                    "schema_version": "1.0",
                    "status": "not_added",
                    "repo": repo,
                    "file": file_path,
                    "message": f"Repository '{repo}' has not been added to CIF yet."
                }

            # Enforce Rule R3 repo isolation
            visibility = r_row["visibility"]
            from backend.security import authenticate_caller
            user, is_admin = authenticate_caller(self.db, headers or {})

            if visibility != "demo" and not is_admin:
                if not user:
                    return {
                        "schema_version": "1.0",
                        "status": "needs_relogin",
                        "status_code": 401,
                        "message": "Authentication required to access repository file context"
                    }
                from backend.auth.repo_access import authorize_repo
                auth_ok, auth_code, auth_msg = authorize_repo(self.db, user, repo, "repo_read")
                if not auth_ok:
                    if auth_code == 401 or "needs_relogin" in str(auth_msg):
                        return {
                            "schema_version": "1.0",
                            "status": "needs_relogin",
                            "status_code": 401,
                            "message": "GitHub authorization expired. Please sign in again."
                        }
                    return {
                        "schema_version": "1.0",
                        "status": "error",
                        "status_code": auth_code,
                        "message": auth_msg
                    }

            norm_path = file_path.replace("\\", "/").strip()
            line_num = None
            if line_str:
                try:
                    line_num = int(line_str)
                except ValueError:
                    pass

            decisions_list: List[Dict[str, Any]] = []
            rejected_alternatives: List[Dict[str, Any]] = []

            with self.db.get_connection() as conn:
                cur = conn.cursor()

                # Check for AST function entity if line number is specified
                affected_func = None
                if line_num is not None:
                    cur.execute("""
                    SELECT entity_id, canonical_path FROM entities
                    WHERE repo = ? AND (canonical_path = ? OR canonical_path LIKE ?)
                    """, (repo, norm_path, f"{norm_path}::%"))
                    for erow in cur.fetchall():
                        cp = erow["canonical_path"]
                        if "::" in cp:
                            affected_func = cp.split("::")[-1]
                            break

                # Query decisions affecting this file
                base_name = os.path.basename(norm_path)
                cur.execute("""
                SELECT DISTINCT d.decision_id, d.title, d.state, d.rationale, d.made_at, d.made_by
                FROM decisions d
                LEFT JOIN decision_artifacts da ON d.decision_id = da.decision_id
                LEFT JOIN entities e ON da.entity_id = e.entity_id
                WHERE (d.repo = ? OR da.repo_full_name = ?)
                  AND (e.canonical_path = ? OR e.canonical_path LIKE ? OR e.canonical_path LIKE ?)
                ORDER BY d.made_at DESC
                """, (repo, repo, norm_path, f"{norm_path}::%", f"%/{base_name}"))
                rows = cur.fetchall()

                # Fallback to repo decisions if file-specific artifact link not found
                if not rows:
                    cur.execute("""
                    SELECT d.decision_id, d.title, d.state, d.rationale, d.made_at, d.made_by
                    FROM decisions d
                    WHERE d.repo = ?
                    ORDER BY d.made_at DESC LIMIT 5
                    """, (repo,))
                    rows = cur.fetchall()

                seen_decs = set()
                for r in rows:
                    did = r["decision_id"]
                    if did in seen_decs:
                        continue
                    seen_decs.add(did)

                    # Get source URL from evidence
                    cur.execute("""
                    SELECT ev.source_url
                    FROM decision_evidence de
                    JOIN events ev ON de.event_id = ev.event_id
                    WHERE de.decision_id = ? AND ev.source_url IS NOT NULL AND ev.source_url != ''
                    LIMIT 1
                    """, (did,))
                    ev_row = cur.fetchone()
                    source_url = ev_row["source_url"] if ev_row else ""

                    state = r["state"]
                    freshness = "fresh"
                    if state == "stale":
                        freshness = "stale"
                    elif state == "proposed":
                        freshness = "under_review"

                    dec_item = {
                        "decision_id": did,
                        "title": r["title"],
                        "state": state,
                        "freshness": freshness,
                        "made_at": r["made_at"] or "",
                        "rationale": r["rationale"] or "",
                        "source_url": source_url
                    }
                    if affected_func:
                        dec_item["affected_function"] = affected_func

                    if state in ("rejected", "reopened", "superseded"):
                        rejected_alternatives.append({
                            "decision_id": did,
                            "title": r["title"],
                            "state": state,
                            "rejection_reason": r["rationale"] or f"Decision {state}",
                            "source_url": source_url
                        })
                    else:
                        decisions_list.append(dec_item)

            return {
                "schema_version": "1.0",
                "status": "ready",
                "repo": repo,
                "file": norm_path,
                "ref": ref_val,
                "decisions": decisions_list,
                "active_decisions": decisions_list,
                "rejected_alternatives": rejected_alternatives
            }

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
                if action in ("reopen", "mark_tested", "revalidate"):
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

            now_iso = dt_class.now(timezone.utc).isoformat()

            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                if item_type in ("decision", "stale_decision"):
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

                        elif action == "revalidate":
                            from backend.engine.staleness import StalenessEngine
                            StalenessEngine(self.db).revalidate_decision(target_id, actor=actor, reason=reason, at=now_iso)

                        elif action == "mark_stale":
                            cursor.execute("UPDATE decisions SET freshness = 'stale' WHERE decision_id = ?", (target_id,))
                            hist_id = f"hist_stale_{target_id}_{time.time_ns()}_{uuid.uuid4().hex[:6]}"
                            cursor.execute("PRAGMA table_info(state_history)")
                            sh_cols = {r["name"] for r in cursor.fetchall()}
                            notes_entry = f"Marked stale: {reason}"
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

                        elif action == "mark_under_review":
                            cursor.execute("UPDATE decisions SET freshness = 'under_review' WHERE decision_id = ?", (target_id,))

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

                elif item_type == "possible_rejected_idea":
                    f_id = target_id
                    cursor.execute("SELECT * FROM ambiguous_findings WHERE finding_id = ?", (f_id,))
                    af_row = cursor.fetchone()
                    pr_id = af_row["pr_id"] if af_row else body.get("pr_id", "")
                    dec_id = af_row["decision_id"] if af_row else body.get("decision_id", "")
                    if action in ("confirm", "accepted"):
                        res = self.rejected_idea_guard.confirm_finding(f_id, pr_id=pr_id, decision_id=dec_id, actor=actor, reason=reason)
                        return {"status": "success", "message": f"Confirmed finding '{f_id}'", "data": res, "actor": actor, "reason": reason}
                    elif action in ("reject", "dismiss", "human_rejected"):
                        res = self.rejected_idea_guard.dismiss_finding(f_id, pr_id=pr_id, decision_id=dec_id, actor=actor, reason=reason)
                        return {"status": "success", "message": f"Dismissed finding '{f_id}'", "data": res, "actor": actor, "reason": reason}
                    elif action == "reopen":
                        res = self.rejected_idea_guard.reopen_decision(dec_id, pr_id=pr_id, actor=actor, reason=reason)
                        return {"status": "success", "message": f"Reopened decision '{dec_id}'", "data": res, "actor": actor, "reason": reason}

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


        # 2. Live Drift Check (Section 8.3 & Step 3.5 Rejected-Idea Guard)
        elif path == "/api/drift-check":
            repo = body.get("repo", "acme-eng/thermal-control-system")
            diff_text = body.get("diff_text", "")
            files = body.get("files", ["src/thermal/control.py"])
            author = body.get("author", "developer")
            title = body.get("title", "")
            pr_body = body.get("body", "")

            report = self.drift_detector.analyze_diff_for_drift(
                repo=repo,
                commit_or_pr_id="live_ci_check",
                author=author,
                changed_files=files,
                diff_text=diff_text
            )
            findings = report.get("findings", [])

            rej_eval = self.rejected_idea_guard.evaluate_proposal(
                repo=repo,
                pr_id="live_ci_check",
                title=title,
                body=pr_body,
                diff_text=diff_text,
                changed_files=files,
                author=author
            )
            rejected_ideas = rej_eval.get("findings", [])

            return {
                "status": "success",
                "drift_detected": (len(findings) > 0 or len(rejected_ideas) > 0),
                "results": findings,
                "rejected_ideas": rejected_ideas,
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
            token = body.get("token") or os.environ.get("GITHUB_TOKEN", None)
            clear_first = body.get("clear_existing", False)
            max_commits = int(body.get("max_commits", 25))
            max_issues = int(body.get("max_issues", 15))

            if os.getenv("CIF_LOCAL_ONLY", "0").lower() in ("1", "true", "yes"):
                # In local-only mode, only local directories are allowed
                if not os.path.exists(repo_input):
                    return {
                        "status": "error",
                        "status_code": 403,
                        "message": "Network ingestion disabled in local-only mode (CIF_LOCAL_ONLY=1). Only local directory paths can be ingested."
                    }

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

        # 5b. Purge Repository (Step 5.1 Retention & Privacy Policy)
        elif path == "/api/purge-repo":
            repo = (body.get("repo") or "").strip()
            confirm = (body.get("confirm") or "").strip()
            if not repo:
                return {"status": "error", "status_code": 400, "message": "Missing required field: repo"}
            if confirm != repo:
                return {
                    "status": "error",
                    "status_code": 400,
                    "message": f"Confirmation mismatch. Body must include 'confirm': '{repo}'"
                }
            counts = self.db.purge_repo(repo)
            return {
                "status": "success",
                "message": f"Successfully purged all records for repository '{repo}'",
                "deleted_counts": counts
            }

        # 6. Findings Feedback (Step 3.5 & Step 3.6)
        elif path == "/api/findings/feedback":
            finding_id = body.get("finding_id", "")
            action = body.get("action", "")
            reason = (body.get("reason") or "").strip()
            pr_id = body.get("pr_id", "")
            decision_id = body.get("decision_id", "")
            token_role = get_authenticated_role(headers, client_ip)
            display_name = (body.get("reviewer") or body.get("reviewer_name") or body.get("display_name") or "").strip()
            actor = f"{token_role}:{display_name}" if display_name else (body.get("actor") or token_role)

            if not finding_id or not action:
                return {"status": "error", "status_code": 400, "message": "Missing required fields: finding_id, action"}

            if action not in ("confirm", "dismiss", "reopen"):
                return {"status": "error", "status_code": 400, "message": f"Invalid action '{action}'. Must be confirm, dismiss, or reopen."}

            if not reason:
                reason = f"Review action: {action}"

            # Auto-resolve decision_id if missing from ambiguous_findings
            if not decision_id:
                with self.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT decision_id, pr_id FROM ambiguous_findings WHERE finding_id = ?", (finding_id,))
                    r = cur.fetchone()
                    if r:
                        decision_id = r["decision_id"]
                        if not pr_id:
                            pr_id = r["pr_id"]

            if action == "dismiss":
                res = self.rejected_idea_guard.dismiss_finding(finding_id, pr_id, decision_id, actor, reason)
                return {"schema_version": "1.0", "status": "success", "message": f"Finding '{finding_id}' dismissed", "data": res}
            elif action == "confirm":
                res = self.rejected_idea_guard.confirm_finding(finding_id, pr_id, decision_id, actor, reason)
                return {"schema_version": "1.0", "status": "success", "message": f"Finding '{finding_id}' confirmed", "data": res}
            elif action == "reopen":
                res = self.rejected_idea_guard.reopen_decision(decision_id, pr_id, actor, reason)
                return {"schema_version": "1.0", "status": "success", "message": f"Decision '{decision_id}' reopened", "data": res}

        # 7. Adaptive Developer Onboarding (Step 5.4)
        elif path == "/api/onboarding":
            repo = body.get("repo")
            role = body.get("role")
            module = body.get("module")
            files = body.get("files")
            if isinstance(files, str):
                files = [f.strip() for f in files.split(",") if f.strip()]
            task = body.get("task")

            from backend.engine.onboarding import OnboardingEngine
            engine = OnboardingEngine(self.db)
            return engine.generate_learning_path(
                repo=repo,
                role=role,
                module=module,
                files=files,
                task=task
            )

        # 8. Add Repo Reviewers (Step 7.4)
        elif path == "/api/repos/reviewers":
            from backend.security import authenticate_caller
            from backend.auth.repo_access import add_repo_reviewer
            user, is_admin = authenticate_caller(self.db, headers or {}, client_ip)
            if not user and not is_admin:
                return {"status_code": 401, "status": "error", "message": "Sign-in required"}
            repo = body.get("repo")
            rev_id = body.get("user_id")
            if not repo or not rev_id:
                return {"status_code": 400, "status": "error", "message": "Missing repo or user_id"}
            user_id = user["user_id"] if user else 0
            if is_admin:
                with self.db.get_connection() as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO repo_reviewers (repo_full_name, user_id, added_by, added_at) VALUES (?, ?, ?, datetime('now'))",
                        (repo, rev_id, user_id)
                    )
                return {"status": "success", "message": "Reviewer added by admin"}
            ok = add_repo_reviewer(self.db, user_id, repo, rev_id)
            if not ok:
                return {"status_code": 403, "status": "error", "message": "Only repo owner can add reviewers"}
            return {"status": "success", "message": "Reviewer added"}

        # 9. Add Repository Flow (Step 7.5)
        elif path == "/api/repos":
            from backend.security import authenticate_caller
            from backend.auth.repo_add import add_repository_flow
            user, is_admin = authenticate_caller(self.db, headers or {}, client_ip)
            if not user and not is_admin:
                return {"status_code": 401, "status": "error", "message": "Sign-in required"}
            user_id = user["user_id"] if user else 0
            code, res = add_repository_flow(self.db, user_id, body)
            res["status_code"] = code
            return res

        # 10. Cancel Ingestion Job (Step 7.6)
        elif path.startswith("/api/jobs/") and path.endswith("/cancel"):
            # Format: /api/jobs/<job_id>/cancel
            parts = path.strip("/").split("/")
            if len(parts) >= 3:
                job_id = parts[2]
                from backend.ingestion.job_runner import IngestJobRunner
                runner = IngestJobRunner.get_instance(self.db)
                ok = runner.cancel_job(job_id)
                if ok:
                    return {"status_code": 200, "status": "success", "message": f"Job '{job_id}' cancelled"}
                else:
                    return {"status_code": 404, "status": "error", "message": f"Job '{job_id}' not found or cannot be cancelled"}
            return {"status_code": 400, "status": "error", "message": "Invalid cancel URL format"}

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
        supported_events = {
            "push", "pull_request", "issues", "issue_comment",
            "pull_request_review", "installation", "installation_repositories"
        }
        if event_type not in supported_events:
            return ({"status": "ok", "message": f"Ignored event type: {event_type}"}, 200)

        now_iso = datetime.datetime.now(timezone.utc).isoformat()

        # 1. Handle installation events
        if event_type == "installation":
            action = body.get("action", "")
            installation = body.get("installation", {})
            inst_id = installation.get("id")
            sender = body.get("sender", {})
            sender_id = sender.get("id")

            if action == "created":
                repos = body.get("repositories", [])
                linked_count = 0
                with self.db.get_connection() as conn:
                    cur = conn.cursor()
                    user_id = None
                    if sender_id:
                        cur.execute("SELECT user_id FROM users WHERE github_id = ?", (sender_id,))
                        urow = cur.fetchone()
                        if urow:
                            user_id = urow[0]

                    for r in repos:
                        r_name = r.get("full_name")
                        if not r_name:
                            continue
                        vis = "private" if r.get("private") else "public"
                        cur.execute("""
                            INSERT OR IGNORE INTO repos (repo_full_name, github_repo_id, visibility, added_at, stats_json)
                            VALUES (?, ?, ?, ?, ?)
                        """, (r_name, r.get("id"), vis, now_iso, json.dumps({"installation_id": inst_id, "status": "active", "sync_enabled": True})))
                        cur.execute("SELECT stats_json FROM repos WHERE repo_full_name = ?", (r_name,))
                        srow = cur.fetchone()
                        if srow and srow[0]:
                            try:
                                st = json.loads(srow[0])
                                st["status"] = "active"
                                st["sync_enabled"] = True
                                st["installation_id"] = inst_id
                                cur.execute("UPDATE repos SET stats_json = ? WHERE repo_full_name = ?", (json.dumps(st), r_name))
                            except Exception:
                                pass
                        if user_id:
                            cur.execute("""
                                INSERT OR REPLACE INTO repo_access (user_id, repo_full_name, level, verified_at)
                                VALUES (?, ?, 'admin', ?)
                            """, (user_id, r_name, now_iso))
                        linked_count += 1
                    conn.commit()
                return ({"status": "ok", "action": "created", "repos_linked": linked_count}, 200)

            elif action in ("deleted", "suspend"):
                removed_count = 0
                with self.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT repo_full_name, stats_json FROM repos")
                    all_repos = cur.fetchall()
                    for r_name, stats_raw in all_repos:
                        s = {}
                        if stats_raw:
                            try:
                                s = json.loads(stats_raw)
                            except Exception:
                                pass
                        if s.get("installation_id") == inst_id or (r_name in [r.get("full_name") for r in body.get("repositories", [])]):
                            s["status"] = "removed"
                            s["sync_enabled"] = False
                            cur.execute("UPDATE repos SET stats_json = ? WHERE repo_full_name = ?", (json.dumps(s), r_name))
                            cur.execute("DELETE FROM repo_access WHERE repo_full_name = ?", (r_name,))
                            removed_count += 1
                    conn.commit()
                return ({"status": "ok", "action": action, "repos_removed": removed_count, "message": "Installation deleted; repos marked removed and syncing stopped"}, 200)

            return ({"status": "ok", "action": action}, 200)

        # 2. Handle installation_repositories events
        elif event_type == "installation_repositories":
            action = body.get("action", "")
            installation = body.get("installation", {})
            inst_id = installation.get("id")
            sender = body.get("sender", {})
            sender_id = sender.get("id")
            repos_added = body.get("repositories_added", [])
            repos_removed = body.get("repositories_removed", [])

            with self.db.get_connection() as conn:
                cur = conn.cursor()
                user_id = None
                if sender_id:
                    cur.execute("SELECT user_id FROM users WHERE github_id = ?", (sender_id,))
                    urow = cur.fetchone()
                    if urow:
                        user_id = urow[0]

                for r in repos_added:
                    r_name = r.get("full_name")
                    if not r_name:
                        continue
                    vis = "private" if r.get("private") else "public"
                    cur.execute("""
                        INSERT OR IGNORE INTO repos (repo_full_name, github_repo_id, visibility, added_at, stats_json)
                        VALUES (?, ?, ?, ?, ?)
                    """, (r_name, r.get("id"), vis, now_iso, json.dumps({"installation_id": inst_id, "status": "active", "sync_enabled": True})))
                    cur.execute("SELECT stats_json FROM repos WHERE repo_full_name = ?", (r_name,))
                    srow = cur.fetchone()
                    if srow and srow[0]:
                        try:
                            st = json.loads(srow[0])
                            st["status"] = "active"
                            st["sync_enabled"] = True
                            st["installation_id"] = inst_id
                            cur.execute("UPDATE repos SET stats_json = ? WHERE repo_full_name = ?", (json.dumps(st), r_name))
                        except Exception:
                            pass
                    if user_id:
                        cur.execute("""
                            INSERT OR REPLACE INTO repo_access (user_id, repo_full_name, level, verified_at)
                            VALUES (?, ?, 'admin', ?)
                        """, (user_id, r_name, now_iso))

                for r in repos_removed:
                    r_name = r.get("full_name")
                    if not r_name:
                        continue
                    cur.execute("SELECT stats_json FROM repos WHERE repo_full_name = ?", (r_name,))
                    srow = cur.fetchone()
                    st = {}
                    if srow and srow[0]:
                        try:
                            st = json.loads(srow[0])
                        except Exception:
                            pass
                    st["status"] = "removed"
                    st["sync_enabled"] = False
                    cur.execute("UPDATE repos SET stats_json = ? WHERE repo_full_name = ?", (json.dumps(st), r_name))
                    cur.execute("DELETE FROM repo_access WHERE repo_full_name = ?", (r_name,))
                conn.commit()

            return ({
                "status": "ok",
                "action": action,
                "repos_added": len(repos_added),
                "repos_removed": len(repos_removed)
            }, 200)

        # 3. Repository-scoped events (push, pull_request, issues, issue_comment, pull_request_review)
        repo_full = body.get("repository", {}).get("full_name", "unknown")

        # Check if repository is marked removed or syncing disabled
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT stats_json FROM repos WHERE repo_full_name = ?", (repo_full,))
            row = cur.fetchone()
            if row and row[0]:
                try:
                    stats = json.loads(row[0])
                    if stats.get("status") == "removed" or stats.get("sync_enabled") is False:
                        return ({"status": "ok", "message": f"Repo {repo_full} is marked removed; syncing stopped"}, 200)
                except Exception:
                    pass

        # 3a. Handle issue_comment events
        if event_type == "issue_comment":
            action = body.get("action", "")
            if action not in ("created", "edited"):
                return ({"status": "ok", "message": f"Ignored comment action: {action}"}, 200)

            comment = body.get("comment", {})
            issue = body.get("issue", {})
            comment_id = comment.get("id")
            if not comment_id:
                return ({"status": "error", "message": "Missing comment id"}, 400)

            is_pr = "pull_request" in issue
            source_type = "pr_review_comment" if is_pr else "issue_comment"
            parent_id = f"pr_{issue.get('number')}" if is_pr else f"issue_{issue.get('number')}"
            author = comment.get("user", {}).get("login", "unknown")
            created_at = comment.get("created_at") or now_iso
            html_url = comment.get("html_url") or f"https://github.com/{repo_full}/issues/{issue.get('number')}#issuecomment-{comment_id}"

            ev = Event(
                event_id=f"comment_{comment_id}",
                source_type=source_type,
                source_id=f"comment_{comment_id}",
                source_url=html_url,
                repo=repo_full,
                author=author,
                timestamp=created_at,
                title=f"Comment on #{issue.get('number')}: {str(issue.get('title', ''))[:50]}",
                body=comment.get("body", "") or "",
                parent_event_ids=[parent_id],
                raw_metadata={"issue_number": issue.get("number"), "is_pr": is_pr}
            )
            event_id = self.db.insert_event(ev)
            with self.db.get_connection() as conn:
                conn.execute("UPDATE repos SET last_synced_at = ? WHERE repo_full_name = ?", (created_at, repo_full))
                conn.commit()

            return ({"status": "ok", "event": "issue_comment", "event_id": event_id, "repo": repo_full}, 200)

        # 3b. Handle issues events
        elif event_type == "issues":
            action = body.get("action", "")
            if action not in ("opened", "edited", "closed", "reopened"):
                return ({"status": "ok", "message": f"Ignored issue action: {action}"}, 200)

            issue = body.get("issue", {})
            if "pull_request" in issue:
                return ({"status": "ok", "message": "Ignored PR in issues event"}, 200)

            issue_num = issue.get("number")
            if not issue_num:
                return ({"status": "error", "message": "Missing issue number"}, 400)

            author = issue.get("user", {}).get("login", "unknown")
            created_at = issue.get("created_at") or now_iso
            html_url = issue.get("html_url") or f"https://github.com/{repo_full}/issues/{issue_num}"

            ev = Event(
                event_id=f"issue_{issue_num}",
                source_type="github_issue",
                source_id=f"issue_{issue_num}",
                source_url=html_url,
                repo=repo_full,
                author=author,
                timestamp=created_at,
                title=issue.get("title", ""),
                body=issue.get("body", "") or "",
                raw_metadata={"state": issue.get("state")}
            )
            event_id = self.db.insert_event(ev)
            with self.db.get_connection() as conn:
                conn.execute("UPDATE repos SET last_synced_at = ? WHERE repo_full_name = ?", (created_at, repo_full))
                conn.commit()

            return ({"status": "ok", "event": "issues", "event_id": event_id, "repo": repo_full}, 200)

        # 3c. Handle pull_request_review events
        elif event_type == "pull_request_review":
            action = body.get("action", "")
            if action not in ("submitted", "edited", "dismissed"):
                return ({"status": "ok", "message": f"Ignored review action: {action}"}, 200)

            review = body.get("review", {})
            pr = body.get("pull_request", {})
            review_id = review.get("id")
            if not review_id:
                return ({"status": "error", "message": "Missing review id"}, 400)

            state = review.get("state", "COMMENTED")
            author = review.get("user", {}).get("login", "unknown")
            submitted_at = review.get("submitted_at") or now_iso
            html_url = review.get("html_url") or f"https://github.com/{repo_full}/pull/{pr.get('number')}#pullrequestreview-{review_id}"
            body_text = review.get("body") or f"PR #{pr.get('number')} review: {state}"

            ev = Event(
                event_id=f"review_{review_id}",
                source_type="pr_review",
                source_id=f"review_{review_id}",
                source_url=html_url,
                repo=repo_full,
                author=author,
                timestamp=submitted_at,
                title=f"PR #{pr.get('number')} Review ({state})",
                body=body_text,
                parent_event_ids=[f"pr_{pr.get('number')}"],
                raw_metadata={"state": state, "pr_number": pr.get("number")}
            )
            event_id = self.db.insert_event(ev)
            with self.db.get_connection() as conn:
                conn.execute("UPDATE repos SET last_synced_at = ? WHERE repo_full_name = ?", (submitted_at, repo_full))
                conn.commit()

            return ({"status": "ok", "event": "pull_request_review", "event_id": event_id, "repo": repo_full}, 200)

        # 3d. Handle push events
        elif event_type == "push":
            commits = body.get("commits", [])
            ref = body.get("ref", "")
            if not commits and not ref:
                return ({"status": "ok", "message": "Ignored event type: push"}, 200)

            synced = 0
            for c in commits:
                c_id = c.get("id", "")
                if not c_id:
                    continue
                c_msg = c.get("message", "")
                author_name = c.get("author", {}).get("username") or c.get("author", {}).get("name", "unknown")
                c_ts = c.get("timestamp") or now_iso
                c_url = c.get("url") or f"https://github.com/{repo_full}/commit/{c_id}"
                modified = (c.get("added", []) or []) + (c.get("modified", []) or [])

                ev = Event(
                    event_id=f"commit_{c_id[:10]}",
                    source_type="git_commit",
                    source_id=c_id[:10],
                    source_url=c_url,
                    repo=repo_full,
                    author=author_name,
                    timestamp=c_ts,
                    title=c_msg.splitlines()[0] if c_msg else "Commit",
                    body=c_msg,
                    artifacts_touched=modified,
                    raw_metadata={"full_sha": c_id, "ref": ref}
                )
                self.db.insert_event(ev)
                synced += 1

            with self.db.get_connection() as conn:
                conn.execute("UPDATE repos SET last_synced_at = ? WHERE repo_full_name = ?", (now_iso, repo_full))
                conn.commit()

            return ({"status": "ok", "event": "push", "commits_synced": synced, "repo": repo_full}, 200)

        # 3e. Handle pull_request events
        elif event_type == "pull_request":
            action = body.get("action", "")
            if action not in ("opened", "synchronize", "reopened"):
                return ({"status": "ok", "message": f"Ignored PR action: {action}"}, 200)

            pr = body.get("pull_request", {})
            pr_number = pr.get("number", 0)
            diff_url = pr.get("diff_url", "")
            comments_url = pr.get("comments_url", "")
            head_sha = pr.get("head", {}).get("sha", "")
            html_url = pr.get("html_url") or f"https://github.com/{repo_full}/pull/{pr_number}"

            # Insert PR event into CIF
            ev = Event(
                event_id=f"pr_{pr_number}",
                source_type="github_pr",
                source_id=f"pr_{pr_number}",
                source_url=html_url,
                repo=repo_full,
                author=pr.get("user", {}).get("login", "unknown"),
                timestamp=pr.get("created_at") or now_iso,
                title=pr.get("title", ""),
                body=pr.get("body", "") or "",
                raw_metadata={"state": pr.get("state"), "head_sha": head_sha}
            )
            self.db.insert_event(ev)

            # R1 Token Resolution: Check for GitHub App installation token (R1) first, then fallback to GITHUB_TOKEN
            installation_id = body.get("installation", {}).get("id")
            token = ""
            r1_status = None
            if installation_id:
                try:
                    from backend.auth.app_token import get_installation_token
                    token, r1_status = get_installation_token(installation_id)
                except Exception as e:
                    r1_status = f"error: {e}"

            if not token:
                token = os.environ.get("GITHUB_TOKEN", "")

            # Fetch diff via GitHub API if token is set
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

            # Run rejected-idea guard analysis (Advisory)
            rej_report = self.rejected_idea_guard.evaluate_proposal(
                repo=repo_full,
                pr_id=f"pr_{pr_number}",
                title=pr.get("title", ""),
                body=pr.get("body", ""),
                diff_text=diff_text,
                changed_files=changed_files,
                author=pr.get("user", {}).get("login", "unknown")
            )
            rejected_ideas = rej_report.get("findings", [])

            # Post PR comment if violations or advisory findings and token available
            comment_posted = False
            all_report_items = findings + rejected_ideas
            if all_report_items and token and comments_url:
                lines = ["**⚠️ Context Intelligence Framework — Decision Guard Review**", ""]
                if findings:
                    lines.append("### Guard Rule Violations")
                    for f in findings[:5]:
                        lines.append(f"- **{f.get('violation_type','drift')}**: {f.get('message', '')[:200]}")
                        if f.get("decision_url"):
                            lines.append(f"  📋 [Evidence]({f['decision_url']})")
                    lines.append("")
                if rejected_ideas:
                    lines.append("### Previously Rejected Approaches (Advisory)")
                    for r in rejected_ideas[:5]:
                        lines.append(f"- **{r.get('tier', 'advisory').upper()}**: {r.get('pr_comment', '')[:250]}")
                    lines.append("")
                lines.append("*Posted by CIF Decision Guard. Advisory findings do not block merge unless strict mode is enabled.*")
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
            elif all_report_items and not token:
                print(f"[CIF] {len(findings)} drift finding(s) and {len(rejected_ideas)} advisory finding(s) for PR#{pr_number} stored. "
                      "Set GITHUB_TOKEN or enable GitHub App RS256 keys to post comments.")

            return ({
                "status": "ok",
                "repo": repo_full,
                "pr": pr_number,
                "findings_count": len(findings),
                "rejected_ideas_count": len(rejected_ideas),
                "check_status": report.get("status", "complete"),
                "errors": report.get("errors", []),
                "comment_posted": comment_posted,
                "diff_fetch_error": fetch_error,
                "r1_status": r1_status
            }, 200)

        return ({"status": "ok", "message": "Unhandled event"}, 200)

    def handle_delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        client_ip: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """
        Phase 7 / Step 7.8: Consent, Deletion and Retention.
        Handles DELETE /api/repos/{owner}/{repo}.
        Only the user who added the repository, or an admin, can delete it.
        Deletes all rows across events, entities, decisions, edges, claims, history,
        jobs, access rows, and vacuums SQLite disk pages.
        """
        headers = headers or {}
        if path.startswith("/api/repos/"):
            repo_part = path[len("/api/repos/"):]
            parts = repo_part.split("/")
            if len(parts) != 2 or not parts[0] or not parts[1]:
                return {"status": "error", "message": "Invalid repo path; must be /api/repos/{owner}/{repo}", "status_code": 400}

            repo_full_name = f"{parts[0]}/{parts[1]}"

            # Check admin or user identity
            user, is_admin = authenticate_caller(self.db, headers, client_ip)
            if not is_admin and not user:
                return {"status": "error", "message": "Authentication required", "status_code": 401}

            # Verify repository exists and verify owner
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT added_by_user_id FROM repos WHERE repo_full_name = ?", (repo_full_name,))
                repo_row = cur.fetchone()
                if not repo_row:
                    cur.execute("SELECT 1 FROM events WHERE repo = ? OR repo_full_name = ? LIMIT 1", (repo_full_name, repo_full_name))
                    if not cur.fetchone():
                        return {"status": "error", "message": f"Repository '{repo_full_name}' not found", "status_code": 404}
                    added_by = None
                else:
                    added_by = repo_row[0]

            if not is_admin:
                if user.get("user_id") != added_by:
                    return {
                        "status": "error",
                        "message": "Forbidden: Only the user who added this repository or an admin can delete it",
                        "status_code": 403
                    }

            # Cascade deletion across all tables and vacuum SQLite
            counts = self.db.delete_repository(repo_full_name)

            return {
                "status": "success",
                "message": f"Successfully deleted repository '{repo_full_name}' and expunged all records",
                "repo": repo_full_name,
                "deleted_counts": counts,
                "status_code": 200
            }

        return {"status": "error", "message": f"Endpoint not found: DELETE {path}", "status_code": 404}
