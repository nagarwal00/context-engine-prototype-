"""
Git Ingestion Adapter (Section 6.1)
Walks commit history, extracts diff summaries and modified functions,
and emits normalized Event records with validated source_url.
"""
from typing import List, Dict, Any, Optional
import re
from backend.models import Event
from backend.db import Database
from backend.ingestion.identity import IdentityResolver
from backend.ingestion.sanitizer import sanitize_event

class GitAdapter:
    def __init__(self, db: Database, identity_resolver: IdentityResolver):
        self.db = db
        self.identity_resolver = identity_resolver

    def ingest_commit_record(
        self,
        repo: str,
        commit_sha: str,
        author_raw: str,
        timestamp: str,
        message: str,
        files_changed: List[str],
        diff_summary: Optional[str] = None,
        modified_functions: Optional[List[str]] = None,
        parent_shas: Optional[List[str]] = None
    ) -> Event:
        author_canonical = self.identity_resolver.resolve(author_raw)
        source_url = f"https://github.com/{repo}/commit/{commit_sha}"

        # Parse title from first line of commit message
        lines = message.strip().split("\n")
        title = lines[0] if lines else f"Commit {commit_sha[:7]}"

        raw_meta = {
            "commit_sha": commit_sha,
            "short_sha": commit_sha[:7],
            "diff_summary": diff_summary or "",
            "modified_functions": modified_functions or [],
            "parent_shas": parent_shas or []
        }

        event = Event(
            event_id=f"evt_git_{repo.replace('/', '_')}_{commit_sha[:10]}",
            source_type="git_commit",
            source_id=commit_sha,
            source_url=source_url,
            repo=repo,
            author=author_canonical,
            timestamp=timestamp,
            title=title,
            body=message,
            artifacts_touched=files_changed,
            parent_event_ids=[f"evt_git_{repo.replace('/', '_')}_{p[:10]}" for p in (parent_shas or [])],
            raw_metadata=raw_meta
        )

        sanitize_event(event)
        self.db.upsert_event(event)
        return event
