"""
Add-Repository Flow and Installation Discovery (Step 7.5)
Implements:
- GET /api/github/repos: discovers repositories on which the GitHub App is installed.
- POST /api/repos: adds repository, verifies App installation, creates ingest job.
- GET /api/repos/status: reports synchronization and active job status.
- Strict token ban in request payloads (Rule R4 / Step 7.5).
"""
import datetime
import json
import logging
import re
import ssl
import urllib.error
import urllib.request
import uuid
from typing import Dict, Any, Optional, Tuple, List

from backend.config import get_config
from backend.db import Database
from backend.auth.sessions import get_user_github_tokens
from backend.auth.github_login import get_secure_ssl_context, refresh_github_token

logger = logging.getLogger("cif.auth.repo_add")

RE_REPO_SLUG = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GITHUB_API_VERSION = "2022-11-28"


def check_for_forbidden_token_fields(data: Any) -> bool:
    """
    Returns True if any key or nested key in data looks like a token/access_token.
    Enforces Rule R4 / Step 7.5: No tokens in any request body.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            k_lower = str(k).lower()
            if "token" in k_lower or "secret" in k_lower or "auth" in k_lower:
                return True
            if check_for_forbidden_token_fields(v):
                return True
    elif isinstance(data, list):
        for item in data:
            if check_for_forbidden_token_fields(item):
                return True
    return False


def _github_get_json(
    url: str,
    access_token: str,
    ssl_context: Optional[ssl.SSLContext] = None
) -> Tuple[int, Any, Dict[str, str]]:
    """Makes an authenticated GET request to GitHub REST API."""
    ctx = ssl_context or get_secure_ssl_context()
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "CIF-App/1.0",
        },
        method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            status = resp.getcode()
            headers = dict(resp.headers)
            body = resp.read().decode("utf-8")
            data = json.loads(body) if body else {}
            return status, data, headers
    except urllib.error.HTTPError as e:
        status = e.code
        headers = dict(e.headers)
        try:
            body = e.read().decode("utf-8")
            data = json.loads(body) if body else {}
        except Exception:
            data = {}
        return status, data, headers


def list_user_installable_repos(
    db: Database,
    user_id: int,
    ssl_context: Optional[ssl.SSLContext] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Discovers all repositories where the signed-in user has installed the GitHub App.
    Returns (status_code, response_dict).
    """
    cfg = get_config()
    slug = cfg.get_github_app_slug() or "context-intelligence-framework"
    install_url = f"https://github.com/apps/{slug}/installations/new"

    tokens = get_user_github_tokens(db, user_id)
    if not tokens or not tokens.get("access_token"):
        return 401, {
            "status": "error",
            "error": "needs_relogin",
            "message": "GitHub access token not available. Please sign in again.",
            "install_url": install_url
        }

    access_token = tokens["access_token"]

    # 1. Fetch user installations
    status, data, _ = _github_get_json("https://api.github.com/user/installations", access_token, ssl_context)
    if status == 401:
        # Attempt refresh
        if tokens.get("refresh_token"):
            refreshed = refresh_github_token(db, user_id, tokens["refresh_token"])
            if refreshed and refreshed.get("access_token"):
                access_token = refreshed["access_token"]
                status, data, _ = _github_get_json("https://api.github.com/user/installations", access_token, ssl_context)

    if status == 401:
        return 401, {
            "status": "error",
            "error": "needs_relogin",
            "message": "GitHub token expired and refresh failed. Please sign in again.",
            "install_url": install_url
        }

    if status != 200:
        return status, {
            "status": "error",
            "message": f"Failed to fetch installations from GitHub: HTTP {status}",
            "install_url": install_url
        }

    installations = data.get("installations", [])

    # 2. Collect repositories across all installations
    discovered_repos = []
    seen_full_names = set()

    for inst in installations:
        inst_id = inst.get("id")
        if not inst_id:
            continue
        page = 1
        while page <= 10:  # Bound pagination
            url = f"https://api.github.com/user/installations/{inst_id}/repositories?per_page=100&page={page}"
            r_status, r_data, r_headers = _github_get_json(url, access_token, ssl_context)
            if r_status != 200:
                break
            repo_list = r_data.get("repositories", [])
            for r in repo_list:
                full_name = r.get("full_name")
                if full_name and full_name not in seen_full_names:
                    seen_full_names.add(full_name)
                    discovered_repos.append({
                        "full_name": full_name,
                        "private": bool(r.get("private")),
                        "github_repo_id": r.get("id"),
                    })
            if len(repo_list) < 100:
                break
            page += 1

    # 3. Check which repositories are already added in local DB
    result_repos = []
    with db.get_connection() as conn:
        for r in discovered_repos:
            fn = r["full_name"]
            row = conn.execute("SELECT repo_full_name, visibility, last_synced_at, partial FROM repos WHERE repo_full_name = ?", (fn,)).fetchone()
            added = row is not None
            active_job = None
            if added:
                job_row = conn.execute(
                    "SELECT job_id, status, phase FROM ingest_jobs WHERE repo_full_name = ? ORDER BY created_at DESC LIMIT 1",
                    (fn,)
                ).fetchone()
                if job_row:
                    active_job = {"job_id": job_row["job_id"], "status": job_row["status"], "phase": job_row["phase"]}

            status_val = "added" if added else "available"
            if active_job and active_job["status"] in ("queued", "running"):
                status_val = active_job["status"]

            result_repos.append({
                "full_name": fn,
                "private": r["private"],
                "added": added,
                "status": status_val,
                "active_job": active_job
            })

    return 200, {
        "status": "success",
        "repos": result_repos,
        "install_url": install_url
    }


