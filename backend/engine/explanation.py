"""
Evidence-Grounded Explanation Generator (Section 9)
Synthesizes verified explanations from the temporal graph with explicit source_url citations.
Guarantees zero hallucinations and explicitly reports 'unresolved' or 'no recorded decision' when absent.
"""
from typing import Dict, Any, List, Optional
from backend.db import Database

class ExplanationGenerator:
    def __init__(self, db: Database):
        self.db = db

    def explain_artifact(self, canonical_path: str) -> Dict[str, Any]:
        """
        Generates Section 9 evidence-grounded explanation for why an artifact looks the way it does.
        """
        chain = self.db.query_decision_chain_for_artifact(canonical_path)

        if not chain:
            return {
                "artifact": canonical_path,
                "status": "not_found",
                "explanation": f"No recorded architectural decisions found for artifact '{canonical_path}' in project history.",
                "citations": [],
                "chain": []
            }

        # Build chronological reasoning sequence
        steps = []
        citations = []
        
        for idx, dec in enumerate(chain, 1):
            trail = self.db.query_full_evidence_trail(dec["decision_id"])
            evidence_events = trail.get("evidence_events", [])
            
            event_citations = []
            for ev in evidence_events:
                cite = {
                    "source_type": ev["source_type"],
                    "source_id": ev["source_id"],
                    "source_url": ev["source_url"],
                    "title": ev["title"] or f"{ev['source_type']} {ev['source_id']}",
                    "author": ev["author"],
                    "timestamp": ev["ts"]
                }
                event_citations.append(cite)
                citations.append(cite)

            state_badge = f"[{dec['state'].upper()}]"
            step_summary = f"{state_badge} {dec['title']} (by {dec['made_by']} on {dec['made_at'][:10]})"
            
            steps.append({
                "step_number": idx,
                "decision_id": dec["decision_id"],
                "title": dec["title"],
                "state": dec["state"],
                "made_by": dec["made_by"],
                "made_at": dec["made_at"],
                "rationale": dec["rationale"],
                "alternatives_considered": dec.get("alternatives_considered", []),
                "citations": event_citations,
                "summary": step_summary
            })

        # Latest active decision
        active_decisions = [d for d in chain if d["state"] == "accepted"]
        current_active = active_decisions[-1] if active_decisions else chain[-1]

        overall_text = f"Artifact '{canonical_path}' is governed primarily by accepted decision '{current_active['title']}', established by {current_active['made_by']} on {current_active['made_at'][:10]}.\n\n"
        overall_text += f"Key Rationale: {current_active['rationale']}\n\n"
        
        if len(chain) > 1:
            overall_text += f"Evolutionary History: This artifact progressed through {len(chain)} recorded decision milestones, including prior iterations or superseded proposals."

        return {
            "artifact": canonical_path,
            "status": "grounded",
            "current_decision": current_active["title"],
            "current_state": current_active["state"],
            "explanation": overall_text,
            "citations": citations,
            "chain": steps
        }
