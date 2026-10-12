"""
General Decision Constraint & Drift Detection Engine (Step 3.4 & Section 8.3)
Evaluates code diffs against active, human-approved decision constraints and detection signatures.
Zero domain keywords hard-coded: entirely driven by database constraints and context graph.
"""
import logging
import re
import uuid
import fnmatch
from typing import List, Dict, Any, Optional, Tuple
from backend.models import Edge
from backend.db import Database

logger = logging.getLogger("cif.drift_detector")


def _path_matches_pattern(filepath: str, pattern: str) -> bool:
    """Checks if a file path matches a glob pattern, supporting ** multi-level wildcards."""
    if not filepath or not pattern:
        return False
    fp = filepath.replace("\\", "/").strip()
    pat = pattern.replace("\\", "/").strip()

    if pat == "*":
        return True

    if "**" not in pat:
        if fnmatch.fnmatch(fp, pat):
            return True
        if "/" not in pat and fnmatch.fnmatch(fp.split("/")[-1], pat):
            return True
        return False

    parts = pat.split("**/")
    regex_parts = []
    for part in parts:
        escaped = re.escape(part).replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
        regex_parts.append(escaped)
    regex = r"(?:.+/)?".join(regex_parts)
    return bool(re.fullmatch(regex, fp))


def _extract_code_part(line: str) -> Tuple[str, bool, bool]:
    """
    Extracts executable code from a line by stripping comments.
    Returns: (code_part, is_pure_comment, has_historical_note)
    """
    stripped = line.strip()
    if not stripped:
        return "", False, False

    # Check historical or decommissioning notes (should never trigger violations)
    lower = stripped.lower()
    has_historical_note = bool(
        "decommissioned" in lower or
        "deprecated" in lower or
        "replaced by" in lower or
        "was replaced" in lower or
        "migrated from" in lower
    )

    # Pure line comments
    if stripped.startswith(("#", "//", "/*", "*", "*/", '"""', "'''")):
        return "", True, has_historical_note

    # Inline comment stripping (for '#' not inside quotes)
    code_part = stripped
    if "#" in stripped:
        in_quote = False
        quote_char = ""
        idx = 0
        while idx < len(stripped):
            ch = stripped[idx]
            if ch in ('"', "'") and (idx == 0 or stripped[idx - 1] != "\\"):
                if not in_quote:
                    in_quote = True
                    quote_char = ch
                elif ch == quote_char:
                    in_quote = False
            elif ch == "#" and not in_quote:
                code_part = stripped[:idx].strip()
                break
            idx += 1

    return code_part, False, has_historical_note


