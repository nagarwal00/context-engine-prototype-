"""
Security and Authorization Module (Step 7.4 / R2)
Enforces:
- Roles: public, user, repo_read, repo_review, admin
- Session-based user identity & CIF_ADMIN_TOKEN (reviewer token replaced by identity)
- Per-repository authorization and strict data isolation via authorize_repo
- CORS origin allowlisting and request constraints
"""
import hmac
import logging
import os
from typing import Dict, Tuple, Optional, Any, List

from backend.db import Database
from backend.auth.sessions import extract_session_token, get_session
from backend.auth.repo_access import authorize_repo, resolve_repo_for_request

logger = logging.getLogger("cif.security")

# Roles defined in Step 7.4
ROLE_PUBLIC = "public"
ROLE_USER = "user"
ROLE_REPO_READ = "repo_read"
ROLE_REPO_REVIEW = "repo_review"
ROLE_ADMIN = "admin"

# Aliases for backward compatibility
ROLE_VIEWER = ROLE_PUBLIC
ROLE_EXEMPT = ROLE_PUBLIC
ROLE_REVIEWER = ROLE_REPO_REVIEW

MAX_BODY_SIZE = 1024 * 1024  # 1 MB


def is_dev_mode(client_ip: Optional[str] = None) -> bool:
    """Checks whether dev mode is enabled and client is local."""
    dev_flag = os.environ.get("CIF_DEV_MODE", "0").strip() == "1"
    if not dev_flag:
        return False
    if client_ip:
        return client_ip in ("127.0.0.1", "localhost", "::1", "testclient")
    return True


def get_cors_origin(origin_header: Optional[str]) -> Optional[str]:
    """
    Returns the origin to echo if it matches CIF_CORS_ORIGINS allowlist or CIF_EXTENSION_IDS.
    Returns None if no allowlist configured or origin not allowed (same-origin only).
    """
    if not origin_header:
        return None
    raw_allowlist = os.environ.get("CIF_CORS_ORIGINS", "").strip()
    if raw_allowlist:
        allowed = [o.strip() for o in raw_allowlist.split(",") if o.strip()]
        if origin_header in allowed:
            return origin_header

    # Check if origin is an allowlisted Chrome extension ID
    if origin_header.startswith("chrome-extension://"):
        ext_id = origin_header[len("chrome-extension://"):].strip("/").split("/")[0]
        try:
            from backend.config import get_config
            configured_exts = get_config().get_extension_ids()
            if ext_id in configured_exts:
                return origin_header
        except (ImportError, AttributeError, ValueError) as e:
            logger.warning("Failed to check extension ID for CORS origin: %s", e)
            return None

    return None


def extract_bearer_token(headers: Dict[str, str]) -> Optional[str]:
    """Extracts bearer token from Authorization header (case-insensitive key)."""
    auth = None
    for k, v in headers.items():
        if k.lower() == "authorization":
            auth = v
            break
    if not auth:
        return None

    parts = auth.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    if len(parts) == 1 and not parts[0].lower().startswith("bearer"):
        return parts[0]
    return None


def authenticate_caller(
    db: Database,
    headers: Dict[str, str],
    client_ip: Optional[str] = "127.0.0.1"
) -> Tuple[Optional[Dict[str, Any]], bool]:
    """
    Identifies the caller from request headers:
    Returns (user_dict_or_None, is_admin_bool).
    """
    admin_token = os.environ.get("CIF_ADMIN_TOKEN", "").strip()
    bearer = extract_bearer_token(headers)

    # Check CIF_ADMIN_TOKEN
    if bearer and admin_token and hmac.compare_digest(bearer.encode("utf-8"), admin_token.encode("utf-8")):
        return {"user_id": 0, "login": "admin", "is_admin": True}, True

    # Check CIF session token (via cookie or Bearer session token)
    raw_session_token, _ = extract_session_token(headers)
    if raw_session_token:
        session = get_session(db, raw_session_token)
        if session:
            user = {
                "user_id": session["user_id"],
                "login": session["login"],
                "avatar_url": session.get("avatar_url"),
                "is_admin": False,
            }
            return user, False

    # Dev mode fallback for local administrative tasks
    if is_dev_mode(client_ip):
        return {"user_id": 0, "login": "dev_user", "is_admin": True}, True

    return None, False


