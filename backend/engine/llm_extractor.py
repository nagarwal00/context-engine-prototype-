"""
LLM-Assisted Decision Extractor with Grounding Validation (Section 3.2 & 3.3)
Extracts decisions using an LLM when available, and strictly validates grounding against cited events.
"""
import json
import re
from typing import List, Dict, Any, Optional
from backend.models import Decision, Event
from backend.db import Database
from backend.engine.extractor import DecisionExtractor, is_decision_candidate
from backend.engine.llm_client import LLMClient
from backend.evaluation.baselines import STOP_WORDS, tokenize

def validate_grounding(candidate: Dict[str, Any], events: List[Event]) -> Dict[str, Any]:
    """
    Grounding Invariant Validator (Section 3.3):
    1. Every evidence_event_id must exist in the event bundle.
    2. At least 50% of rationale content words must appear in cited events' text.
    3. If grounding fails, downgrades to 'unresolved' state with pending_review.
    """
    event_map = {e.event_id: ((e.title or "") + " " + (e.body or "")) for e in events}
    cited_ids = candidate.get("evidence_event_ids", [])

    # Check 1: Existence of cited event IDs
    if not cited_ids or any(cid not in event_map for cid in cited_ids):
        candidate["state"] = "proposed"
        candidate["evidence_assessment"] = "insufficient"
        candidate["confidence"] = min(candidate.get("confidence", 0.3), 0.3)
        candidate["review_status"] = "pending_review"
        candidate["rationale"] = f"Unverified Grounding: Cited event IDs {cited_ids} not found in bundle."
        return candidate

    # Check 2: Content word overlap >= 50%
    rationale = candidate.get("rationale", "")
    rationale_tokens = set(tokenize(rationale))
    if not rationale_tokens:
        return candidate

    cited_corpus = " ".join(event_map[cid] for cid in cited_ids)
    cited_tokens = set(tokenize(cited_corpus))

    overlap = len(rationale_tokens.intersection(cited_tokens))
    support_ratio = overlap / len(rationale_tokens)

    if support_ratio < 0.5:
        candidate["state"] = "proposed"
        candidate["evidence_assessment"] = "insufficient"
        candidate["confidence"] = min(candidate.get("confidence", 0.3), 0.3)
        candidate["review_status"] = "pending_review"
        candidate["rationale"] = f"Ungrounded Claim ({round(support_ratio*100,1)}% match): {rationale}"

    return candidate

class LLMDecisionExtractor:
    def __init__(self, db: Database, llm_client: Optional[LLMClient] = None):
        self.db = db
        self.heuristic_extractor = DecisionExtractor(db)
        self.llm_client = llm_client or LLMClient()

    def extract_from_event_bundle(
        self,
        bundle_name: str,
        events: List[Event],
        repo: str,
        target_entities: List[str]
    ) -> List[Decision]:
        """
        Extracts decisions using LLM when configured, validates grounding,
        and falls back to heuristic extractor if unavailable.
        """
        if not self.llm_client.available():
            return self.heuristic_extractor.extract_from_event_bundle(bundle_name, events, repo, target_entities)

        candidate_events = [e for e in events if is_decision_candidate(e)]
        if not candidate_events:
            return []

        prompt = f"Repository: {repo}\nBundle: {bundle_name}\n\nEvents:\n"
        for e in candidate_events:
            prompt += f"- ID: {e.event_id}, Source: {e.source_type} #{e.source_id}, Title: {e.title}\n  Body: {e.body}\n\n"

        prompt += """Extract any architectural or engineering decisions made or rejected in the above events.
Respond with a JSON object containing a "decisions" array:
{
  "decisions": [
    {
      "title": "Short title",
      "state": "accepted" | "rejected" | "proposed",
      "rationale": "Grounded rationale strictly from events",
      "evidence_event_ids": ["event_id_1"],
      "confidence": 0.9,
      "alternatives": [
        {
          "description": "Alternative description",
          "rejection_reason": "Why rejected",
          "evidence_event_ids": ["event_id_1"]
        }
      ]
    }
  ]
}"""

        resp_text = self.llm_client.complete_json(prompt)
        if not resp_text:
            return self.heuristic_extractor.extract_from_event_bundle(bundle_name, events, repo, target_entities)

        try:
            parsed_json = json.loads(resp_text)
            raw_candidates = parsed_json.get("decisions", [])
        except Exception:
            return self.heuristic_extractor.extract_from_event_bundle(bundle_name, events, repo, target_entities)

        extracted_decisions = []
        for idx, item in enumerate(raw_candidates):
            validated = validate_grounding(item, candidate_events)
            dec_id = f"dec_llm_{repo.replace('/', '_')}_{candidate_events[0].source_id}_{idx}"
            dec = Decision(
                decision_id=dec_id,
                title=validated.get("title", "LLM Extracted Decision"),
                state=validated.get("state", "accepted"),
                made_by=candidate_events[0].author,
                made_at=candidate_events[0].timestamp,
                artifacts_affected=target_entities,
                alternatives_considered=validated.get("alternatives", []),
                rationale=validated.get("rationale", ""),
                evidence_event_ids=validated.get("evidence_event_ids", []),
                confidence=validated.get("confidence", 0.8),
                review_status=validated.get("review_status", "pending_review"),
                repo=repo
            )
            extracted_decisions.append(dec)

        return extracted_decisions
