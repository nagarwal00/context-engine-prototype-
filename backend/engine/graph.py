"""
Temporal Context Graph Engine (Section 7.2 & 7.3)
Manages time-bounded edges, graph traversal, and canonical graph query execution.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
import json
from backend.models import Edge, Decision, Entity, Event
from backend.db import Database


def _parse_iso(ts: str, field_name: str = "timestamp") -> datetime:
    if not ts or not isinstance(ts, str):
        raise ValueError(f"{field_name} must be a non-empty ISO-8601 string")
    clean_ts = ts.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(clean_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        raise ValueError(f"Invalid ISO-8601 {field_name} '{ts}': {e}") from e


class TemporalGraph:
    def __init__(self, db: Database):
        self.db = db

    def add_edge(
        self,
        edge_or_type: Any = None,
        from_id: Optional[str] = None,
        from_type: Optional[str] = None,
        to_id: Optional[str] = None,
        to_type: Optional[str] = None,
        valid_from: Optional[str] = None,
        valid_to: Optional[str] = None,
        edge_type: Optional[str] = None
    ) -> Edge:
        if isinstance(edge_or_type, Edge):
            edge = edge_or_type
            if not edge.valid_from:
                raise ValueError("valid_from is required for Edge")
            dt_from = _parse_iso(edge.valid_from, "valid_from")
            if edge.valid_to:
                dt_to = _parse_iso(edge.valid_to, "valid_to")
                if dt_to < dt_from:
                    raise ValueError(f"valid_to ({edge.valid_to}) must be >= valid_from ({edge.valid_from})")
            self.db.upsert_edge(edge)
            return edge

        if not valid_from:
            raise ValueError("valid_from is required for add_edge")

        dt_from = _parse_iso(valid_from, "valid_from")
        if valid_to:
            dt_to = _parse_iso(valid_to, "valid_to")
            if dt_to < dt_from:
                raise ValueError(f"valid_to ({valid_to}) must be >= valid_from ({valid_from})")

        actual_type = edge_type or edge_or_type or "related_to"
        edge_id = f"edge_{actual_type}_{str(from_id)[:16]}_{str(to_id)[:16]}"
        edge = Edge(
            edge_id=edge_id,
            edge_type=actual_type,
            from_id=from_id,
            from_type=from_type or "unknown",
            to_id=to_id,
            to_type=to_type or "unknown",
            valid_from=valid_from,
            valid_to=valid_to
        )
        self.db.upsert_edge(edge)
        return edge

    def link_decision_to_artifacts_and_evidence(self, decision: Decision):
        """Creates standard graph edges when a decision is extracted."""
        # 1. Evidenced By: Decision -> Event
        for eid in decision.evidence_event_ids:
            self.add_edge(
                edge_type="evidenced_by",
                from_id=decision.decision_id,
                from_type="decision",
                to_id=eid,
                to_type="event",
                valid_from=decision.made_at
            )

        # 2. Affects: Decision -> Entity
        for ent_id in decision.artifacts_affected:
            self.add_edge(
                edge_type="affects",
                from_id=decision.decision_id,
                from_type="decision",
                to_id=ent_id,
                to_type="entity",
                valid_from=decision.made_at
            )

        # 3. Supersedes: Decision -> Decision
        if decision.supersedes_decision_id:
            self.add_edge(
                edge_type="supersedes",
                from_id=decision.decision_id,
                from_type="decision",
                to_id=decision.supersedes_decision_id,
                to_type="decision",
                valid_from=decision.made_at
            )
            # Invalidate old decision's validity
            with self.db.get_connection() as conn:
                conn.execute("""
                UPDATE edges SET valid_to = ?
                WHERE from_id = ? AND edge_type = 'affects' AND valid_to IS NULL
                """, (decision.made_at, decision.supersedes_decision_id))
                conn.commit()

    def get_full_graph_visualization_data(self, repo: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns nodes and links formatted for interactive node-link visualization
        (Context Graph surface per Section 11.2).
        """
        nodes = []
        links = []
        seen_node_ids: Set[str] = set()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Decision nodes
            dec_query = "SELECT * FROM decisions WHERE review_status != 'human_rejected'"
            dec_params = []
            if repo:
                dec_query += " AND repo = ?"
                dec_params.append(repo)
            cursor.execute(dec_query, dec_params)
            for r in cursor.fetchall():
                d = dict(r)
                node_id = d["decision_id"]
                seen_node_ids.add(node_id)
                nodes.append({
                    "id": node_id,
                    "label": d["title"],
                    "type": "decision",
                    "state": d["state"],
                    "confidence": d["confidence"],
                    "made_by": d["made_by"],
                    "made_at": d["made_at"],
                    "review_status": d["review_status"],
                    "repo": d["repo"],
                    "color": "#10b981" if d["state"] == "accepted" else (
                        "#ef4444" if d["state"] == "rejected" else (
                            "#8b5cf6" if d["state"] == "superseded" else (
                                "#f59e0b" if d["state"] == "proposed" else "#6b7280"
                            )
                        )
                    )
                })

            # 2. Entity nodes
            ent_query = "SELECT * FROM entities"
            ent_params = []
            if repo:
                ent_query += " WHERE repo = ?"
                ent_params.append(repo)
            cursor.execute(ent_query, ent_params)
            for r in cursor.fetchall():
                e = dict(r)
                node_id = e["entity_id"]
                seen_node_ids.add(node_id)
                nodes.append({
                    "id": node_id,
                    "label": e["canonical_path"],
                    "type": "entity",
                    "entity_type": e["entity_type"],
                    "repo": e["repo"],
                    "summary": e["current_state_summary"],
                    "color": "#3b82f6"
                })

            # 3. Event nodes (sample top linked events)
            evt_query = "SELECT event_id, source_type, source_url, title, author, ts, repo FROM events"
            evt_params = []
            if repo:
                evt_query += " WHERE repo = ?"
                evt_params.append(repo)
            evt_query += " LIMIT 50"
            cursor.execute(evt_query, evt_params)
            for r in cursor.fetchall():
                ev = dict(r)
                node_id = ev["event_id"]
                seen_node_ids.add(node_id)
                nodes.append({
                    "id": node_id,
                    "label": ev["title"] or ev["source_type"],
                    "type": "event",
                    "source_type": ev["source_type"],
                    "source_url": ev["source_url"],
                    "author": ev["author"],
                    "timestamp": ev["ts"],
                    "repo": ev["repo"],
                    "color": "#ec4899"
                })

            # 4. Edges
            cursor.execute("SELECT * FROM edges")
            for r in cursor.fetchall():
                ed = dict(r)
                # Only include edge if both endpoints are in seen_node_ids
                if ed["from_id"] in seen_node_ids and ed["to_id"] in seen_node_ids:
                    links.append({
                        "id": ed["edge_id"],
                        "source": ed["from_id"],
                        "target": ed["to_id"],
                        "type": ed["edge_type"],
                        "valid_from": ed["valid_from"],
                        "valid_to": ed["valid_to"],
                        "is_active": ed["valid_to"] is None
                    })

        return {"nodes": nodes, "links": links}
