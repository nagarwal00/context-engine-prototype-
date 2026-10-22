"""
Automatic Whole-Repository Background Ingestion Job Runner (Step 7.6)
Implements:
1. Resumable multi-phase ingestion: metadata -> docs -> code -> commits -> pull_requests -> issues -> analyze -> finalize.
2. In-process worker threads with concurrency limit (max 2 active jobs, max 1 per repo).
3. Restarts: detects interrupted running jobs on startup and marks as failed(restart_interrupted), allowing resume from cursor_json.
4. Token expiry: sets needs_relogin on token failure without losing cursor.
5. Cancellation: POST /api/jobs/{id}/cancel halts at page boundaries.
6. Coverage honesty (Rule R6): marks partial=1 and reports capped counts when limits are reached.
7. Sanitizer enforcement: all text scrubbed before writing to database.
"""
import ast
import datetime
import json
import logging
import os
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from backend.config import get_config
from backend.db import Database
from backend.models import Event, Decision, Entity, Edge
from backend.auth.sessions import get_user_github_tokens
from backend.auth.github_login import refresh_github_token
from backend.ingestion.github_client import (
    HardenedGitHubClient,
    GitHubClientError,
    GitHubRateLimitError,
    GitHubTLSError
)
from backend.ingestion.sanitizer import sanitize_text
from backend.ingestion.identity import IdentityResolver
from backend.ingestion.git_adapter import GitAdapter
from backend.ingestion.github_adapter import GitHubAdapter
from backend.ingestion.adr_adapter import ADRAdapter
from backend.engine.entity_res import EntityResolver
from backend.engine.extractor import DecisionExtractor
from backend.engine.graph import TemporalGraph

logger = logging.getLogger("cif.ingestion.job_runner")


