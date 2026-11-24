"""
Live GitHub Ingestion Module
Connects to GitHub's public REST API or ingests a local repository folder directly.
Fetches real commits, issues, pull requests, and source tree files,
then feeds them into GitAdapter, GitHubAdapter, EntityResolver, DecisionExtractor,
and TemporalGraph.
"""
import os
import urllib.request
import urllib.parse
import urllib.error
import json
import re
import ast
from typing import List, Dict, Any, Optional, Tuple
from backend.models import Event, Decision, Entity, Edge
from backend.db import Database
from backend.ingestion.identity import IdentityResolver
from backend.ingestion.git_adapter import GitAdapter
from backend.ingestion.github_adapter import GitHubAdapter
from backend.ingestion.adr_adapter import ADRAdapter
from backend.engine.entity_res import EntityResolver
from backend.engine.extractor import DecisionExtractor
from backend.engine.graph import TemporalGraph

import ssl

GITHUB_API_BASE = "https://api.github.com"

class GitHubTLSError(Exception):
    """Raised when GitHub API requests fail due to TLS certificate verification failure."""
    pass


class GitHubIngestError(ValueError):
    """An ingestion failure with the HTTP status and machine-readable code the API should return.

    Subclasses ValueError so existing callers that catch ValueError keep working.
    """

    def __init__(self, status_code: int, error_code: str, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.retry_after = retry_after


RATE_LIMIT_MESSAGE = "GitHub API rate limit exceeded. Please try again later."
RATE_LIMIT_HINT = (" Without a token GitHub allows 60 requests per hour; set GITHUB_TOKEN or paste a "
                   "Personal Access Token in the ingest dialog to raise the limit.")
# Optional requests (commit details, file contents, ADR history) stop when GitHub reports fewer
# remaining requests than this, so one ingestion cannot exhaust the hourly allowance.
REQUEST_RESERVE = 5


def classify_github_failure(repo: str, status: int, message: str, info: Optional[Dict[str, Any]] = None) -> GitHubIngestError:
    """Maps a failed GitHub API response to the error the CIF API returns."""
    info = info or {}
    message = message or ""
    if info.get("rate_limited") or (status in (403, 429) and "rate limit" in message.lower()):
        return GitHubIngestError(429, "GITHUB_RATE_LIMIT", RATE_LIMIT_MESSAGE + RATE_LIMIT_HINT,
                                 retry_after=info.get("retry_after"))
    if info.get("network_error"):
        return GitHubIngestError(503, "GITHUB_UNREACHABLE",
                                 f"Could not reach GitHub ({message}). Check your internet connection and try again.")
    if status == 404:
        return GitHubIngestError(404, "REPOSITORY_NOT_FOUND",
                                 f"GitHub repository '{repo}' was not found. Check the owner/name; if it is private, "
                                 "provide a Personal Access Token that can read it.")
    if status == 401:
        return GitHubIngestError(400, "INVALID_GITHUB_TOKEN",
                                 "GitHub rejected the access token (HTTP 401). Check or remove the token and try again.")
    if status == 403:
        return GitHubIngestError(403, "GITHUB_ACCESS_DENIED",
                                 f"GitHub refused access to '{repo}' (HTTP 403): {message}")
    if status == 409:
        return GitHubIngestError(422, "EMPTY_REPOSITORY",
                                 f"Repository '{repo}' is empty. Push at least one commit before ingesting.")
    return GitHubIngestError(502, "GITHUB_ERROR", f"GitHub API error for '{repo}' (HTTP {status}): {message}")

def _create_secure_ssl_context() -> ssl.SSLContext:
    """Creates a secure SSL context using system defaults or CIF_CA_BUNDLE if set."""
    ca_bundle = os.environ.get("CIF_CA_BUNDLE")
    if ca_bundle and os.path.exists(ca_bundle):
        return ssl.create_default_context(cafile=ca_bundle)
    for default_path in [
        "C:/msys64/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt"
    ]:
        if os.path.exists(default_path):
            return ssl.create_default_context(cafile=default_path)
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    return ssl.create_default_context()

class LiveGitHubIngestor:
    def __init__(self, db: Database, token: Optional[str] = None):
        self.db = db
        self.token = token.strip() if token and token.strip() else None
        if not self.token:
            env_tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            if env_tok and env_tok.strip():
                self.token = env_tok.strip()
        self.identity_resolver = IdentityResolver(db)
        self.git_adapter = GitAdapter(db, self.identity_resolver)
        self.github_adapter = GitHubAdapter(db, self.identity_resolver)
        self.adr_adapter = ADRAdapter(db, self.identity_resolver)
        self.entity_resolver = EntityResolver(db)
        self.extractor = DecisionExtractor(db)
        self.graph = TemporalGraph(db)
        self.ssl_context = _create_secure_ssl_context()
        self.requests_made = 0
        self.rate_limit_remaining: Optional[int] = None
        self.last_error: Optional[Dict[str, Any]] = None

    def _make_request(self, endpoint: str) -> Tuple[int, Any]:
        """Makes an HTTP GET request to GitHub API with proper headers and SSL context."""
        if os.getenv("CIF_LOCAL_ONLY", "0").lower() in ("1", "true", "yes"):
            raise RuntimeError("Network ingestion disabled in local-only mode (CIF_LOCAL_ONLY=1)")
        # CIF_GITHUB_API_BASE: optional override (GitHub Enterprise, or a local test server).
        base = (os.environ.get("CIF_GITHUB_API_BASE") or GITHUB_API_BASE).rstrip("/")
        url = f"{base}/{endpoint.lstrip('/')}"
        headers = {
            "User-Agent": "Context-Intelligence-Framework/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        req = urllib.request.Request(url, headers=headers)
        self.requests_made = getattr(self, "requests_made", 0) + 1
        try:
            with urllib.request.urlopen(req, timeout=12, context=self.ssl_context) as response:
                status = response.getcode()
                remaining = response.headers.get("X-RateLimit-Remaining") if response.headers else None
                if remaining is not None and str(remaining).isdigit():
                    self.rate_limit_remaining = int(remaining)
                data = json.loads(response.read().decode("utf-8"))
                return status, data
        except ssl.SSLCertVerificationError as e:
            raise GitHubTLSError(
                "TLS certificate verification failed connecting to GitHub API. "
                "Please update OS root certificates or set CIF_CA_BUNDLE."
            ) from e
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                msg = err_body.get("message", str(e))
            except Exception:
                msg = str(e)
            hdrs = e.headers or {}
            remaining = hdrs.get("X-RateLimit-Remaining")
            rate_limited = e.code == 429 or (e.code == 403 and (remaining == "0" or "rate limit" in msg.lower()))
            retry_after = None
            if rate_limited:
                try:
                    if hdrs.get("Retry-After"):
                        retry_after = int(hdrs.get("Retry-After"))
                    elif hdrs.get("X-RateLimit-Reset"):
                        import time as _time
                        retry_after = max(1, int(hdrs.get("X-RateLimit-Reset")) - int(_time.time()))
                except (TypeError, ValueError):
                    retry_after = None
                if retry_after is not None:
                    retry_after = min(retry_after, 3600)  # GitHub windows are at most 1 hour; guards against clock skew
                self.rate_limit_remaining = 0
            info = {"error": msg, "rate_limited": rate_limited, "retry_after": retry_after}
            self.last_error = info
            return e.code, info
        except urllib.error.URLError as e:
            reason = getattr(e, "reason", None)
            if isinstance(reason, ssl.SSLCertVerificationError) or (
                isinstance(reason, str) and (
                    "CERTIFICATE_VERIFY_FAILED" in reason or "certificate verify failed" in reason.lower()
                )
            ):
                raise GitHubTLSError(
                    "TLS certificate verification failed connecting to GitHub API. "
                    "Please update OS root certificates or set CIF_CA_BUNDLE."
                ) from e
            info = {"error": str(reason if reason is not None else e), "network_error": True}
            self.last_error = info
            return 503, info
        except Exception as e:
            info = {"error": str(e), "network_error": isinstance(e, (TimeoutError, OSError))}
            self.last_error = info
            return 500, info

    def _budget_ok(self) -> bool:
        """False once GitHub reports that few requests remain (optional fetches then stop)."""
        remaining = getattr(self, "rate_limit_remaining", None)
        return remaining is None or remaining > REQUEST_RESERVE

    def parse_repo_identifier(self, raw_input: str) -> str:
        """Parses 'https://github.com/owner/repo', 'git@github.com:owner/repo.git', or 'owner/repo' into canonical 'owner/repo'."""
        if not raw_input or not isinstance(raw_input, str):
            raise ValueError("Repository identifier cannot be empty.")
        cleaned = raw_input.strip().split("#")[0].split("?")[0].rstrip("/")
        # Handle SSH git@github.com:owner/repo(.git)
        if cleaned.startswith("git@github.com:"):
            cleaned = cleaned[len("git@github.com:"):]
        elif "github.com/" in cleaned:
            cleaned = cleaned.split("github.com/")[-1]
        elif cleaned.startswith("github.com:"):
            cleaned = cleaned.split("github.com:")[-1]

        cleaned = cleaned.lstrip("/")
        parts = [p.strip() for p in cleaned.split("/") if p.strip()]
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1]
            if repo.endswith(".git"):
                repo = repo[:-4]
            # Disallow invalid protocol tokens or empty pieces
            if owner.lower() in ("http:", "https:", "git:", "ssh:") or not owner or not repo:
                raise ValueError(f"Invalid repository format '{raw_input}'. Please use 'owner/repo' or GitHub URL.")
            slug = f"{owner}/{repo}".strip()
            if not re.match(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]{1,100}$", slug) or ".." in slug:
                raise ValueError(f"Invalid repository format '{raw_input}'. Please use 'owner/repo' or GitHub URL.")
            return slug
        raise ValueError(f"Invalid repository format '{raw_input}'. Please use 'owner/repo' or GitHub URL.")

    def fetch_commits(self, repo: str, max_count: int = 25) -> Tuple[int, List[Dict[str, Any]], Optional[str]]:
        """Fetches the latest commits from the repository."""
        status, data = self._make_request(f"/repos/{repo}/commits?per_page={max_count}")
        if status != 200:
            err_msg = data.get("error", f"HTTP {status}") if isinstance(data, dict) else str(data)
            return status, [], err_msg
        return status, (data if isinstance(data, list) else []), None

    def fetch_issues(self, repo: str, max_count: int = 20) -> List[Dict[str, Any]]:
        """Fetches issues and pull requests."""
        status, data = self._make_request(f"/repos/{repo}/issues?state=all&per_page={max_count}")
        if status != 200:
            return []
        return data if isinstance(data, list) else []

    def fetch_repo_tree(self, repo: str, branch: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetches repository tree to discover files and documentation across default branches."""
        branches = [branch] if branch else ["main", "master", "develop"]
        for b in branches:
            status, data = self._make_request(f"/repos/{repo}/git/trees/{b}?recursive=1")
            if status == 200 and isinstance(data, dict):
                return data.get("tree", [])
        return []

    def fetch_file_content(self, repo: str, path: str) -> Optional[str]:
        """Fetches raw text content of a file from GitHub."""
        status, data = self._make_request(f"/repos/{repo}/contents/{path}")
        if status == 200 and isinstance(data, dict):
            import base64
            content = data.get("content", "")
            if content and data.get("encoding") == "base64":
                try:
                    return base64.b64decode(content).decode("utf-8", errors="replace")
                except Exception:
                    pass
        return None

    # ------------------------------------------------------------------
    # Local folder ingestion (audit fixes INT-04 / ALG-05)
    #
    # Previously this function stamped every issue file as issue #5 by "sarah_chen" on
    # 2026-01-08 touching src/payment.py, every ADR as written by "alex_rodriguez", linked
    # each ADR to every function in the repository, and used a second keyword extractor
    # with substring triggers ("add" matched "address"). Metadata now comes from git when the
    # folder is a git repository, otherwise it is reported as unknown; decisions are extracted
    # by the same DecisionExtractor used for GitHub ingestion.
    # ------------------------------------------------------------------
    @staticmethod
    def _git(abs_path: str, *args: str) -> Optional[str]:
        """Runs git inside abs_path only if that folder is itself a git repository.

        (`git -C sub` without sub/.git would silently read the PARENT repository's history.)
        """
        if not os.path.exists(os.path.join(abs_path, ".git")):
            return None
        import subprocess
        try:
            res = subprocess.run(["git", "-C", abs_path, *args], capture_output=True,
                                 text=True, timeout=60, encoding="utf-8", errors="replace")
        except (OSError, subprocess.SubprocessError):
            return None
        return res.stdout if res.returncode == 0 else None

    def _local_commits(self, abs_path: str, max_commits: int = 500) -> Tuple[List[Dict[str, Any]], str]:
        """Returns (commits, source) where source is 'git' or 'commits.json' or 'none'."""
        out = self._git(abs_path, "log", "--no-merges", f"-n{max_commits}", "--name-only",
                        "--format=%x1e%H%x1f%an%x1f%aI%x1f%s%x1f%b%x1f")
        if out is not None:
            commits = []
            for rec in out.split("\x1e"):
                parts = rec.split("\x1f")
                if len(parts) < 6:
                    continue
                sha, author, date, subject, body, files_blob = parts[:6]
                files = [f.strip() for f in files_blob.strip().splitlines() if f.strip()]
                message = subject if not body.strip() else f"{subject}\n\n{body.strip()}"
                commits.append({"sha": sha, "author": author, "date": date, "message": message, "files": files})
            return commits, "git"
        fixture = os.path.join(abs_path, "commits.json")
        if os.path.exists(fixture):
            with open(fixture, "r", encoding="utf-8") as f:
                data = json.load(f)
            commits = []
            for c in data if isinstance(data, list) else []:
                # A fixture entry must be complete; nothing is invented for missing fields.
                if all(isinstance(c.get(k), str) and c.get(k).strip() for k in ("sha", "author", "date", "message")):
                    commits.append({**c, "files": [f for f in c.get("files", []) if isinstance(f, str)]})
            return commits, "commits.json"
        return [], "none"

    def _file_origin(self, abs_path: str, rel_path: str) -> Tuple[str, str]:
        """(author, ISO timestamp) of the commit that added rel_path; ('unknown', mtime) without git."""
        out = self._git(abs_path, "log", "--diff-filter=A", "--format=%an%x1f%aI", "--", rel_path)
        if out and out.strip():
            author, date = out.strip().splitlines()[-1].split("\x1f")[:2]
            return author, date
        import datetime as _dt
        mtime = os.path.getmtime(os.path.join(abs_path, rel_path))
        return "unknown", _dt.datetime.fromtimestamp(mtime, _dt.timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def _mentioned_files(text: str, known_files: List[str]) -> List[str]:
        """Repository files whose path or file name is explicitly mentioned in text."""
        low = text.lower()
        hits = []
        for path in known_files:
            name = os.path.basename(path).lower()
            if path.lower() in low or re.search(rf"(?<![\w/]){re.escape(name)}\b", low):
                hits.append(path)
        return hits

    def ingest_local_directory(self, local_path: str, clear_existing: bool = True) -> Dict[str, Any]:
        """Ingests a local repository folder (git history if present, else commits.json fixture)."""
        abs_path = os.path.abspath(local_path)
        repo = f"local/{os.path.basename(abs_path)}"

        if clear_existing:
            self.db.purge_repo(repo)  # audit fix DB-02 (was a global wipe)

        stats = {
            "repo": repo,
            "commits_ingested": 0,
            "issues_ingested": 0,
            "prs_ingested": 0,
            "entities_created": 0,
            "decisions_extracted": 0,
            "edges_created": 0,
        }
        ingested_events: List[Event] = []

        # 1. Commits
        commits, commit_source = self._local_commits(abs_path)
        stats["commit_source"] = commit_source
        for c in commits:
            ev = self.git_adapter.ingest_commit_record(
                repo=repo, commit_sha=c["sha"], author_raw=c["author"], timestamp=c["date"],
                message=c["message"], files_changed=c.get("files", []))
            ingested_events.append(ev)
            stats["commits_ingested"] += 1

        # 2. Source files -> file and function entities (Python AST)
        python_files = []
        for root, dirs, files in os.walk(abs_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules", "venv")]
            for f in files:
                if f.endswith(".py"):
                    full = os.path.join(root, f)
                    python_files.append((os.path.relpath(full, abs_path).replace("\\", "/"), full))
        python_files.sort()
        known_files = [rel for rel, _ in python_files]
        for rel_p, full_p in python_files:
            self.entity_resolver.resolve_file_entity(repo, rel_p, f"Source module: {rel_p}")
            stats["entities_created"] += 1
            with open(full_p, "r", encoding="utf-8", errors="replace") as f:
                code_content = f.read()
            for fn in self.entity_resolver.parse_python_ast_functions(code_content, rel_p):
                self.entity_resolver.resolve_function_entity(repo, rel_p, fn["name"], f"Function at line {fn['lineno']}")
                stats["entities_created"] += 1

        # 3. Issues from docs/issues/*.md (number parsed from the file name or "# Issue #N" heading)
        issues_dir = os.path.join(abs_path, "docs", "issues")
        if os.path.isdir(issues_dir):
            for fname in sorted(os.listdir(issues_dir)):
                if not fname.endswith(".md"):
                    continue
                rel = f"docs/issues/{fname}"
                with open(os.path.join(issues_dir, fname), "r", encoding="utf-8") as f:
                    text = f.read()
                m = re.search(r"issue[_\- ]?#?(\d+)", fname, re.I) or re.search(r"^#\s*Issue\s*#(\d+)", text, re.I | re.M)
                if not m:
                    continue  # cannot identify the issue: skip rather than guess
                heading = re.search(r"^#\s*(.+)$", text, re.M)
                author, created = self._file_origin(abs_path, rel)
                ev = self.github_adapter.ingest_issue(
                    repo=repo, issue_number=int(m.group(1)),
                    title=(re.sub(r"^Issue\s*#\d+:\s*", "", heading.group(1).strip(), flags=re.I)
                           if heading else fname[:-3].replace("_", " ")),
                    body=text, author_raw=author, created_at=created,
                    artifacts_touched=self._mentioned_files(text, known_files))
                ingested_events.append(ev)
                stats["issues_ingested"] += 1

        # 4. ADRs from docs/adr/*.md
        adr_events: List[Event] = []
        # Conventional ADR locations: adr-tools (doc/adr), common (docs/adr), MADR (docs/decisions).
        adr_dirs = [d for d in ("docs/adr", "doc/adr", "docs/decisions", "docs/architecture/decisions")
                    if os.path.isdir(os.path.join(abs_path, d))]
        for adr_rel_dir in adr_dirs:
            adr_dir = os.path.join(abs_path, adr_rel_dir)
            for fname in sorted(os.listdir(adr_dir)):
                if not fname.endswith(".md"):
                    continue
                rel = f"{adr_rel_dir}/{fname}"
                with open(os.path.join(adr_dir, fname), "r", encoding="utf-8") as f:
                    adr_text = f.read()
                author, created = self._file_origin(abs_path, rel)
                adr_ev = self.adr_adapter.parse_adr_markdown(
                    repo=repo, file_path=rel, markdown_content=adr_text, author=author, timestamp=created)
                adr_ev.artifacts_touched = self._mentioned_files(adr_text, known_files)
                self.db.upsert_event(adr_ev)  # persist the file links found above
                adr_events.append(adr_ev)

        # 5. Decision extraction: one extractor for every source (same as GitHub ingestion)
        extracted_decisions = []
        for ev in adr_events + ingested_events:
            for d in self.extractor.extract_from_event_bundle(
                    bundle_name=ev.source_id, events=[ev], repo=repo,
                    target_entities=ev.artifacts_touched or []):
                self.db.upsert_decision(d)
                extracted_decisions.append(d)
                stats["decisions_extracted"] += 1
        ingested_events.extend(adr_events)

        # 5. Connect Graph Edges
        for dec in extracted_decisions:
            for ent_p in dec.artifacts_affected:
                with self.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT entity_id FROM entities WHERE repo = ? AND canonical_path = ?", (repo, ent_p))
                    row = cur.fetchone()
                    if row:
                        edge = Edge(
                            edge_id=f"edge_affects_{dec.decision_id}_{row['entity_id']}",
                            from_id=dec.decision_id,
                            to_id=row["entity_id"],
                            edge_type="affects",
                            valid_from=dec.made_at
                        )
                        self.graph.add_edge(edge)
                        stats["edges_created"] += 1

            for ev_id in dec.evidence_event_ids:
                edge = Edge(
                    edge_id=f"edge_evidence_{dec.decision_id}_{ev_id[-8:]}",
                    from_id=dec.decision_id,
                    to_id=ev_id,
                    edge_type="evidenced_by",
                    valid_from=dec.made_at
                )
                self.graph.add_edge(edge)
                stats["edges_created"] += 1

        return stats

    def ingest_local_repository(self, local_path: str, clear_existing: bool = True) -> Dict[str, Any]:
        """Alias for ingest_local_directory."""
        return self.ingest_local_directory(local_path, clear_existing=clear_existing)

    def ingest_custom_repository(
        self,
        raw_repo_input: str,
        clear_existing: bool = False,
        max_commits: int = 25,
        max_issues: int = 15
    ) -> Dict[str, Any]:
        """
        Ingests a GitHub repository (owner/repo or URL) or a local folder path.

        Raises GitHubIngestError (a ValueError) with the HTTP status the API should return.
        Only data returned by GitHub is stored: no commits, files, authors, dates or decisions are
        invented. Optional requests stop before the GitHub rate limit is exhausted; the result is
        then marked partial with a warning.
        """
        clean_input = (raw_repo_input or "").strip()
        if not clean_input:
            raise GitHubIngestError(400, "MISSING_REPOSITORY", "Missing repository: enter owner/repo, a GitHub URL or a local folder path.")
        local_cand = clean_input if os.path.exists(clean_input) else os.path.join(os.getcwd(), clean_input)
        if os.path.exists(local_cand) and os.path.isdir(local_cand):
            return self.ingest_local_directory(local_cand, clear_existing=clear_existing)
        if re.match(r"^(/|\\|\.{1,2}[/\\]|~|[A-Za-z]:[/\\])", clean_input):
            raise GitHubIngestError(400, "LOCAL_PATH_NOT_FOUND", f"Local folder not found on the server: '{clean_input}'.")

        try:
            repo = self.parse_repo_identifier(clean_input)
        except ValueError as exc:
            raise GitHubIngestError(400, "INVALID_REPOSITORY", str(exc)) from exc

        stats: Dict[str, Any] = {
            "repo": repo, "source": "github",
            "commits_ingested": 0, "issues_ingested": 0, "prs_ingested": 0,
            "entities_created": 0, "decisions_extracted": 0, "edges_created": 0,
            "partial": False, "warnings": [],
        }

        def warn(msg: str) -> None:
            stats["partial"] = True
            if msg not in stats["warnings"]:
                stats["warnings"].append(msg)

        budget_msg = ("Stopped optional GitHub requests early to stay within the API rate limit; "
                      "some file details are missing. Add a token for complete ingestion.")

        # 1. Commits (first call: validates that the repository exists and is readable)
        self.last_error = None
        fetch_status, raw_commits, err_msg = self.fetch_commits(repo, max_count=max_commits)
        if fetch_status != 200:
            raise classify_github_failure(repo, fetch_status, err_msg or "", self.last_error)
        if not raw_commits:
            raise GitHubIngestError(422, "EMPTY_REPOSITORY",
                                    f"Repository '{repo}' has no commits. Push at least one commit before ingesting.")

        if clear_existing:
            # Re-ingest replaces THIS repository's data only (audit fix DB-02).
            self.db.purge_repo(repo)

        # 2. Default branch and file tree (fetched once)
        tree_items: List[Dict[str, Any]] = []
        meta_status, meta = self._make_request(f"/repos/{repo}")
        branch = meta.get("default_branch") if meta_status == 200 and isinstance(meta, dict) else None
        if branch:
            tree_items = self.fetch_repo_tree(repo, branch=branch)
        if not tree_items:
            warn("The repository file tree could not be read; code entities may be incomplete.")
        repo_files = [t["path"] for t in tree_items
                      if t.get("type", "blob") == "blob" and t.get("path") and not t["path"].startswith(".git")]

        # 3. Commits -> events (changed files only from GitHub's commit details)
        ingested_events: List[Event] = []
        files_encountered: set = set()
        for idx, c in enumerate(raw_commits):
            sha = c.get("sha", "")
            commit_meta = c.get("commit", {}) or {}
            author_info = commit_meta.get("author", {}) or {}
            author_name = author_info.get("name") or (c.get("author") or {}).get("login")
            date = author_info.get("date")
            if not sha or not author_name or not date:
                warn("Skipped commits with missing SHA, author or date.")
                continue
            changed_files: List[str] = []
            if idx < 15:
                if self._budget_ok():
                    status, detail = self._make_request(f"/repos/{repo}/commits/{sha}")
                    if status == 200 and isinstance(detail, dict):
                        changed_files = [f["filename"] for f in detail.get("files", []) if f.get("filename")]
                        files_encountered.update(changed_files)
                    elif (self.last_error or {}).get("rate_limited"):
                        warn(budget_msg)
                else:
                    warn(budget_msg)
            event = self.git_adapter.ingest_commit_record(
                repo=repo, commit_sha=sha, author_raw=author_name, timestamp=date,
                message=commit_meta.get("message", ""), files_changed=changed_files,
                diff_summary=f"Modified {len(changed_files)} files" if changed_files else None)
            ingested_events.append(event)
            stats["commits_ingested"] += 1

        # 4. Issues and pull requests (linked only to files their text mentions)
        raw_issues = self.fetch_issues(repo, max_count=max_issues) if self._budget_ok() else []
        if not self._budget_ok() and not raw_issues:
            warn(budget_msg)
        for itm in raw_issues:
            number = itm.get("number")
            created_at = itm.get("created_at")
            author = (itm.get("user") or {}).get("login")
            if not number or not created_at or not author:
                continue
            title = itm.get("title", "")
            body = itm.get("body") or ""
            mentioned = self._mentioned_files(f"{title}\n{body}", repo_files)
            if "pull_request" in itm:
                ev = self.github_adapter.ingest_pull_request(
                    repo=repo, pr_number=number, title=title, body=body, author_raw=author,
                    created_at=created_at,
                    merged_at=itm.get("closed_at") if itm.get("state") == "closed" else None,
                    artifacts_touched=mentioned)
                stats["prs_ingested"] += 1
            else:
                labels = [lbl.get("name") for lbl in itm.get("labels", []) if isinstance(lbl, dict)]
                ev = self.github_adapter.ingest_issue(
                    repo=repo, issue_number=number, title=title, body=body, author_raw=author,
                    created_at=created_at, labels=labels, artifacts_touched=mentioned)
                stats["issues_ingested"] += 1
            ingested_events.append(ev)

        # 5. Code entities: real files only; Python files parsed into functions
        candidates = sorted(set(repo_files) | (files_encountered & set(repo_files or files_encountered)),
                            key=lambda f: (not f.endswith(".py"), f))[:25]
        for file_path in candidates:
            self.entity_resolver.resolve_file_entity(repo=repo, canonical_path=file_path,
                                                     summary=f"Repository source file: {file_path}")
            stats["entities_created"] += 1
            if file_path.endswith(".py"):
                if not self._budget_ok():
                    warn(budget_msg)
                    continue
                content = self.fetch_file_content(repo, file_path)
                for fn in self.entity_resolver.parse_python_ast_functions(content or "", file_path) if content else []:
                    self.entity_resolver.resolve_function_entity(
                        repo=repo, canonical_path=file_path, function_name=fn["name"],
                        summary=f"Function at line {fn['lineno']}")
                    stats["entities_created"] += 1

        # 6. ADRs: author/date from the commit that last changed the file (no invented metadata)
        adr_events: List[Event] = []
        adr_files = [f for f in repo_files if "adr" in f.lower() and f.endswith(".md")][:5]
        for adr_path in adr_files:
            if not self._budget_ok():
                warn(budget_msg)
                break
            h_status, history = self._make_request(f"/repos/{repo}/commits?path={urllib.parse.quote(adr_path)}&per_page=1")
            if h_status != 200 or not history:
                continue
            h_author = (((history[0] or {}).get("commit") or {}).get("author") or {})
            adr_text = self.fetch_file_content(repo, adr_path)
            if not adr_text or not h_author.get("name") or not h_author.get("date"):
                continue
            adr_ev = self.adr_adapter.parse_adr_markdown(
                repo=repo, file_path=adr_path, markdown_content=adr_text,
                author=h_author["name"], timestamp=h_author["date"])
            adr_ev.artifacts_touched = self._mentioned_files(adr_text, repo_files)
            self.db.upsert_event(adr_ev)
            adr_events.append(adr_ev)

        # 7. Decisions: the same DecisionExtractor used for local ingestion and the benchmark
        extracted_decisions = []
        for ev in adr_events + ingested_events:
            for d in self.extractor.extract_from_event_bundle(
                    bundle_name=ev.source_id, events=[ev], repo=repo,
                    target_entities=ev.artifacts_touched or []):
                self.db.upsert_decision(d)
                extracted_decisions.append(d)
                stats["decisions_extracted"] += 1
        if not extracted_decisions:
            stats["warnings"].append("No architectural decisions were found in the fetched history "
                                     "(this is a result, not an error).")

        # 8. Graph edges
        for dec in extracted_decisions:
            for ent_path in dec.artifacts_affected:
                with self.db.get_connection() as conn:
                    row = conn.execute("SELECT entity_id FROM entities WHERE repo = ? AND canonical_path = ?",
                                       (repo, ent_path)).fetchone()
                if row:
                    self.graph.add_edge(Edge(edge_id=f"edge_affects_{dec.decision_id}_{row['entity_id']}",
                                             from_id=dec.decision_id, to_id=row["entity_id"],
                                             edge_type="affects", valid_from=dec.made_at))
                    stats["edges_created"] += 1
            for ev_id in dec.evidence_event_ids:
                self.graph.add_edge(Edge(edge_id=f"edge_evidence_{dec.decision_id}_{ev_id[-8:]}",
                                         from_id=dec.decision_id, to_id=ev_id,
                                         edge_type="evidenced_by", valid_from=dec.made_at))
                stats["edges_created"] += 1

        stats["github_requests"] = self.requests_made
        return stats

    def clear_database(self):
        """Wipes ALL repositories' decision data (global, admin-only via POST /api/clear-db).

        Users, sessions and repository registrations are kept. For a single repository use
        Database.purge_repo().
        """
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM claim_evidence")
            conn.execute("DELETE FROM decision_claims")
            conn.execute("DELETE FROM decision_assumptions")
            conn.execute("DELETE FROM guard_rules")
            conn.execute("DELETE FROM finding_feedback")
            conn.execute("DELETE FROM ambiguous_findings")
            conn.execute("DELETE FROM state_history")
            conn.execute("DELETE FROM edges")
            conn.execute("DELETE FROM decision_evidence")
            conn.execute("DELETE FROM decision_artifacts")
            conn.execute("DELETE FROM decisions")
            conn.execute("DELETE FROM entities")
            conn.execute("DELETE FROM events")
            conn.commit()
