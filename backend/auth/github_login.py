"""
GitHub OAuth Login Flow for CIF (Step 7.3)
Implements:
- GET /auth/github/login (web & extension client support, next_path validation, PKCE/state)
- GET /auth/github/callback (single-use 10-minute state check, token exchange, user upsert, session creation)
- Extension redirect with 60-second one-time code to chromiumapp.org
- Web client redirect with HttpOnly, SameSite=Lax cookie
- Automatic token refresh on 401 or near expiry
"""
import datetime
import json
import logging
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional, Tuple, List

from backend.config import get_config
from backend.db import Database
from backend.auth.sessions import (
    create_session,
    create_extension_code,
    hash_token,
    generate_token,
    parse_iso,
    store_user_github_tokens,
    get_user_github_tokens,
)

logger = logging.getLogger("cif.auth.github")


def get_secure_ssl_context() -> ssl.SSLContext:
    """Creates a strictly verified SSL context (Step 1.1 / P0-a)."""
    ca_bundle = os.environ.get("CIF_CA_BUNDLE")
    if ca_bundle and os.path.exists(ca_bundle):
        return ssl.create_default_context(cafile=ca_bundle)
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass

    # Auto-detect certifi bundle from Windows user cache if not on sys.path
    win_local = os.environ.get("LOCALAPPDATA", "")
    if win_local:
        candidates = [
            os.path.join(win_local, "Packages", "PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0", "LocalCache", "local-packages", "Python311", "site-packages", "certifi", "cacert.pem"),
            os.path.join(win_local, "Programs", "Python", "Python311", "Lib", "site-packages", "certifi", "cacert.pem"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return ssl.create_default_context(cafile=c)

    ctx = ssl.create_default_context()
    if hasattr(ssl, "enum_certificates"):
        try:
            for store in ("ROOT", "CA"):
                for cert, encoding, trust in ssl.enum_certificates(store):
                    if encoding == "x509_asn":
                        ctx.load_verify_locations(cdata=cert)
        except Exception:
            pass
    return ctx


def validate_next_path(next_path: Optional[str]) -> str:
    """
    Validates next redirect path:
    Must start with '/' and NOT with '//' to prevent open redirect vulnerabilities.
    Defaults to '/repos'.
    """
    if not next_path:
        return "/repos"
    cleaned = next_path.strip()
    if not cleaned.startswith("/") or cleaned.startswith("//") or "\\" in cleaned:
        raise ValueError(f"Invalid next_path redirect: {next_path!r}")
    return cleaned


def _auth_error(status: int, code: str, message: str) -> Tuple[int, str, Dict[str, str]]:
    """Refusal with a machine-readable code (server.py turns it into a login-page message).

    Never sets a cookie: a failed GitHub sign-in must not create any session.
    """
    return status, message, {"X-CIF-Auth-Error": code}


def initiate_github_login(
    db: Database,
    next_path: Optional[str] = None,
    client: str = "web",
    ext_id: Optional[str] = None
) -> Tuple[int, str, Dict[str, str]]:
    """
    Initiates GitHub OAuth flow:
    - Validates next_path and ext_id (if client == 'extension')
    - Generates 32-byte cryptographically secure random state
    - Stores SHA-256 of state in oauth_states (10-minute TTL)
    - Returns (302, redirect_url, headers)
    """
    try:
        valid_next = validate_next_path(next_path)
    except ValueError as e:
        return _auth_error(400, "INVALID_NEXT", str(e))

    cfg = get_config()
    if not cfg.is_login_enabled():
        # Previously a web client was silently signed in as "demo-developer" here, so "Continue with
        # GitHub" appeared to work without GitHub. The demo account has its own explicit button.
        return _auth_error(503, "GITHUB_NOT_CONFIGURED",
                           "GitHub sign-in is not configured on this server: set GITHUB_CLIENT_ID and "
                           "GITHUB_CLIENT_SECRET (or GITHUB_APP_CLIENT_ID / GITHUB_APP_CLIENT_SECRET) and restart.")

    client = (client or "web").lower().strip()
    if client == "extension":
        if not ext_id or not cfg.is_extension_id_allowed(ext_id):
            return 400, f"Unauthorized extension ID: {ext_id!r}", {}
    elif client == "vscode":
        ext_id = (ext_id or "cif.cif-vscode").strip()
        if not cfg.is_vscode_extension_allowed(ext_id):
            return 400, f"Unauthorized VS Code extension ID: {ext_id!r}", {}
    else:
        ext_id = None

    # Generate 32-byte urlsafe state
    raw_state = generate_token(32)
    state_hash = hash_token(raw_state)
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with db.get_connection() as conn:
        conn.execute("""
        INSERT INTO oauth_states (state_hash, created_at, next_path, client, ext_id)
        VALUES (?, ?, ?, ?, ?);
        """, (state_hash, created_at, valid_next, client, ext_id))

    redirect_uri = cfg.get_github_callback_url()

    params = {
        "client_id": cfg.get_github_client_id(),
        "redirect_uri": redirect_uri,
        "state": raw_state,
    }
    auth_url = f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"
    headers = {"Location": auth_url}
    return 302, auth_url, headers


def handle_github_callback(
    db: Database,
    query_params: Dict[str, List[str]],
    ssl_context: Optional[ssl.SSLContext] = None
) -> Tuple[int, str, Dict[str, str]]:
    """
    Handles OAuth callback from GitHub:
    - Validates state against oauth_states (single use, <= 10 min lifetime)
    - Deletes state immediately
    - Exchanges code for user access_token and refresh_token
    - Fetches GitHub user profile
    - Upserts users table and stores GitHub tokens
    - Issues CIF session (web cookie or extension redirect with one-time code)
    """
    cfg = get_config()
    code = query_params.get("code", [None])[0]
    raw_state = query_params.get("state", [None])[0]
    error = query_params.get("error", [None])[0]

    if error:
        error_desc = query_params.get("error_description", [error])[0]
        logger.warning("GitHub OAuth returned error: %s", error)
        if raw_state:  # consume the state so it cannot be replayed
            with db.get_connection() as conn:
                conn.execute("DELETE FROM oauth_states WHERE state_hash = ?", (hash_token(raw_state.strip()),))
        if error == "access_denied":
            return _auth_error(403, "ACCESS_DENIED", "GitHub sign-in was cancelled: access was not authorized.")
        if error == "redirect_uri_mismatch":
            return _auth_error(400, "CALLBACK_MISMATCH",
                               f"GitHub rejected the callback URL. Register exactly {cfg.get_github_callback_url()} "
                               "as the Authorization callback URL of your GitHub OAuth app.")
        return _auth_error(400, "GITHUB_AUTH_ERROR", f"GitHub authentication error: {error_desc}")

    if not code or not raw_state:
        return _auth_error(400, "MISSING_PARAMETERS", "Missing required OAuth callback parameters (code, state)")

    state_hash = hash_token(raw_state.strip())
    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. State lookup and immediate single-use deletion
    with db.get_connection() as conn:
        row = conn.execute("""
        SELECT state_hash, created_at, next_path, client, ext_id
        FROM oauth_states
        WHERE state_hash = ?;
        """, (state_hash,)).fetchone()

        if not row:
            return _auth_error(400, "INVALID_STATE", "Invalid or already-used OAuth state. Start the sign-in again.")

        # Delete immediately so it cannot be reused
        conn.execute("DELETE FROM oauth_states WHERE state_hash = ?", (state_hash,))

        created_at = parse_iso(row["created_at"])
        if (now - created_at).total_seconds() > 600.0:  # 10 minutes
            return _auth_error(400, "STATE_EXPIRED", "The sign-in took longer than 10 minutes. Start it again.")

        next_path = row["next_path"] or "/repos"
        client = row["client"]
        ext_id = row["ext_id"]

    # 2. Exchange code for access_token with GitHub
    ctx = ssl_context or get_secure_ssl_context()
    token_url = "https://github.com/login/oauth/access_token"
    token_data = urllib.parse.urlencode({
        "client_id": cfg.get_github_client_id(),
        "client_secret": cfg.get_github_client_secret(),
        "code": code,
        "redirect_uri": cfg.get_github_callback_url(),
    }).encode("utf-8")

    req = urllib.request.Request(
        token_url,
        data=token_data,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
        method="POST"
    )

    token_resp = None
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            token_resp = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("GitHub token exchange failed (network): %s", type(exc).__name__)
        return _auth_error(503, "GITHUB_UNAVAILABLE", "Could not reach GitHub to complete sign-in. Try again shortly.")
    except ValueError:
        return _auth_error(502, "TOKEN_EXCHANGE_FAILED", "GitHub returned an unreadable response during sign-in.")

    # Previously any failure here signed a web user in as "demo-developer". Now: no session, clear reason.
    if not isinstance(token_resp, dict) or token_resp.get("error") or not token_resp.get("access_token"):
        gh_error = token_resp.get("error", "") if isinstance(token_resp, dict) else ""
        logger.warning("GitHub token exchange rejected: %s", gh_error or "no access_token")
        if gh_error == "bad_verification_code":
            return _auth_error(400, "INVALID_CODE", "The GitHub authorization code is invalid or has expired. Sign in again.")
        if gh_error == "redirect_uri_mismatch":
            return _auth_error(400, "CALLBACK_MISMATCH",
                               f"GitHub rejected the callback URL. Register exactly {cfg.get_github_callback_url()} "
                               "as the Authorization callback URL of your GitHub OAuth app.")
        if gh_error == "incorrect_client_credentials":
            return _auth_error(502, "INVALID_APP_CREDENTIALS",
                               "GitHub rejected this server's client ID or client secret. Check the OAuth app credentials.")
        return _auth_error(502, "TOKEN_EXCHANGE_FAILED", f"GitHub sign-in failed ({gh_error or 'no access token returned'}).")

    access_token = token_resp.get("access_token")
    refresh_token = token_resp.get("refresh_token")
    expires_in = token_resp.get("expires_in", 28800)

    # 3. Fetch user profile from GitHub API
    user_req = urllib.request.Request(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
    )

    try:
        with urllib.request.urlopen(user_req, context=ctx, timeout=30) as resp:
            user_data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        # Previously an invented user ("github-user", id 999999) was signed in here.
        logger.warning("Failed to fetch user profile from GitHub: %s", type(exc).__name__)
        return _auth_error(502, "PROFILE_FAILED", "Signed in at GitHub, but your GitHub profile could not be read. Try again.")

    github_id = user_data.get("id") if isinstance(user_data, dict) else None
    login = user_data.get("login") if isinstance(user_data, dict) else None
    avatar_url = user_data.get("avatar_url", "") if isinstance(user_data, dict) else ""

    if not github_id or not login:
        return _auth_error(502, "PROFILE_FAILED", "GitHub returned an incomplete user profile.")

    # 4. Upsert user in database
    now_iso = now.isoformat()
    with db.get_connection() as conn:
        conn.execute("""
        INSERT INTO users (github_id, login, avatar_url, created_at, last_login_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(github_id) DO UPDATE SET
            login = excluded.login,
            avatar_url = excluded.avatar_url,
            last_login_at = excluded.last_login_at;
        """, (github_id, login, avatar_url, now_iso, now_iso))

        user_row = conn.execute("SELECT user_id FROM users WHERE github_id = ?", (github_id,)).fetchone()
        user_id = user_row["user_id"]

    # 5. Store GitHub tokens
    store_user_github_tokens(db, user_id, access_token, refresh_token, expires_in)

    # 6. Create CIF session
    try:
        raw_session_token, _ = create_session(db, user_id, client=client)
    except Exception:
        logger.exception("Could not create a session after GitHub sign-in")
        return _auth_error(500, "SESSION_FAILED", "Signed in at GitHub, but the session could not be created.")

    # 7. Response delivery
    base_url = cfg.get_base_url()
    if client == "extension":
        one_time_code = create_extension_code(db, raw_session_token)
        ext_redirect = f"https://{ext_id}.chromiumapp.org/cb?code={one_time_code}"
        return 302, ext_redirect, {"Location": ext_redirect}
    elif client == "vscode":
        one_time_code = create_extension_code(db, raw_session_token)
        vscode_redirect = f"vscode://{ext_id}/auth?code={one_time_code}"
        return 302, vscode_redirect, {"Location": vscode_redirect}

    # Web client: Set-Cookie and redirect to next_path
    cookie_str = f"cif_session={raw_session_token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800"
    if base_url.lower().startswith("https://"):
        cookie_str += "; Secure"

    redirect_target = f"{base_url}{next_path}" if next_path.startswith("/") else next_path
    headers = {
        "Location": redirect_target,
        "Set-Cookie": cookie_str,
    }
    return 302, redirect_target, headers


def refresh_github_token(
    db: Database,
    user_id: int,
    ssl_context: Optional[ssl.SSLContext] = None
) -> Tuple[bool, Optional[str]]:
    """
    Refreshes an expiring or 401'd user token using grant_type=refresh_token.
    On failure, clears user tokens and returns (False, None) signaling 'needs_relogin'.
    """
    tokens = get_user_github_tokens(db, user_id)
    if not tokens or not tokens.get("refresh_token"):
        return False, None

    cfg = get_config()
    ctx = ssl_context or get_secure_ssl_context()
    token_url = "https://github.com/login/oauth/access_token"
    payload = json.dumps({
        "client_id": cfg.get_github_client_id(),
        "client_secret": cfg.get_github_client_secret(),
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
    }).encode("utf-8")

    req = urllib.request.Request(
        token_url,
        data=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "CIF-Backend",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return False, None

    if "error" in data or not data.get("access_token"):
        return False, None

    new_access = data["access_token"]
    new_refresh = data.get("refresh_token", tokens["refresh_token"])
    expires_in = data.get("expires_in", 28800)

    store_user_github_tokens(db, user_id, new_access, new_refresh, expires_in)
    return True, new_access
