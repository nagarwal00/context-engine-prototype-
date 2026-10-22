"""
Sessions and Token Management (Step 7.3)
Implements:
- 32-byte cryptographic random session tokens, hashed with SHA-256 at rest
- 7-day session lifetime with 24-hour sliding idle timeout
- One-time extension authorization codes (60-second lifetime, single-use)
- Encrypted user token storage at rest (R1) or in-memory fallback
- CSRF validation and cookie helper utilities
"""
import datetime
import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
import time
from typing import Dict, Any, Optional, Tuple, List
from urllib.parse import urlparse

from backend.db import Database
from backend.config import get_config

# Optional Rule R1 cryptography import
try:
    from cryptography.fernet import Fernet
    _CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    Fernet = None
    _CRYPTOGRAPHY_AVAILABLE = False


# In-memory storage for pending extension codes -> (raw_session_token, expiry_ts)
_PENDING_EXT_CODES: Dict[str, Tuple[str, float]] = {}
_EXT_CODES_LOCK = threading.Lock()

# In-memory fallback for user GitHub tokens when cryptography/enc_key is unavailable
# user_id -> { "access_token": str, "refresh_token": str, "expires_at": float }
_USER_GITHUB_TOKENS: Dict[int, Dict[str, Any]] = {}
_USER_TOKENS_LOCK = threading.Lock()


def hash_token(token: str) -> str:
    """Returns SHA-256 hex digest of a token string."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token(nbytes: int = 32) -> str:
    """Generates a cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(nbytes)


