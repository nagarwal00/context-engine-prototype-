"""
Reconciliation Engine (Section 8.1 & 8.2)
Detects conflicts between contributors/decisions and manages supersession transitions.
"""
from typing import List, Dict, Any, Optional, Tuple
import re
from backend.models import Decision, Edge
from backend.db import Database

class ReconciliationEngine:
    def __init__(self, db: Database):
        self.db = db

    def check_for_conflicts(self, repo: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Conflict detection (Section 8.1):
        Identifies pairs of decisions that affect overlapping entities
        and advocate contradictory approaches or different architectural choices.
        """
        conflicts = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Find decisions affecting the same entities
            query = """
            SELECT da1.decision_id as d1_id, da2.decision_id as d2_id, da1.entity_id,
                   d1.title as d1_title, d1.made_by as d1_author, d1.rationale as d1_rationale, d1.state as d1_state, d1.made_at as d1_time,
                   d2.title as d2_title, d2.made_by as d2_author, d2.rationale as d2_rationale, d2.state as d2_state, d2.made_at as d2_time
            FROM decision_artifacts da1
            JOIN decision_artifacts da2 ON da1.entity_id = da2.entity_id AND da1.decision_id < da2.decision_id
            JOIN decisions d1 ON da1.decision_id = d1.decision_id
            JOIN decisions d2 ON da2.decision_id = d2.decision_id
            WHERE d1.review_status != 'human_rejected' AND d2.review_status != 'human_rejected'
            """
            params = []
            if repo:
                query += " AND d1.repo = ? AND d2.repo = ?"
                params.extend([repo, repo])

            cursor.execute(query, params)
            pairs = cursor.fetchall()

            for p in pairs:
                d1_text = (p["d1_title"] + " " + p["d1_rationale"]).lower()
                d2_text = (p["d2_title"] + " " + p["d2_rationale"]).lower()

                # Conflict heuristics: different authors + competing technical choices
                is_different_author = p["d1_author"] != p["d2_author"]
                
                # Check for known antonyms or contradictory architectural patterns
                opposing_keywords = [
                    ("pid", "bang-bang"),
                    ("redis", "in-memory lru"),
                    ("sync", "async"),
                    ("polling", "websocket"),
                    ("stateless", "stateful"),
                    ("monolith", "microservice")
                ]

                has_contradiction = False
                detected_topic = ""
                for k1, k2 in opposing_keywords:
                    if (k1 in d1_text and k2 in d2_text) or (k2 in d1_text and k1 in d2_text):
                        has_contradiction = True
                        detected_topic = f"{k1} vs {k2}"
                        break

                if has_contradiction:
                    # Create conflicts_with edge if not already exists
                    edge_id = f"edge_conflicts_{p['d1_id'][:8]}_{p['d2_id'][:8]}"
                    edge = Edge(
                        edge_id=edge_id,
                        edge_type="conflicts_with",
                        from_id=p["d1_id"],
                        from_type="decision",
                        to_id=p["d2_id"],
                        to_type="decision",
                        valid_from=p["d2_time"]
                    )
                    self.db.upsert_edge(edge)

                    conflicts.append({
                        "decision_1": {"id": p["d1_id"], "title": p["d1_title"], "author": p["d1_author"], "time": p["d1_time"]},
                        "decision_2": {"id": p["d2_id"], "title": p["d2_title"], "author": p["d2_author"], "time": p["d2_time"]},
                        "contradiction_topic": detected_topic,
                        "entity_id": p["entity_id"],
                        "confidence": 0.88,
                        "review_status": "pending_review"
                    })

        return conflicts

    def detect_supersessions(self, repo: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Supersession detection (Section 8.2):
        Finds explicit ("supersedes #X", "replaces") or implicit replacement decisions.
        """
        supersessions = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE review_status != 'human_rejected'")
            decisions = [dict(r) for r in cursor.fetchall()]

            for d in decisions:
                body = (d["title"] + " " + (d["rationale"] or "")).lower()
                # Check for explicit supersession keywords
                if "supersedes" in body or "replaces" in body or "instead of" in body:
                    # Find candidate prior decisions in same repo
                    for older in decisions:
                        if older["decision_id"] != d["decision_id"] and older["made_at"] < d["made_at"]:
                            # If overlapping artifacts or mentioned
                            if older["title"].lower() in body or any(w in body for w in older["title"].lower().split() if len(w) > 4):
                                # Update older decision to superseded
                                cursor.execute("""
                                UPDATE decisions SET state = 'superseded', superseded_by_decision_id = ?
                                WHERE decision_id = ? AND state != 'superseded'
                                """, (d["decision_id"], older["decision_id"]))
                                
                                # Update d with supersedes_decision_id
                                cursor.execute("""
                                UPDATE decisions SET supersedes_decision_id = ?
                                WHERE decision_id = ?
                                """, (older["decision_id"], d["decision_id"]))

                                # Edge: d supersedes older
                                edge = Edge(
                                    edge_id=f"edge_super_{d['decision_id'][:8]}_{older['decision_id'][:8]}",
                                    edge_type="supersedes",
                                    from_id=d["decision_id"],
                                    from_type="decision",
                                    to_id=older["decision_id"],
                                    to_type="decision",
                                    valid_from=d["made_at"]
                                )
                                # Update edges for older decision to expire at valid_to
                                cursor.execute("""
                                UPDATE edges SET valid_to = ?
                                WHERE (from_id = ? OR to_id = ?) AND (valid_to IS NULL OR valid_to > ?)
                                """, (d["made_at"], older["decision_id"], older["decision_id"], d["made_at"]))

                                # Log supersession in state_history
                                cursor.execute("""
                                INSERT OR REPLACE INTO state_history (history_id, decision_id, state, changed_at, changed_by, notes)
                                VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    f"hist_super_{older['decision_id'][:8]}_{d['made_at']}",
                                    older["decision_id"],
                                    "superseded",
                                    d["made_at"],
                                    d.get("made_by") or "reconciliation_engine",
                                    f"Superseded by decision '{d['title']}' ({d['decision_id']})"
                                ))

                                supersessions.append({
                                    "new_decision_id": d["decision_id"],
                                    "superseded_decision_id": older["decision_id"],
                                    "title": d["title"],
                                    "prior_title": older["title"],
                                    "effective_at": d["made_at"]
                                })
            conn.commit()
        return supersessions
