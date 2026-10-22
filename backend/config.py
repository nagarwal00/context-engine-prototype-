"""
Configuration Module for CIF (Step 7.1)
Reads environment variables once, validates them, and exposes safe getters.
Guarantees that sensitive secrets are never logged or exposed in __repr__ / __str__.
"""
import os
from typing import Dict, Any, List, Optional, Set


class Config:
    """Application configuration holder with masked string representations."""

    def __init__(self, env: Optional[Dict[str, str]] = None):
        if env is None:
            env = os.environ

        # Base URL
        base_url = env.get("CIF_BASE_URL", "http://127.0.0.1:8080").strip()
        self._base_url = base_url.rstrip("/") if base_url else "http://127.0.0.1:8080"

        # Session Secret
        self._session_secret = env.get("CIF_SESSION_SECRET", "").strip()

        # GitHub App parameters
        self._app_slug = env.get("GITHUB_APP_SLUG", "").strip()
        
        raw_app_id = env.get("GITHUB_APP_ID", "").strip()
        self._app_id: Optional[int] = None
        if raw_app_id:
            try:
                self._app_id = int(raw_app_id)
            except ValueError:
                self._app_id = None

        self._client_id = env.get("GITHUB_APP_CLIENT_ID", "").strip()
        self._client_secret = env.get("GITHUB_APP_CLIENT_SECRET", "").strip()
        self._private_key_path = env.get("GITHUB_APP_PRIVATE_KEY_PATH", "").strip() or None
        self._token_enc_key = env.get("CIF_TOKEN_ENC_KEY", "").strip() or None

        # Extension IDs
        raw_ext_ids = env.get("CIF_EXTENSION_IDS", "").strip()
        if raw_ext_ids:
            self._extension_ids: List[str] = [x.strip() for x in raw_ext_ids.split(",") if x.strip()]
        else:
            self._extension_ids = []

        # VS Code Extension IDs (e.g. cif.cif-vscode)
        raw_vscode_ids = env.get("CIF_VSCODE_EXT_IDS", "").strip()
        if raw_vscode_ids:
            self._vscode_ext_ids: List[str] = [x.strip() for x in raw_vscode_ids.split(",") if x.strip()]
        else:
            self._vscode_ext_ids = []

        # Caps and limits (with fallbacks to defaults)
        self._max_commits = self._parse_positive_int(env.get("CIF_MAX_COMMITS"), 5000)
        self._max_prs = self._parse_positive_int(env.get("CIF_MAX_PRS"), 1500)
        self._max_issues = self._parse_positive_int(env.get("CIF_MAX_ISSUES"), 1500)
        self._max_tarball_mb = self._parse_positive_int(env.get("CIF_MAX_TARBALL_MB"), 100)

    @staticmethod
    def _parse_positive_int(val: Optional[str], default: int) -> int:
        if val is None or not str(val).strip():
            return default
        try:
            parsed = int(str(val).strip())
            return parsed if parsed > 0 else default
        except (ValueError, TypeError):
            return default

    # --- Safe Public Getters ---

    def get_base_url(self) -> str:
        return self._base_url

    def get_session_secret(self) -> str:
        return self._session_secret

    def get_github_app_slug(self) -> str:
        return self._app_slug

    def get_github_app_id(self) -> Optional[int]:
        return self._app_id

    def get_github_client_id(self) -> str:
        return self._client_id

    def get_github_client_secret(self) -> str:
        return self._client_secret

    def get_github_private_key_path(self) -> Optional[str]:
        return self._private_key_path

    def get_token_enc_key(self) -> Optional[str]:
        return self._token_enc_key

    def get_extension_ids(self) -> List[str]:
        return list(self._extension_ids)

    def is_extension_id_allowed(self, ext_id: str) -> bool:
        if not ext_id:
            return False
        return ext_id.strip() in self._extension_ids

    def get_vscode_ext_ids(self) -> List[str]:
        return list(self._vscode_ext_ids)

    def is_vscode_extension_allowed(self, ext_id: str) -> bool:
        if not ext_id:
            return False
        # If explicitly restricted in env, check against configured list
        if self._vscode_ext_ids:
            return ext_id.strip() in self._vscode_ext_ids
        # Otherwise permit standard cif VS Code extension identifiers
        return ext_id.strip() in ["cif.cif-vscode", "cif.cif-vscode-dev"]

    def get_max_commits(self) -> int:
        return self._max_commits

    def get_max_prs(self) -> int:
        return self._max_prs

    def get_max_issues(self) -> int:
        return self._max_issues

    def get_max_tarball_mb(self) -> int:
        return self._max_tarball_mb

    def is_login_enabled(self) -> bool:
        """
        Login is enabled only when minimum GitHub App credentials are configured:
        both client ID and client secret must be present.
        """
        return bool(self._client_id and self._client_secret)

    def get_public_auth_config(self) -> Dict[str, Any]:
        """
        Public configuration endpoint payload.
        Returns only login_enabled and app_slug. NEVER exposes any secrets or IDs.
        """
        return {
            "login_enabled": self.is_login_enabled(),
            "app_slug": self._app_slug,
        }

    # --- Sensitive Data Masking ---

    def _mask_secret(self, val: Optional[str]) -> str:
        if not val:
            return "<unset>"
        return "[REDACTED]"

    def to_dict_safe(self) -> Dict[str, Any]:
        """Returns safe representation of configuration without sensitive secrets."""
        return {
            "CIF_BASE_URL": self._base_url,
            "CIF_SESSION_SECRET": self._mask_secret(self._session_secret),
            "GITHUB_APP_SLUG": self._app_slug,
            "GITHUB_APP_ID": self._app_id,
            "GITHUB_APP_CLIENT_ID": self._client_id,
            "GITHUB_APP_CLIENT_SECRET": self._mask_secret(self._client_secret),
            "GITHUB_APP_PRIVATE_KEY_PATH": self._private_key_path,
            "CIF_TOKEN_ENC_KEY": self._mask_secret(self._token_enc_key),
            "CIF_EXTENSION_IDS": self._extension_ids,
            "CIF_MAX_COMMITS": self._max_commits,
            "CIF_MAX_PRS": self._max_prs,
            "CIF_MAX_ISSUES": self._max_issues,
            "CIF_MAX_TARBALL_MB": self._max_tarball_mb,
            "login_enabled": self.is_login_enabled(),
        }

    def __repr__(self) -> str:
        safe_fields = ", ".join(f"{k}={v!r}" for k, v in self.to_dict_safe().items())
        return f"Config({safe_fields})"

    def __str__(self) -> str:
        return self.__repr__()


# Module-level cached configuration instance
_GLOBAL_CONFIG: Optional[Config] = None


def get_config() -> Config:
    """Returns the globally loaded configuration instance, instantiating if needed."""
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None:
        _GLOBAL_CONFIG = Config()
    return _GLOBAL_CONFIG


def reload_config(env: Optional[Dict[str, str]] = None) -> Config:
    """Forces reloading configuration (useful for testing)."""
    global _GLOBAL_CONFIG
    _GLOBAL_CONFIG = Config(env=env)
    return _GLOBAL_CONFIG
