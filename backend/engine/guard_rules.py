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
    Proposes candidate guard rules from a decision's rationale and rejected alternatives.
    All proposals are stored as 'proposed' and NEVER auto-activated.
    """
    rules: List[GuardRule] = []
    text = (decision.title + " " + (decision.rationale or "")).lower()

    # Rule Type 1: forbid_import (from rejected alternatives or explicit anti-patterns)
    for alt in decision.alternatives_considered:
        alt_desc = alt.get("description", "").lower()
        alt_reason = alt.get("rejection_reason", "").lower()
        combined = alt_desc + " " + alt_reason

        # Detect forbidden imports/modules
        forbid_modules = [
            ("sticky_sessions", "sticky_sessions"),
            ("raw memory cache", "local_cache"),
            ("in-memory dict", "dict_cache"),
            ("braintree", "braintree"),
            ("userfaultfd", "userfaultfd"),
            ("raw psycopg2", "psycopg2")
        ]
        for pattern_word, mod_name in forbid_modules:
            if pattern_word in combined or mod_name in combined:
                rules.append(GuardRule(
                    rule_id=f"rule_forbid_import_{decision.decision_id[:8]}_{mod_name}",
                    decision_id=decision.decision_id,
                    rule_type="forbid_import",
                    params={
                        "module": mod_name,
                        "paths": ["*.py", "**/*.py", "src/**/*.py", "vmm/**/*.rs", "pkg/**/*.go"]
                    },
                    status="proposed",
                    created_by="rule_synthesizer",
                    created_at=decision.made_at
                ))

        # Rule Type 3: forbid_pattern (regex anti-patterns)
        if "hysteresis" in combined or "bang-bang" in combined:
            rules.append(GuardRule(
                rule_id=f"rule_forbid_pattern_{decision.decision_id[:8]}_bangbang",
                decision_id=decision.decision_id,
                rule_type="forbid_pattern",
                params={
                    "regex": r"(?:on_off_relay|threshold_high|hysteresis_loop|bang_bang)",
                    "paths": ["src/thermal/**/*.py", "**/control.py"],
                    "message": "Reintroduces rejected bang-bang threshold hysteresis"
                },
                status="proposed",
                created_by="rule_synthesizer",
                created_at=decision.made_at
            ))

        if "local_cache" in combined or "dict_cache" in combined:
            rules.append(GuardRule(
                rule_id=f"rule_forbid_pattern_{decision.decision_id[:8]}_dictcache",
                decision_id=decision.decision_id,
                rule_type="forbid_pattern",
                params={
                    "regex": r"(?:dict_cache\s*=\s*\{\}|local_cache\s*=\s*\{\})",
                    "paths": ["src/cache/**/*.py", "**/store.py"],
                    "message": "Reintroduces rejected in-memory dictionary cache"
                },
                status="proposed",
                created_by="rule_synthesizer",
                created_at=decision.made_at
            ))

    # Rule Type 2: require_import (from accepted architectural decisions)
    if decision.state == "accepted":
        if "stripe" in text:
            rules.append(GuardRule(
                rule_id=f"rule_require_import_{decision.decision_id[:8]}_stripe",
                decision_id=decision.decision_id,
                rule_type="require_import",
                params={
                    "module": "stripe",
                    "paths": ["src/payments/**/*.py"]
                },
                status="proposed",
                created_by="rule_synthesizer",
                created_at=decision.made_at
            ))

        if "redis" in text and "cluster" in text:
            rules.append(GuardRule(
                rule_id=f"rule_require_import_{decision.decision_id[:8]}_redis",
                decision_id=decision.decision_id,
                rule_type="require_import",
                params={
                    "module": "redis",
                    "paths": ["src/cache/**/*.py"]
                },
                status="proposed",
                created_by="rule_synthesizer",
                created_at=decision.made_at
            ))

    # Rule Type 4: config_value
    if "timeout" in text:
        rules.append(GuardRule(
            rule_id=f"rule_config_val_{decision.decision_id[:8]}_timeout",
            decision_id=decision.decision_id,
            rule_type="config_value",
            params={
                "file": "config.json",
                "key": "timeout_seconds",
                "must_equal": "30"
            },
            status="proposed",
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

