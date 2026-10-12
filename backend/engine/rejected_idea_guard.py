"""
Rejected-Idea Guard Engine (Step 3.5 - Headline Novelty)
Detects proposed code or designs in PRs that reintroduce previously rejected
architectural decisions or rejected alternatives.

Advisory only (never auto-blocks). Provides original discussion links,
recorded rejection reasons, changed-circumstances hints, and developer feedback loop.
"""
import fnmatch
import math
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.db import Database
from backend.models import Decision, GuardRule
from backend.engine.lifecycle import transition
from backend.engine.entity_res import EntityResolver

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "did", "do", "does", "doing", "don", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
    "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off",
    "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own",
    "same", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "you", "your", "yours", "yourself", "yourselves",
    "pr", "pull", "request", "issue", "feat", "fix", "update", "patch", "closes", "resolves"
}


def _path_matches_pattern(filepath: str, pattern: str) -> bool:
    """Check if a file path matches a glob pattern, supporting ** wildcards."""
    fp = filepath.replace("\\", "/").strip()
    pat = pattern.replace("\\", "/").strip()

    if "**" not in pat:
        if fnmatch.fnmatch(fp, pat):
            return True
        if "/" not in pat and fnmatch.fnmatch(os.path.basename(fp), pat):
            return True
        return False

    parts = pat.split("**/")
    regex_parts = []
    for part in parts:
        escaped = re.escape(part).replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
        regex_parts.append(escaped)
    regex = r"(?:.+/)?".join(regex_parts)
    return bool(re.fullmatch(regex, fp))


def compute_tfidf_cosine(doc1_tokens: List[str], doc2_tokens: List[str]) -> float:
    """Computes TF-IDF cosine similarity between two lists of tokens using Python standard library."""
    if not doc1_tokens or not doc2_tokens:
        return 0.0

    vocab = list(set(doc1_tokens) | set(doc2_tokens))
    if not vocab:
        return 0.0

    from collections import Counter
    c1 = Counter(doc1_tokens)
    c2 = Counter(doc2_tokens)

    v1: List[float] = []
    v2: List[float] = []
    len1 = len(doc1_tokens)
    len2 = len(doc2_tokens)

    for w in vocab:
        df = (1 if w in c1 else 0) + (1 if w in c2 else 0)
        # Standard smoothed 2-doc IDF
        idf = math.log(1.0 + 2.0 / df)
        w1 = (c1[w] / len1) * idf
        w2 = (c2[w] / len2) * idf
        v1.append(w1)
        v2.append(w2)

    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return float(dot / (norm1 * norm2))