class DriftDetector:
    def __init__(self, db: Database):
        self.db = db

    def parse_diff(self, diff_text: str, default_files: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Parses diff text into structured file hunks with 1-indexed line numbers.
        """
        import textwrap
        diff_text = textwrap.dedent(diff_text or "")
        file_entries: List[Dict[str, Any]] = []
        current_file = default_files[0] if default_files else ""
        current_entry: Optional[Dict[str, Any]] = None

        new_lineno = 1
        old_lineno = 1
        hunk_header_re = re.compile(r"^@@\s+-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@")

        for line in diff_text.splitlines():
            # Diff file headers
            if line.startswith("+++ b/"):
                current_file = line[6:].strip()
                current_entry = {
                    "file": current_file,
                    "added_lines": [],
                    "removed_lines": [],
                    "all_lines": []
                }
                file_entries.append(current_entry)
                continue
            elif line.startswith("+++ "):
                current_file = line[4:].strip()
                current_entry = {
                    "file": current_file,
                    "added_lines": [],
                    "removed_lines": [],
                    "all_lines": []
                }
                file_entries.append(current_entry)
                continue

            # Ensure entry exists
            if current_entry is None:
                current_entry = {
                    "file": current_file or (default_files[0] if default_files else "unknown"),
                    "added_lines": [],
                    "removed_lines": [],
                    "all_lines": []
                }
                file_entries.append(current_entry)

            # Hunk header
            match = hunk_header_re.match(line)
            if match:
                old_lineno = int(match.group(1))
                new_lineno = int(match.group(2))
                continue

            # Added line
            if line.startswith("+") and not line.startswith("+++"):
                raw = line[1:]
                code_part, is_comment, is_hist = _extract_code_part(raw)
                item = {
                    "line_number": new_lineno,
                    "raw": raw,
                    "code": code_part,
                    "is_pure_comment": is_comment,
                    "is_historical": is_hist,
                    "diff_prefix": "+"
                }
                current_entry["added_lines"].append(item)
                current_entry["all_lines"].append(item)
                new_lineno += 1

            # Removed line
            elif line.startswith("-") and not line.startswith("---"):
                raw = line[1:]
                code_part, is_comment, is_hist = _extract_code_part(raw)
                item = {
                    "line_number": old_lineno,
                    "raw": raw,
                    "code": code_part,
                    "is_pure_comment": is_comment,
                    "is_historical": is_hist,
                    "diff_prefix": "-"
                }
                current_entry["removed_lines"].append(item)
                current_entry["all_lines"].append(item)
                old_lineno += 1

            else:
                # Context line
                new_lineno += 1
                old_lineno += 1

        return file_entries

    def analyze_diff_for_drift(
        self,
        repo: str,
        commit_or_pr_id: str,
        author: str,
        changed_files: List[str],
        diff_text: str
    ) -> Dict[str, Any]:
        """
        Runs Step 3.4 General Drift Detection Pass:
        1. Parse diff into structured hunks and lines with line numbers.
        2. Identify touched files and entities in database.
        3. Fetch only active, human-approved decision constraints whose applies_to overlaps.
        4. Evaluate each constraint against added lines (and removed lines for require_*).
        5. Return potential violations with evidence passages, line numbers, and signal strength.
        """
        findings: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        parsed_files = self.parse_diff(diff_text, default_files=changed_files)
        all_touched_files = set(changed_files)
        for pf in parsed_files:
            if pf["file"] and pf["file"] != "unknown":
                all_touched_files.add(pf["file"])

        # 1. Look up matching entities
        touched_entities: List[Dict[str, Any]] = []
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                for fp in all_touched_files:
                    cursor.execute("""
                    SELECT entity_id, canonical_path FROM entities
                    WHERE repo = ? AND (canonical_path = ? OR canonical_path LIKE ?)
                    """, (repo, fp, f"{fp}::%"))
                    touched_entities.extend([dict(r) for r in cursor.fetchall()])
        except Exception as e:
            logger.error("Error querying entities: %s", e)
            errors.append({
                "stage": "entities_lookup",
                "rule_id": None,
                "error_type": e.__class__.__name__,
                "message": f"Entity lookup error: {str(e)[:150]}"
            })

        touched_entity_ids = {e["entity_id"] for e in touched_entities}
        canonical_paths = {e["canonical_path"] for e in touched_entities}

        # 2. Fetch active decision constraints
        active_rules: List[Dict[str, Any]] = []
        try:
            active_rules = self.db.get_guard_rules(status="active")
        except Exception as e:
            logger.error("Error fetching active constraints: %s", e)
            errors.append({
                "stage": "constraints_fetch",
                "rule_id": None,
                "error_type": e.__class__.__name__,
                "message": f"Constraints fetch error: {str(e)[:150]}"
            })

        # 3. Evaluate overlapping constraints
        for rule in active_rules:
            rule_id = rule.get("rule_id", "unknown")
            decision_id = rule.get("decision_id", "")
            rule_type = rule.get("rule_type", "")
            params = rule.get("params") or {}
            polarity = rule.get("polarity", "must_not")
            applies_to = rule.get("applies_to") or params.get("paths", ["*"])
            citation = rule.get("decision_title") or f"Decision {decision_id}"

            if not isinstance(applies_to, list):
                applies_to = [str(applies_to)]

            for file_entry in parsed_files:
                filepath = file_entry["file"]

                # Check applies_to overlap (must match entity ID, file path glob, or parameter path)
                applies_overlap = any(
                    item in touched_entity_ids or
                    item in canonical_paths or
                    _path_matches_pattern(filepath, item)
                    for item in applies_to
                )

                if not applies_overlap and applies_to != ["*"]:
                    continue

                try:
                    # Evaluate Rule Types
                    if rule_type == "forbid_import":
                        mod = params.get("module", "")
                        if not mod:
                            continue
                        import_pattern = re.compile(
                            r'(?:^|[^\w])(?:import\s+' + re.escape(mod) + r'\b|from\s+' + re.escape(mod) + r'(?:\.|\s+import)\b)'
                        )

                        for item in file_entry["added_lines"]:
                            # Ignore pure comments
                            if item["is_pure_comment"] or item["is_historical"]:
                                continue
                            line_to_check = item["code"] or item["raw"]
                            if import_pattern.search(line_to_check):
                                finding = self._build_finding(
                                    rule_id=rule_id,
                                    decision_id=decision_id,
                                    filepath=filepath,
                                    item=item,
                                    reason=f"Violation of constraint '{rule_id}': Forbidden import '{mod}' introduced in {filepath}.",
                                    citation=citation,
                                    commit_or_pr_id=commit_or_pr_id,
                                    author=author,
                                    signals_matched=3
                                )
                                findings.append(finding)
                                self._record_drift_edge(filepath, decision_id)

                    elif rule_type == "forbid_pattern":
                        regex_str = params.get("regex", "")
                        if not regex_str:
                            continue
                        compiled_re = re.compile(regex_str, re.IGNORECASE)

                        # Check if diff has real code changes
                        has_real_code = any(not it["is_pure_comment"] for it in file_entry["added_lines"])

                        for item in file_entry["added_lines"]:
                            # Clean changes: comments mentioning historical/decommissioned terms produce NO finding
                            if item["is_historical"]:
                                continue
                            # If it's a pure comment line and the diff has no executable code added, skip
                            if item["is_pure_comment"] and not has_real_code:
                                continue

                            # Check raw added line against pattern
                            if compiled_re.search(item["raw"]):
                                msg = params.get("message") or f"Forbidden pattern matching /{regex_str}/"
                                signals = 3 if item["code"] else 2
                                finding = self._build_finding(
                                    rule_id=rule_id,
                                    decision_id=decision_id,
                                    filepath=filepath,
                                    item=item,
                                    reason=f"Violation of constraint '{rule_id}': {msg} in {filepath}.",
                                    citation=citation,
                                    commit_or_pr_id=commit_or_pr_id,
                                    author=author,
                                    signals_matched=signals
                                )
                                findings.append(finding)
                                self._record_drift_edge(filepath, decision_id)

                    elif rule_type == "require_import":
                        mod = params.get("module", "")
                        if not mod:
                            continue
                        import_pattern = re.compile(
                            r'(?:^|[^\w])(?:import\s+' + re.escape(mod) + r'\b|from\s+' + re.escape(mod) + r'(?:\.|\s+import)\b)'
                        )

                        # Check if a removed line removed the required import
                        for item in file_entry["removed_lines"]:
                            if import_pattern.search(item["code"] or item["raw"]):
                                finding = self._build_finding(
                                    rule_id=rule_id,
                                    decision_id=decision_id,
                                    filepath=filepath,
                                    item=item,
                                    reason=f"Violation of constraint '{rule_id}': Required import '{mod}' was removed from {filepath}.",
                                    citation=citation,
                                    commit_or_pr_id=commit_or_pr_id,
                                    author=author,
                                    signals_matched=3
                                )
                                findings.append(finding)
                                self._record_drift_edge(filepath, decision_id)

                    elif rule_type == "config_value":
                        cfg_file = params.get("file")
                        key = params.get("key")
                        must_equal = params.get("must_equal")

                        if cfg_file and _path_matches_pattern(filepath, cfg_file) and key and must_equal is not None:
                            for item in file_entry["added_lines"]:
                                if item["is_pure_comment"]:
                                    continue
                                line_text = item["raw"]
                                if f'"{key}"' in line_text or f"'{key}'" in line_text:
                                    if str(must_equal) not in line_text:
                                        finding = self._build_finding(
                                            rule_id=rule_id,
                                            decision_id=decision_id,
                                            filepath=filepath,
                                            item=item,
                                            reason=f"Violation of constraint '{rule_id}': Config key '{key}' must equal '{must_equal}' in {filepath}.",
                                            citation=citation,
                                            commit_or_pr_id=commit_or_pr_id,
                                            author=author,
                                            signals_matched=3
                                        )
                                        findings.append(finding)
                                        self._record_drift_edge(filepath, decision_id)

                except Exception as e:
                    logger.error("Error evaluating constraint %s: %s", rule_id, e)
                    errors.append({
                        "stage": "constraint_eval",
                        "rule_id": rule_id,
                        "error_type": e.__class__.__name__,
                        "message": f"Rule evaluation error: {str(e)[:150]}"
                    })

        return {
            "status": "incomplete" if errors else "complete",
            "findings": findings,
            "errors": errors
        }

    def _build_finding(
        self,
        rule_id: str,
        decision_id: str,
        filepath: str,
        item: Dict[str, Any],
        reason: str,
        citation: str,
        commit_or_pr_id: str,
        author: str,
        signals_matched: int
    ) -> Dict[str, Any]:
        """Constructs a Step 3.4 finding record with evidence passages and uncalibrated signal strength."""
        lineno = item.get("line_number", 1)
        raw_line = item.get("raw", "").strip()

        evidence_passages = []
        try:
            raw_passages = self.db.get_decision_evidence_passages(decision_id)
            for p in raw_passages:
                evidence_passages.append({
                    "passage_text": p.get("passage_text", ""),
                    "source_url": p.get("source_url", "")
                })
        except Exception:
            evidence_passages = []

        if signals_matched >= 3:
            signal_strength = "high"
        elif signals_matched == 2:
            signal_strength = "medium"
        else:
            signal_strength = "low"

        finding_id = f"finding_{rule_id[:12]}_{lineno}_{uuid.uuid4().hex[:6]}"

        return {
            "finding_id": finding_id,
            "status": "potential_violation",
            "rule_id": rule_id,
            "decision_id": decision_id,
            "file": filepath,
            "line_number": lineno,
            "line_numbers": [lineno],
            "offending_line": raw_line,
            "violating_diff_snippet": raw_line,
            "evidence_passages": evidence_passages,
            "signal_strength": signal_strength,
            "confidence": 0.0,
            "calibrated": False,
            "reviewed": False,
            "reason": reason,
            "message": reason,
            "drift_type": "drift",
            "citation": f"Governed by Decision '{citation}' ({decision_id})",
            "commit_or_pr_id": commit_or_pr_id,
            "author": author
        }

    def _record_drift_edge(self, entity_id: str, decision_id: str, valid_from: Optional[str] = None):
        if not valid_from:
            from datetime import datetime, timezone
            valid_from = datetime.now(timezone.utc).isoformat()
        edge_id = f"edge_drift_{entity_id[:8]}_{decision_id[:8]}"
        edge = Edge(
            edge_id=edge_id,
            edge_type="drifts_from",
            from_id=entity_id,
            from_type="entity",
            to_id=decision_id,
            to_type="decision",
            valid_from=valid_from
        )
        self.db.upsert_edge(edge)
