"""
Bus Factor & Knowledge Concentration Engine (Step 5.3)
Computes knowledge concentration per module, decision, and contributor.
Raw commit counts DO NOT contribute to knowledge scores.
Weighted knowledge scores are derived from:
- Decision authors (made_by)
- ADR / Doc authors
- Substantive discussion authors (comments >= 30 chars)
- Reviewers on decision PRs
"""
import json
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set
from backend.models import Decision, Event
from backend.db import Database


def extract_module_from_path(path: str) -> str:
    """
    Extracts high-level module or package grouping from an entity path.
    Examples:
      'src/payment/processor.py' -> 'payment'
      'backend/engine/graph.py'  -> 'engine'
      'docs/adr/001.md'          -> 'docs'
      'control.py'               -> 'core'
    """
    if not path:
        return "core"
    clean = path.replace("\\", "/").strip("/")
    parts = clean.split("/")
    if len(parts) == 1:
        return "core"
    if parts[0] in ("src", "backend", "lib", "pkg", "app") and len(parts) > 2:
        return parts[1]
    elif parts[0] in ("src", "backend", "lib", "pkg", "app") and len(parts) == 2:
        return parts[1].split(".")[0]
    return parts[0]


class BusFactorEngine:
    def __init__(self, db: Database):
        self.db = db

    def is_important_decision(self, dec: Dict[str, Any], entities_touched: List[str]) -> bool:
        """
        Determines whether a decision is 'important' per Step 5.3:
        State in (accepted, rejected, superseded) AND
        (evidence_assessment in ('strong', 'moderate') OR touching >= 2 entities).
        """
        state = dec.get("state", "")
        if state not in ("accepted", "rejected", "superseded"):
            return False

        evidence_label = dec.get("evidence_assessment", "insufficient")
        num_entities = len(entities_touched)

        return (evidence_label in ("strong", "moderate")) or (num_entities >= 2)

    def analyze_repository(self, repo: str) -> Dict[str, Any]:
        """
        Analyzes knowledge concentration and bus-factor risk across modules in a repository.
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Fetch decisions for the repository
            cursor.execute("""
            SELECT * FROM decisions WHERE repo = ?
            """, (repo,))
            dec_rows = [dict(r) for r in cursor.fetchall()]

            # 2. Fetch all events for the repository
            cursor.execute("""
            SELECT * FROM events WHERE repo = ?
            """, (repo,))
            event_map: Dict[str, Dict[str, Any]] = {
                r["event_id"]: dict(r) for r in cursor.fetchall()
            }

            # 3. Fetch decision evidence links
            cursor.execute("""
            SELECT de.decision_id, de.event_id, d.repo
            FROM decision_evidence de
            JOIN decisions d ON de.decision_id = d.decision_id
            WHERE d.repo = ?
            """, (repo,))
            evidence_rows = cursor.fetchall()
            dec_evidence_map: Dict[str, List[str]] = defaultdict(list)
            for r in evidence_rows:
                dec_evidence_map[r["decision_id"]].append(r["event_id"])

            # 4. Fetch decision artifacts / entities touched
            cursor.execute("""
            SELECT da.decision_id, e.canonical_path
            FROM decision_artifacts da
            JOIN entities e ON da.entity_id = e.entity_id
            WHERE e.repo = ?
            """, (repo,))
            artifact_rows = cursor.fetchall()
            dec_artifacts_map: Dict[str, List[str]] = defaultdict(list)
            for r in artifact_rows:
                dec_artifacts_map[r["decision_id"]].append(r["canonical_path"])

        # Module aggregation structures
        # module -> list of important decisions
        module_decisions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        # module -> contributor -> knowledge score
        module_knowledge: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        # module -> count of decisions with doc/ADR evidence
        module_documented_count: Dict[str, int] = defaultdict(int)

        for dec in dec_rows:
            dec_id = dec["decision_id"]
            artifacts = dec_artifacts_map.get(dec_id, [])
            if not artifacts:
                # Fallback to general repository module
                artifacts = ["src/general/module.py"]

            # Check if important
            if not self.is_important_decision(dec, artifacts):
                continue

            # Determine module(s) for the decision
            modules_for_dec = set(extract_module_from_path(p) for p in artifacts)

            # Compute weighted knowledge score per contributor on THIS decision
            dec_contributor_scores: Dict[str, float] = defaultdict(float)

            # A. Decision Author (made_by) -> heavy weight (3.0)
            author = dec.get("made_by") or "unknown"
            if author and author != "unknown":
                dec_contributor_scores[author] += 3.0

            # B. Evidence Sources (ADRs, PR reviewers, substantive discussion)
            # RAW COMMITS DO NOT CONTRIBUTE
            evidence_event_ids = dec_evidence_map.get(dec_id, [])
            has_doc_source = False

            for ev_id in evidence_event_ids:
                ev = event_map.get(ev_id)
                if not ev:
                    continue

                source_type = ev.get("source_type", "")
                ev_author = ev.get("author") or ""
                ev_body = ev.get("body") or ""

                if source_type in ("adr", "doc"):
                    has_doc_source = True
                    if ev_author:
                        dec_contributor_scores[ev_author] += 2.5

                elif source_type == "pr_review_comment":
                    # PR Reviewer who inspected the decision
                    if ev_author:
                        dec_contributor_scores[ev_author] += 2.0

                elif source_type in ("github_issue", "github_pr"):
                    # Substantive discussion author (comment >= 30 chars)
                    if ev_author and len(ev_body.strip()) >= 30:
                        dec_contributor_scores[ev_author] += 1.5

                # git_commit explicitly skipped: raw commit counts do NOT inflate knowledge!

            # Assign to each affected module
            for mod in modules_for_dec:
                module_decisions[mod].append({
                    "decision": dec,
                    "contributor_scores": dict(dec_contributor_scores),
                    "has_doc_source": has_doc_source
                })
                if has_doc_source:
                    module_documented_count[mod] += 1

                for contrib, score in dec_contributor_scores.items():
                    module_knowledge[mod][contrib] += score

        # Compute metrics per module
        module_reports = []
        for mod, dec_list in module_decisions.items():
            total_important = len(dec_list)
            scores = module_knowledge[mod]
            total_mod_score = sum(scores.values()) or 1.0

            sorted_contributors = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            top_contributor = sorted_contributors[0][0] if sorted_contributors else "none"
            top_score = sorted_contributors[0][1] if sorted_contributors else 0.0
            top_share = (top_score / total_mod_score) if total_mod_score > 0 else 1.0

            # Count decisions supported primarily (or solely) by one contributor
            single_contributor_decisions = 0
            for item in dec_list:
                item_scores = item["contributor_scores"]
                if len(item_scores) == 1:
                    single_contributor_decisions += 1
                elif len(item_scores) > 1:
                    max_item_s = max(item_scores.values())
                    if (max_item_s / sum(item_scores.values())) >= 0.8:
                        single_contributor_decisions += 1

            single_contributor_share = (
                single_contributor_decisions / total_important
            ) if total_important > 0 else 0.0

            # Bus factor calculation: how many top contributors needed to cover >= 50% of knowledge
            cum_score = 0.0
            bus_factor = 0
            for contrib, sc in sorted_contributors:
                cum_score += sc
                bus_factor += 1
                if cum_score >= 0.5 * total_mod_score:
                    break
            if bus_factor == 0:
                bus_factor = 1

            # Concentration Risk Level
            if bus_factor == 1 or single_contributor_share >= 0.75 or top_share >= 0.70:
                risk_level = "high"
            elif bus_factor == 2 or single_contributor_share >= 0.40 or top_share >= 0.45:
                risk_level = "medium"
            else:
                risk_level = "low"

            doc_coverage = (
                module_documented_count[mod] / total_important
            ) if total_important > 0 else 0.0

            # Generate actionable Onboarding / Documentation Hint
            hints = []
            if risk_level == "high":
                hints.append(f"Concentration risk: {top_contributor} holds {int(top_share * 100)}% of module knowledge.")
            if doc_coverage < 0.5:
                hints.append(f"Low documentation: only {int(doc_coverage * 100)}% of decisions backed by ADR/doc.")
            if not hints:
                hints.append("Balanced knowledge distribution across contributors.")

            onboarding_hint = " ".join(hints)

            module_reports.append({
                "module": mod,
                "important_decisions_count": total_important,
                "bus_factor": bus_factor,
                "risk_level": risk_level,
                "top_contributor": top_contributor,
                "top_contributor_share": round(top_share, 3),
                "single_contributor_decisions": single_contributor_decisions,
                "single_contributor_share": round(single_contributor_share, 3),
                "documentation_coverage": round(doc_coverage, 3),
                "contributors": [
                    {"contributor": c, "knowledge_score": round(s, 2), "share": round(s / total_mod_score, 3)}
                    for c, s in sorted_contributors[:5]
                ],
                "onboarding_hint": onboarding_hint
            })

        # Rank modules: Highest risk first (high -> medium -> low), then by top_contributor_share descending
        risk_priority = {"high": 3, "medium": 2, "low": 1}
        module_reports.sort(
            key=lambda m: (risk_priority.get(m["risk_level"], 0), m["top_contributor_share"]),
            reverse=True
        )

        overall_bus_factor = min((m["bus_factor"] for m in module_reports), default=1)

        return {
            "status": "success",
            "repo": repo,
            "overall_bus_factor": overall_bus_factor,
            "total_modules": len(module_reports),
            "modules": module_reports
        }
