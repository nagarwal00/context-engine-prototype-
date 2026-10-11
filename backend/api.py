"""
Context Intelligence Framework - REST API Handler
Provides clean JSON REST endpoints for all 6 UI surfaces, review actions, and evaluation.
"""
from typing import Dict, Any, List, Optional
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
from backend.evaluation.benchmark import BenchmarkRunner
from backend.seed_data import populate_seed_data

class APIHandler:
    def __init__(self, db: Database):
        self.db = db
        self.graph = TemporalGraph(db)
        self.explanation_gen = ExplanationGenerator(db)
        self.reconciliation = ReconciliationEngine(db)
        self.drift_detector = DriftDetector(db)
        self.benchmark_runner = BenchmarkRunner(db)

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
            artifact = query_params.get("artifact", ["src/thermal/control.py::regulate_temperature"])[0]
            return {"status": "success", "data": self.explanation_gen.explain_artifact(artifact)}

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
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Low confidence decisions (< 0.90) or pending_review
                cursor.execute("""
                SELECT * FROM decisions
                WHERE (confidence < 0.90 OR review_status = 'pending_review') AND review_status NOT IN ('human_rejected', 'human_confirmed')
                ORDER BY confidence ASC
                """)
                for r in cursor.fetchall():
                    d = dict(r)
                    d["queue_reason"] = f"Low extraction confidence ({round(d['confidence']*100)}%) or pending review"
                    d["item_type"] = "decision"
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

        return {"status": "error", "message": f"Unknown endpoint {path}"}

    def handle_post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Review Actions (confirm | reject | merge | correct per Section 10)
        if path == "/api/review-action":
            action = body.get("action") # confirm | reject | merge | correct
            target_id = body.get("target_id")
            item_type = body.get("item_type", "decision")
            notes = body.get("notes", "Human review triage action")

            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                if item_type == "decision":
                    if action == "confirm":
                        cursor.execute("""
                        UPDATE decisions SET review_status = 'human_confirmed', confidence = 1.0
                        WHERE decision_id = ?
                        """, (target_id,))
                    elif action == "reject":
                        # Soft delete per Section 10
                        cursor.execute("""
                        UPDATE decisions SET review_status = 'human_rejected'
                        WHERE decision_id = ?
                        """, (target_id,))
                    elif action == "correct":
                        new_title = body.get("title")
                        new_state = body.get("state")
                        new_rationale = body.get("rationale")
                        cursor.execute("""
                        UPDATE decisions SET
                            title = COALESCE(?, title),
                            state = COALESCE(?, state),
                            rationale = COALESCE(?, rationale),
                            review_status = 'human_corrected'
                        WHERE decision_id = ?
                        """, (new_title, new_state, new_rationale, target_id))
                    # Record triage state transition in state_history
                    now_iso = datetime.utcnow().isoformat() + "Z"
                    cursor.execute("SELECT state FROM decisions WHERE decision_id = ?", (target_id,))
                    d_row = cursor.fetchone()
                    cur_state = d_row["state"] if d_row else "accepted"
                    hist_id = f"hist_rev_{target_id[:8]}_{int(time.time()*1000)}"
                    cursor.execute("""
                    INSERT INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (hist_id, target_id, cur_state, now_iso, "human_reviewer", f"Triage action: {action}. Notes: {notes}"))

                    conn.commit()

                elif item_type in ("conflict", "drift"):
                    if action in ("confirm", "reject"):
                        # Dismiss or resolve edge
                        cursor.execute("DELETE FROM edges WHERE edge_id = ?", (target_id,))
                        conn.commit()

            return {"status": "success", "message": f"Action '{action}' executed successfully on {target_id}"}

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
            results = self.drift_detector.analyze_diff_for_drift(
                repo=repo,
                commit_or_pr_id="live_ci_check",
                author=author,
                changed_files=files,
                diff_text=diff_text
            )
            return {"status": "success", "drift_detected": len(results) > 0, "results": results}

        # 3. Reseed Pilot Database
        elif path == "/api/reseed":
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
        findings = self.drift_detector.analyze_diff_for_drift(
            repo=repo_full,
            commit_or_pr_id=f"pr_{pr_number}",
            author=pr.get("user", {}).get("login", "unknown"),
            changed_files=changed_files,
            diff_text=diff_text
        )

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
            "comment_posted": comment_posted,
            "diff_fetch_error": fetch_error
        }, 200)
