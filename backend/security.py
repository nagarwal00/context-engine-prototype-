"""
Security and Authorization Module (Step 1.2 / P0-b)
Enforces role-based authorization, CORS origin allowlisting, and request constraints.
"""
import hmac
import os
from typing import Dict, Tuple, Optional

ROLE_VIEWER = "viewer"
ROLE_REVIEWER = "reviewer"
ROLE_ADMIN = "admin"
ROLE_EXEMPT = "exempt"

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
    Returns the origin to echo if it matches CIF_CORS_ORIGINS allowlist.
    Returns None if no allowlist configured or origin not allowed (same-origin only).
    """
    if not origin_header:
        return None
    raw_allowlist = os.environ.get("CIF_CORS_ORIGINS", "").strip()
    if not raw_allowlist:
        return None
    allowed = [o.strip() for o in raw_allowlist.split(",") if o.strip()]
    if origin_header in allowed:
        return origin_header
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


def authorize(
    headers: Dict[str, str],
    required_role: str,
    client_ip: Optional[str] = "127.0.0.1"
) -> Tuple[bool, int, str]:
    """
    Authorizes a request for required_role:
    - viewer / exempt: always allowed (200)
    - dev mode + local client: allowed (200)
    - reviewer: requires CIF_REVIEWER_TOKEN or CIF_ADMIN_TOKEN
    - admin: requires CIF_ADMIN_TOKEN
    Returns (is_authorized, status_code, message).
    """
    if required_role in (ROLE_VIEWER, ROLE_EXEMPT):
        return True, 200, "Authorized"

    if is_dev_mode(client_ip):
        return True, 200, "Authorized (Dev Mode)"

    admin_token = os.environ.get("CIF_ADMIN_TOKEN", "").strip()
    reviewer_token = os.environ.get("CIF_REVIEWER_TOKEN", "").strip()

    # Check if necessary role tokens are configured in environment
    if required_role == ROLE_ADMIN and not admin_token:
        return False, 403, "Role disabled: CIF_ADMIN_TOKEN not configured"
    if required_role == ROLE_REVIEWER and not reviewer_token and not admin_token:
        return False, 403, "Role disabled: CIF_REVIEWER_TOKEN not configured"

    token = extract_bearer_token(headers)
    if not token:
        return False, 401, "Missing or invalid Authorization header (Bearer token required)"

    token_bytes = token.encode("utf-8")

    # Admin token satisfies all roles
    if admin_token and hmac.compare_digest(token_bytes, admin_token.encode("utf-8")):
        return True, 200, "Authorized as admin"

    # Reviewer token satisfies reviewer role
    if required_role == ROLE_REVIEWER and reviewer_token and hmac.compare_digest(token_bytes, reviewer_token.encode("utf-8")):
        return True, 200, "Authorized as reviewer"

    return False, 403, "Forbidden: Invalid token or insufficient permissions"
