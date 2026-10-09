"""
Code-Level Drift Detection Engine (Section 8.3)
Runs on commit/PR diffs to detect violations of accepted decisions
or re-introductions of previously rejected architectural approaches.
"""
from typing import List, Dict, Any, Optional
import re
from backend.models import Edge, Decision
from backend.db import Database

class DriftDetector:
    def __init__(self, db: Database):
        self.db = db

    def analyze_diff_for_drift(
        self,
        repo: str,
        commit_or_pr_id: str,
        author: str,
        changed_files: List[str],
        diff_text: str
    ) -> List[Dict[str, Any]]:
        """
        Runs Section 8.3 Drift Detection Pass:
        1. Identifies entities touched by the diff.
        2. Retrieves the most recent accepted and rejected decisions for those entities.
        3. Checks if new code violates constraints or reintroduces rejected patterns.
        4. If drift or reintroduction detected, generates a 'drifts_from' edge and queues for review.
        """
        detected_drifts = []

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            for file_path in changed_files:
                # Find matching entity in database
                cursor.execute("""
                SELECT entity_id, canonical_path, current_state_summary FROM entities
                WHERE repo = ? AND (canonical_path = ? OR canonical_path LIKE ?)
                """, (repo, file_path, f"{file_path}::%"))
                matching_entities = cursor.fetchall()

                for ent in matching_entities:
                    ent_id = ent["entity_id"]
                    canonical_path = ent["canonical_path"]

                    # 1. Look up recent accepted decisions affecting this entity
                    cursor.execute("""
                    SELECT d.* FROM decisions d
                    JOIN decision_artifacts da ON d.decision_id = da.decision_id
                    WHERE da.entity_id = ? AND d.state = 'accepted'
                    ORDER BY d.made_at DESC LIMIT 3
                    """, (ent_id,))
                    accepted_decisions = [dict(r) for r in cursor.fetchall()]

                    # 2. Look up rejected alternatives/decisions affecting this entity
                    cursor.execute("""
                    SELECT d.* FROM decisions d
                    JOIN decision_artifacts da ON d.decision_id = da.decision_id
                    WHERE da.entity_id = ? AND d.state = 'rejected'
                    ORDER BY d.made_at DESC LIMIT 3
                    """, (ent_id,))
                    rejected_decisions = [dict(r) for r in cursor.fetchall()]
                    added_lines = []
                    for line in diff_text.splitlines():
                        s = line.strip()
                        if s.startswith('+') and not s.startswith('+++'):
                            added_lines.append(s[1:])
                    diff_lower = "\n".join(added_lines).lower() if added_lines else diff_text.lower()

                    # Drift Rule 1: Re-introduction of a rejected pattern
                    for rej in rejected_decisions:
                        rej_title = rej["title"].lower()
                        # Extract key keywords from rejected decision (e.g. "bang-bang", "synchronous polling", "raw memory cache")
                        keywords = [w for w in rej_title.split() if len(w) > 4 and w not in ("decision", "switch", "rejected", "system")]
                        if keywords and all(k in diff_lower for k in keywords):
                            drift_record = {
                                "drift_type": "reintroduces_rejected",
                                "entity_id": ent_id,
                                "canonical_path": canonical_path,
                                "decision_id": rej["decision_id"],
                                "decision_title": rej["title"],
                                "violating_diff_snippet": diff_text[:500],
                                "reason": f"Diff appears to reintroduce pattern from rejected decision '{rej['title']}'.",
                                "confidence": 0.92,
                                "commit_or_pr_id": commit_or_pr_id,
                                "author": author
                            }
                            detected_drifts.append(drift_record)
                            self._record_drift_edge(ent_id, rej["decision_id"])

                    # Drift Rule 2: Inconsistent or violating code against accepted decision
                    for acc in accepted_decisions:
                        acc_text = (acc["title"] + " " + (acc["rationale"] or "")).lower()
                        
                        # Scenario A: PID controller accepted, but diff reverts to simple threshold/hysteresis
                        if "pid" in acc_text and ("threshold" in diff_lower or "on_off" in diff_lower or "hysteresis" in diff_lower):
                            if "pid_gain" not in diff_lower and "integral" not in diff_lower:
                                drift_record = {
                                    "drift_type": "drift",
                                    "entity_id": ent_id,
                                    "canonical_path": canonical_path,
                                    "decision_id": acc["decision_id"],
                                    "decision_title": acc["title"],
                                    "violating_diff_snippet": diff_text[:500],
                                    "reason": f"Diff removes or bypasses PID control logic established in accepted decision '{acc['title']}'.",
                                    "confidence": 0.89,
                                    "commit_or_pr_id": commit_or_pr_id,
                                    "author": author
                                }
                                detected_drifts.append(drift_record)
                                self._record_drift_edge(ent_id, acc["decision_id"])

                        # Scenario B: Redis cluster accepted, but diff imports local in-memory dict cache
                        if "redis" in acc_text and ("dict_cache = {}" in diff_lower or "local_cache = {}" in diff_lower or "in-memory" in diff_lower):
                            drift_record = {
                                "drift_type": "drift",
                                "entity_id": ent_id,
                                "canonical_path": canonical_path,
                                "decision_id": acc["decision_id"],
                                "decision_title": acc["title"],
                                "violating_diff_snippet": diff_text[:500],
                                "reason": f"Diff introduces in-memory cache defying accepted distributed Redis decision '{acc['title']}'.",
                                "confidence": 0.94,
                                "commit_or_pr_id": commit_or_pr_id,
                                "author": author
                            }
                            detected_drifts.append(drift_record)
                            self._record_drift_edge(ent_id, acc["decision_id"])

        return detected_drifts

    def _record_drift_edge(self, entity_id: str, decision_id: str):
        edge_id = f"edge_drift_{entity_id[:8]}_{decision_id[:8]}"
        edge = Edge(
            edge_id=edge_id,
            edge_type="drifts_from",
            from_id=entity_id,
            from_type="entity",
            to_id=decision_id,
            to_type="decision"
        )
        self.db.upsert_edge(edge)