def parse_iso(ts_str: str) -> datetime.datetime:
    """Parses an ISO datetime string into a timezone-aware UTC datetime."""
    # Replace trailing Z with +00:00 for fromisoformat compatibility
    cleaned = ts_str.replace("Z", "+00:00")
    dt = datetime.datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def create_session(db: Database, user_id: int, client: str = "web") -> Tuple[str, Dict[str, Any]]:
    """
    Creates a new CIF session for user_id.
    Stores only the SHA-256 hash in the database.
    Returns (raw_session_token, session_info).
    """
    raw_token = generate_token(32)
    session_hash = hash_token(raw_token)
    now = datetime.datetime.now(datetime.timezone.utc)
    created_at = now.isoformat()
    expires_at = (now + datetime.timedelta(days=7)).isoformat()
    last_seen_at = created_at

    with db.get_connection() as conn:
        conn.execute("""
        INSERT INTO sessions (session_hash, user_id, client, created_at, expires_at, last_seen_at)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (session_hash, user_id, client, created_at, expires_at, last_seen_at))

    return raw_token, {
        "session_hash": session_hash,
        "user_id": user_id,
        "client": client,
        "created_at": created_at,
        "expires_at": expires_at,
        "last_seen_at": last_seen_at,
    }


def get_session(db: Database, raw_token: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Retrieves and validates a session by raw session token:
    - Verifies 7-day expiry and 24-hour idle timeout
    - Updates sliding last_seen_at on activity
    - Returns joined user information
    """
    if not raw_token or not raw_token.strip():
        return None

    session_hash = hash_token(raw_token.strip())
    now = datetime.datetime.now(datetime.timezone.utc)

    with db.get_connection() as conn:
        row = conn.execute("""
        SELECT s.session_hash, s.user_id, s.client, s.created_at, s.expires_at, s.last_seen_at,
               u.github_id, u.login, u.avatar_url
        FROM sessions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.session_hash = ?;
        """, (session_hash,)).fetchone()

        if not row:
            return None

        # Check total expiration (7 days)
        expires_at = parse_iso(row["expires_at"])
        if now > expires_at:
            conn.execute("DELETE FROM sessions WHERE session_hash = ?", (session_hash,))
            return None

        # Check idle timeout (24 hours)
        last_seen_at = parse_iso(row["last_seen_at"])
        if (now - last_seen_at).total_seconds() > (24 * 3600):
            conn.execute("DELETE FROM sessions WHERE session_hash = ?", (session_hash,))
            return None

        # Update sliding last_seen_at
        now_iso = now.isoformat()
        conn.execute("UPDATE sessions SET last_seen_at = ? WHERE session_hash = ?", (now_iso, session_hash))

        return {
            "session_hash": row["session_hash"],
            "user_id": row["user_id"],
            "client": row["client"],
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "last_seen_at": now_iso,
            "github_id": row["github_id"],
            "login": row["login"],
            "avatar_url": row["avatar_url"],
        }


def delete_session(db: Database, raw_token: Optional[str]) -> bool:
    """Deletes a session row on logout."""
    if not raw_token:
        return False
    session_hash = hash_token(raw_token.strip())
    with db.get_connection() as conn:
        cur = conn.execute("DELETE FROM sessions WHERE session_hash = ?", (session_hash,))
        return cur.rowcount > 0


def create_extension_code(db: Database, raw_session_token: str) -> str:
    """
    Creates a single-use one-time code for the Chrome extension (60-second lifetime).
    Stores only code_hash in the database bound to session_hash.
    Keeps raw_session_token in an in-memory pending exchange map for 60 seconds.
    """
    raw_code = generate_token(32)
    code_hash = hash_token(raw_code)
    session_hash = hash_token(raw_session_token)
    now = datetime.datetime.now(datetime.timezone.utc)
    created_at = now.isoformat()

    with db.get_connection() as conn:
        conn.execute("""
        INSERT INTO ext_codes (code_hash, session_hash, created_at)
        VALUES (?, ?, ?);
        """, (code_hash, session_hash, created_at))

    with _EXT_CODES_LOCK:
        _clean_expired_ext_codes()
        _PENDING_EXT_CODES[code_hash] = (raw_session_token, time.time() + 60.0)

    return raw_code


def exchange_extension_code(db: Database, raw_code: str) -> Optional[Dict[str, Any]]:
    """
    Exchanges a one-time extension code for the raw session token.
    Single-use: deletes the code from database and in-memory store immediately.
    Rejects reused or expired codes (> 60 seconds).
    """
    if not raw_code or not raw_code.strip():
        return None

    code_hash = hash_token(raw_code.strip())
    now = datetime.datetime.now(datetime.timezone.utc)

    with _EXT_CODES_LOCK:
        _clean_expired_ext_codes()
        pending = _PENDING_EXT_CODES.pop(code_hash, None)

    with db.get_connection() as conn:
        row = conn.execute("SELECT code_hash, session_hash, created_at FROM ext_codes WHERE code_hash = ?", (code_hash,)).fetchone()
        if not row:
            return None

        # Always delete immediately (single use)
        conn.execute("DELETE FROM ext_codes WHERE code_hash = ?", (code_hash,))

        # Check 60-second lifetime
        created_at = parse_iso(row["created_at"])
        if (now - created_at).total_seconds() > 60.0:
            return None

        if not pending or pending[1] < time.time():
            return None

        raw_session_token = pending[0]

        # Verify session is still valid and fetch user details
        sess_row = conn.execute("""
            SELECT s.expires_at, u.login, u.avatar_url
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.session_hash = ?
        """, (row["session_hash"],)).fetchone()
        if not sess_row:
            return None

        return {
            "token": raw_session_token,
            "expires_at": sess_row["expires_at"],
            "login": sess_row["login"],
            "avatar_url": sess_row["avatar_url"],
        }


def _clean_expired_ext_codes():
    """Removes expired pending extension codes from the in-memory map."""
    now_ts = time.time()
    expired = [k for k, v in _PENDING_EXT_CODES.items() if v[1] < now_ts]
    for k in expired:
        _PENDING_EXT_CODES.pop(k, None)


# --- User GitHub Token Storage (Rule R1) ---

def store_user_github_tokens(
    db: Database,
    user_id: int,
    access_token: str,
    refresh_token: Optional[str] = None,
    expires_in_seconds: int = 28800
) -> None:
    """
    Stores GitHub user-to-server tokens:
    - If cryptography and CIF_TOKEN_ENC_KEY are configured, encrypts and writes to user_tokens.
    - Otherwise keeps tokens only in memory (a dict protected by a lock).
    """
    cfg = get_config()
    enc_key = cfg.get_token_enc_key()
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = (now + datetime.timedelta(seconds=expires_in_seconds)).isoformat()

    if _CRYPTOGRAPHY_AVAILABLE and enc_key:
        try:
            # Fernet key must be 32 url-safe base64-encoded bytes
            fernet = Fernet(enc_key.encode("utf-8") if isinstance(enc_key, str) else enc_key)
            token_cipher = fernet.encrypt(access_token.encode("utf-8"))
            refresh_cipher = fernet.encrypt(refresh_token.encode("utf-8")) if refresh_token else None

            with db.get_connection() as conn:
                conn.execute("""
                INSERT INTO user_tokens (user_id, token_cipher, refresh_cipher, expires_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    token_cipher = excluded.token_cipher,
                    refresh_cipher = excluded.refresh_cipher,
                    expires_at = excluded.expires_at;
                """, (user_id, token_cipher, refresh_cipher, expires_at))
            return
        except Exception:
            # Fallback to in-memory on any crypto failure
            pass

    with _USER_TOKENS_LOCK:
        _USER_GITHUB_TOKENS[user_id] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }


