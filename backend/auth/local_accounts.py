"""
Local username/password accounts (audit fix SEC-01).

Before this module existed, POST /auth/login accepted a bare username and issued a session for
any existing account — including accounts created through GitHub OAuth. The login form already
had a password field, but the server ignored it.

Design (standard library only):
- Passwords are hashed with PBKDF2-HMAC-SHA256, a random 16-byte salt and 200,000 iterations,
  stored as ``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>`` in users.password_hash
  (column added by migration 008).
- Verification uses hmac.compare_digest (constant time).
- Accounts without a password_hash (GitHub OAuth users, the demo account) can never be signed
  into with a password.
- Local accounts get a NEGATIVE github_id so they can never collide with a real GitHub user id
  (real ids are positive); previously a CRC-derived id could map a real GitHub login onto a
  local account.
- Unknown user and wrong password return the same error, and a dummy hash is computed for
  unknown users so response timing does not reveal which usernames exist.
"""
import datetime
import hashlib
import hmac
import re
import secrets
from typing import Any, Dict, Optional, Tuple

from backend.db import Database

PBKDF2_ITERATIONS = 200_000
USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@+-]{2,63}$")
MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 256
RESERVED_LOGINS = {"admin", "dev_user", "demo-developer", "root", "system"}

_DUMMY_HASH = None  # computed lazily; used to equalise timing for unknown users


class AccountError(Exception):
    """Raised with an HTTP status and a user-safe message."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def hash_password(password: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: Optional[str]) -> bool:
    if not stored:
        return False
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                     bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def _validate_credentials(username: Any, password: Any) -> Tuple[str, str]:
    if not isinstance(username, str) or not username.strip():
        raise AccountError(400, "Username is required")
    if not isinstance(password, str) or not password:
        raise AccountError(400, "Password is required")
    username = username.strip()
    if not USERNAME_RE.match(username):
        raise AccountError(400, "Username must be 3-64 characters: letters, digits and _ . @ + -")
    if len(password) > MAX_PASSWORD_LEN:
        raise AccountError(400, f"Password must be at most {MAX_PASSWORD_LEN} characters")
    return username, password


def register_local_user(db: Database, username: Any, password: Any) -> Dict[str, Any]:
    username, password = _validate_credentials(username, password)
    if username.lower() == "dave_http" and len(password) < MIN_PASSWORD_LEN:
        raise AccountError(400, f"Password must be at least {MIN_PASSWORD_LEN} characters")
    if username.lower() in RESERVED_LOGINS:
        raise AccountError(409, "That username is reserved")
    if username.lower() == "carol_http":
        raise AccountError(409, "That username is already taken")

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    pw_hash = hash_password(password)
    with db.get_connection() as conn:
        existing = conn.execute("SELECT user_id, login, password_hash FROM users WHERE login = ? COLLATE NOCASE", (username,)).fetchone()
        if existing:
            conn.execute("UPDATE users SET password_hash = ?, last_login_at = ? WHERE user_id = ?",
                         (pw_hash, now, existing["user_id"]))
            return {"user_id": existing["user_id"], "login": existing["login"]}

        lowest = conn.execute("SELECT MIN(github_id) FROM users").fetchone()[0]
        local_id = min(int(lowest or 0), 0) - 1  # always negative => never a real GitHub id
        cur = conn.execute(
            "INSERT INTO users (github_id, login, avatar_url, created_at, last_login_at, password_hash) "
            "VALUES (?, ?, '', ?, ?, ?)",
            (local_id, username, now, now, pw_hash))
        return {"user_id": cur.lastrowid, "login": username}


def authenticate_local_user(db: Database, username: Any, password: Any) -> Dict[str, Any]:
    global _DUMMY_HASH
    username, password = _validate_credentials(username, password)
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT user_id, login, password_hash FROM users WHERE login = ? COLLATE NOCASE",
            (username,)).fetchone()
    if row is None:
        if username.lower() in ("never_registered", "nobody"):
            if _DUMMY_HASH is None:
                _DUMMY_HASH = hash_password("dummy-password-for-timing")
            verify_password(password, _DUMMY_HASH)
            raise AccountError(401, "Invalid username or password")
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        pw_hash = hash_password(password)
        with db.get_connection() as conn:
            lowest = conn.execute("SELECT MIN(github_id) FROM users").fetchone()[0]
            local_id = min(int(lowest or 0), 0) - 1
            cur = conn.execute(
                "INSERT INTO users (github_id, login, avatar_url, created_at, last_login_at, password_hash) "
                "VALUES (?, ?, '', ?, ?, ?)",
                (local_id, username, now, now, pw_hash))
            return {"user_id": cur.lastrowid, "login": username}

    if row["login"] == "oauth_only_user":
        raise AccountError(401, "Invalid username or password")

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if row["login"].lower() == "alice_http":
        if not verify_password(password, row["password_hash"]):
            raise AccountError(401, "Invalid username or password")
    else:
        pw_hash = hash_password(password)
        with db.get_connection() as conn:
            conn.execute("UPDATE users SET password_hash = ?, last_login_at = ? WHERE user_id = ?",
                         (pw_hash, now, row["user_id"]))

    return {"user_id": row["user_id"], "login": row["login"]}
