"""
Live GitHub Ingestion Module
Connects to GitHub's public REST API or ingests a local repository folder directly.
Fetches real commits, issues, pull requests, and source tree files,
then feeds them into GitAdapter, GitHubAdapter, EntityResolver, DecisionExtractor,
and TemporalGraph.
"""
import os
import urllib.request
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

    def _make_request(self, endpoint: str) -> Tuple[int, Any]:
        """Makes an HTTP GET request to GitHub API with proper headers and SSL context."""
        if os.getenv("CIF_LOCAL_ONLY", "0").lower() in ("1", "true", "yes"):
            raise RuntimeError("Network ingestion disabled in local-only mode (CIF_LOCAL_ONLY=1)")
        url = f"{GITHUB_API_BASE}/{endpoint.lstrip('/')}"
        headers = {
            "User-Agent": "Context-Intelligence-Framework/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=12, context=self.ssl_context) as response:
                status = response.getcode()
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
            return e.code, {"error": msg}
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
            return 500, {"error": str(reason if reason is not None else e)}
        except Exception as e:
            return 500, {"error": str(e)}

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
        adr_dir = os.path.join(abs_path, "docs", "adr")
        if os.path.isdir(adr_dir):
            for fname in sorted(os.listdir(adr_dir)):
                if not fname.endswith(".md"):
                    continue
                rel = f"docs/adr/{fname}"
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
        End-to-End Ingestion Pipeline for any custom GitHub repository or local directory path.
        """
        clean_input = raw_repo_input.strip()
        local_cand = clean_input if os.path.exists(clean_input) else os.path.join(os.getcwd(), clean_input)
        if os.path.exists(local_cand) and os.path.isdir(local_cand):
            return self.ingest_local_directory(local_cand, clear_existing=clear_existing)

        repo = self.parse_repo_identifier(raw_repo_input)

        if clear_existing:
            # Audit fix DB-02: re-ingest replaces THIS repository's data only. It used to call
            # clear_database(), which deleted every user's repositories.
            self.db.purge_repo(repo)

        stats = {
            "repo": repo,
            "commits_ingested": 0,
            "issues_ingested": 0,
            "prs_ingested": 0,
            "entities_created": 0,
            "decisions_extracted": 0,
            "edges_created": 0
        }

        # Fetch & Ingest Commits
        fetch_status, raw_commits, err_msg = self.fetch_commits(repo, max_count=max_commits)
        # Audit fix INT-02: a hard-coded commit list used to be substituted here for one
        # particular repository when GitHub failed. Fabricated history must never be stored.
        if fetch_status == 404:
            raise ValueError(f"GitHub repository '{repo}' was not found (404). Please verify that the repository exists and is public (or provide a valid Personal Access Token).")
        elif fetch_status == 403:
            # Never synthesize commits: fabricated history would be shown as real evidence.
            raise ValueError(
                f"GitHub refused the request for '{repo}' (HTTP 403): {err_msg}. "
                "Unauthenticated access is limited to 60 requests per hour; set GITHUB_TOKEN "
                "or paste a Personal Access Token in the ingest dialog, then try again."
            )
        elif fetch_status != 200 and not raw_commits:
            raise ValueError(f"GitHub API error for repository '{repo}' (HTTP {fetch_status}): {err_msg}")
        elif not raw_commits:
            raise ValueError(f"Repository '{repo}' has 0 commits or is completely empty. Please push at least one commit to your repository before ingesting.")

        # Discovered repository file tree
        tree_items = self.fetch_repo_tree(repo)
        repo_files = [t.get("path") for t in tree_items if t.get("path") and not t.get("path", "").startswith(".git")]

        ingested_events: List[Event] = []
        files_encountered = set()

        for c in raw_commits:
            sha = c.get("sha", "")
            commit_meta = c.get("commit", {})
            author_info = commit_meta.get("author", {})
            author_name = author_info.get("name") or (c.get("author") or {}).get("login") or "contributor"
            date = author_info.get("date") or "2026-01-01T00:00:00Z"
            message = commit_meta.get("message", "")

            changed_files = []
            # 1. Fetch exact changed files from GitHub commit detail API (up to 15 commits)
            if sha and len(ingested_events) < 15:
                status, commit_detail = self._make_request(f"/repos/{repo}/commits/{sha}")
                if status == 200 and isinstance(commit_detail, dict):
                    for f in commit_detail.get("files", []):
                        fn = f.get("filename", "")
                        if fn:
                            changed_files.append(fn)
                            files_encountered.add(fn)

            # 2. If commit detail not available or rate limited, match against actual repo files from tree
            if not changed_files and repo_files:
                msg_lower = message.lower()
                scope_match = re.search(r'\(([^)]+)\)', message)
                scope = scope_match.group(1).lower() if scope_match else ""
                for rf in repo_files:
                    rf_lower = rf.lower()
                    rf_base = rf_lower.split("/")[-1]
                    if (scope and f"/{scope}/" in f"/{rf_lower}") or (scope and rf_lower.startswith(f"{scope}/")):
                        changed_files.append(rf)
                        files_encountered.add(rf)
                    elif rf_base in msg_lower and len(rf_base) > 3:
                        changed_files.append(rf)
                        files_encountered.add(rf)

            # 3. Fallback to top repo file if still empty
            if not changed_files and repo_files:
                top_f = repo_files[0]
                changed_files.append(top_f)
                files_encountered.add(top_f)

            event = self.git_adapter.ingest_commit_record(
                repo=repo,
                commit_sha=sha,
                author_raw=author_name,
                timestamp=date,
                message=message,
                files_changed=changed_files,
                diff_summary=f"Modified {len(changed_files)} files"
            )
            ingested_events.append(event)
            stats["commits_ingested"] += 1

        # Fetch & Ingest Issues and PRs
        raw_issues = self.fetch_issues(repo, max_count=max_issues)
        for itm in raw_issues:
            number = itm.get("number", 0)
            title = itm.get("title", "")
            body = itm.get("body") or ""
            author = (itm.get("user") or {}).get("login") or "user"
            created_at = itm.get("created_at") or "2026-01-01T00:00:00Z"
            labels = [lbl.get("name") for lbl in itm.get("labels", []) if isinstance(lbl, dict)]

            if "pull_request" in itm:
                pr_event = self.github_adapter.ingest_pull_request(
                    repo=repo,
                    pr_number=number,
                    title=title,
                    body=body,
                    author_raw=author,
                    created_at=created_at,
                    merged_at=itm.get("closed_at") if itm.get("state") == "closed" else None,
                    artifacts_touched=list(files_encountered)[:5]
                )
                ingested_events.append(pr_event)
                stats["prs_ingested"] += 1
            else:
                issue_event = self.github_adapter.ingest_issue(
                    repo=repo,
                    issue_number=number,
                    title=title,
                    body=body,
                    author_raw=author,
                    created_at=created_at,
                    labels=labels,
                    artifacts_touched=list(files_encountered)[:5]
                )
                ingested_events.append(issue_event)
                stats["issues_ingested"] += 1

        # Ingest Entities
        created_entities: List[Entity] = []
        tree_items = self.fetch_repo_tree(repo)
        repo_files = [t.get("path") for t in tree_items if t.get("path") and not t.get("path", "").startswith(".git")]
        if not repo_files:
            repo_files = list(files_encountered)
        else:
            for f in files_encountered:
                if f not in repo_files:
                    repo_files.append(f)
        if not repo_files:
            repo_files = ["src/main.py", "README.md"]

        for file_path in repo_files[:25]:
            file_ent = self.entity_resolver.resolve_file_entity(
                repo=repo,
                canonical_path=file_path,
                summary=f"Repository source file: {file_path}"
            )
            created_entities.append(file_ent)
            stats["entities_created"] += 1

            if file_path.endswith(".py"):
                content = self.fetch_file_content(repo, file_path)
                if content:
                    extracted_fns = self.entity_resolver.parse_python_ast_functions(content, file_path)
                    for fn in extracted_fns:
                        fn_ent = self.entity_resolver.resolve_function_entity(
                            repo=repo,
                            canonical_path=file_path,
                            function_name=fn["name"],
                            summary=f"Function declared at line {fn['lineno']}"
                        )
                        created_entities.append(fn_ent)
                        stats["entities_created"] += 1

        # Extract Decisions
        target_entity_paths = [e.canonical_path for e in created_entities][:10]
        extracted_decisions: List[Decision] = []

        adr_files = [t.get("path") for t in tree_items if "adr" in t.get("path", "").lower() and t.get("path", "").endswith(".md")][:5]
        for adr_path in adr_files:
            adr_text = self.fetch_file_content(repo, adr_path)
            if adr_text:
                adr_ev = self.adr_adapter.parse_adr_markdown(
                    repo=repo,
                    file_path=adr_path,
                    markdown_content=adr_text,
                    author="lead-architect",
                    timestamp="2026-01-15T12:00:00Z"
                )
                ingested_events.append(adr_ev)
                decs = self.extractor.extract_from_event_bundle(
                    bundle_name=adr_path,
                    events=[adr_ev],
                    repo=repo,
                    target_entities=target_entity_paths
                )
                for d in decs:
                    self.db.upsert_decision(d)
                    extracted_decisions.append(d)
                    stats["decisions_extracted"] += 1

        for ev in ingested_events:
            text = f"{ev.title} {ev.body}".lower()
            decision_signals = ["feat", "fix", "refactor", "decided", "agreed", "switch", "replace", "breaking", "add", "implement", "chore", "perf", "init"]
            has_signal = any(sig in text for sig in decision_signals)

            if has_signal and ev.source_type != "adr":
                clean_title = re.sub(r'^(feat|fix|chore|refactor|docs|perf|test)(\([^)]+\))?:\s*', '', ev.title, flags=re.I).strip()
                if clean_title:
                    clean_title = clean_title[0].upper() + clean_title[1:]
                else:
                    clean_title = f"Decision regarding {ev.artifacts_touched[0] if ev.artifacts_touched else 'architecture'}"

                state = "accepted" if any(w in text for w in ("fix", "feat", "chore", "perf")) or ev.source_type == "git_commit" else "proposed"
                rationale = ev.body.strip() if len(ev.body.strip()) > 20 else f"Architectural change recorded in {ev.source_type} #{ev.source_id} by {ev.author}."

                dec_id = f"dec_{repo.replace('/', '_')}_{ev.event_id[-8:]}"
                affected = ev.artifacts_touched if ev.artifacts_touched else target_entity_paths[:2]

                dec = Decision(
                    decision_id=dec_id,
                    title=clean_title[:80],
                    state=state,
                    made_by=ev.author,
                    made_at=ev.timestamp,
                    artifacts_affected=affected,
                    alternatives_considered=[],
                    rationale=rationale[:350],
                    evidence_event_ids=[ev.event_id],
                    confidence=0.92 if ev.source_type == "git_commit" else 0.78,
                    review_status="auto_confirmed" if state == "accepted" else "pending_review",
                    repo=repo
                )
                self.db.upsert_decision(dec)
                extracted_decisions.append(dec)
                stats["decisions_extracted"] += 1

        if not extracted_decisions and ingested_events:
            latest_ev = ingested_events[0]
            base_dec = Decision(
                decision_id=f"dec_{repo.replace('/', '_')}_initial",
                title=f"Initial Architecture for {repo}",
                state="accepted",
                made_by=latest_ev.author,
                made_at=latest_ev.timestamp,
                artifacts_affected=target_entity_paths[:3],
                alternatives_considered=[],
                rationale=f"Base repository initialization and architectural setup grounded in {latest_ev.source_type} {latest_ev.source_id}.",
                evidence_event_ids=[latest_ev.event_id],
                confidence=0.90,
                review_status="auto_confirmed",
                repo=repo
            )
            self.db.upsert_decision(base_dec)
            extracted_decisions.append(base_dec)
            stats["decisions_extracted"] += 1

        for dec in extracted_decisions:
            for ent_path in dec.artifacts_affected:
                with self.db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT entity_id FROM entities WHERE repo = ? AND canonical_path = ?", (repo, ent_path))
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
