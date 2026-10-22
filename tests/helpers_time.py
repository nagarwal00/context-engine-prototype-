"""
Time helper functions for tests to prevent clock-dependent test failures.
"""
from datetime import datetime, timedelta, timezone


def iso_z(offset_seconds: int = 0) -> str:
    """Returns an ISO 8601 UTC timestamp string with second precision (e.g. 2026-10-23T01:00:00Z)."""
    return (
        datetime.now(timezone.utc).replace(microsecond=0)
        + timedelta(seconds=offset_seconds)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
