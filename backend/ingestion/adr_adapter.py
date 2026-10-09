"""
ADR and Documentation Ingestion Adapter (Section 6.3)
Parses Architectural Decision Records (Nygard template) and documentation files.
"""
from typing import List, Dict, Any, Optional
import re
from backend.models import Event
from backend.db import Database
from backend.ingestion.identity import IdentityResolver

class ADRAdapter:
    def __init__(self, db: Database, identity_resolver: IdentityResolver):
        self.db = db
        self.identity_resolver = identity_resolver

    def parse_nygard_adr(self, raw_markdown: str) -> Dict[str, Any]:
        """
        Parses Markdown structured as:
        # [Number]. [Title]
        ## Status
        [Status text]
        ## Context
        [Context text]
        ## Decision
        [Decision text]
        ## Consequences
        [Consequences text]
        """
        data = {
            "title": "",
            "status": "proposed",
            "context": "",
            "decision": "",
            "consequences": "",
            "raw": raw_markdown
        }

        lines = raw_markdown.strip().split("\n")
        current_section = None
        section_buffers: Dict[str, List[str]] = {
            "context": [],
            "decision": [],
            "consequences": [],
            "status": []
        }

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# ") and not data["title"]:
                data["title"] = stripped[2:].strip()
                continue
            
            section_match = re.match(r"^##\s+(Status|Context|Decision|Consequences)", stripped, re.IGNORECASE)
            if section_match:
                current_section = section_match.group(1).lower()
                continue
            
            if current_section and current_section in section_buffers:
                section_buffers[current_section].append(line)

        for sec, buf in section_buffers.items():
            content = "\n".join(buf).strip()
            if sec == "status":
                status_lower = content.lower()
                if "accept" in status_lower:
                    data["status"] = "accepted"
                elif "reject" in status_lower:
                    data["status"] = "rejected"
                elif "supersed" in status_lower:
                    data["status"] = "superseded"
                elif "deprecat" in status_lower:
                    data["status"] = "deprecated"
                else:
                    data["status"] = "proposed"
            else:
                data[sec] = content

        return data

    def ingest_adr_file(
        self,
        repo: str,
        file_path: str,
        raw_markdown: str,
        author_raw: str,
        timestamp: str,
        commit_sha: Optional[str] = None
    ) -> Event:
        author_canonical = self.identity_resolver.resolve(author_raw)
        parsed = self.parse_nygard_adr(raw_markdown)
        adr_id = file_path.replace("/", "_").replace(".md", "")
        source_url = f"https://github.com/{repo}/blob/main/{file_path}"
        event_id = f"evt_adr_{repo.replace('/', '_')}_{adr_id}"

        event = Event(
            event_id=event_id,
            source_type="adr",
            source_id=file_path,
            source_url=source_url,
            repo=repo,
            author=author_canonical,
            timestamp=timestamp,
            title=f"ADR: {parsed['title'] or file_path}",
            body=f"Status: {parsed['status']}\n\nContext:\n{parsed['context']}\n\nDecision:\n{parsed['decision']}\n\nConsequences:\n{parsed['consequences']}",
            artifacts_touched=[file_path],
            parent_event_ids=[],
            raw_metadata={
                "parsed_adr": parsed,
                "commit_sha": commit_sha,
                "file_path": file_path
            }
        )
        self.db.upsert_event(event)
        return event

    def parse_adr_markdown(
        self,
        repo: str,
        file_path: str,
        markdown_content: str,
        author: str = "architect",
        timestamp: str = "2026-01-15T12:00:00Z"
    ) -> Event:
        """Helper alias for ingesting ADR markdown content."""
        return self.ingest_adr_file(
            repo=repo,
            file_path=file_path,
            raw_markdown=markdown_content,
            author_raw=author,
            timestamp=timestamp
        )

    def ingest_doc_file(
        self,
        repo: str,
        file_path: str,
        title: str,
        content: str,
        author_raw: str,
        timestamp: str
    ) -> Event:
        author_canonical = self.identity_resolver.resolve(author_raw)
        source_url = f"https://github.com/{repo}/blob/main/{file_path}"
        doc_id = file_path.replace("/", "_").replace(".md", "").replace(".txt", "")
        event_id = f"evt_doc_{repo.replace('/', '_')}_{doc_id}"

        event = Event(
            event_id=event_id,
            source_type="doc",
            source_id=file_path,
            source_url=source_url,
            repo=repo,
            author=author_canonical,
            timestamp=timestamp,
            title=f"Doc: {title}",
            body=content,
            artifacts_touched=[file_path],
            parent_event_ids=[],
            raw_metadata={"file_path": file_path}
        )
        self.db.upsert_event(event)
        return event