def get_user_github_tokens(db: Database, user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves user's stored GitHub tokens, decrypting if stored in database."""
    cfg = get_config()
    enc_key = cfg.get_token_enc_key()

    if _CRYPTOGRAPHY_AVAILABLE and enc_key:
        try:
            fernet = Fernet(enc_key.encode("utf-8") if isinstance(enc_key, str) else enc_key)
            with db.get_connection() as conn:
                row = conn.execute("SELECT token_cipher, refresh_cipher, expires_at FROM user_tokens WHERE user_id = ?", (user_id,)).fetchone()
                if row:
                    access_token = fernet.decrypt(row["token_cipher"]).decode("utf-8")
                    refresh_token = fernet.decrypt(row["refresh_cipher"]).decode("utf-8") if row["refresh_cipher"] else None
                    return {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_at": row["expires_at"],
                    }
        except Exception:
            pass

    with _USER_TOKENS_LOCK:
        tokens = _USER_GITHUB_TOKENS.get(user_id)
        if tokens:
            return dict(tokens)
    return None


# --- CSRF and Cookie Helpers ---

def generate_csrf_token(session_hash: str) -> str:
    """Generates a deterministic HMAC CSRF token bound to the session."""
    secret = get_config().get_session_secret() or "cif_default_csrf_secret"
    return hmac.new(secret.encode("utf-8"), session_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def validate_csrf_origin(origin_header: Optional[str], base_url: str) -> bool:
    """
    Validates the Origin header for state-changing cookie-authenticated requests.
    Returns True if Origin matches the origin component of CIF_BASE_URL.
    """
    if not origin_header:
        return False
    parsed_base = urlparse(base_url)
    expected_origin = f"{parsed_base.scheme}://{parsed_base.netloc}"
    return origin_header.rstrip("/").lower() == expected_origin.rstrip("/").lower()


def build_session_cookie(raw_token: str, base_url: str, max_age: int = 604800) -> str:
    """Builds Set-Cookie header string for cif_session."""
    cookie = f"cif_session={raw_token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={max_age}"
    if base_url.lower().startswith("https://"):
        cookie += "; Secure"
    return cookie


def build_logout_cookie(base_url: str) -> str:
    """Builds Set-Cookie header string clearing cif_session."""
    cookie = "cif_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"
    if base_url.lower().startswith("https://"):
        cookie += "; Secure"
    return cookie


def extract_session_token(headers: Dict[str, str]) -> Tuple[Optional[str], str]:
    """
    Extracts session token and auth mechanism from request headers:
    Returns (raw_token, 'bearer') or (raw_token, 'cookie') or (None, 'none').
    """
    # 1. Check Bearer Authorization header
    auth_header = None
    for k, v in headers.items():
        if k.lower() == "authorization":
            auth_header = v
            break
    if auth_header:
        parts = auth_header.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1].strip(), "bearer"
        if len(parts) == 1 and not parts[0].lower().startswith("bearer"):
            return parts[0].strip(), "bearer"

    # 2. Check Cookie header
    cookie_header = None
    for k, v in headers.items():
        if k.lower() == "cookie":
            cookie_header = v
            break
    if cookie_header:
        from http.cookies import SimpleCookie
        try:
            cookie = SimpleCookie()
            cookie.load(cookie_header)
            if "cif_session" in cookie:
                val = cookie["cif_session"].value.strip()
                if val:
                    return val, "cookie"
        except Exception:
            pass

    return None, "none"