class RejectedIdeaGuard:
    """
    Evaluates pull requests and proposals against previously rejected architectural
    decisions and rejected alternatives.
    """

    def __init__(self, db: Database):
        self.db = db
        self.entity_resolver = EntityResolver(db)

    def extract_proposal_design(
        self,
        title: str,
        body: str,
        diff_text: str,
        changed_files: List[str]
    ) -> Dict[str, Any]:
        """
        Extracts structural indicators, identifiers, config keys, and substantive tokens
        from a proposal or PR. Filters out historical decommissioning comments.
        """
        HISTORICAL_MARKERS = [
            "decommissioned", "deprecated", "replaced by", "was replaced",
            "migrated from", "superseded", "historical note", "obsolete", "removed in"
        ]

        text = (title or "") + " " + (body or "")
        words = re.findall(r"[a-zA-Z0-9_\-\.]{3,}", text.lower())
        tokens = [w for w in words if w not in STOPWORDS]

        added_imports: Set[str] = set()
        added_identifiers: Set[str] = set()
        added_configs: Set[str] = set()
        clean_added_lines: List[str] = []
        has_executable_code = False

        for line in diff_text.splitlines():
            sline = line.strip()
            if not sline.startswith("+") or sline.startswith("+++"):
                continue
            raw = sline[1:].strip()
            if not raw:
                continue

            is_comment = raw.startswith(("#", "//", "/*", "*", "'''", '"""'))
            is_historical = is_comment and any(h in raw.lower() for h in HISTORICAL_MARKERS)
            if is_historical:
                # Skip historical documentation comments from code design analysis
                continue

            if not is_comment:
                has_executable_code = True

            clean_added_lines.append(raw)

            # 1. Imports / dependencies
            m_imp = re.match(r"^(?:import\s+([a-zA-Z0-9_\.]+)|from\s+([a-zA-Z0-9_\.]+)\s+import)", raw)
            if m_imp:
                mod = m_imp.group(1) or m_imp.group(2)
                if mod:
                    added_imports.add(mod.split(".")[0].lower())

            # 2. Function calls or definitions
            m_def = re.match(r"^(?:def|class)\s+([a-zA-Z0-9_]+)", raw)
            if m_def:
                added_identifiers.add(m_def.group(1).lower())
            for fn_call in re.findall(r"\b([a-zA-Z0-9_]{3,})\s*\(", raw):
                added_identifiers.add(fn_call.lower())

            # 3. Variable assignments
            m_assign = re.match(r"^([a-zA-Z0-9_]{3,})\s*=", raw)
            if m_assign:
                added_identifiers.add(m_assign.group(1).lower())

            # 4. Config keys (JSON/YAML/code)
            m_cfg = re.match(r"^[\"']?([a-zA-Z0-9_\.\-]{3,})[\"']?\s*[:=]", raw)
            if m_cfg:
                added_configs.add(m_cfg.group(1).lower())

            # Dependency manifest lines (requirements.txt / Cargo.toml)
            if any(cf.endswith(("requirements.txt", "package.json", "Cargo.toml")) for cf in changed_files):
                m_dep = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*[=><~:]", raw)
                if m_dep:
                    added_imports.add(m_dep.group(1).lower())

        # Include identifier tokens in substance comparison
        all_tokens = list(tokens) + list(added_identifiers) + list(added_imports)

        norm_files = [f.replace("\\", "/").strip() for f in changed_files if f and f != "unknown"]

        return {
            "tokens": all_tokens,
            "added_imports": list(added_imports),
            "added_identifiers": list(added_identifiers),
            "added_configs": list(added_configs),
            "clean_added_lines": clean_added_lines,
            "changed_files": norm_files,
            "has_executable_code": has_executable_code
        }

    def get_rejected_candidates(self, repo: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all candidate rejected decisions and rejected alternatives.
        """
        candidates: List[Dict[str, Any]] = []
        all_decisions = self.db.get_all_decisions(repo=repo) if repo else self.db.get_all_decisions()

        for d in all_decisions:
            # 1. Decision itself is in state 'rejected' or 'reopened'
            if d.state in ("rejected", "reopened"):
                text_content = f"{d.title} {d.rationale or ''}"
                words = re.findall(r"[a-zA-Z0-9_\-\.]{3,}", text_content.lower())
                tokens = [w for w in words if w not in STOPWORDS]

                evidence_passages = self.db.get_decision_evidence_passages(d.decision_id)

                candidates.append({
                    "candidate_id": f"cand_{d.decision_id}",
                    "decision_id": d.decision_id,
                    "decision_title": d.title,
                    "decision_state": d.state,
                    "repo": d.repo,
                    "made_by": d.made_by,
                    "made_at": d.made_at,
                    "rejection_reason": d.rationale or f"Decision marked {d.state}",
                    "description": d.title,
                    "tokens": tokens,
                    "artifacts_affected": d.artifacts_affected or [],
                    "evidence_passages": evidence_passages,
                    "is_alternative": False,
                    "alternative_index": None
                })

            # 2. Decision has alternatives_considered with a rejection reason
            for idx, alt in enumerate(d.alternatives_considered or []):
                alt_desc = alt.get("description", "")
                alt_reason = alt.get("rejection_reason", "")
                if not alt_desc and not alt_reason:
                    continue

                text_content = f"{d.title} {d.rationale or ''} {alt_desc} {alt_reason}"
                words = re.findall(r"[a-zA-Z0-9_\-\.]{3,}", text_content.lower())
                tokens = [w for w in words if w not in STOPWORDS]

                evidence_passages = self.db.get_decision_evidence_passages(d.decision_id)

                candidates.append({
                    "candidate_id": f"cand_{d.decision_id}_alt_{idx}",
                    "decision_id": d.decision_id,
                    "decision_title": d.title,
                    "decision_state": d.state,
                    "repo": d.repo,
                    "made_by": d.made_by,
                    "made_at": d.made_at,
                    "rejection_reason": alt_reason or f"Rejected in favor of: {d.title}",
                    "description": alt_desc or d.title,
                    "rationale": d.rationale or "",
                    "tokens": tokens,
                    "artifacts_affected": d.artifacts_affected or [],
                    "evidence_passages": evidence_passages,
                    "is_alternative": True,
                    "alternative_index": idx
                })

        return candidates

    def _get_changed_circumstances(
        self,
        candidate: Dict[str, Any],
        proposal: Dict[str, Any]
    ) -> List[str]:
        """
        Identifies changed-circumstances hints (time elapsed, later decisions, dependency shifts).
        """
        hints: List[str] = []
        made_at_str = candidate.get("made_at", "")

        # 1. Time since decision
        if made_at_str:
            try:
                # Normalise ISO timestamp
                ts_clean = made_at_str.replace("Z", "+00:00")
                dt_made = datetime.fromisoformat(ts_clean)
                dt_now = datetime.now(timezone.utc)
                days_ago = max(0, (dt_now - dt_made).days)
                hints.append(f"Decided {days_ago} days ago ({made_at_str[:10]})")
            except Exception:
                hints.append(f"Original decision timestamp: {made_at_str[:10]}")

        # 2. Later related decisions on overlapping entities
        cand_entities = candidate.get("artifacts_affected", [])
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                for ent in cand_entities:
                    cur.execute("""
                    SELECT d.decision_id, d.title, d.made_at
                    FROM decisions d
                    JOIN decision_artifacts da ON d.decision_id = da.decision_id
                    WHERE da.entity_id = ? AND d.decision_id != ? AND d.made_at > ?
                    ORDER BY d.made_at DESC LIMIT 2
                    """, (ent, candidate["decision_id"], made_at_str or "1970-01-01"))
                    for row in cur.fetchall():
                        hints.append(f"Later decision '{row['title']}' ({row['decision_id']}) also modified this component on {row['made_at'][:10]}")
        except Exception:
            pass

        # 3. Reopened status reminder
        if candidate.get("decision_state") == "reopened":
            hints.append("Decision state is currently 'reopened'. Historical rejection may no longer apply.")

        return hints

    def evaluate_proposal(
        self,
        repo: str,
        pr_id: str,
        title: str,
        body: str,
        diff_text: str,
        changed_files: List[str],
        author: str = "contributor"
    ) -> Dict[str, Any]:
        """
        Main Step 3.5 Rejected-Idea Guard workflow:
        1. Extract design approach.
        2. Retrieve candidate rejected decisions/alternatives.
        3. Compare on substance via 4 independent signals.
        4. Tier into 'strong' or 'possible'.
        5. Return structured advisory findings with changed-circumstances hints.
        """
        proposal = self.extract_proposal_design(title, body, diff_text, changed_files)
        candidates = self.get_rejected_candidates(repo=repo)
        findings: List[Dict[str, Any]] = []

        # Retrieve active guard rules for signature matching
        all_rules: List[Dict[str, Any]] = []
        try:
            all_rules = self.db.get_guard_rules()
        except Exception:
            all_rules = []

        rules_by_decision: Dict[str, List[Dict[str, Any]]] = {}
        for r in all_rules:
            dec_id = r.get("decision_id")
            if dec_id:
                rules_by_decision.setdefault(dec_id, []).append(r)

        for cand in candidates:
            dec_id = cand["decision_id"]

            # Suppress dismissed findings for this PR + decision
            if self.db.is_finding_dismissed(pr_id, dec_id):
                continue

            structural_signals: List[str] = []
            matched_signal_names: List[str] = []

            # Signal (a): Entity / Path Overlap
            cand_artifacts = cand.get("artifacts_affected", [])
            cand_paths = set()
            for art in cand_artifacts:
                cand_paths.add(art)
                if "::" in art:
                    cand_paths.add(art.split("::")[0])
                try:
                    with self.db.get_connection() as conn:
                        cur = conn.cursor()
                        cur.execute("SELECT canonical_path FROM entities WHERE entity_id = ?", (art,))
                        row = cur.fetchone()
                        if row and row["canonical_path"]:
                            cp = row["canonical_path"]
                            cand_paths.add(cp)
                            if "::" in cp:
                                cand_paths.add(cp.split("::")[0])
                except Exception:
                    pass

            entity_overlap = False
            for cf in proposal["changed_files"]:
                for cp in cand_paths:
                    if cf == cp or _path_matches_pattern(cf, cp) or _path_matches_pattern(cp, cf):
                        entity_overlap = True
                        break
                    if cf.endswith(cp) or cp.endswith(cf):
                        entity_overlap = True
                        break
                if entity_overlap:
                    break

            if entity_overlap:
                structural_signals.append("entity_path_overlap")
                matched_signal_names.append("entity_path_overlap")

            # Signal (b): Signature / Guard-Rule Match
            signature_match = False
            cand_rules = rules_by_decision.get(dec_id, [])
            for r in cand_rules:
                rtype = r.get("rule_type", "")
                params = r.get("params") or {}

                if rtype == "forbid_import":
                    mod = params.get("module", "").lower()
                    if mod and mod in proposal["added_imports"]:
                        signature_match = True
                        break

                elif rtype == "forbid_pattern":
                    regex_str = params.get("regex", "")
                    if regex_str:
                        try:
                            compiled = re.compile(regex_str, re.IGNORECASE)
                            for l_code in proposal["clean_added_lines"]:
                                if l_code.startswith(("#", "//", "/*", "*")):
                                    continue
                                if compiled.search(l_code):
                                    signature_match = True
                                    break
                        except Exception:
                            pass
                    if signature_match:
                        break

            # Also check alternative rejection keywords as detection signatures
            if not signature_match:
                alt_sig_words = [
                    ("sticky_sessions", ["sticky_sessions", "sticky sessions"]),
                    ("local_cache", ["local_cache", "local cache", "local_buffer"]),
                    ("dict_cache", ["dict_cache", "dict cache", "in-memory dict", "memory dict"]),
                    ("deadband", ["deadband", "dead band"]),
                    ("on_off_relay", ["on_off_relay", "on_off", "on-off", "on off"]),
                    ("hysteresis", ["hysteresis"]),
                    ("bang_bang", ["bang_bang", "bang-bang", "bang bang"])
                ]
                cand_lower = (cand["description"] + " " + cand["rejection_reason"] + " " + cand.get("rationale", "")).lower()
                for concept_id, patterns in alt_sig_words:
                    cand_has_concept = any(p in cand_lower for p in patterns)
                    if cand_has_concept:
                        for l_code in proposal["clean_added_lines"]:
                            l_lower = l_code.lower()
                            if any(p in l_lower for p in patterns):
                                signature_match = True
                                break
                        if not signature_match:
                            for ident in proposal["added_identifiers"]:
                                ident_norm = ident.replace("_", " ")
                                if any(p == ident or p == ident_norm for p in patterns):
                                    signature_match = True
                                    break
                    if signature_match:
                        break

            if signature_match:
                structural_signals.append("signature_guard_rule_match")
                matched_signal_names.append("signature_guard_rule_match")

            # Signal (c): Dependency / Library Match
            dependency_match = False
            cand_text_lower = (cand["description"] + " " + cand["rejection_reason"]).lower()
            for imp in proposal["added_imports"]:
                if imp in cand_text_lower:
                    dependency_match = True
                    break

            if dependency_match:
                structural_signals.append("dependency_library_match")
                matched_signal_names.append("dependency_library_match")

            # Signal (d): Token TF-IDF Cosine Similarity
            text_sim = compute_tfidf_cosine(proposal["tokens"], cand["tokens"])
            if text_sim >= 0.25:
                matched_signal_names.append(f"text_similarity ({round(text_sim, 2)})")

            # --- Explicit Tiers (§3.5) ---
            has_substance = signature_match or dependency_match or (text_sim >= 0.25)
            structural_count = len(structural_signals)
            total_signals_count = len(matched_signal_names)

            tier = None
            if entity_overlap and (signature_match or dependency_match):
                tier = "strong"
            elif structural_count >= 1 and total_signals_count >= 2 and has_substance:
                tier = "strong"
            elif (signature_match or dependency_match) or text_sim >= 0.55:
                tier = "possible"
            elif entity_overlap and text_sim >= 0.20:
                tier = "possible"

            if not tier:
                # Keyword coincidence or path-only without substance produces NO finding
                continue

            # Build finding payload
            hints = self._get_changed_circumstances(cand, proposal)
            passages = cand.get("evidence_passages", [])

            is_reopened = (cand["decision_state"] == "reopened")
            if is_reopened:
                msg = (
                    f"Notice: Proposal introduces an approach from decision '{cand['decision_title']}' ({cand['decision_id']}) "
                    f"which was previously rejected, but the decision is currently REOPENED. Reopening reason: '{cand['rejection_reason']}'."
                )
                comment_text = f"Notice: Decision {cand['decision_id']} was previously rejected but is currently REOPENED — please review current direction."
            else:
                msg = (
                    f"Possible reintroduction of previously rejected approach from '{cand['decision_title']}' ({cand['decision_id']}): "
                    f"'{cand['rejection_reason']}' (Decided by {cand['made_by']} on {cand['made_at'][:10]})."
                )
                comment_text = (
                    f"Possible reintroduction of a previously rejected approach — please review: "
                    f"'{cand['rejection_reason']}' (Original Decision: {cand['decision_title']} [{cand['decision_id']}])."
                )

            finding_id = f"rej_{dec_id[:8]}_{uuid.uuid4().hex[:6]}"

            findings.append({
                "finding_id": finding_id,
                "status": "potential_violation",
                "finding_type": "rejected_idea",
                "advisory": True,
                "tier": tier,
                "signals_matched": matched_signal_names,
                "structural_signals_count": structural_count,
                "text_similarity": round(text_sim, 3),
                "decision_id": dec_id,
                "decision_title": cand["decision_title"],
                "decision_state": cand["decision_state"],
                "rejection_reason": cand["rejection_reason"],
                "made_by": cand["made_by"],
                "made_at": cand["made_at"],
                "message": msg,
                "pr_comment": comment_text,
                "evidence_passages": passages,
                "changed_circumstances": hints,
                "reviewed": False,
                "calibrated": False,
                "dismissed": False
            })

        return {
            "status": "complete",
            "repo": repo,
            "pr_id": pr_id,
            "findings_count": len(findings),
            "findings": findings
        }

    # --- Developer Actions (§3.5 Item 7 & Step 3.6) ---

    def dismiss_finding(
        self,
        finding_id: str,
        pr_id: str,
        decision_id: str,
        actor: str,
        reason: str
    ) -> Dict[str, Any]:
        """Dismisses an advisory finding for a given PR + decision."""
        fb_id = f"fb_dismiss_{uuid.uuid4().hex[:8]}"
        self.db.record_finding_feedback(
            feedback_id=fb_id,
            finding_id=finding_id,
            finding_type="rejected_idea",
            action="dismiss",
            reason=reason,
            actor=actor,
            pr_id=pr_id,
            decision_id=decision_id
        )
        return {"status": "dismissed", "feedback_id": fb_id, "pr_id": pr_id, "decision_id": decision_id}

    def confirm_finding(
        self,
        finding_id: str,
        pr_id: str,
        decision_id: str,
        actor: str,
        reason: str
    ) -> Dict[str, Any]:
        """Confirms that a finding is indeed a rejected approach violation."""
        fb_id = f"fb_confirm_{uuid.uuid4().hex[:8]}"
        self.db.record_finding_feedback(
            feedback_id=fb_id,
            finding_id=finding_id,
            finding_type="rejected_idea",
            action="confirm",
            reason=reason,
            actor=actor,
            pr_id=pr_id,
            decision_id=decision_id
        )
        return {"status": "confirmed", "feedback_id": fb_id, "pr_id": pr_id, "decision_id": decision_id}

    def reopen_decision(
        self,
        decision_id: str,
        pr_id: str,
        actor: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Invokes the reconciled lifecycle engine to transition rejected -> reopened,
        using the proposal / PR as evidence.
        """
        now = datetime.now(timezone.utc).isoformat()
        res = transition(
            self.db,
            decision_id=decision_id,
            to_state="reopened",
            actor=actor,
            reason=f"Reopened via PR {pr_id}: {reason}",
            at=now
        )

        fb_id = f"fb_reopen_{uuid.uuid4().hex[:8]}"
        self.db.record_finding_feedback(
            feedback_id=fb_id,
            finding_id=f"rej_{decision_id[:8]}",
            finding_type="rejected_idea",
            action="reopen",
            reason=reason,
            actor=actor,
            pr_id=pr_id,
            decision_id=decision_id
        )

        return {
            "status": "reopened",
            "decision_id": decision_id,
            "lifecycle_result": res,
            "feedback_id": fb_id
        }
