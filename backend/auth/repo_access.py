"""
Identity-Based Authorization and Repository Scoping (Step 7.4)
Implements:
- authorize_repo(user, repo_full_name, need)
  - demo repos: readable by everyone (anonymous included); no writes.
  - non-demo repos: requires verified repo_access row (15-min TTL for private, 1-hr for public).
  - stale rows re-verified via GET /repos/{owner}/{repo} with user's GitHub token.
  - repo_review requires verified permissions.push (or fallback to repo owner + repo_reviewers).
- resolve_repo_for_request(db, path, query_params, body_json)
  - extracts repo from parameter or resolves from entity/decision/finding/event ID.
- list_accessible_repos(db, user)
  - returns only repositories caller is authorized to view.
- add_repo_reviewer(db, owner_user_id, repo_full_name, reviewer_user_id)
"""
import datetime
import json
import logging
import ssl
import urllib.error
import urllib.request
from typing import Dict, Any, Optional, Tuple, List

from backend.db import Database
from backend.auth.sessions import (
    parse_iso,
    get_user_github_tokens,
)
from backend.auth.github_login import get_secure_ssl_context, refresh_github_token

logger = logging.getLogger("cif.auth.repo")


def authorize_repo(
    db: Database,
    user: Optional[Dict[str, Any]],
    repo_full_name: Optional[str],
    need: str,
    ssl_context: Optional[ssl.SSLContext] = None
) -> Tuple[bool, int, str]:
    """
    Authorizes caller access to repository repo_full_name for need in ('repo_read', 'repo_review'):
    - Demo repos: readable by anyone (including anonymous); review/writes denied for non-admin.
    - Private / Public repos: requires verified access row or active GitHub permission.
    - Stale permissions are re-verified with GitHub API using user's token.
    - If user has no valid token, returns 401 with needs_relogin.
    """
    if not repo_full_name or not str(repo_full_name).strip():
        return False, 400, "Repository name is required"

    repo_full_name = str(repo_full_name).strip()

    # Admin callers always bypass repo isolation
    if user and user.get("is_admin"):
        return True, 200, "Authorized as admin"

    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT repo_full_name, visibility, added_by_user_id FROM repos WHERE repo_full_name = ?",
            (repo_full_name,)
        ).fetchone()

        if not row:
            # Check if it is a known demo repository
            if repo_full_name in ("acme-eng/thermal-control-system", "acme-eng/distributed-cache-service"):
                now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                conn.execute(
                    "INSERT OR IGNORE INTO repos (repo_full_name, visibility, added_at, partial) VALUES (?, 'demo', ?, 0)",
                    (repo_full_name, now_iso)
                )
                visibility = "demo"
                added_by_user_id = None
            else:
                return False, 404, f"Repository not found: {repo_full_name}"
        else:
            visibility = row["visibility"]
            added_by_user_id = row["added_by_user_id"]

    # 1. Demo Repositories
    if visibility == "demo":
        if need == "repo_read":
            return True, 200, "Authorized (demo repo)"
        elif need == "repo_review":
            return False, 403, "Writes and reviews are disabled on demo repositories"
        return False, 400, f"Invalid need: {need}"

    # 2. Non-demo repositories (public or private added by users)
    if not user:
        return False, 401, "Authentication required to access this repository"

    user_id = user["user_id"]

    # Allow if user has an explicit row in repo_reviewers for that repo
    with db.get_connection() as conn:
        rev_row = conn.execute(
            "SELECT 1 FROM repo_reviewers WHERE repo_full_name = ? AND user_id = ?",
            (repo_full_name, user_id)
        ).fetchone()

    if rev_row:
        return True, 200, "Authorized as reviewer"

    now = datetime.datetime.now(datetime.timezone.utc)
    # TTL: 15 minutes for private repos, 1 hour for public repos
    ttl_seconds = 900.0 if visibility == "private" else 3600.0

    with db.get_connection() as conn:
        acc = conn.execute(
            "SELECT level, verified_at FROM repo_access WHERE user_id = ? AND repo_full_name = ?",
            (user_id, repo_full_name)
        ).fetchone()

    # Otherwise require a row in repo_access
    if not acc:
        return False, 403, f"Access denied to repository: {repo_full_name}"

    cached_level = acc["level"]
    needs_recheck = False
    verified_at = parse_iso(acc["verified_at"])
    if (now - verified_at).total_seconds() > ttl_seconds:
        needs_recheck = True

    if needs_recheck:
        tokens = get_user_github_tokens(db, user_id)
        if not tokens or not tokens.get("access_token"):
            ok, new_token = refresh_github_token(db, user_id, ssl_context=ssl_context)
            if not ok or not new_token:
                return False, 401, json.dumps({"error": "needs_relogin"})
            tokens = {"access_token": new_token}

        access_token = tokens["access_token"]
        ctx = ssl_context or get_secure_ssl_context()
        url = f"https://api.github.com/repos/{repo_full_name}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "CIF-Backend",
            }
        )

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                gh_code = getattr(resp, "status", getattr(resp, "code", 200))
        except urllib.error.HTTPError as err:
            gh_code = err.code
            data = {}
        except Exception as exc:
            logger.error("GitHub API error checking repo access: %s", type(exc).__name__)
            return False, 502, "Failed to verify repository permissions with GitHub"

        if gh_code == 200:
            permissions = data.get("permissions")
            if isinstance(permissions, dict):
                push_perm = bool(permissions.get("push") or permissions.get("admin") or permissions.get("maintain"))
                level = "review" if push_perm else "read"
            else:
                is_adder = (added_by_user_id == user_id)
                level = "review" if is_adder else "read"

            now_iso = now.isoformat()
            with db.get_connection() as conn:
                conn.execute("""
                INSERT INTO repo_access (user_id, repo_full_name, level, verified_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, repo_full_name) DO UPDATE SET
                    level = excluded.level,
                    verified_at = excluded.verified_at;
                """, (user_id, repo_full_name, level, now_iso))
            cached_level = level

        elif gh_code in (403, 404):
            # Access revoked or repo not accessible
            with db.get_connection() as conn:
                conn.execute("DELETE FROM repo_access WHERE user_id = ? AND repo_full_name = ?", (user_id, repo_full_name))
            return False, 403, f"Access denied on GitHub for repository: {repo_full_name}"
        else:
            return False, gh_code, f"GitHub API error: {gh_code}"

    # Evaluate required need
    if need == "repo_read":
        return True, 200, "Authorized"
    elif need == "repo_review":
        if cached_level in ("review", "admin"):
            return True, 200, "Authorized"
        return False, 403, "Review permission (push access) required for this repository"

    return False, 400, f"Unknown permission need: {need}"


