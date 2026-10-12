"""
Adaptive Developer Onboarding Engine (Step 5.4)
Generates personalized, data-driven learning paths for new contributors
by traversing the context graph, ranking active decisions, identifying
pitfalls/rejected alternatives, and tracking progress via interactive checklists.
"""
import os
import json
import re
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set, Tuple
from backend.models import Decision, Event
from backend.db import Database


class OnboardingEngine:
    def __init__(self, db: Database):
        self.db = db

    def _resolve_entities(
        self,
        repo: str,
        module: Optional[str] = None,
        files: Optional[List[str]] = None,
        task: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Resolves matching code-context entities from DB based on role/module/files/task."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if repo:
                cursor.execute("SELECT * FROM entities WHERE repo = ?", (repo,))
            else:
                cursor.execute("SELECT * FROM entities")
            all_entities = [dict(r) for r in cursor.fetchall()]

        if not all_entities:
            return []

        clean_files = [f.replace("\\", "/").strip().lower() for f in (files or []) if f.strip()]
        clean_module = (module or "").strip().lower()
        clean_task = (task or "").strip().lower()

        matched = []
        for ent in all_entities:
            cpath = ent.get("canonical_path", "").replace("\\", "/").lower()
            aliases = []
            if ent.get("aliases"):
                try:
                    aliases = json.loads(ent["aliases"])
                except Exception:
                    aliases = []

            # Check direct file match
            file_match = any(
                (f == cpath or f in cpath or cpath.endswith(f))
                for f in clean_files
            ) if clean_files else False

            # Check module match
            mod_match = False
            if clean_module:
                # check if module is a path segment (e.g., src/thermal/... or thermal)
                parts = cpath.split("/")
                mod_match = (clean_module in parts) or (clean_module in cpath)

            # Check task keyword match
            task_match = False
            if clean_task:
                task_tokens = [w for w in re.split(r"\W+", clean_task) if len(w) > 3]
                task_match = any(tok in cpath for tok in task_tokens)

            if file_match or mod_match or task_match:
                matched.append(ent)

        # If no specific filter matched or filters weren't supplied, return all entities in repo
        return matched if (clean_files or clean_module or clean_task) else all_entities

    def _rank_decisions(
        self,
        decisions: List[Dict[str, Any]],
        direct_entity_ids: Set[str],
        role: Optional[str] = None
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Ranks decisions for onboarding per Step 5.4:
        - Active/Accepted first
        - Evidence label weight
        - Recency
        - Pitfalls / Rejected alternatives richness
        - Role keyword alignment
        """
        clean_role = (role or "").lower()
        scored = []

        state_base_weights = {
            "accepted": 100.0,
            "tested": 80.0,
            "proposed": 65.0,
            "under_review": 60.0,
            "reopened": 55.0,
            "stale": 50.0,
            "superseded": 40.0,
            "rejected": 30.0,
        }

        evidence_weights = {
            "strong": 30.0,
            "moderate": 20.0,
            "weak": 10.0,
            "insufficient": 0.0,
            "contradicted": -10.0,
        }

        for dec in decisions:
            state = dec.get("state", "proposed")
            score = state_base_weights.get(state, 50.0)

            ev_label = dec.get("evidence_assessment", "insufficient")
            score += evidence_weights.get(ev_label, 0.0)

            # Check if decision touches directly resolved entities
            artifacts = dec.get("artifacts_affected") or []
            if isinstance(artifacts, str):
                try:
                    artifacts = json.loads(artifacts)
                except Exception:
                    artifacts = [artifacts]

            touches_direct = any(
                (a in direct_entity_ids or any(de_id in a for de_id in direct_entity_ids))
                for a in artifacts
            )
            if touches_direct:
                score += 25.0

            # Alternatives considered bonus (richer context)
            alts = dec.get("alternatives_considered") or []
            if isinstance(alts, str):
                try:
                    alts = json.loads(alts)
                except Exception:
                    alts = []
            score += min(len(alts) * 5.0, 15.0)

            # Role keywords alignment
            if clean_role:
                role_tokens = [w for w in re.split(r"\W+", clean_role) if len(w) > 3]
                text_content = f"{dec.get('title','')} {dec.get('rationale','')} {dec.get('category','')}".lower()
                role_matches = sum(1 for tok in role_tokens if tok in text_content)
                score += min(role_matches * 10.0, 30.0)

            scored.append((score, dec))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    def generate_learning_path(
        self,
        repo: str,
        role: Optional[str] = None,
        module: Optional[str] = None,
        files: Optional[List[str]] = None,
        task: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Builds a structured, request-driven learning path:
        1. Overview of the module
        2. Key active decisions
        3. Important commits / architectural discussions
        4. Rejected alternatives & known pitfalls
        5. Open / stale items
        """
        # Auto-detect repo if missing
        if not repo:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT DISTINCT repo FROM decisions LIMIT 1")
                r = cur.fetchone()
                repo = r["repo"] if r else "acme-ecommerce/payment-core"

        # 1. Resolve matching entities
        resolved_entities = self._resolve_entities(repo, module=module, files=files, task=task)
        resolved_entity_ids = {e["entity_id"] for e in resolved_entities}
        resolved_paths = [e["canonical_path"] for e in resolved_entities]

        # 2. Fetch decisions and associated artifacts/evidence
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Decision-artifact links for resolved entities
            if resolved_entity_ids:
                placeholders = ",".join("?" for _ in resolved_entity_ids)
                cur.execute(f"""
                SELECT DISTINCT decision_id FROM decision_artifacts
                WHERE entity_id IN ({placeholders})
                """, list(resolved_entity_ids))
                linked_dec_ids = {r["decision_id"] for r in cur.fetchall()}
            else:
                linked_dec_ids = set()

            # Fetch all repo decisions
            cur.execute("SELECT * FROM decisions WHERE repo = ?", (repo,))
            repo_decisions = [dict(r) for r in cur.fetchall()]

            # Fetch all repo events
            cur.execute("SELECT * FROM events WHERE repo = ?", (repo,))
            event_map = {r["event_id"]: dict(r) for r in cur.fetchall()}

            # Fetch decision evidence links
            cur.execute("""
            SELECT de.decision_id, de.event_id
            FROM decision_evidence de
            JOIN decisions d ON de.decision_id = d.decision_id
            WHERE d.repo = ?
            """, (repo,))
            dec_evidence_map: Dict[str, List[str]] = defaultdict(list)
            for r in cur.fetchall():
                dec_evidence_map[r["decision_id"]].append(r["event_id"])

            # Fetch assumptions
            cur.execute("""
            SELECT da.*
            FROM decision_assumptions da
            JOIN decisions d ON da.decision_id = d.decision_id
            WHERE d.repo = ?
            """, (repo,))
            assumptions_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            for r in cur.fetchall():
                assumptions_map[r["decision_id"]].append(dict(r))

        # Filter candidate decisions:
        # Those linked to resolved entities, or whose text touches module/files/task
        candidate_decisions = []
        clean_mod = (module or "").lower()
        clean_files = [f.lower() for f in (files or [])]
        clean_task = (task or "").lower()

        for d in repo_decisions:
            dec_id = d["decision_id"]
            d_text = f"{d.get('title','')} {d.get('rationale','')} {d.get('made_by','')}".lower()
            d_artifacts = d.get("artifacts_affected") or []
            if isinstance(d_artifacts, str):
                try:
                    d_artifacts = json.loads(d_artifacts)
                except Exception:
                    d_artifacts = [d_artifacts]
            d_art_text = " ".join(str(a) for a in d_artifacts).lower()

            is_linked = dec_id in linked_dec_ids
            touches_mod = clean_mod and (clean_mod in d_text or clean_mod in d_art_text)
            touches_file = any((f in d_text or f in d_art_text) for f in clean_files) if clean_files else False
            touches_task = clean_task and any(
                tok in d_text or tok in d_art_text
                for tok in re.split(r"\W+", clean_task) if len(tok) > 3
            )

            # If user specified filters, require at least one match; otherwise include all
            if (clean_mod or clean_files or clean_task or resolved_entity_ids):
                if is_linked or touches_mod or touches_file or touches_task:
                    candidate_decisions.append(d)
            else:
                candidate_decisions.append(d)

        # 3. Rank Decisions
        scored_decisions = self._rank_decisions(
            candidate_decisions,
            direct_entity_ids=resolved_entity_ids,
            role=role
        )

        # 4. Construct Learning Path Sections
        checklist_items = []
        active_decisions_list = []
        pitfalls_list = []
        open_stale_list = []
        discussion_evidence_set: Set[str] = set()
        discussion_evidence_list = []

        module_label = module.capitalize() if module else "Core Subsystem"
        scope_title = f"{module_label} Architectural Onboarding"
        if role:
            scope_title += f" ({role})"

        # Overview section
        top_contributors = defaultdict(int)
        for _, d in scored_decisions:
            if d.get("made_by"):
                top_contributors[d["made_by"]] += 1

        top_contrib_names = sorted(top_contributors.items(), key=lambda x: x[1], reverse=True)
        primary_architects = [c[0] for c in top_contrib_names[:3]]

        overview_item_id = "chk_overview_01"
        checklist_items.append({
            "id": overview_item_id,
            "category": "overview",
            "title": f"Review Subsystem Architecture & Key Artifacts for {module_label}",
            "completed": False
        })

        overview_section = {
            "title": scope_title,
            "module": module or "all",
            "role": role or "developer",
            "task": task or "",
            "affected_artifacts": resolved_paths[:8] if resolved_paths else ["src/core"],
            "primary_architects": primary_architects,
            "total_relevant_decisions": len(scored_decisions),
            "summary": (
                f"Onboarding guide for {module_label} in repository '{repo}'. "
                f"Contains {len(candidate_decisions)} relevant architectural decisions "
                f"curated for {role or 'engineering'}."
            )
        }

        # Populate decision categories
        for score, dec in scored_decisions:
            dec_id = dec["decision_id"]
            state = dec.get("state", "proposed")
            freshness = dec.get("freshness", "fresh")
            title = dec.get("title", "")
            rationale = dec.get("rationale") or dec.get("title") or ""
            evidence_label = dec.get("evidence_assessment", "insufficient")
            ev_ids = dec_evidence_map.get(dec_id, [])
            assumptions = assumptions_map.get(dec_id, [])

            # Source links for evidence
            citations = []
            for eid in ev_ids:
                ev = event_map.get(eid)
                if ev:
                    citations.append({
                        "event_id": eid,
                        "source_type": ev.get("source_type"),
                        "source_url": ev.get("source_url"),
                        "title": ev.get("title") or f"{ev.get('source_type')} {ev.get('source_id')}",
                        "author": ev.get("author")
                    })
                    if eid not in discussion_evidence_set:
                        discussion_evidence_set.add(eid)
                        discussion_evidence_list.append({
                            "event_id": eid,
                            "source_type": ev.get("source_type"),
                            "source_url": ev.get("source_url"),
                            "title": ev.get("title") or ev.get("source_id"),
                            "author": ev.get("author"),
                            "timestamp": ev.get("timestamp"),
                            "summary": (ev.get("body") or "")[:250]
                        })

            # 4.A Active Decisions (accepted / tested)
            if state in ("accepted", "tested") and freshness != "stale":
                item_id = f"chk_dec_{dec_id}"
                checklist_items.append({
                    "id": item_id,
                    "category": "active_decision",
                    "title": f"Study Decision: {title}",
                    "decision_id": dec_id,
                    "completed": False
                })
                active_decisions_list.append({
                    "decision_id": dec_id,
                    "title": title,
                    "state": state,
                    "evidence_label": evidence_label,
                    "made_by": dec.get("made_by", "unknown"),
                    "made_at": dec.get("made_at"),
                    "rationale": rationale,
                    "citations": citations,
                    "assumptions": [a.get("text") for a in assumptions]
                })

            # 4.B Pitfalls & Rejected/Superseded Alternatives
            # If the decision is explicitly rejected or superseded
            if state in ("rejected", "superseded"):
                pitfall_id = f"chk_pitfall_{dec_id}"
                label_prefix = "Superseded Architecture:" if state == "superseded" else "Avoid Pitfall:"
                checklist_items.append({
                    "id": pitfall_id,
                    "category": "superseded" if state == "superseded" else "pitfall",
                    "title": f"{label_prefix} {title}",
                    "decision_id": dec_id,
                    "completed": False
                })
                pitfalls_list.append({
                    "decision_id": dec_id,
                    "title": f"{label_prefix} {title}",
                    "rejection_reason": rationale,
                    "rejected_by": dec.get("made_by", "architecture-review"),
                    "citations": citations
                })

            # Also unpack alternatives_considered inside accepted/tested decisions
            raw_alts = dec.get("alternatives_considered") or []
            if isinstance(raw_alts, str):
                try:
                    raw_alts = json.loads(raw_alts)
                except Exception:
                    raw_alts = []
            for idx, alt in enumerate(raw_alts):
                desc = alt.get("description") if isinstance(alt, dict) else str(alt)
                reason = alt.get("rejection_reason") if isinstance(alt, dict) else "Discarded in favor of accepted approach"
                pitfall_id = f"chk_alt_{dec_id}_{idx}"
                checklist_items.append({
                    "id": pitfall_id,
                    "category": "pitfall",
                    "title": f"Known Alternative Pitfall in '{title}': {desc[:60]}...",
                    "decision_id": dec_id,
                    "completed": False
                })
                pitfalls_list.append({
                    "decision_id": dec_id,
                    "title": f"Rejected Alternative: {desc}",
                    "rejection_reason": reason,
                    "rejected_by": dec.get("made_by", "team"),
                    "citations": citations
                })

            # 4.C Open Items & Stale Decisions
            if freshness in ("stale", "under_review") or state in ("proposed", "reopened"):
                open_id = f"chk_open_{dec_id}"
                checklist_items.append({
                    "id": open_id,
                    "category": "open_stale",
                    "title": f"Review Open/Stale Item: {title}",
                    "decision_id": dec_id,
                    "completed": False
                })
                open_stale_list.append({
                    "decision_id": dec_id,
                    "title": title,
                    "state": state,
                    "freshness": freshness,
                    "rationale": rationale,
                    "broken_assumptions": [a.get("text") for a in assumptions if a.get("status") == "broken"],
                    "citations": citations
                })

        # Add checklist item for architectural evidence reading
        if discussion_evidence_list:
            checklist_items.append({
                "id": "chk_evidence_docs",
                "category": "evidence",
                "title": f"Read Core ADRs and Design PRs ({len(discussion_evidence_list)} references)",
                "completed": False
            })

        return {
            "status": "success",
            "repo": repo,
            "role": role or "developer",
            "module": module or "all",
            "files": files or [],
            "task": task or "",
            "total_items": len(checklist_items),
            "checklist": checklist_items,
            "sections": {
                "overview": overview_section,
                "active_decisions": active_decisions_list,
                "architectural_evidence": discussion_evidence_list[:10],
                "rejected_pitfalls": pitfalls_list,
                "open_stale_items": open_stale_list
            }
        }

    def plain_search(self, repo: str, query: str, limit: int = 10) -> List[str]:
        """
        Baseline naive text search against decisions for recall comparison.
        Returns matched decision IDs.
        """
        tokens = [w.lower() for w in re.split(r"\W+", query) if len(w) > 2]
        if not tokens:
            return []

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT decision_id, title, rationale, made_by FROM decisions WHERE repo = ?", (repo,))
            rows = [dict(r) for r in cur.fetchall()]

        matched = []
        for r in rows:
            text = f"{r.get('title','')} {r.get('rationale','')} {r.get('made_by','')}".lower()
            match_count = sum(1 for tok in tokens if tok in text)
            if match_count > 0:
                matched.append((match_count, r["decision_id"]))

        matched.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matched[:limit]]

    def evaluate_onboarding_tasks(self, tasks_path: str) -> Dict[str, Any]:
        """
        Loads evaluation/onboarding_tasks.json and computes:
        1. Onboarding Recall: fraction of required ground-truth decisions found in learning path.
        2. Plain Search Recall: fraction found by naive keyword search.
        3. Comparison metric showing adaptive onboarding superiority.
        """
        if not os.path.exists(tasks_path):
            raise FileNotFoundError(f"Onboarding tasks file not found: {tasks_path}")

        with open(tasks_path, "r", encoding="utf-8") as f:
            tasks = json.load(f)

        results = []
        total_onboarding_hits = 0
        total_search_hits = 0
        total_required_decisions = 0

        for t in tasks:
            task_id = t["task_id"]
            repo = t["repo"]
            role = t.get("role")
            module = t.get("module")
            files = t.get("files", [])
            query = t.get("search_query") or f"{module} {role}"
            required = set(t.get("required_decision_ids", []))

            # 1. Run adaptive onboarding
            path_result = self.generate_learning_path(
                repo=repo,
                role=role,
                module=module,
                files=files,
                task=t.get("task_description")
            )

            # Extract all decision IDs present in the learning path
            found_path_dec_ids = set()
            for dec in path_result["sections"]["active_decisions"]:
                found_path_dec_ids.add(dec["decision_id"])
            for pitfall in path_result["sections"]["rejected_pitfalls"]:
                found_path_dec_ids.add(pitfall["decision_id"])
            for open_it in path_result["sections"]["open_stale_items"]:
                found_path_dec_ids.add(open_it["decision_id"])

            onboarding_hits = len(required & found_path_dec_ids)
            onboarding_recall = (onboarding_hits / len(required)) if required else 1.0

            # 2. Run plain keyword search
            search_found_ids = set(self.plain_search(repo, query, limit=10))
            search_hits = len(required & search_found_ids)
            search_recall = (search_hits / len(required)) if required else 1.0

            total_onboarding_hits += onboarding_hits
            total_search_hits += search_hits
            total_required_decisions += len(required)

            results.append({
                "task_id": task_id,
                "task_name": t.get("task_name"),
                "repo": repo,
                "required_count": len(required),
                "onboarding_hits": onboarding_hits,
                "onboarding_recall": round(onboarding_recall, 3),
                "search_hits": search_hits,
                "search_recall": round(search_recall, 3),
                "recall_gain": round(onboarding_recall - search_recall, 3)
            })

        overall_onboarding_recall = (
            total_onboarding_hits / total_required_decisions
        ) if total_required_decisions > 0 else 1.0

        overall_search_recall = (
            total_search_hits / total_required_decisions
        ) if total_required_decisions > 0 else 0.0

        return {
            "status": "success",
            "total_tasks": len(tasks),
            "total_required_decisions": total_required_decisions,
            "overall_onboarding_recall": round(overall_onboarding_recall, 4),
            "overall_search_recall": round(overall_search_recall, 4),
            "recall_gain": round(overall_onboarding_recall - overall_search_recall, 4),
            "tasks": results
        }
