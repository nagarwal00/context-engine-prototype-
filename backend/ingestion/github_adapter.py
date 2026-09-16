"""
GitHub Ingestion Adapter (Section 6.2)
Ingests Issues, Pull Requests, and Review Comments.
Extracts parent links ('Closes #123') and guarantees clickable source URLs.
"""
from typing import List, Dict, Any, Optional
import re
from backend.models import Event
from backend.db import Database
from backend.ingestion.identity import IdentityResolver

class GitHubAdapter:
    def __init__(self, db: Database, identity_resolver: IdentityResolver):
        self.db = db
        self.identity_resolver = identity_resolver

    def _extract_closed_issue_numbers(self, text: str) -> List[int]:
        """Extracts patterns like 'Closes #42', 'Fixes #101', 'Resolves #8'"""
        pattern = r"(?:closes|close|fixes|fix|resolves|resolve)\s+#(\d+)"
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        return [int(m) for m in matches]

    def ingest_issue(
        self,
        repo: str,
        issue_number: int,
        title: str,
        body: str,
        author_raw: str,
        created_at: str,
        labels: Optional[List[str]] = None,
        artifacts_touched: Optional[List[str]] = None
    ) -> Event:
        author_canonical = self.identity_resolver.resolve(author_raw)
        source_url = f"https://github.com/{repo}/issues/{issue_number}"
        event_id = f"evt_issue_{repo.replace('/', '_')}_{issue_number}"

        event = Event(
            event_id=event_id,
            source_type="github_issue",
            source_id=str(issue_number),
            source_url=source_url,
            repo=repo,
            author=author_canonical,
            timestamp=created_at,
            title=f"#{issue_number}: {title}",
            body=body,
            artifacts_touched=artifacts_touched or [],
            parent_event_ids=[],
            raw_metadata={"labels": labels or [], "issue_number": issue_number}
        )
        self.db.upsert_event(event)
        return event

    def ingest_pull_request(
        self,
        repo: str,
        pr_number: int,
        title: str,
        body: str,
        author_raw: str,
        created_at: str,
        merged_at: Optional[str],
        artifacts_touched: List[str],
        commit_shas: Optional[List[str]] = None
    ) -> Event:
        author_canonical = self.identity_resolver.resolve(author_raw)
        source_url = f"https://github.com/{repo}/pull/{pr_number}"
        event_id = f"evt_pr_{repo.replace('/', '_')}_{pr_number}"

        closed_issues = self._extract_closed_issue_numbers(body)
        parent_ids = [f"evt_issue_{repo.replace('/', '_')}_{num}" for num in closed_issues]
        if commit_shas:
            parent_ids.extend([f"evt_git_{repo.replace('/', '_')}_{sha[:10]}" for sha in commit_shas])

        event = Event(
            event_id=event_id,
            source_type="github_pr",
            source_id=str(pr_number),
            source_url=source_url,
            repo=repo,
            author=author_canonical,
            timestamp=created_at,
            title=f"PR #{pr_number}: {title}",
            body=body,
            artifacts_touched=artifacts_touched,
            parent_event_ids=parent_ids,
            raw_metadata={
                "pr_number": pr_number,
                "merged_at": merged_at,
                "linked_issues": closed_issues,
                "commit_shas": commit_shas or []
            }
        )
        self.db.upsert_event(event)
        return event

    def ingest_review_comment(
        self,
        repo: str,
        pr_number: int,
        comment_id: str,
        author_raw: str,
        timestamp: str,
        body: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> Event:
        author_canonical = self.identity_resolver.resolve(author_raw)
        source_url = f"https://github.com/{repo}/pull/{pr_number}#discussion_r{comment_id}"
        event_id = f"evt_rev_{repo.replace('/', '_')}_{comment_id}"
        pr_event_id = f"evt_pr_{repo.replace('/', '_')}_{pr_number}"

        artifacts = [file_path] if file_path else []

        event = Event(
            event_id=event_id,
            source_type="pr_review_comment",
            source_id=comment_id,
            source_url=source_url,
            repo=repo,
            author=author_canonical,
            timestamp=timestamp,
            title=f"Review on PR #{pr_number} by {author_canonical}",
            body=body,
            artifacts_touched=artifacts,
            parent_event_ids=[pr_event_id],
            raw_metadata={
                "pr_number": pr_number,
                "comment_id": comment_id,
                "file_path": file_path,
                "line_number": line_number
            }
        )
        self.db.upsert_event(event)
        return event
