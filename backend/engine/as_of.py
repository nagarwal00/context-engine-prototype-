"""
Temporal Context & Counterfactual Engine (Step 2.6)
Implements historical point-in-time ("as of") belief reconstruction:
- Decisions made on or before cutoff with state reconstructed from state_history.
- Graph edges valid at cutoff.
- Evidence events partitioned into known-at-cutoff vs later-evidence.
- Documented alternatives with recorded rejection reasons (strictly non-speculative).
- Changed afterwards: subsequent state transitions, supersessions, and later decisions on the same entities.
"""
from datetime import datetime, timezone
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from backend.db import Database
from backend.models import Decision, Event


def parse_ts(ts: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp string into a timezone-aware datetime."""
    if not ts or not isinstance(ts, str):
        return None
    clean = ts.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def parse_cutoff(cutoff: str) -> Tuple[datetime, str]:
    """
    Parses cutoff string into (datetime, normalized_iso_str).
    If a date only (YYYY-MM-DD) is provided, treats cutoff as the end of that day (23:59:59.999999Z).
    """
    if not cutoff or not isinstance(cutoff, str):
        raise ValueError("Cutoff must be a non-empty string")
    s = cutoff.strip()
    if len(s) == 10 and s[4] == '-' and s[7] == '-':
        s_norm = f"{s}T23:59:59.999999Z"
    else:
        s_norm = s
    dt = parse_ts(s_norm)
    if not dt:
        raise ValueError(f"Invalid date/timestamp format for cutoff: '{cutoff}'")
    return dt, s_norm


def as_of(
    db: Database,
    repo: Optional[str],
    cutoff: str,
    artifact: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reconstructs what the engineering team believed as of the specified cutoff point in time.
    Returns:
      - cutoff: normalized cutoff ISO string
      - repo: repository filter applied
      - artifact: artifact filter applied
      - decisions: list of decisions active/known at cutoff with reconstructed states
      - valid_edges: graph edges valid at cutoff
      - evidence: evidence events known at or before cutoff
      - later_evidence: evidence events that appeared after cutoff
      - documented_alternatives: alternatives documented with rejection reasons or untried status
      - changed_afterwards: subsequent transitions, supersessions, or new decisions on same entities
      - explanation: grounded summary of what was believed and why
    """
    cutoff_dt, cutoff_iso = parse_cutoff(cutoff)

    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Check state_history table columns
        cursor.execute("PRAGMA table_info(state_history)")
        sh_cols = {r["name"] for r in cursor.fetchall()}
        has_from_state = "from_state" in sh_cols
        has_reconstructed = "reconstructed" in sh_cols

        # 1. Fetch all decisions for repo (or all repos if None/empty)
        query = "SELECT * FROM decisions"
        params: List[Any] = []
        if repo:
            query += " WHERE repo = ?"
            params.append(repo)
        cursor.execute(query, params)
        all_decision_rows = [dict(r) for r in cursor.fetchall()]

        # Collect entities for artifact filtering if artifact is specified
        target_entity_ids: Set[str] = set()
        if artifact:
            cursor.execute("""
            SELECT entity_id FROM entities 
            WHERE canonical_path = ? OR canonical_path LIKE ?
            """, (artifact, f"%{artifact}%"))
            target_entity_ids = {r["entity_id"] for r in cursor.fetchall()}
            target_entity_ids.add(artifact)

        decisions_as_of: List[Dict[str, Any]] = []
        decisions_made_later: List[Dict[str, Any]] = []
        entities_believed: Set[str] = set()

        for d_row in all_decision_rows:
            d_id = d_row["decision_id"]
            made_at_str = d_row["made_at"]
            made_at_dt = parse_ts(made_at_str)

            # Artifact affected list from decision_artifacts table
            cursor.execute("""
            SELECT da.entity_id, e.canonical_path
            FROM decision_artifacts da
            LEFT JOIN entities e ON da.entity_id = e.entity_id
            WHERE da.decision_id = ?
            """, (d_id,))
            artifact_rows = cursor.fetchall()
            aff_list = [r["entity_id"] for r in artifact_rows]
            aff_paths = [r["canonical_path"] for r in artifact_rows if r["canonical_path"]]

            # If artifact filter applied and this decision does not affect it, skip
            if artifact:
                matches_artifact = (
                    any(ent in target_entity_ids for ent in aff_list) or
                    any(artifact in p or p.endswith(artifact) for p in aff_paths) or
                    artifact in aff_list
                )
                if not matches_artifact:
                    continue

            # Evidence events from decision_evidence table
            cursor.execute("SELECT event_id FROM decision_evidence WHERE decision_id = ?", (d_id,))
            ev_list = [r["event_id"] for r in cursor.fetchall()]

            # Fetch state history for this decision
            cursor.execute("""
            SELECT * FROM state_history
            WHERE decision_id = ?
            ORDER BY changed_at ASC
            """, (d_id,))
            hist_rows = [dict(r) for r in cursor.fetchall()]

            # Partition history into before/at cutoff vs after cutoff
            hist_before: List[Dict[str, Any]] = []
            hist_after: List[Dict[str, Any]] = []
            for h in hist_rows:
                h_dt = parse_ts(h["changed_at"])
                if h_dt and h_dt <= cutoff_dt:
                    hist_before.append(h)
                else:
                    hist_after.append(h)

            if made_at_dt and made_at_dt <= cutoff_dt:
                # Decision was made at or before cutoff
                state_as_of = None
                reconstructed_only = False

                if hist_before:
                    latest_h = hist_before[-1]
                    state_as_of = latest_h.get("state")
                    # Check if all rows before cutoff are reconstructed
                    if has_reconstructed:
                        reconstructed_only = all(bool(h.get("reconstructed", 0)) for h in hist_before)
                    else:
                        reconstructed_only = all(
                            h.get("changed_by") == "system:backfill" or "reconstructed" in (h.get("notes") or "").lower()
                            for h in hist_before
                        )
                else:
                    # No history before cutoff, but made_at <= cutoff
                    # Initial state from creation or proposed
                    state_as_of = "proposed"
                    reconstructed_only = True

                for ent in aff_list:
                    entities_believed.add(ent)

                decisions_as_of.append({
                    "decision_id": d_id,
                    "title": d_row["title"],
                    "state_as_of_cutoff": state_as_of,
                    "current_state": d_row["state"],
                    "made_by": d_row["made_by"],
                    "made_at": d_row["made_at"],
                    "repo": d_row["repo"],
                    "rationale": d_row["rationale"],
                    "artifacts_affected": aff_list,
                    "evidence_event_ids": ev_list,
                    "alternatives_considered": json.loads(d_row["alternatives_json"]) if d_row.get("alternatives_json") else [],
                    "evidence_assessment": d_row.get("evidence_assessment", "insufficient"),
                    "freshness": d_row.get("freshness", "fresh"),
                    "has_reconstructed_history_only": reconstructed_only,
                    "hist_after": hist_after
                })
            else:
                # Decision made after cutoff
                decisions_made_later.append({
                    "decision_id": d_id,
                    "title": d_row["title"],
                    "made_at": d_row["made_at"],
                    "made_by": d_row["made_by"],
                    "state": d_row["state"],
                    "artifacts_affected": aff_list,
                    "rationale": d_row["rationale"]
                })

        # 2. Query valid edges at cutoff
        cursor.execute("SELECT * FROM edges")
        all_edge_rows = [dict(r) for r in cursor.fetchall()]
        valid_edges: List[Dict[str, Any]] = []
        for ed in all_edge_rows:
            from_dt = parse_ts(ed["valid_from"])
            if from_dt and from_dt <= cutoff_dt:
                if ed["valid_to"]:
                    to_dt = parse_ts(ed["valid_to"])
                    if to_dt and to_dt <= cutoff_dt:
                        continue  # Expired before cutoff
                valid_edges.append({
                    "edge_id": ed["edge_id"],
                    "edge_type": ed["edge_type"],
                    "from_id": ed["from_id"],
                    "from_type": ed["from_type"],
                    "to_id": ed["to_id"],
                    "to_type": ed["to_type"],
                    "valid_from": ed["valid_from"],
                    "valid_to": ed["valid_to"]
                })

        # 3. Evidence events partition: known at cutoff vs later evidence
        all_evidence_ids: Set[str] = set()
        for d in decisions_as_of:
            for eid in d["evidence_event_ids"]:
                all_evidence_ids.add(eid)

        evidence_known: List[Dict[str, Any]] = []
        later_evidence: List[Dict[str, Any]] = []

        if all_evidence_ids:
            placeholders = ",".join("?" for _ in all_evidence_ids)
            cursor.execute(f"SELECT * FROM events WHERE event_id IN ({placeholders})", list(all_evidence_ids))
            ev_rows = [dict(r) for r in cursor.fetchall()]
            for ev in ev_rows:
                ev_dt = parse_ts(ev["ts"])
                ev_item = {
                    "event_id": ev["event_id"],
                    "source_type": ev["source_type"],
                    "source_id": ev["source_id"],
                    "source_url": ev["source_url"],
                    "title": ev["title"],
                    "author": ev["author"],
                    "timestamp": ev["ts"],
                    "repo": ev["repo"]
                }
                if ev_dt and ev_dt <= cutoff_dt:
                    evidence_known.append(ev_item)
                else:
                    later_evidence.append(ev_item)

        # 4. Documented Alternatives (strictly non-speculative)
        documented_alternatives: List[Dict[str, Any]] = []
        for d in decisions_as_of:
            for alt in d["alternatives_considered"]:
                desc = alt.get("description", "")
                reason = alt.get("rejection_reason")
                if not reason or not reason.strip():
                    reason = "no recorded outcome — consequences of the untried alternative are unknown."

                # Verify if alternative rejection evidence is dated <= cutoff
                alt_eids = alt.get("evidence_event_ids", [])
                rejection_dated_le_cutoff = True
                if alt_eids:
                    # check evidence timestamps
                    for eid in alt_eids:
                        cursor.execute("SELECT ts FROM events WHERE event_id = ?", (eid,))
                        row = cursor.fetchone()
                        if row:
                            ts_dt = parse_ts(row["ts"])
                            if ts_dt and ts_dt > cutoff_dt:
                                rejection_dated_le_cutoff = False
                                break

                documented_alternatives.append({
                    "for_decision_id": d["decision_id"],
                    "for_decision_title": d["title"],
                    "description": desc,
                    "rejection_reason": reason,
                    "rejected_by_cutoff": rejection_dated_le_cutoff,
                    "evidence_event_ids": alt_eids
                })

        # Also include any rejected decisions whose made_at <= cutoff
        for d in decisions_as_of:
            if d["state_as_of_cutoff"] == "rejected":
                reason = d.get("rationale") or "Rejected by team decision."
                documented_alternatives.append({
                    "for_decision_id": d["decision_id"],
                    "for_decision_title": d["title"],
                    "description": d["title"],
                    "rejection_reason": reason,
                    "rejected_by_cutoff": True,
                    "evidence_event_ids": d["evidence_event_ids"]
                })

        # 5. Changed Afterwards
        changed_afterwards: List[Dict[str, Any]] = []

        # A. Later transitions on decisions believed at cutoff
        for d in decisions_as_of:
            for h in d["hist_after"]:
                changed_afterwards.append({
                    "type": "later_transition",
                    "decision_id": d["decision_id"],
                    "decision_title": d["title"],
                    "from_state": h.get("from_state"),
                    "to_state": h.get("state"),
                    "changed_at": h.get("changed_at"),
                    "changed_by": h.get("changed_by"),
                    "notes": h.get("notes") or ""
                })

        # B. New decisions made after cutoff on the same entities
        for dl in decisions_made_later:
            dl_aff = set(dl["artifacts_affected"])
            if dl_aff.intersection(entities_believed) or not entities_believed:
                changed_afterwards.append({
                    "type": "later_decision",
                    "decision_id": dl["decision_id"],
                    "decision_title": dl["title"],
                    "made_at": dl["made_at"],
                    "made_by": dl["made_by"],
                    "state": dl["state"],
                    "rationale": dl["rationale"],
                    "shared_entities": list(dl_aff.intersection(entities_believed))
                })

        # Clean decisions_as_of internal field
        for d in decisions_as_of:
            d.pop("hist_after", None)

        # 6. Generate grounded summary (strictly non-speculative)
        explanation = _synthesize_as_of_explanation(
            cutoff_str=cutoff,
            decisions=decisions_as_of,
            alternatives=documented_alternatives,
            changed_afterwards=changed_afterwards,
            later_evidence=later_evidence
        )

        return {
            "status": "success",
            "data": {
                "cutoff": cutoff_iso,
                "cutoff_input": cutoff,
                "repo": repo or "all",
                "artifact": artifact,
                "decisions": decisions_as_of,
                "edges": valid_edges,
                "evidence": evidence_known,
                "later_evidence": later_evidence,
                "documented_alternatives": documented_alternatives,
                "changed_afterwards": changed_afterwards,
                "explanation": explanation
            }
        }


def _synthesize_as_of_explanation(
    cutoff_str: str,
    decisions: List[Dict[str, Any]],
    alternatives: List[Dict[str, Any]],
    changed_afterwards: List[Dict[str, Any]],
    later_evidence: List[Dict[str, Any]]
) -> str:
    """Produces a factual, evidence-grounded summary without speculative extrapolation."""
    if not decisions:
        return f"As of {cutoff_str}, no architectural decisions had been recorded in the specified repository scope."

    parts: List[str] = []
    parts.append(f"As of {cutoff_str}, the team recognized {len(decisions)} architectural decision(s):")

    for d in decisions:
        state = d["state_as_of_cutoff"]
        rec_notice = " [reconstructed]" if d.get("has_reconstructed_history_only") else ""
        parts.append(f"- '{d['title']}' was held as {state.upper()}{rec_notice} (decided by {d['made_by']} on {d['made_at'][:10]}). Rationale: {d['rationale']}")

    if alternatives:
        parts.append("\nDocumented alternatives considered:")
        for a in alternatives:
            parts.append(f"- Regarding '{a['for_decision_title']}': Alternative '{a['description']}' — {a['rejection_reason']}")

    if changed_afterwards:
        parts.append(f"\nChanged afterwards ({len(changed_afterwards)} post-cutoff events):")
        for ca in changed_afterwards[:5]:
            if ca["type"] == "later_transition":
                parts.append(f"- Decision '{ca['decision_title']}' transitioned to {ca['to_state']} on {ca['changed_at'][:10]} by {ca['changed_by']}.")
            elif ca["type"] == "later_decision":
                parts.append(f"- New decision '{ca['decision_title']}' adopted on {ca['made_at'][:10]} affecting shared entities.")

    if later_evidence:
        parts.append(f"\nNote: {len(later_evidence)} supporting evidence citation(s) emerged after {cutoff_str}.")

    return "\n".join(parts)
