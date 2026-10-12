"""
Decision Extraction Pipeline (Section 6.4)
Extracts candidate decisions from bundles of related events.
Enforces that every rationale and alternative links strictly to concrete event IDs.
"""
import os
import re
from typing import List, Dict, Any, Optional
from backend.models import Decision, Event
from backend.db import Database


TRIVIAL_COMMIT_PATTERNS = [
    r"^added\s+(readme|license|\.gitignore|requirements\.txt|deps|assets|images)$",
    r"^updated\s+(readme|license|\.gitignore|docs|comments)$",
    r"^fix(?:ed)?\s+(?:typo|lint|formatting|indentation|whitespace)",
    r"^merge\s+(?:branch|pull\s+request|remote-tracking)",
    r"^initial\s+commit",
    r"^bump\s+(?:version|dependency|deps|\w+)",
    r"^chore(?:\(.*\))?:?\s*(?:bump|format|typo|lint|cleanup)"
]

IGNORED_NON_CODE_ARTIFACTS = {
    "readme.md", "license", "license.md", ".gitignore", "package-lock.json",
    "yarn.lock", "poetry.lock", "gemfile.lock", "cargo.lock", ".prettierrc", ".eslintrc"
}

def is_decision_candidate(event: Event) -> bool:
    """
    Pre-filters events to reject trivial commits, typos, and non-architectural noise.
    ADR events are always accepted as authoritative decision candidates.
    """
    if event.source_type in ("adr", "github_adr"):
        return True

    title = (event.title or "").strip().lower()
    body = (event.body or "").strip().lower()

    # Reject trivial commit messages matching known patterns
    for pattern in TRIVIAL_COMMIT_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return False

    # Check if event touches only non-architectural documentation/lockfiles
    if event.artifacts_touched:
        non_doc_artifacts = [
            a for a in event.artifacts_touched 
            if os.path.basename(a).lower() not in IGNORED_NON_CODE_ARTIFACTS and not a.endswith((".md", ".txt", ".lock"))
        ]
        # If artifacts are listed but none are source code / config, reject unless body has explicit decision markers
        if not non_doc_artifacts:
            decision_markers = ["decided to", "we should use", "opted for", "agreed to", "instead of", "replaces"]
            if not any(m in body for m in decision_markers):
                return False

    # Reject short empty messages without body content
    if len(title) < 5 and len(body) < 15:
        return False

    return True

REJECTION_PATTERNS = [
    r"\breject(?:ed|s)?\b",
    r"\bmust reject\b",
    r"\bcannot use\b",
    r"\bnot viable\b",
    r"\babandoned\b"
]

AFFIRMATIVE_DECISION_PATTERNS = [
    r"\bdecided to\b",
    r"\bwe should use\b",
    r"\bwe must use\b",
    r"\bmust use\b",
    r"\bopted for\b",
    r"\bagreed to\b",
    r"\bchose\b",
    r"\binstead of\b",
    r"\breplaces?\b",
    r"\bin favou?r of\b",
    r"\badopt(?:ed|ing|s)?\b",
    r"\bmigrat(?:e|ed|ing|es|ion)\b",
    r"\bswitch(?:ed|ing|es)? to\b",
    r"\bimplement(?:ed|ing|s)?\b",
    r"\benable(?:d|s|ing)?\b",
    r"\bintroduce(?:d|s|ing)?\b",
    r"\bsupport(?:ed|ing|s)?\b",
    r"\bisolat(?:e|ed|ing|ion)\b",
    r"\bbatch(?:ed|ing|es)?\b",
    r"\bpinning\b",
    r"\bfeat(?:\([^\)]+\))?:",
    r"\brefactor(?:\([^\)]+\))?:"
]