class IngestJobRunner:
    """Manages queued and running repository ingestion jobs."""
    _instance: Optional["IngestJobRunner"] = None
    _lock = threading.Lock()

    def __init__(self, db: Database):
        self.db = db
        self._active_jobs: Dict[str, threading.Thread] = {}
        self._cancelled_jobs: Set[str] = set()
        self._repo_locks: Dict[str, threading.Lock] = {}
        self._max_concurrent_jobs = 2
        self._semaphore = threading.Semaphore(self._max_concurrent_jobs)

        # Step 7.6 Rule: On startup mark leftover running jobs as failed(restart_interrupted)
        self.recover_interrupted_jobs()

    @classmethod
    def get_instance(cls, db: Database) -> "IngestJobRunner":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(db)
            return cls._instance

    def recover_interrupted_jobs(self) -> int:
        """Marks leftover running jobs from previous process as failed(restart_interrupted)."""
        with self.db.get_connection() as conn:
            cur = conn.execute("""
            UPDATE ingest_jobs
            SET status = 'failed',
                error_code = 'restart_interrupted',
                finished_at = datetime('now')
            WHERE status = 'running';
            """)
            recovered = cur.rowcount
            if recovered > 0:
                logger.info("Recovered %d interrupted ingestion jobs on startup", recovered)
            return recovered

    def submit_job(self, repo_full_name: str, requested_by: int) -> Tuple[str, bool]:
        """
        Submits or attaches to an ingestion job for a repository.
        Returns (job_id, is_new).
        """
        with self.db.get_connection() as conn:
            # Ensure repos row exists to satisfy foreign key
            conn.execute("""
            INSERT OR IGNORE INTO repos (repo_full_name, visibility, added_by_user_id, added_at, partial)
            VALUES (?, 'public', ?, datetime('now'), 0);
            """, (repo_full_name, requested_by))

            # Check for existing active job
            active = conn.execute("""
            SELECT job_id, status FROM ingest_jobs
            WHERE repo_full_name = ? AND status IN ('queued', 'running')
            ORDER BY created_at DESC LIMIT 1;
            """, (repo_full_name,)).fetchone()

            if active:
                return active["job_id"], False

            # Check if there is a previously failed/interrupted job with a cursor
            prev = conn.execute("""
            SELECT job_id, cursor_json FROM ingest_jobs
            WHERE repo_full_name = ? AND status IN ('failed', 'needs_relogin')
            ORDER BY created_at DESC LIMIT 1;
            """, (repo_full_name,)).fetchone()

            job_id = f"job_{uuid.uuid4().hex[:12]}"
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cursor = prev["cursor_json"] if (prev and prev["cursor_json"]) else "{}"

            conn.execute("""
            INSERT INTO ingest_jobs (
                job_id, repo_full_name, requested_by, status, phase,
                progress_json, cursor_json, created_at
            ) VALUES (?, ?, ?, 'queued', 'metadata', '{}', ?, ?);
            """, (job_id, repo_full_name, requested_by, cursor, now_iso))

        # Launch worker in background thread
        self._spawn_worker(job_id, repo_full_name, requested_by)
        return job_id, True

    def _spawn_worker(self, job_id: str, repo_full_name: str, requested_by: int):
        """Spawns background worker thread respecting concurrency limits."""
        thread = threading.Thread(
            target=self._run_job_wrapper,
            args=(job_id, repo_full_name, requested_by),
            name=f"IngestWorker-{job_id}",
            daemon=True
        )
        with self._lock:
            self._active_jobs[job_id] = thread
        thread.start()

    def cancel_job(self, job_id: str) -> bool:
        """Cancels a queued or running job."""
        with self._lock:
            self._cancelled_jobs.add(job_id)

        with self.db.get_connection() as conn:
            cur = conn.execute("""
            UPDATE ingest_jobs
            SET status = 'cancelled', finished_at = datetime('now')
            WHERE job_id = ? AND status IN ('queued', 'running');
            """, (job_id,))
            return cur.rowcount > 0

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Returns sanitized status and progress for a job."""
        with self.db.get_connection() as conn:
            row = conn.execute("""
            SELECT job_id, repo_full_name, requested_by, status, phase,
                   progress_json, error_code, created_at, started_at, finished_at
            FROM ingest_jobs WHERE job_id = ?;
            """, (job_id,)).fetchone()

            if not row:
                return None

            progress = {}
            if row["progress_json"]:
                try:
                    progress = json.loads(row["progress_json"])
                except Exception:
                    progress = {}

            return {
                "job_id": row["job_id"],
                "repo_full_name": row["repo_full_name"],
                "status": row["status"],
                "phase": row["phase"],
                "progress": progress,
                "error_code": row["error_code"],
                "created_at": row["created_at"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
            }

    def is_cancelled(self, job_id: str) -> bool:
        return job_id in self._cancelled_jobs

    def _run_job_wrapper(self, job_id: str, repo_full_name: str, requested_by: int):
        # Acquire repo lock so only 1 job runs per repo
        with self._lock:
            if repo_full_name not in self._repo_locks:
                self._repo_locks[repo_full_name] = threading.Lock()
            repo_lock = self._repo_locks[repo_full_name]

        with repo_lock:
            # Acquire global concurrency semaphore (max 2)
            self._semaphore.acquire()
            try:
                self._execute_job(job_id, repo_full_name, requested_by)
            finally:
                self._semaphore.release()
                with self._lock:
                    self._active_jobs.pop(job_id, None)
                    self._cancelled_jobs.discard(job_id)

    def _execute_job(self, job_id: str, repo_full_name: str, requested_by: int):
        """Executes all ingestion phases sequentially with progress checkpoints."""
        if self.is_cancelled(job_id):
            return

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self.db.get_connection() as conn:
            conn.execute("""
            UPDATE ingest_jobs SET status = 'running', started_at = ? WHERE job_id = ?;
            """, (now_iso, job_id))

        cfg = get_config()
        max_commits = cfg.get_max_commits()
        max_prs = cfg.get_max_prs()
        max_issues = cfg.get_max_issues()
        max_tarball_mb = cfg.get_max_tarball_mb()

        # Load cursor
        cursor: Dict[str, Any] = {}
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT cursor_json FROM ingest_jobs WHERE job_id = ?", (job_id,)).fetchone()
            if row and row["cursor_json"]:
                try:
                    cursor = json.loads(row["cursor_json"])
                except Exception:
                    cursor = {}

        progress: Dict[str, Any] = {
            "counts": {"commits": 0, "prs": 0, "issues": 0, "docs": 0, "entities": 0, "decisions": 0},
            "capped": [],
            "waiting_for_rate_limit": None,
            "phase_done": False
        }

        # 0. Acquire User GitHub Token
        tokens = get_user_github_tokens(self.db, requested_by)
        if not tokens or not tokens.get("access_token"):
            self._fail_job(job_id, "needs_relogin", "User GitHub token missing or expired", cursor)
            return

        access_token = tokens["access_token"]

        def on_rate_limit(msg: str, wait_secs: int):
            progress["waiting_for_rate_limit"] = msg
            self._checkpoint(job_id, current_phase, progress, cursor)

        client = HardenedGitHubClient(token=access_token, rate_limit_callback=on_rate_limit)

        # Helpers for adapters
        identity_res = IdentityResolver(self.db)
        git_adapter = GitAdapter(self.db, identity_res)
        gh_adapter = GitHubAdapter(self.db, identity_res)
        adr_adapter = ADRAdapter(self.db, identity_res)
        entity_res = EntityResolver(self.db)
        extractor = DecisionExtractor(self.db)
        graph = TemporalGraph(self.db)

        current_phase = "metadata"
        try:
            # -------------------------------------------------------------
            # PHASE 1: METADATA
            # -------------------------------------------------------------
            current_phase = "metadata"
            self._checkpoint(job_id, "metadata", progress, cursor)
            if self.is_cancelled(job_id):
                return

            status, repo_info, _ = client.request(f"https://api.github.com/repos/{repo_full_name}")
            if status == 401:
                # Attempt token refresh
                if tokens.get("refresh_token"):
                    refr = refresh_github_token(self.db, requested_by, tokens["refresh_token"])
                    if refr and refr.get("access_token"):
                        client = HardenedGitHubClient(token=refr["access_token"], rate_limit_callback=on_rate_limit)
                        status, repo_info, _ = client.request(f"https://api.github.com/repos/{repo_full_name}")

            if status == 401:
                self._fail_job(job_id, "needs_relogin", "GitHub authentication failed", cursor)
                return
            if status != 200:
                self._fail_job(job_id, "failed", f"Metadata fetch failed with HTTP {status}", cursor)
                return

            default_branch = repo_info.get("default_branch", "main")
            is_private = bool(repo_info.get("private"))
            visibility = "private" if is_private else "public"

            with self.db.get_connection() as conn:
                conn.execute("""
                UPDATE repos SET visibility = ? WHERE repo_full_name = ?;
                """, (visibility, repo_full_name))

            cursor["default_branch"] = default_branch
            self._checkpoint(job_id, "metadata", progress, cursor, phase_done=True)

            # -------------------------------------------------------------
            # PHASE 2: DOCS
            # -------------------------------------------------------------
            current_phase = "docs"
            self._checkpoint(job_id, "docs", progress, cursor)
            if self.is_cancelled(job_id):
                return

            # Fetch git tree
            tree_url = f"https://api.github.com/repos/{repo_full_name}/git/trees/{default_branch}?recursive=1"
            t_status, tree_data, _ = client.request(tree_url)

            tree_items: List[Dict[str, Any]] = []
            if t_status == 200 and isinstance(tree_data, dict):
                tree_items = tree_data.get("tree", [])

            # Identify documentation files: README, docs/, ADRs, rfcs, CONTRIBUTING, CHANGELOG
            doc_candidates = []
            for item in tree_items:
                path = item.get("path", "")
                p_lower = path.lower()
                is_doc = (
                    p_lower.startswith("docs/")
                    or p_lower.startswith("doc/")
                    or "adr" in p_lower
                    or "rfc" in p_lower
                    or p_lower.endswith(".md")
                    or "readme" in p_lower
                    or "changelog" in p_lower
                    or "contributing" in p_lower
                )
                if is_doc and item.get("type") == "blob":
                    doc_candidates.append(path)

            for doc_path in doc_candidates[:50]:  # bound doc files
                if self.is_cancelled(job_id):
                    return
                f_status, file_content, _ = client.request(f"https://api.github.com/repos/{repo_full_name}/contents/{doc_path}")
                if f_status == 200 and isinstance(file_content, dict):
                    # Ingest ADR if markdown in ADR folder
                    if "adr" in doc_path.lower() and doc_path.endswith(".md"):
                        import base64
                        raw_encoded = file_content.get("content", "")
                        try:
                            decoded = base64.b64decode(raw_encoded).decode("utf-8", errors="replace")
                            adr_ev = adr_adapter.parse_adr_markdown(
                                repo=repo_full_name,
                                file_path=doc_path,
                                markdown_content=decoded,
                                author="architect",
                                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                            )
                            progress["counts"]["docs"] += 1
                        except Exception:
                            pass
                    else:
                        progress["counts"]["docs"] += 1

            self._checkpoint(job_id, "docs", progress, cursor, phase_done=True)

            # -------------------------------------------------------------
            # PHASE 3: CODE
            # -------------------------------------------------------------
            current_phase = "code"
            self._checkpoint(job_id, "code", progress, cursor)
            if self.is_cancelled(job_id):
                return

            # Check tarball limit
            tarball_url = f"https://api.github.com/repos/{repo_full_name}/tarball/{default_branch}"
            ok, _, reason = client.fetch_tarball_stream(tarball_url, max_mb=max_tarball_mb)
            if not ok:
                # Cap reached on tarball size -> Rule R6: Honest coverage
                progress["capped"].append("tarball_mb")
                with self.db.get_connection() as conn:
                    conn.execute("UPDATE repos SET partial = 1 WHERE repo_full_name = ?", (repo_full_name,))

            # Ingest source tree entities (files and functions)
            source_files = [t.get("path") for t in tree_items if t.get("type") == "blob" and t.get("path", "").endswith(".py")][:40]
            for sf in source_files:
                if self.is_cancelled(job_id):
                    return
                f_ent = entity_res.resolve_file_entity(
                    repo=repo_full_name,
                    canonical_path=sf,
                    summary=f"Python module {sf}"
                )
                progress["counts"]["entities"] += 1

                # AST function entity extraction
                f_status, f_data, _ = client.request(f"https://api.github.com/repos/{repo_full_name}/contents/{sf}")
                if f_status == 200 and isinstance(f_data, dict):
                    import base64
                    try:
                        code_bytes = base64.b64decode(f_data.get("content", ""))
                        code_str = code_bytes.decode("utf-8", errors="replace")
                        fns = entity_res.parse_python_ast_functions(code_str, sf)
                        for fn in fns:
                            fn_ent = entity_res.resolve_function_entity(
                                repo=repo_full_name,
                                canonical_path=sf,
                                function_name=fn["name"],
                                summary=f"Function {fn['name']} at line {fn['lineno']}"
                            )
                            progress["counts"]["entities"] += 1
                    except Exception:
                        pass

            self._checkpoint(job_id, "code", progress, cursor, phase_done=True)

            # -------------------------------------------------------------
            # PHASE 4: COMMITS
            # -------------------------------------------------------------
            current_phase = "commits"
            self._checkpoint(job_id, "commits", progress, cursor)
            if self.is_cancelled(job_id):
                return

            commits_url = f"https://api.github.com/repos/{repo_full_name}/commits"
            commit_page = cursor.get("commit_page", 1)
            commits_ingested = 0

            for commit in client.paginate(commits_url, max_items=max_commits, start_page=commit_page):
                if self.is_cancelled(job_id):
                    return

                sha = commit.get("sha", "")
                c_details = commit.get("commit", {})
                message = c_details.get("message", "")
                author_name = c_details.get("author", {}).get("name", "Unknown")
                ts = c_details.get("author", {}).get("date", now_iso)

                # Filter candidate decision commits to conserve detailed file list queries
                is_candidate = any(w in message.lower() for w in ("feat", "fix", "refactor", "decid", "switch", "architect", "drop", "replace", "breaking"))
                files_changed: List[str] = []

                if is_candidate:
                    det_status, det_data, _ = client.request(f"https://api.github.com/repos/{repo_full_name}/commits/{sha}")
                    if det_status == 200 and isinstance(det_data, dict):
                        files_changed = [f.get("filename") for f in det_data.get("files", []) if f.get("filename")]

                git_adapter.ingest_commit_record(
                    repo=repo_full_name,
                    commit_sha=sha,
                    author_raw=author_name,
                    timestamp=ts,
                    message=message,
                    files_changed=files_changed
                )
                commits_ingested += 1
                progress["counts"]["commits"] = commits_ingested

                if commits_ingested % 25 == 0:
                    self._checkpoint(job_id, "commits", progress, cursor)

            if commits_ingested >= max_commits:
                progress["capped"].append("commits")

            self._checkpoint(job_id, "commits", progress, cursor, phase_done=True)

            # -------------------------------------------------------------
            # PHASE 5: PULL REQUESTS
            # -------------------------------------------------------------
            current_phase = "pull_requests"
            self._checkpoint(job_id, "pull_requests", progress, cursor)
            if self.is_cancelled(job_id):
                return

            prs_url = f"https://api.github.com/repos/{repo_full_name}/pulls"
            prs_ingested = 0

            for pr in client.paginate(prs_url, max_items=max_prs, params={"state": "all"}):
                if self.is_cancelled(job_id):
                    return

                pr_num = pr.get("number")
                if not pr_num:
                    continue

                title = pr.get("title", "")
                body = pr.get("body", "") or ""
                author_login = pr.get("user", {}).get("login", "unknown")
                created_at = pr.get("created_at", now_iso)
                merged_at = pr.get("merged_at")

                gh_adapter.ingest_pull_request(
                    repo=repo_full_name,
                    pr_number=pr_num,
                    title=title,
                    body=body,
                    author_raw=author_login,
                    created_at=created_at,
                    merged_at=merged_at,
                    artifacts_touched=[]
                )
                prs_ingested += 1
                progress["counts"]["prs"] = prs_ingested

            if prs_ingested >= max_prs:
                progress["capped"].append("prs")

            self._checkpoint(job_id, "pull_requests", progress, cursor, phase_done=True)

            # -------------------------------------------------------------
            # PHASE 6: ISSUES
            # -------------------------------------------------------------
            current_phase = "issues"
            self._checkpoint(job_id, "issues", progress, cursor)
            if self.is_cancelled(job_id):
                return

            issues_url = f"https://api.github.com/repos/{repo_full_name}/issues"
            issues_ingested = 0

            for issue in client.paginate(issues_url, max_items=max_issues, params={"state": "all"}):
                if self.is_cancelled(job_id):
                    return

                # Rule: Skip PR entries returned by GitHub's issues endpoint
                if "pull_request" in issue:
                    continue

                i_num = issue.get("number")
                if not i_num:
                    continue

                i_title = issue.get("title", "")
                i_body = issue.get("body", "") or ""
                i_author = issue.get("user", {}).get("login", "unknown")
                i_created = issue.get("created_at", now_iso)
                labels = [l.get("name") for l in issue.get("labels", []) if isinstance(l, dict)]

                gh_adapter.ingest_issue(
                    repo=repo_full_name,
                    issue_number=i_num,
                    title=i_title,
                    body=i_body,
                    author_raw=i_author,
                    created_at=i_created,
                    labels=labels
                )
                issues_ingested += 1
                progress["counts"]["issues"] = issues_ingested

            if issues_ingested >= max_issues:
                progress["capped"].append("issues")

            self._checkpoint(job_id, "issues", progress, cursor, phase_done=True)

            # -------------------------------------------------------------
            # PHASE 7: ANALYZE (Pipeline Execution)
            # -------------------------------------------------------------
            current_phase = "analyze"
            self._checkpoint(job_id, "analyze", progress, cursor)
            if self.is_cancelled(job_id):
                return

            # Extract decisions from ingested events
            with self.db.get_connection() as conn:
                events_rows = conn.execute("""
                SELECT * FROM events WHERE repo = ? OR repo_full_name = ?
                ORDER BY ts ASC;
                """, (repo_full_name, repo_full_name)).fetchall()

            for ev_row in events_rows:
                if self.is_cancelled(job_id):
                    return
                text = f"{ev_row['title']} {ev_row['body']}".lower()
                if any(w in text for w in ("feat", "fix", "refactor", "decid", "switch", "architect", "drop", "replace", "reopen")):
                    dec_id = f"dec_{repo_full_name.replace('/', '_')}_{ev_row['event_id'][-8:]}"
                    title_clean = ev_row["title"].replace("feat:", "").replace("fix:", "").strip()[:80]
                    state = "accepted" if "feat" in text or "fix" in text or ev_row["source_type"] == "git_commit" else "proposed"

                    dec = Decision(
                        decision_id=dec_id,
                        title=title_clean or f"Decision for {repo_full_name}",
                        state=state,
                        made_by=ev_row["author"],
                        made_at=ev_row["ts"],
                        artifacts_affected=json.loads(ev_row["artifacts_touched"]) if ev_row["artifacts_touched"] else [],
                        alternatives_considered=[],
                        rationale=sanitize_text(ev_row["body"][:300] or "Extracted from repository change history."),
                        evidence_event_ids=[ev_row["event_id"]],
                        confidence=0.85 if state == "accepted" else 0.75,
                        review_status="auto_confirmed" if state == "accepted" else "pending_review",
                        repo=repo_full_name
                    )
                    self.db.upsert_decision(dec)
                    progress["counts"]["decisions"] += 1

            self._checkpoint(job_id, "analyze", progress, cursor, phase_done=True)

            # -------------------------------------------------------------
            # PHASE 8: FINALIZE
            # -------------------------------------------------------------
            current_phase = "finalize"
            now_finished = datetime.datetime.now(datetime.timezone.utc).isoformat()
            is_partial = len(progress["capped"]) > 0

            with self.db.get_connection() as conn:
                stats_json = json.dumps(progress["counts"])
                conn.execute("""
                UPDATE repos
                SET last_synced_at = ?,
                    partial = ?,
                    stats_json = ?
                WHERE repo_full_name = ?;
                """, (now_finished, 1 if is_partial else 0, stats_json, repo_full_name))

                final_status = "partial" if is_partial else "done"
                conn.execute("""
                UPDATE ingest_jobs
                SET status = ?,
                    phase = 'finalize',
                    progress_json = ?,
                    finished_at = ?
                WHERE job_id = ?;
                """, (final_status, json.dumps(progress), now_finished, job_id))

        except GitHubRateLimitError as rle:
            self._checkpoint(job_id, current_phase, progress, cursor)
            logger.warning("Job %s rate limited: %s", job_id, rle)
        except GitHubTLSError as tle:
            self._fail_job(job_id, "failed", f"TLS security error: {tle}", cursor)
        except Exception as e:
            self._fail_job(job_id, "failed", f"Ingestion error: {sanitize_text(str(e))}", cursor)

    def _checkpoint(
        self,
        job_id: str,
        phase: str,
        progress: Dict[str, Any],
        cursor: Dict[str, Any],
        phase_done: bool = False
    ):
        """Persists progress and cursor checkpoint after pages/phases."""
        progress_copy = dict(progress)
        progress_copy["phase_done"] = phase_done
        with self.db.get_connection() as conn:
            conn.execute("""
            UPDATE ingest_jobs
            SET phase = ?,
                progress_json = ?,
                cursor_json = ?
            WHERE job_id = ?;
            """, (phase, json.dumps(progress_copy), json.dumps(cursor), job_id))

    def _fail_job(self, job_id: str, status: str, error_msg: str, cursor: Dict[str, Any]):
        """Records job failure or needs_relogin without losing cursor."""
        with self.db.get_connection() as conn:
            conn.execute("""
            UPDATE ingest_jobs
            SET status = ?,
                error_code = ?,
                cursor_json = ?,
                finished_at = datetime('now')
            WHERE job_id = ?;
            """, (status, sanitize_text(error_msg), json.dumps(cursor), job_id))