def add_repository_flow(
    db: Database,
    user_id: int,
    body: Dict[str, Any],
    ssl_context: Optional[ssl.SSLContext] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Handles POST /api/repos:
    - Validates no tokens in body.
    - Validates repo slug.
    - Verifies GitHub App is installed on repo.
    - Creates/updates repos row, creates ingest_jobs row, updates repo_access.
    """
    cfg = get_config()
    slug = cfg.get_github_app_slug() or "context-intelligence-framework"
    install_url = f"https://github.com/apps/{slug}/installations/new"

    # Reject token in payload
    if check_for_forbidden_token_fields(body):
        return 400, {
            "status": "error",
            "message": "Tokens or secrets must never be sent in request body (Rule R4)"
        }

    repo_raw = body.get("repo") or body.get("repo_full_name")
    if not repo_raw or not str(repo_raw).strip():
        return 400, {
            "status": "error",
            "message": "Missing required field 'repo' (expected 'owner/name')"
        }

    repo = str(repo_raw).strip()
    if not RE_REPO_SLUG.match(repo):
        return 400, {
            "status": "error",
            "message": f"Invalid repository format '{repo}'. Must be 'owner/name'"
        }

    tokens = get_user_github_tokens(db, user_id)
    if not tokens or not tokens.get("access_token"):
        return 401, {
            "status": "error",
            "error": "needs_relogin",
            "message": "GitHub access token not available. Please sign in again.",
            "install_url": install_url
        }

    access_token = tokens["access_token"]

    # Verify App installation and access
    # First check via user installations
    disc_status, disc_data = list_user_installable_repos(db, user_id, ssl_context)
    if disc_status == 401:
        return disc_status, disc_data

    matching_repo = None
    if disc_status == 200:
        for r in disc_data.get("repos", []):
            if r["full_name"].lower() == repo.lower():
                matching_repo = r
                break

    # If not found in installation repos, check directly with GitHub API
    is_installed = matching_repo is not None
    repo_visibility = "public"
    github_repo_id = None

    if not is_installed:
        r_status, r_data, _ = _github_get_json(f"https://api.github.com/repos/{repo}", access_token, ssl_context)
        if r_status in (404, 403):
            return 409, {
                "status": "error",
                "error": "app_not_installed",
                "message": f"The CIF GitHub App is not installed on '{repo}' or you lack access.",
                "install_url": install_url
            }
        elif r_status == 200:
            # Accessible on GitHub, but is the App installed?
            # If not in user's installation list, the App is not installed
            return 409, {
                "status": "error",
                "error": "app_not_installed",
                "message": f"The CIF GitHub App is not installed on '{repo}'. Please install the App first.",
                "install_url": install_url
            }
        else:
            return 409, {
                "status": "error",
                "error": "app_not_installed",
                "message": f"Cannot verify App installation on '{repo}'",
                "install_url": install_url
            }
    else:
        repo_visibility = "private" if matching_repo.get("private") else "public"
        github_repo_id = matching_repo.get("github_repo_id")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with db.get_connection() as conn:
        # Upsert repos row
        conn.execute("""
        INSERT INTO repos (repo_full_name, github_repo_id, visibility, added_by_user_id, added_at, partial)
        VALUES (?, ?, ?, ?, ?, 0)
        ON CONFLICT(repo_full_name) DO UPDATE SET
            visibility = excluded.visibility,
            added_by_user_id = excluded.added_by_user_id;
        """, (repo, github_repo_id, repo_visibility, user_id, now_iso))

        # Upsert repo_access row granting review level to adding user
        conn.execute("""
        INSERT INTO repo_access (user_id, repo_full_name, level, verified_at)
        VALUES (?, ?, 'review', ?)
        ON CONFLICT(user_id, repo_full_name) DO UPDATE SET
            level = 'review',
            verified_at = excluded.verified_at;
        """, (user_id, repo, now_iso))

        # Check for existing active job (idempotent / duplicate add reuses active job)
        active_job = conn.execute("""
        SELECT job_id, status FROM ingest_jobs
        WHERE repo_full_name = ? AND status IN ('queued', 'running')
        ORDER BY created_at DESC LIMIT 1;
        """, (repo,)).fetchone()

        if active_job:
            job_id = active_job["job_id"]
        else:
            job_id = f"job_{uuid.uuid4().hex[:12]}"
            conn.execute("""
            INSERT INTO ingest_jobs (job_id, repo_full_name, requested_by, status, phase, progress_json, created_at)
            VALUES (?, ?, ?, 'queued', 'metadata', '{}', ?);
            """, (job_id, repo, user_id, now_iso))

    return 200, {
        "status": "success",
        "job_id": job_id,
        "repo": repo,
        "visibility": repo_visibility,
        "message": f"Repository '{repo}' successfully added. Ingestion job queued."
    }


def get_repo_sync_status(
    db: Database,
    repo_full_name: str
) -> Dict[str, Any]:
    """
    Handles GET /api/repos/status?repo=owner/name:
    Returns { added: bool, partial: bool, last_synced_at, active_job }
    """
    if not repo_full_name or not str(repo_full_name).strip():
        return {
            "status": "error",
            "message": "Query parameter 'repo' is required"
        }

    repo = str(repo_full_name).strip()

    with db.get_connection() as conn:
        repo_row = conn.execute(
            "SELECT repo_full_name, visibility, last_synced_at, partial, stats_json FROM repos WHERE repo_full_name = ?",
            (repo,)
        ).fetchone()

        if not repo_row:
            return {
                "status": "success",
                "repo": repo,
                "added": False,
                "partial": False,
                "last_synced_at": None,
                "active_job": None
            }

        job_row = conn.execute("""
        SELECT job_id, status, phase, progress_json, error_code, created_at, started_at, finished_at
        FROM ingest_jobs
        WHERE repo_full_name = ?
        ORDER BY created_at DESC LIMIT 1;
        """, (repo,)).fetchone()

        active_job = None
        if job_row:
            progress = {}
            if job_row["progress_json"]:
                try:
                    progress = json.loads(job_row["progress_json"])
                except Exception:
                    progress = {}
            active_job = {
                "job_id": job_row["job_id"],
                "status": job_row["status"],
                "phase": job_row["phase"],
                "progress": progress,
                "error_code": job_row["error_code"],
                "created_at": job_row["created_at"],
                "started_at": job_row["started_at"],
                "finished_at": job_row["finished_at"]
            }

        return {
            "status": "success",
            "repo": repo,
            "added": True,
            "visibility": repo_row["visibility"],
            "partial": bool(repo_row["partial"]),
            "last_synced_at": repo_row["last_synced_at"],
            "active_job": active_job
        }