class DecisionExtractor:
    def __init__(self, db: Database):
        self.db = db

    def extract_from_event_bundle(
        self,
        bundle_name: str,
        events: List[Event],
        repo: str,
        target_entities: List[str]
    ) -> List[Decision]:
        """
        Extracts candidate decisions from a set of related events.
        Enforces evidence grounding: each candidate references event IDs in the bundle.
        """
        extracted = []
        if not events:
            return extracted

        # Filter out trivial non-decision events
        candidate_events = [e for e in events if is_decision_candidate(e)]
        if not candidate_events:
            return extracted

        # Collect text and event maps
        event_map = {e.event_id: e for e in candidate_events}
        events = candidate_events

        # Heuristic/Pattern extraction for decision signals (e.g. ADRs, PR closures, explicit statements)
        for ev in events:
            # 1. ADRs are authoritative explicit decisions
            if ev.source_type in ("adr", "github_adr"):
                parsed = ev.raw_metadata.get("parsed_adr", {})
                title = parsed.get("title") or ev.title or "Architectural Decision"
                status = parsed.get("status", "accepted")
                context = parsed.get("context", "")
                decision_text = parsed.get("decision", "")
                consequences = parsed.get("consequences", "")

                rationale = f"{context}\n\nChosen: {decision_text}\n\nConsequences: {consequences}".strip()
                
                # Check for alternatives discussed
                alternatives = []
                alt_matches = re.findall(r"considered\s+([^,\.\n]+)(?:,\s*but\s+([^,\.\n]+))?", rationale, re.IGNORECASE)
                for alt, reason in alt_matches:
                    alternatives.append({
                        "description": alt.strip(),
                        "rejection_reason": reason.strip() if reason else "Rejected in favor of chosen architecture",
                        "evidence_event_ids": [ev.event_id]
                    })

                dec = Decision(
                    decision_id=f"dec_{repo.replace('/', '_')}_{ev.source_type}_{str(ev.source_id).replace('/', '_').replace('.', '_')}",
                    title=title.replace("ADR:", "").strip(),
                    state=status if status in ("proposed", "accepted", "rejected", "superseded") else "accepted",
                    made_by=ev.author,
                    made_at=ev.timestamp,
                    artifacts_affected=target_entities or ev.artifacts_touched,
                    alternatives_considered=alternatives,
                    rationale=rationale or "Documented in architectural decision record",
                    evidence_event_ids=[ev.event_id],
                    confidence=0.95,
                    review_status="auto_confirmed" if status == "accepted" else "pending_review",
                    repo=repo
                )
                extracted.append(dec)
                continue

            title = (ev.title or "").strip()
            body = (ev.body or "").strip()
            full_text = f"{title} {body}"

            # 2. PR Review Comments with rejection cues -> Rejected decision
            is_rejection = (
                ev.source_type == "pr_review_comment" and (
                    any(re.search(pat, full_text, re.IGNORECASE) for pat in REJECTION_PATTERNS) or
                    title.lower().startswith("reject")
                )
            )
            if is_rejection:
                clean_title = re.sub(r"^Review on PR #\d+:\s*", "", title, flags=re.IGNORECASE).strip()
                dec = Decision(
                    decision_id=f"dec_{repo.replace('/', '_')}_{ev.source_type}_{str(ev.source_id).replace('/', '_').replace('.', '_')}",
                    title=clean_title[:80],
                    state="rejected",
                    made_by=ev.author,
                    made_at=ev.timestamp,
                    artifacts_affected=target_entities or ev.artifacts_touched,
                    alternatives_considered=[{
                        "description": clean_title,
                        "rejection_reason": body[:200] if body else "Rejected during review",
                        "evidence_event_ids": [ev.event_id]
                    }],
                    rationale=body[:400] or clean_title,
                    evidence_event_ids=[ev.event_id],
                    confidence=0.85,
                    review_status="auto_confirmed",
                    repo=repo
                )
                extracted.append(dec)
                continue

            # 3. PRs and Git Commits with architectural implementation cues -> Accepted decision
            if ev.source_type in ("github_pr", "git_commit"):
                has_signal = any(re.search(pat, full_text, re.IGNORECASE) for pat in AFFIRMATIVE_DECISION_PATTERNS)
                if has_signal:
                    clean_title = re.sub(r"^(?:PR #\d+:\s*|feat(?:\([^\)]+\))?:\s*|refactor(?:\([^\)]+\))?:\s*)", "", title, flags=re.IGNORECASE).strip()
                    clean_title = re.sub(r"\s*\(Closes\s*#\d+\)$", "", clean_title, flags=re.IGNORECASE).strip() or title

                    # Evidence includes the event itself AND any closed issue / parent events
                    evidence_ids = [ev.event_id] + [p for p in (ev.parent_event_ids or []) if p]

                    alternatives = []
                    if "instead of" in full_text.lower():
                        parts = re.split(r"instead of", body, flags=re.IGNORECASE)
                        if len(parts) > 1:
                            alternatives.append({
                                "description": parts[1].strip()[:100],
                                "rejection_reason": "Superseded by selected implementation",
                                "evidence_event_ids": [ev.event_id]
                            })

                    conf = 0.90 if ev.source_type == "git_commit" else 0.85
                    dec = Decision(
                        decision_id=f"dec_{repo.replace('/', '_')}_{ev.source_type}_{str(ev.source_id).replace('/', '_').replace('.', '_')}",
                        title=clean_title[:80],
                        state="accepted",
                        made_by=ev.author,
                        made_at=ev.timestamp,
                        artifacts_affected=target_entities or ev.artifacts_touched,
                        alternatives_considered=alternatives,
                        rationale=body[:400] or title,
                        evidence_event_ids=evidence_ids,
                        confidence=conf,
                        review_status="auto_confirmed" if conf >= 0.8 else "pending_review",
                        repo=repo
                    )
                    extracted.append(dec)
                    continue

            # 4. GitHub Issues with explicit architectural proposal cues -> Proposed decision
            if ev.source_type == "github_issue":
                has_signal = any(re.search(pat, full_text, re.IGNORECASE) for pat in AFFIRMATIVE_DECISION_PATTERNS)
                if has_signal:
                    clean_title = re.sub(r"^Issue #\d+:\s*", "", title, flags=re.IGNORECASE).strip() or title
                    dec = Decision(
                        decision_id=f"dec_{repo.replace('/', '_')}_{ev.source_type}_{str(ev.source_id).replace('/', '_').replace('.', '_')}",
                        title=clean_title[:80],
                        state="proposed",
                        evidence_assessment="weak",
                        made_by=ev.author,
                        made_at=ev.timestamp,
                        artifacts_affected=target_entities or ev.artifacts_touched,
                        alternatives_considered=[],
                        rationale=body[:400] or title,
                        evidence_event_ids=[ev.event_id],
                        confidence=0.65,
                        review_status="pending_review",
                        repo=repo
                    )
                    extracted.append(dec)
                    continue

        return extracted
