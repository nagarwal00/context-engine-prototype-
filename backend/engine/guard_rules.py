"""
Decision Guard Rules Engine (Section 5 - Novelty Feature)
Proposes deterministic, enforceable guard rules from architectural decisions
and validates pull requests / diffs against active rules.
"""
import os
import re
import fnmatch
from typing import List, Dict, Any, Optional
from backend.models import Decision, GuardRule
from backend.db import Database
from backend.engine.identifiers import (
    extract_identifiers,
    is_module_like,
    derive_paths_from_artifacts,
    extract_require_import_modules,
)


def _path_matches_pattern(filepath: str, pattern: str) -> bool:
    """Check if a file path matches a glob pattern, supporting ** multi-level wildcards."""
    # Normalise to forward slashes
    fp = filepath.replace("\\", "/")
    pat = pattern.replace("\\", "/")

    # If no ** in pattern, use standard fnmatch (also try basename for simple patterns)
    if "**" not in pat:
        if fnmatch.fnmatch(fp, pat):
            return True
        if "/" not in pat and fnmatch.fnmatch(os.path.basename(fp), pat):
            return True
        return False

    # Translate ** glob pattern to regex.
    # '**/' matches zero or more directory components (including none).
    parts = pat.split("**/")
    regex_parts = []
    for i, part in enumerate(parts):
        # Escape the non-wildcard text, then translate single-star and ?
        escaped = re.escape(part).replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
        regex_parts.append(escaped)
    # Join with "(?:.+/)?" to allow zero or more intermediate directories
    regex = r"(?:.+/)?".join(regex_parts)
    return bool(re.fullmatch(regex, fp))


ALLOWED_RULE_TYPES = {"forbid_import", "require_import", "forbid_pattern", "config_value"}

def propose_rules_from_decision(decision: Decision) -> List[GuardRule]:
    """
    Proposes candidate guard rules from a decision's rationale and rejected alternatives
    using generic syntax and concept extraction (no hard-coded scenario vocabulary).
    All proposals are stored with status='proposed' and source='synthesized', and NEVER auto-activated.
    """
    rules: List[GuardRule] = []
    p_paths = derive_paths_from_artifacts(decision.artifacts_affected)

    accepted_text = (decision.title + " " + (decision.rationale or "")).lower()
    accepted_identifiers = {
        ident.lower()
        for ident in extract_identifiers(decision.title + " " + (decision.rationale or ""))
    }

    # For rejected alternatives of an accepted decision:
    for alt in decision.alternatives_considered:
        if isinstance(alt, dict):
            alt_desc = alt.get("description", "")
            alt_reason = alt.get("rejection_reason", "")
        else:
            alt_desc = str(alt)
            alt_reason = ""
        combined_alt = alt_desc + " " + alt_reason
        alt_candidates = extract_identifiers(combined_alt)

        for cand in sorted(alt_candidates):
            cand_lower = cand.lower()
            # Identifiers that appear in the rejected text but NOT in the accepted decision's text
            if cand_lower not in accepted_text and cand_lower not in accepted_identifiers:
                cand_clean = re.sub(r"[^a-zA-Z0-9_]", "_", cand)[:24]
                rule_id_pat = f"rule_forbid_pattern_{decision.decision_id[:8]}_{cand_clean}"
                rules.append(GuardRule(
                    rule_id=rule_id_pat,
                    decision_id=decision.decision_id,
                    rule_type="forbid_pattern",
                    params={
                        "regex": rf"\b{re.escape(cand)}\b",
                        "paths": p_paths,
                        "message": f"Reintroduces rejected concept: {cand}"
                    },
                    status="proposed",
                    polarity="must_not",
                    applies_to=p_paths,
                    source="synthesized",
                    created_by="rule_synthesizer",
                    created_at=decision.made_at
                ))

                if is_module_like(cand):
                    rule_id_imp = f"rule_forbid_import_{decision.decision_id[:8]}_{cand_clean}"
                    rules.append(GuardRule(
                        rule_id=rule_id_imp,
                        decision_id=decision.decision_id,
                        rule_type="forbid_import",
                        params={
                            "module": cand,
                            "paths": p_paths
                        },
                        status="proposed",
                        polarity="must_not",
                        applies_to=p_paths,
                        source="synthesized",
                        created_by="rule_synthesizer",
                        created_at=decision.made_at
                    ))

    # For a rejected decision: the decision itself is rejected
    if decision.state == "rejected":
        rej_candidates = extract_identifiers(decision.title + " " + (decision.rationale or ""))
        for cand in sorted(rej_candidates):
            cand_clean = re.sub(r"[^a-zA-Z0-9_]", "_", cand)[:24]
            rules.append(GuardRule(
                rule_id=f"rule_forbid_pattern_{decision.decision_id[:8]}_{cand_clean}",
                decision_id=decision.decision_id,
                rule_type="forbid_pattern",
                params={
                    "regex": rf"\b{re.escape(cand)}\b",
                    "paths": p_paths,
                    "message": f"Reintroduces rejected decision concept: {cand}"
                },
                status="proposed",
                polarity="must_not",
                applies_to=p_paths,
                source="synthesized",
                created_by="rule_synthesizer",
                created_at=decision.made_at
            ))
            if is_module_like(cand):
                rules.append(GuardRule(
                    rule_id=f"rule_forbid_import_{decision.decision_id[:8]}_{cand_clean}",
                    decision_id=decision.decision_id,
                    rule_type="forbid_import",
                    params={
                        "module": cand,
                        "paths": p_paths
                    },
                    status="proposed",
                    polarity="must_not",
                    applies_to=p_paths,
                    source="synthesized",
                    created_by="rule_synthesizer",
                    created_at=decision.made_at
                ))

    # require_import only from explicit backticked phrases such as "must use `X`"
    if decision.state == "accepted":
        req_mods = extract_require_import_modules(decision.title + " " + (decision.rationale or ""))
        for mod in sorted(req_mods):
            mod_clean = re.sub(r"[^a-zA-Z0-9_]", "_", mod)[:24]
            rules.append(GuardRule(
                rule_id=f"rule_require_import_{decision.decision_id[:8]}_{mod_clean}",
                decision_id=decision.decision_id,
                rule_type="require_import",
                params={
                    "module": mod,
                    "paths": p_paths
                },
                status="proposed",
                polarity="must",
                applies_to=p_paths,
                source="synthesized",
                created_by="rule_synthesizer",
                created_at=decision.made_at
            ))

    # Deduplicate rules by rule_id
    dedup: Dict[str, GuardRule] = {}
    for r in rules:
        if r.rule_type in ALLOWED_RULE_TYPES:
            dedup[r.rule_id] = r

    return list(dedup.values())