def resolve_repo_for_request(
    db: Database,
    path: str,
    query_params: Optional[Dict[str, List[str]]] = None,
    body_json: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Extracts or resolves repo_full_name for any API request:
    1. Direct repo query parameter or JSON body field.
    2. Resolution from decision_id / target_id.
    3. Resolution from artifact / entity canonical path.
    4. Resolution from rule_id (guard_rules).
    5. Resolution from finding_id (ambiguous_findings).
    6. Default to first demo repository for legacy demo endpoints with no parameters.
    """
    query_params = query_params or {}
    body_json = body_json or {}

    # 1. Direct parameter
    direct_repo = query_params.get("repo", [None])[0] or body_json.get("repo") or body_json.get("repo_full_name")
    if direct_repo and str(direct_repo).strip():
        return str(direct_repo).strip()

    with db.get_connection() as conn:
        # 2. Decision ID or target ID
        dec_id = (
            query_params.get("decision_id", [None])[0]
            or body_json.get("decision_id")
            or body_json.get("target_id")
        )
        if dec_id:
            row = conn.execute("SELECT repo FROM decisions WHERE decision_id = ?", (dec_id,)).fetchone()
            if row:
                return row["repo"]

        # 3. Artifact / entity
        art = query_params.get("artifact", [None])[0] or body_json.get("artifact")
        if art:
            row = conn.execute(
                "SELECT repo FROM entities WHERE canonical_path = ? OR entity_id = ?",
                (art, art)
            ).fetchone()
            if row:
                return row["repo"]

        # 4. Guard Rule ID
        rule_id = body_json.get("rule_id") or query_params.get("rule_id", [None])[0]
        if rule_id:
            row = conn.execute("""
            SELECT d.repo
            FROM guard_rules g
            JOIN decisions d ON g.decision_id = d.decision_id
            WHERE g.rule_id = ?;
            """, (rule_id,)).fetchone()
            if row:
                return row["repo"]

        # 5. Finding ID
        finding_id = body_json.get("finding_id") or query_params.get("finding_id", [None])[0]
        if finding_id:
            row = conn.execute("SELECT repo FROM ambiguous_findings WHERE finding_id = ?", (finding_id,)).fetchone()
            if row:
                return row["repo"]

        # 6. Event ID
        event_id = query_params.get("event_id", [None])[0] or body_json.get("event_id")
        if event_id:
            row = conn.execute("SELECT repo FROM events WHERE event_id = ?", (event_id,)).fetchone()
            if row:
                return row["repo"]

    # Endpoints that default to demo repo when no repo is supplied
    demo_defaults = (
        "/api/timeline",
        "/api/graph",
        "/api/artifacts",
        "/api/decisions",
        "/api/evidence",
        "/api/review-queue",
        "/api/benchmark",
        "/api/stats",
        "/api/guard-rules",
        "/api/decision-history",
        "/api/as-of",
        "/api/findings/feedback",
        "/api/bus-factor",
        "/api/onboarding",
    )
    if path in demo_defaults:
        return "acme-eng/thermal-control-system"

    return None


def list_accessible_repos(db: Database, user: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Returns list of repositories accessible to caller:
    - Anonymous: only visibility='demo' repositories.
    - Signed-in: demo repos + repos user added + repos where user has cached repo_access.
    - Admin: all repositories.
    """
    with db.get_connection() as conn:
        if user and user.get("is_admin"):
            rows = conn.execute("SELECT * FROM repos ORDER BY visibility DESC, repo_full_name ASC").fetchall()
            return [dict(r) for r in rows]

        if not user:
            rows = conn.execute("SELECT * FROM repos WHERE visibility = 'demo' ORDER BY repo_full_name ASC").fetchall()
            return [dict(r) for r in rows]

        user_id = user["user_id"]
        rows = conn.execute("""
        SELECT DISTINCT r.*
        FROM repos r
        LEFT JOIN repo_access a ON r.repo_full_name = a.repo_full_name AND a.user_id = ?
        WHERE r.visibility = 'demo'
           OR r.added_by_user_id = ?
           OR a.user_id = ?
        ORDER BY r.visibility DESC, r.repo_full_name ASC;
        """, (user_id, user_id, user_id)).fetchall()
        return [dict(r) for r in rows]


def add_repo_reviewer(
    db: Database,
    owner_user_id: int,
    repo_full_name: str,
    reviewer_user_id: int
) -> bool:
    """Adds a user to repo_reviewers table. Restricted to repo adder or admin."""
    with db.get_connection() as conn:
        repo_row = conn.execute("SELECT added_by_user_id FROM repos WHERE repo_full_name = ?", (repo_full_name,)).fetchone()
        if not repo_row or repo_row["added_by_user_id"] != owner_user_id:
            return False

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute("""
        INSERT OR REPLACE INTO repo_reviewers (repo_full_name, user_id, added_by, added_at)
        VALUES (?, ?, ?, ?);
        """, (repo_full_name, reviewer_user_id, owner_user_id, now_iso))
        return True
