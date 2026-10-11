"""
Reconciliation Engine (Section 8.1 & 8.2)
Detects conflicts between contributors/decisions and manages supersession transitions.
"""
from typing import List, Dict, Any, Optional, Tuple
import re
from backend.models import Decision, Edge
from backend.db import Database

GENERIC_STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing",
    "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is",
    "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should",
    "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd",
    "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's",
    "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves",
    # Generic domain filler terms
    "architecture", "decision", "system", "service", "module", "update", "implement", "support",
    "database", "data", "code", "design", "refactor", "change", "feature", "fix", "improve", "optimize",
    "switch", "use", "using", "new", "initial", "setup", "standard", "pattern", "component", "method",
    "function", "logic", "handler", "request", "response", "server", "client", "model", "pipeline",
    "query", "local", "memory", "store", "project", "app", "application", "file", "test", "tests"
}

REPLACEMENT_CUES = ("supersedes", "replaces", "instead of", "migrate from", "migrated from", "superseded by")


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
        Evidence-based supersession detection (P1-d / Step 1.6):
        Priority:
          (1) Explicit reference (decision id, ADR number, #PR/issue number, 'supersedes ADR-0003')
          (2) Shared affected entity (>= 1 common entity) AND later in time AND replacement cue
          (3) Title-word overlap used ONLY to break ties among candidates that already share an entity.
        
        Ambiguous cases (>1 candidate or word overlap only) are routed to the review queue
        as 'supersession_candidate' and never auto-linked.
        """
        supersessions = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Fetch all non-rejected decisions
            dec_query = "SELECT * FROM decisions WHERE review_status != 'human_rejected'"
            dec_params = []
            if repo:
                dec_query += " AND repo = ?"
                dec_params.append(repo)
            cursor.execute(dec_query, dec_params)
            decisions = [dict(r) for r in cursor.fetchall()]

            # Fetch artifact mappings for all decisions
            cursor.execute("SELECT decision_id, entity_id FROM decision_artifacts")
            artifact_map: Dict[str, Set[str]] = {}
            for r in cursor.fetchall():
                artifact_map.setdefault(r["decision_id"], set()).add(r["entity_id"])

            for d in decisions:
                d_id = d["decision_id"]
                d_time = d["made_at"]
                d_text = (d["title"] + " " + (d.get("rationale") or "")).lower()
                d_entities = artifact_map.get(d_id, set())

                # Check if decision text mentions any replacement cue
                has_replacement_cue = any(cue in d_text for cue in REPLACEMENT_CUES)

                # Find prior decisions that could be candidates
                candidates_p1 = []  # Priority 1: Explicit reference
                candidates_p2 = []  # Priority 2: Shared entity + later in time + replacement cue
                candidates_p3 = []  # Priority 3: Shared entity + word overlap only

                for older in decisions:
                    older_id = older["decision_id"]
                    older_time = older["made_at"]
                    if older_id == d_id or older_time >= d_time:
                        continue
                    if repo and older.get("repo") != d.get("repo"):
                        continue

                    older_title = older["title"].lower()
                    older_text = (older["title"] + " " + (older.get("rationale") or "")).lower()
                    shared_entities = d_entities.intersection(artifact_map.get(older_id, set()))

                    # Priority 1: Explicit reference check
                    is_explicit = False
                    reason = ""

                    # 1a. Decision ID match
                    if older_id.lower() in d_text:
                        is_explicit = True
                        reason = f"Explicit decision ID reference '{older_id}'"

                    # 1b. ADR identifier match (e.g. ADR-0003, ADR 0003, ADR-3)
                    older_adrs = re.findall(r'\badr[-_ ]?0*(\d+)\b', older_title)
                    if not is_explicit and older_adrs:
                        for adr_num in older_adrs:
                            if re.search(r'\badr[-_ ]?0*' + adr_num + r'\b', d_text):
                                is_explicit = True
                                reason = f"Explicit ADR reference 'ADR-{adr_num}'"
                                break

                    # 1c. PR / issue number match with cue (e.g. supersedes #101, closes #101)
                    older_prs = re.findall(r'#(\d+)\b', older_title + " " + older_text)
                    if not is_explicit and older_prs:
                        for pr_num in older_prs:
                            if re.search(r'(?:supersedes|replaces|instead of|closes)\s+#0*' + pr_num + r'\b', d_text):
                                is_explicit = True
                                reason = f"Explicit issue/PR reference '#{pr_num}'"
                                break

                    # 1d. Exact older title match with replacement cue
                    if not is_explicit and len(older_title) > 8 and older_title in d_text and has_replacement_cue:
                        is_explicit = True
                        reason = f"Explicit title citation '{older['title']}' with replacement cue"

                    if is_explicit:
                        candidates_p1.append({
                            "decision": older,
                            "reason": reason,
                            "priority": 1
                        })
                        continue

                    # Priority 2: Shared affected entity + replacement cue
                    if len(shared_entities) >= 1 and has_replacement_cue:
                        candidates_p2.append({
                            "decision": older,
                            "reason": f"Shared entity ({len(shared_entities)} common) with replacement cue",
                            "priority": 2
                        })
                        continue

                    # Priority 3: Title-word overlap among candidates that share an entity
                    if len(shared_entities) >= 1:
                        older_words = {
                            w for w in re.findall(r'[a-zA-Z0-9]+', older_title)
                            if len(w) > 3 and w not in GENERIC_STOP_WORDS
                        }
                        d_words = {
                            w for w in re.findall(r'[a-zA-Z0-9]+', d_text)
                            if len(w) > 3 and w not in GENERIC_STOP_WORDS
                        }
                        overlap = older_words.intersection(d_words)
                        if overlap:
                            candidates_p3.append({
                                "decision": older,
                                "reason": f"Shared entity with non-stopword title overlap: {overlap}",
                                "overlap_count": len(overlap),
                                "priority": 3
                            })

                # Selection logic per §1.6:
                chosen_candidate = None

                if len(candidates_p1) == 1:
                    chosen_candidate = candidates_p1[0]["decision"]
                elif len(candidates_p1) > 1:
                    # Ambiguous explicit references: send to review queue
                    self._create_review_queue_supersession_candidates(cursor, d, candidates_p1)
                elif len(candidates_p2) == 1:
                    chosen_candidate = candidates_p2[0]["decision"]
                elif len(candidates_p2) > 1:
                    # Tie-break using non-stop word overlap among shared-entity candidates
                    scored = []
                    for c in candidates_p2:
                        older_w = {
                            w for w in re.findall(r'[a-zA-Z0-9]+', c["decision"]["title"].lower())
                            if len(w) > 3 and w not in GENERIC_STOP_WORDS
                        }
                        d_w = {
                            w for w in re.findall(r'[a-zA-Z0-9]+', d_text)
                            if len(w) > 3 and w not in GENERIC_STOP_WORDS
                        }
                        scored.append((len(older_w.intersection(d_w)), c))
                    scored.sort(key=lambda x: x[0], reverse=True)
                    # If strictly top score without tie:
                    if len(scored) > 1 and scored[0][0] > scored[1][0] and scored[0][0] > 0:
                        chosen_candidate = scored[0][1]["decision"]
                    else:
                        # Ambiguous: send to review queue
                        self._create_review_queue_supersession_candidates(cursor, d, candidates_p2)
                elif candidates_p3:
                    # Only match is word overlap: DO NOT auto-link, route to review queue
                    self._create_review_queue_supersession_candidates(cursor, d, candidates_p3)

                # Auto-link ONLY if a single qualified candidate was selected
                if chosen_candidate:
                    older = chosen_candidate
                    from backend.engine.lifecycle import transition
                    try:
                        transition(
                            conn,
                            older["decision_id"],
                            "superseded",
                            actor=d.get("made_by") or "reconciliation_engine",
                            reason=f"Superseded by decision '{d['title']}' ({d_id})",
                            at=d_time,
                            superseded_by_id=d_id
                        )
                        supersessions.append({
                            "new_decision_id": d_id,
                            "superseded_decision_id": older["decision_id"],
                            "title": d["title"],
                            "prior_title": older["title"],
                            "effective_at": d_time
                        })
                    except Exception:
                        pass

            conn.commit()

        return supersessions

    def _create_review_queue_supersession_candidates(
        self,
        cursor,
        new_dec: Dict[str, Any],
        candidates: List[Dict[str, Any]]
    ):
        """Creates review queue items for ambiguous supersession candidates."""
        for c in candidates:
            older = c["decision"]
            edge_id = f"edge_super_cand_{new_dec['decision_id']}_{older['decision_id']}"
            cursor.execute("""
            INSERT OR REPLACE INTO edges (edge_id, edge_type, from_id, from_type, to_id, to_type, valid_from, valid_to)
            VALUES (?, 'supersession_candidate', ?, 'decision', ?, 'decision', ?, NULL)
            """, (
                edge_id,
                new_dec["decision_id"],
                older["decision_id"],
                new_dec["made_at"]
            ))