def check_diff_against_guard_rules_with_report(
    rules: List[Dict[str, Any]],
    changed_files: List[str],
    diff_text: str
) -> Dict[str, Any]:
    """
    Evaluates active guard rules against newly added lines in a pull request diff.
    Isolates rule evaluations so errors in one rule do not suppress others.
    Returns: { "status": "complete" | "incomplete", "violations": [...], "errors": [...] }
    """
    violations = []
    errors = []

    # Extract added lines only (lines starting with + but not +++)
    added_lines_with_file = []
    current_file = changed_files[0] if changed_files else ""

    for line in diff_text.splitlines():
        s = line.strip()
        if s.startswith("+++ b/"):
            current_file = s[6:].strip()
        elif s.startswith("+") and not s.startswith("+++"):
            added_lines_with_file.append((current_file, s[1:].strip()))

    for rule in rules:
        if rule.get("status") != "active":
            continue

        rule_id = rule.get("rule_id", "unknown")
        try:
            if rule.get("_parse_error") or rule.get("params") is None:
                raise ValueError(f"Malformed rule parameters: {rule.get('_parse_error', 'Invalid params')}")

            rule_type = rule.get("rule_type")
            params = rule.get("params", {})
            decision_id = rule.get("decision_id")
            decision_title = rule.get("decision_title", "Architectural Decision")
            paths = params.get("paths", ["*"])

            for filepath, line_content in added_lines_with_file:
                # Check if file path matches any path pattern (supports ** multi-level globs)
                matches_path = any(_path_matches_pattern(filepath, pat) for pat in paths)
                if not matches_path and paths != ["*"]:
                    continue

                if rule_type == "forbid_import":
                    mod = params.get("module", "")
                    if mod and (
                        re.search(r'\bimport\s+' + re.escape(mod) + r'\b', line_content) or
                        re.search(r'\bfrom\s+' + re.escape(mod) + r'(?:\.|\s+import)\b', line_content)
                    ):
                        violations.append({
                            "rule_id": rule_id,
                            "decision_id": decision_id,
                            "rule_type": rule_type,
                            "file": filepath,
                            "line": line_content,
                            "message": f"Violation of Rule '{rule_id}': Forbidden import '{mod}' detected in {filepath}.",
                            "citation": f"Governed by Decision '{decision_title}' ({decision_id})"
                        })

                elif rule_type == "forbid_pattern":
                    regex_pat = params.get("regex", "")
                    if regex_pat:
                        if re.search(regex_pat, line_content):
                            msg = params.get("message") or f"Forbidden code pattern matching /{regex_pat}/"
                            violations.append({
                                "rule_id": rule_id,
                                "decision_id": decision_id,
                                "rule_type": rule_type,
                                "file": filepath,
                                "line": line_content,
                                "message": f"Violation of Rule '{rule_id}': {msg} in {filepath}.",
                                "citation": f"Governed by Decision '{decision_title}' ({decision_id})"
                            })

                elif rule_type == "config_value":
                    cfg_file = params.get("file")
                    key = params.get("key")
                    must_equal = params.get("must_equal")
                    if cfg_file and fnmatch.fnmatch(filepath, cfg_file) and key and must_equal:
                        if f'"{key}"' in line_content and str(must_equal) not in line_content:
                            violations.append({
                                "rule_id": rule_id,
                                "decision_id": decision_id,
                                "rule_type": rule_type,
                                "file": filepath,
                                "line": line_content,
                                "message": f"Violation of Rule '{rule_id}': Config key '{key}' must equal '{must_equal}' in {filepath}.",
                                "citation": f"Governed by Decision '{decision_title}' ({decision_id})"
                            })
        except Exception as e:
            errors.append({
                "stage": "guard_rules",
                "rule_id": rule_id,
                "error_type": e.__class__.__name__,
                "message": f"Rule evaluation error: {e.__class__.__name__}: {str(e)[:150]}"
            })

    return {
        "status": "incomplete" if errors else "complete",
        "violations": violations,
        "errors": errors
    }


def check_diff_against_guard_rules(
    rules: List[Dict[str, Any]],
    changed_files: List[str],
    diff_text: str
) -> List[Dict[str, Any]]:
    """Evaluates guard rules against diff, returning violations list."""
    report = check_diff_against_guard_rules_with_report(rules, changed_files, diff_text)
    return report["violations"]

