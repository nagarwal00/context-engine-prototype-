"""
Identity Resolution Mapping (Section 6.5)
Maps contributors across Git emails, GitHub logins, and display names.
"""
from typing import Dict, Optional, List
from backend.models import Identity
from backend.db import Database

INITIAL_IDENTITIES: List[Identity] = [
    Identity(
        canonical_id="sarah_chen",
        display_name="Sarah Chen (Lead Architect)",
        git_emails=["sarah.chen@acme.org", "schen@users.noreply.github.com"],
        github_logins=["sarahc-eng", "schen"]
    ),
    Identity(
        canonical_id="marcus_vance",
        display_name="Marcus Vance (Senior Systems Eng)",
        git_emails=["mvance@acme.org", "marcus.vance@techcorp.io"],
        github_logins=["mvance-dev", "marcus-v"]
    ),
    Identity(
        canonical_id="priya_patel",
        display_name="Priya Patel (Core Infra Eng)",
        git_emails=["priya.patel@acme.org", "ppatel@users.noreply.github.com"],
        github_logins=["priyapatel-tech", "priyap"]
    ),
    Identity(
        canonical_id="alex_rodriguez",
        display_name="Alex Rodriguez (Staff SRE)",
        git_emails=["alex.r@acme.org", "arodriguez@ops.net"],
        github_logins=["alexr-ops", "alex-rodriguez"]
    ),
    Identity(
        canonical_id="elena_rostova",
        display_name="Elena Rostova (Performance Eng)",
        git_emails=["elena.r@acme.org", "erostova@systems.org"],
        github_logins=["erostova-dev"]
    )
]

class IdentityResolver:
    def __init__(self, db: Optional[Database] = None):
        self.db = db
        self._cache: Dict[str, str] = {}
        self._load()

    def _load(self):
        for ident in INITIAL_IDENTITIES:
            if self.db:
                self.db.upsert_identity(ident)
            for email in ident.git_emails:
                self._cache[email.lower()] = ident.canonical_id
            for login in ident.github_logins:
                self._cache[login.lower()] = ident.canonical_id
            self._cache[ident.display_name.lower()] = ident.canonical_id
            self._cache[ident.canonical_id.lower()] = ident.canonical_id

    def resolve(self, raw_identifier: Optional[str]) -> str:
        if not raw_identifier:
            return "unknown_contributor"
        clean = raw_identifier.strip().lower()
        # Direct lookup
        if clean in self._cache:
            return self._cache[clean]
        # Partial lookup inside string (e.g. "Sarah Chen <sarah.chen@acme.org>")
        for key, canonical in self._cache.items():
            if key in clean:
                return canonical
        return raw_identifier
