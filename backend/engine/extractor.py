"""
Decision Extraction Pipeline (Section 6.4)
Extracts candidate decisions from bundles of related events.
Enforces that every rationale and alternative links strictly to concrete event IDs.
"""
from typing import List, Dict, Any, Optional
import re
from backend.models import Decision, Event
from backend.db import Database

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

        # Collect text and event maps
        event_map = {e.event_id: e for e in events}
        all_text = "\n".join([f"[{e.source_type} {e.source_id}] {e.title or ''}: {e.body}" for e in events])

        # Heuristic/Pattern extraction for decision signals (e.g. ADRs, PR closures, explicit statements)
        for ev in events:
            # ADRs are authoritative explicit decisions
            if ev.source_type == "adr":
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
                    decision_id=f"dec_{repo.replace('/', '_')}_{ev.event_id[:12]}",
                    title=title.replace("ADR:", "").strip(),
                    state=status if status in ("proposed", "accepted", "rejected", "superseded") else "accepted",
                    made_by=ev.author,
                    made_at=ev.timestamp,
                    artifacts_affected=target_entities,
                    alternatives_considered=alternatives,
                    rationale=rationale or "Documented in architectural decision record",
                    evidence_event_ids=[ev.event_id],
                    confidence=0.95,
                    review_status="auto_confirmed" if status == "accepted" else "pending_review",
                    repo=repo
                )
                extracted.append(dec)

            # PRs and review discussions with decision keywords
            elif ev.source_type in ("github_pr", "pr_review_comment"):
                body_lower = ev.body.lower()
                decision_markers = ["decided to", "we should use", "opted for", "agreed to", "chose", "instead of", "replaces"]
                
                has_decision_signal = any(m in body_lower for m in decision_markers)
                if has_decision_signal:
                    confidence = 0.85 if ev.source_type == "github_pr" else 0.75
                    title = f"Decision in {ev.title}" if ev.title else f"Discussion decision by {ev.author}"
                    
                    # Look for alternatives mentioned in the review thread
                    alternatives = []
                    if "instead of" in body_lower:
                        parts = re.split(r"instead of", ev.body, flags=re.IGNORECASE)
                        if len(parts) > 1:
                            alternatives.append({
                                "description": parts[1].strip()[:100],
                                "rejection_reason": "Superseded by selected implementation",
                                "evidence_event_ids": [ev.event_id]
                            })

                    dec = Decision(
                        decision_id=f"dec_{repo.replace('/', '_')}_{ev.event_id[:12]}",
                        title=title[:80],
                        state="accepted" if "merged" in str(ev.raw_metadata.get("merged_at", "")) or ev.source_type == "github_pr" else "proposed",
                        made_by=ev.author,
                        made_at=ev.timestamp,
                        artifacts_affected=target_entities,
                        alternatives_considered=alternatives,
                        rationale=ev.body.strip()[:400],
                        evidence_event_ids=[ev.event_id],
                        confidence=confidence,
                        review_status="auto_confirmed" if confidence >= 0.8 else "pending_review",
                        repo=repo
                    )
                    extracted.append(dec)

        # If no explicit decision could be grounded with evidence, mark unresolved
        if not extracted and events:
            unres_dec = Decision(
                decision_id=f"dec_{repo.replace('/', '_')}_unres_{events[0].event_id[:8]}",
                title=f"Unresolved Decision for {bundle_name}",
                state="unresolved",
                made_by="system",
                made_at=events[0].timestamp,
                artifacts_affected=target_entities,
                alternatives_considered=[],
                rationale="Insufficient evidence in repository history to confirm design rationale.",
                evidence_event_ids=[], # Allowed ONLY for unresolved
                confidence=0.2,
                review_status="pending_review",
                repo=repo
            )
            extracted.append(unres_dec)

        return extracted
