"""
Centralized Rate Limiter for Context Intelligence Framework (CIF)
Implements an in-memory thread-safe sliding window rate limiter.
Protects sensitive endpoints, mitigates denial-of-service, and enforces quota limits.
"""
import time
import threading
import os
from typing import Dict, List, Tuple, Optional, Any
from backend.logging_config import get_logger

logger = get_logger("cif.rate_limit")


class RateLimiter:
    """
    Thread-safe sliding window rate limiter supporting per-IP and per-user tracking.
    """

    def __init__(self, env: Optional[Dict[str, str]] = None):
        if env is None:
            env = os.environ

        self._lock = threading.Lock()
        
        # Configuration
        enabled_str = env.get("CIF_RATE_LIMIT_ENABLED", "true").strip().lower()
        self.enabled: bool = enabled_str not in ("0", "false", "no", "off")

        self.window_seconds: int = self._parse_int(env.get("CIF_RATE_LIMIT_WINDOW"), 60)
        
        # Category maximums per window
        self.limits: Dict[str, int] = {
            "auth": self._parse_int(env.get("CIF_RATE_LIMIT_AUTH_MAX"), 10),
            "ingest": self._parse_int(env.get("CIF_RATE_LIMIT_INGEST_MAX"), 5),
            "expensive": self._parse_int(env.get("CIF_RATE_LIMIT_EXPENSIVE_MAX"), 15),
            # One dashboard load issues ~13 API calls; 60/min allowed only ~4 loads per minute,
            # so switching the repository filter during a demo returned 429s (audit 2026-11-21).
            "api": self._parse_int(env.get("CIF_RATE_LIMIT_API_MAX"), 300),
        }

        # In-memory storage: (category, key) -> list of timestamp floats
        self._history: Dict[Tuple[str, str], List[float]] = {}

        # Observability metrics
        self._total_checked: int = 0
        self._total_blocked: int = 0

    @staticmethod
    def _parse_int(val: Optional[str], default: int) -> int:
        if val is None or not str(val).strip():
            return default
        try:
            parsed = int(str(val).strip())
            return parsed if parsed > 0 else default
        except (ValueError, TypeError):
            return default

    def check_rate_limit(self, key: str, category: str = "api") -> Tuple[bool, int, int, int]:
        """
        Check whether an incoming request from `key` in `category` is permitted.
        Returns:
            (allowed: bool, retry_after: int, remaining: int, limit: int)
        """
        if not self.enabled:
            limit = self.limits.get(category, self.limits["api"])
            return True, 0, limit, limit

        limit = self.limits.get(category, self.limits["api"])
        now = time.time()
        window_start = now - self.window_seconds
        storage_key = (category, key)

        with self._lock:
            self._total_checked += 1
            timestamps = self._history.get(storage_key, [])
            
            # Prune timestamps outside current sliding window
            timestamps = [t for t in timestamps if t > window_start]

            if len(timestamps) >= limit:
                # Limit exceeded: calculate retry-after from oldest recorded hit in window
                oldest_hit = timestamps[0]
                retry_after = max(1, int(oldest_hit + self.window_seconds - now + 0.99))
                self._history[storage_key] = timestamps
                self._total_blocked += 1
                logger.warning(
                    f"Rate limit exceeded for key='{key}' on category='{category}'. "
                    f"Count={len(timestamps)}/{limit}. Retry after {retry_after}s."
                )
                return False, retry_after, 0, limit

            # Record this valid request
            timestamps.append(now)
            self._history[storage_key] = timestamps
            remaining = max(0, limit - len(timestamps))
            return True, 0, remaining, limit

    @staticmethod
    def get_category_for_path(path: str, method: str = "GET") -> str:
        """
        Determines the rate limiting category based on HTTP method and endpoint path.
        """
        clean_path = path.split("?")[0].rstrip("/")
        if not clean_path:
            clean_path = "/"

        # Auth endpoints
        if clean_path in (
            "/auth/login",
            "/auth/register",
            "/api/auth/login",
            "/api/auth/register",
            "/auth/extension/exchange",
            "/auth/token/exchange",
            "/api/auth/token/exchange",
            "/auth/logout",
            "/api/auth/logout"
        ) or clean_path.startswith("/auth/"):
            return "auth"

        # Ingestion endpoints
        if clean_path in (
            "/api/ingest",
            "/api/ingest-repo",
            "/api/purge-repo",
            "/api/webhook/github"
        ):
            return "ingest"

        # Resource-intensive computation endpoints
        if clean_path in (
            "/api/reseed",
            "/api/clear-db",
            "/api/benchmark",
            "/api/drift-check",
            "/api/query"
        ):
            return "expensive"

        # Default standard API
        return "api"

    def get_stats(self) -> Dict[str, Any]:
        """Provides operational metrics for monitoring dashboards and diagnostics."""
        with self._lock:
            active_keys = len(self._history)
            return {
                "enabled": self.enabled,
                "window_seconds": self.window_seconds,
                "configured_limits": dict(self.limits),
                "total_requests_checked": self._total_checked,
                "total_requests_blocked": self._total_blocked,
                "active_rate_limit_keys": active_keys,
            }

    def reset(self) -> None:
        """Resets in-memory tracking. Used primarily for test harnesses."""
        with self._lock:
            self._history.clear()
            self._total_checked = 0
            self._total_blocked = 0


# Global singleton instance
_GLOBAL_RATE_LIMITER: Optional[RateLimiter] = None
_RATE_LIMITER_LOCK = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    """Returns or creates the process-wide RateLimiter instance."""
    global _GLOBAL_RATE_LIMITER
    with _RATE_LIMITER_LOCK:
        if _GLOBAL_RATE_LIMITER is None:
            _GLOBAL_RATE_LIMITER = RateLimiter()
        return _GLOBAL_RATE_LIMITER


def reset_rate_limiter(env: Optional[Dict[str, str]] = None) -> None:
    """Resets global rate limiter history and reloads limits from environment."""
    global _GLOBAL_RATE_LIMITER
    with _RATE_LIMITER_LOCK:
        _GLOBAL_RATE_LIMITER = RateLimiter(env=env)
