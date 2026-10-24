"""
Context Intelligence Framework - GitHub App Token Minting (Rule R1).

Rule R1 (docs/process/ANTIGRAVITY_HANDOFF_V3_EXTENSION.md):
- Optional dependency exception for 'cryptography':
  (a) signing the GitHub App JSON Web Token (RS256) to mint installation tokens
      (webhook PR comments, background re-sync).
  (b) encrypting stored GitHub refresh tokens at rest.
- Standard-library only backend with try/except ImportError for cryptography.
- Without cryptography: reports "unavailable: install cryptography".
"""
import base64
import json
import os
import time
import urllib.request
import urllib.error
from typing import Optional, Tuple

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


def is_r1_available() -> bool:
    """Returns True if cryptography is available for RS256 signing and token encryption."""
    return HAS_CRYPTOGRAPHY


def mint_app_jwt(app_id: str, private_key_pem: bytes) -> Tuple[Optional[str], Optional[str]]:
    """
    Mints an RS256 JWT for GitHub App authentication.
    Returns (jwt_str, error_msg).
    If cryptography is not installed, returns (None, "unavailable: install cryptography").
    """
    if not HAS_CRYPTOGRAPHY:
        return None, "unavailable: install cryptography"

    if not app_id:
        return None, "unavailable: GITHUB_APP_ID not provided"

    if not private_key_pem:
        return None, "unavailable: GitHub App private key not provided"

    try:
        now = int(time.time())
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {
            "iat": now - 60,
            "exp": now + 600,  # 10 minutes maximum per GitHub requirements
            "iss": str(app_id),
        }

        def b64url(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

        header_b64 = b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

        pkey = load_pem_private_key(private_key_pem, password=None)
        sig = pkey.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        sig_b64 = b64url(sig)

        return f"{header_b64}.{payload_b64}.{sig_b64}", None
    except Exception as e:
        return None, f"error minting JWT: {e}"


def get_installation_token(
    installation_id: int,
    app_id: Optional[str] = None,
    private_key_path: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Requests a GitHub App installation access token.
    Returns (token_str, error_msg).
    If cryptography is missing, returns (None, "unavailable: install cryptography").
    """
    if not HAS_CRYPTOGRAPHY:
        return None, "unavailable: install cryptography"

    app_id = app_id or os.environ.get("GITHUB_APP_ID", "")
    if not app_id:
        return None, "unavailable: GITHUB_APP_ID not configured"

    key_path = private_key_path or os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH", "")
    if not key_path or not os.path.exists(key_path):
        return None, "unavailable: GitHub App private key not configured"

    try:
        with open(key_path, "rb") as f:
            key_pem = f.read()
    except Exception as e:
        return None, f"unavailable: failed to read private key: {e}"

    jwt_str, err = mint_app_jwt(app_id, key_pem)
    if err or not jwt_str:
        return None, err or "failed to generate app jwt"

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    req = urllib.request.Request(
        url,
        data=b"{}",
        headers={
            "Authorization": f"Bearer {jwt_str}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "CIF-Bot/1.0"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("token"), None
    except urllib.error.HTTPError as e:
        return None, f"GitHub installation token error: HTTP {e.code}"
    except Exception as e:
        return None, f"installation token request error: {e}"