def authorize(
    headers: Dict[str, str],
    required_role: str,
    client_ip: Optional[str] = "127.0.0.1",
    db: Optional[Database] = None,
    path: Optional[str] = None,
    query_params: Optional[Dict[str, List[str]]] = None,
    body_json: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, int, str]:
    """
    Enforces Step 7.4 role requirements:
    - public: always allowed.
    - admin: requires CIF_ADMIN_TOKEN.
    - user: requires valid signed-in CIF user.
    - repo_read / repo_review: calls authorize_repo on the resolved repository.
    """
    if required_role in (ROLE_PUBLIC, "exempt"):
        return True, 200, "Authorized"

    # Authenticate caller
    if db is None:
        # Fallback for simple token tests without DB
        admin_token = os.environ.get("CIF_ADMIN_TOKEN", "").strip()
        bearer = extract_bearer_token(headers)
        if bearer and admin_token and hmac.compare_digest(bearer.encode("utf-8"), admin_token.encode("utf-8")):
            return True, 200, "Authorized as admin"
        if required_role == ROLE_ADMIN:
            return False, 403, "Role disabled or invalid token: CIF_ADMIN_TOKEN required"
        if is_dev_mode(client_ip):
            return True, 200, "Authorized (Dev Mode)"
        return False, 401, "Authentication required"

    user, is_admin = authenticate_caller(db, headers, client_ip)

    if is_admin:
        return True, 200, "Authorized as admin"

    if required_role == ROLE_ADMIN:
        return False, 403, "Admin permission required"

    bearer = extract_bearer_token(headers)
    raw_session, _ = extract_session_token(headers)

    if required_role == ROLE_USER:
        if not user:
            return False, 401, "Sign-in required or session expired"
        return True, 200, "Authorized"

    if required_role == ROLE_REPO_REVIEW:
        if not user:
            if bearer or raw_session:
                return False, 403, "Invalid token or session"
            return False, 401, "Authentication required"
        repo_name = resolve_repo_for_request(db, path or "", query_params, body_json)
        if not repo_name:
            return False, 404, "Repository not found or could not be determined"
        return authorize_repo(db, user, repo_name, required_role)

    if required_role == ROLE_REPO_READ:
        repo_name = resolve_repo_for_request(db, path or "", query_params, body_json)
        if not repo_name:
            if not user and (bearer or raw_session):
                return False, 403, "Invalid token or session"
            return False, 404, "Repository not found or could not be determined"
        return authorize_repo(db, user, repo_name, required_role)

    return False, 403, f"Unknown role requirement: {required_role}"



def get_authenticated_role(
    headers: Optional[Dict[str, str]] = None,
    client_ip: Optional[str] = "127.0.0.1",
    db: Optional[Database] = None
) -> str:
    """Returns the authenticated role for the request: 'admin', 'reviewer', or 'viewer'."""
    headers = headers or {}
    admin_token = os.environ.get("CIF_ADMIN_TOKEN", "").strip()
    token = extract_bearer_token(headers)
    if token and admin_token and hmac.compare_digest(token.encode("utf-8"), admin_token.encode("utf-8")):
        return ROLE_ADMIN

    if db:
        user, is_admin = authenticate_caller(db, headers, client_ip)
        if is_admin:
            return ROLE_ADMIN
        if user:
            return ROLE_REVIEWER

    raw_session_token, _ = extract_session_token(headers)
    if raw_session_token:
        return ROLE_REVIEWER

    if is_dev_mode(client_ip):
        return ROLE_ADMIN

    return ROLE_VIEWER

