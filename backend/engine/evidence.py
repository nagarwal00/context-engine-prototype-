"""
Context Intelligence Framework - Evidence Assessment Engine
Implements Step 3.2 of docs/process/ANTIGRAVITY_HANDOFF_V2.md:
- Pure deterministic assessment function `assess(decision, db=None, all_events=None, claim_evidences=None)`
- Thresholds are design choices, not statistics (documented in METRICS.md and code comments).
- Rule hierarchy:
    1. contradicted: at least one contradicting relation from an active source.
    2. strong: >= 2 independent source groups with direct support (>= 2 direct groups).
    3. moderate: 1 direct group plus >= 1 other group (any relation, e.g. 1 direct + 1 indirect), or 2 independent indirect groups.
    4. weak: exactly 1 source group (e.g. 1 direct source without corroboration, or 1 group with duplicate copies).
    5. insufficient: no evidence, or only one indirect group.
- Missing corroboration generation: identifies absence of independent sources, ADR isolation, and missing outcome/test evidence.
- Conflicting evidence listing: reports contradicting passages and conflicting/superseding decisions on the same entities.
"""
from typing import Dict, Any, List, Optional, Set, Sequence
import json

from backend.models import Decision, Event, DecisionClaim, ClaimEvidence
from backend.engine.independence import (
    independence_key,
    extract_best_passage,
    extract_claims_from_decision,
    link_claim_to_event,
    calculate_independent_sources
)


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def assess(
    decision: Any,
    db: Any = None,
    all_events: Optional[Sequence[Any]] = None,
    claim_evidences: Optional[Sequence[Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates evidence quality and source corroboration for a decision using a documented deterministic rule.
    Returns:
    {
        "label": "strong" | "moderate" | "weak" | "insufficient" | "contradicted",
        "direct_support": [...],
        "indirect_support": [...],
        "contradicting": [...],
        "missing_corroboration": [...],
        "conflicting_evidence": [...],
        "independent_sources": int,
        "source_groups": [...]
    }
    """
    dec_id = _get_attr(decision, "decision_id", "")
    dec_title = _get_attr(decision, "title", "")
    dec_state = _get_attr(decision, "state", "proposed")
    evidence_event_ids = _get_attr(decision, "evidence_event_ids", []) or []

    # 1. Resolve claim evidences
    records: List[Dict[str, Any]] = []

    if claim_evidences is not None:
        for ce in claim_evidences:
            records.append({
                "claim_id": _get_attr(ce, "claim_id", ""),
                "event_id": _get_attr(ce, "event_id", ""),
                "relation": _get_attr(ce, "relation", "indirect"),
                "passage_text": _get_attr(ce, "passage_text"),
                "passage_start": _get_attr(ce, "passage_start"),
                "passage_end": _get_attr(ce, "passage_end"),
                "source_group": _get_attr(ce, "source_group", "")
            })
    elif db is not None and dec_id:
        try:
            db_records = db.get_all_claim_evidence_for_decision(dec_id)
            if db_records:
                records = db_records
        except Exception:
            records = []

    # If records still empty and decision has evidence_event_ids
    if not records and evidence_event_ids:
        # Synthesize from decision rationale/alternatives and available events
        claims = extract_claims_from_decision(decision)
        if not claims and _get_attr(decision, "rationale", ""):
            claims = [DecisionClaim(
                claim_id=f"clm_{dec_id}_rat",
                decision_id=dec_id,
                claim_type="rationale",
                text=_get_attr(decision, "rationale", "")
            )]

        events_map: Dict[str, Any] = {}
        if all_events:
            for ev in all_events:
                eid = _get_attr(ev, "event_id", "")
                if eid:
                    events_map[eid] = ev
        elif db is not None:
            for eid in evidence_event_ids:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM events WHERE event_id = ?", (eid,))
                    row = cursor.fetchone()
                    if row:
                        events_map[eid] = dict(row)

        for clm in claims:
            for eid in evidence_event_ids:
                ev = events_map.get(eid)
                if ev:
                    ce = link_claim_to_event(clm, ev, all_events=list(events_map.values()))
                    records.append(ce.to_dict())
                else:
                    records.append({
                        "claim_id": clm.claim_id,
                        "event_id": eid,
                        "relation": "indirect",
                        "passage_text": None,
                        "passage_start": None,
                        "passage_end": None,
                        "source_group": f"event:{eid}"
                    })

    # 2. Categorize relations
    direct_support: List[Dict[str, Any]] = []
    indirect_support: List[Dict[str, Any]] = []
    contradicting: List[Dict[str, Any]] = []

    direct_groups: Set[str] = set()
    indirect_groups: Set[str] = set()
    contradicting_groups: Set[str] = set()
    all_groups: Set[str] = set()

    for r in records:
        rel = r.get("relation", "indirect")
        sg = r.get("source_group", "")
        if sg:
            all_groups.add(sg)

        if rel == "direct":
            direct_support.append(r)
            if sg:
                direct_groups.add(sg)
        elif rel == "contradicting":
            contradicting.append(r)
            if sg:
                contradicting_groups.add(sg)
        else:
            indirect_support.append(r)
            if sg:
                indirect_groups.add(sg)

    # 3. Deterministic rule evaluation
    # Thresholds are design choices, not statistics:
    # - contradicted: at least one contradicting relation from an active source.
    # - strong: >= 2 independent source groups with direct support (>= 2 direct groups).
    # - moderate: 1 direct group plus >= 1 other group (any relation, e.g. 1 direct + 1 indirect), or 2 independent indirect groups.
    # - weak: exactly 1 source group.
    # - insufficient: no evidence, or only one indirect group.

    if contradicting:
        label = "contradicted"
    elif len(direct_groups) >= 2:
        label = "strong"
    elif len(direct_groups) == 1 and len(all_groups) >= 2:
        label = "moderate"
    elif len(indirect_groups) >= 2 and len(direct_groups) == 0:
        label = "moderate"
    elif len(all_groups) == 1:
        if len(direct_groups) == 1:
            label = "weak"
        else:
            label = "insufficient"
    else:
        label = "insufficient"

    # 4. Generate missing corroboration notes
    missing_corroboration: List[str] = []
    if len(all_groups) == 0:
        missing_corroboration.append("No evidence events linked to decision claims.")
    elif len(all_groups) == 1:
        sg_item = next(iter(all_groups))
        if sg_item.startswith("doc:"):
            missing_corroboration.append("no independent source besides the ADR")
        else:
            missing_corroboration.append("no independent corroborating source recorded (single source group)")

    if len(direct_groups) == 0 and len(all_groups) > 0:
        missing_corroboration.append("no direct passage evidence supporting claims (indirect only)")

    # Check for test/outcome evidence
    has_outcome_evidence = False
    for r in records:
        ev_type = r.get("source_type", "")
        passage = (r.get("passage_text") or "").lower()
        if "benchmark" in passage or "test" in passage or "passed" in passage or "verified" in passage:
            has_outcome_evidence = True
            break
    if not has_outcome_evidence and len(all_groups) > 0:
        missing_corroboration.append("no outcome/test evidence linked")

    # 5. Conflicting evidence list
    conflicting_evidence: List[Dict[str, Any]] = []
    for c in contradicting:
        conflicting_evidence.append({
            "type": "contradicting_passage",
            "event_id": c.get("event_id"),
            "passage_text": c.get("passage_text"),
            "source_group": c.get("source_group"),
            "relation": "contradicting"
        })

    # If db is available, check for later decisions or supersessions on affected entities
    if db is not None and dec_id:
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT d2.decision_id, d2.title, d2.state, d2.made_at
                FROM decision_artifacts da1
                JOIN decision_artifacts da2 ON da1.entity_id = da2.entity_id AND da1.decision_id != da2.decision_id
                JOIN decisions d2 ON da2.decision_id = d2.decision_id
                WHERE da1.decision_id = ? AND d2.state IN ('superseded', 'accepted')
                GROUP BY d2.decision_id
                """, (dec_id,))
                for row in cursor.fetchall():
                    conflicting_evidence.append({
                        "type": "related_decision_on_entity",
                        "decision_id": row["decision_id"],
                        "title": row["title"],
                        "state": row["state"],
                        "made_at": row["made_at"]
                    })
        except Exception:
            pass

    return {
        "label": label,
        "direct_support": direct_support,
        "indirect_support": indirect_support,
        "contradicting": contradicting,
        "missing_corroboration": missing_corroboration,
        "conflicting_evidence": conflicting_evidence,
        "independent_sources": len(all_groups),
        "source_groups": sorted(list(all_groups))
    }
