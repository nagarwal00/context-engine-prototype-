"""
CIF Decision Guard CI Check (Phase 7.3)
Runs on pull requests to check for guard rule violations without needing a running server.

Usage:
    python tools/ci_check.py --base <base_sha> --head <head_sha> [--rules cif_rules.json]

Exit codes:
    0  - No active rule violations
    1  - One or more guard rule violations found
    2  - Error (bad arguments, rules file missing, etc.)

Environment:
    GITHUB_TOKEN  - Optional; used to fetch diff from GitHub API. Falls back to local git diff.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Compute project root from this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Avoid touching the real DB - CI check reads rules from exported JSON only
DEFAULT_RULES_FILE = PROJECT_ROOT / "cif_rules.json"

def get_diff_text(base_sha: str, head_sha: str) -> str:
    """Get the diff between two commits using local git. stdlib only (subprocess)."""
    try:
        result = subprocess.run(
            ["git", "diff", f"{base_sha}..{head_sha}"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=60,
            encoding="utf-8",
            errors="replace"
        )
        if result.returncode != 0:
            print(f"[CI_CHECK] WARNING: git diff failed: {result.stderr.strip()}", file=sys.stderr)
            return ""
        return result.stdout
    except Exception as e:
        print(f"[CI_CHECK] ERROR fetching diff: {e}", file=sys.stderr)
        return ""

def get_changed_files(diff_text: str) -> list:
    """Extract list of changed file paths from a unified diff."""
    files = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            files.append(line[6:].strip())
    return files or ["unknown"]

def load_rules(rules_file: str) -> list:
    """Load guard rules from the exported JSON file."""
    path = Path(rules_file)
    if not path.exists():
        print(f"[CI_CHECK] WARNING: Rules file not found: {rules_file}", file=sys.stderr)
        print("[CI_CHECK] No active guard rules — all changes permitted.", file=sys.stderr)
        return []
    with open(path, "r", encoding="utf-8") as f:
        rules = json.load(f)
    active = [r for r in rules if r.get("status") == "active"]
    print(f"[CI_CHECK] Loaded {len(active)} active rule(s) from {rules_file}", file=sys.stderr)
    return active

def main():
    parser = argparse.ArgumentParser(
        description="CIF Decision Guard CI Check - validates diffs against active guard rules."
    )
    parser.add_argument("--base", required=True, help="Base commit SHA or ref")
    parser.add_argument("--head", required=True, help="Head commit SHA or ref")
    parser.add_argument(
        "--rules",
        default=str(DEFAULT_RULES_FILE),
        help=f"Path to exported cif_rules.json (default: {DEFAULT_RULES_FILE})"
    )
    args = parser.parse_args()

    rules = load_rules(args.rules)
    if not rules:
        print("[CI_CHECK] PASS: No active rules to check.", file=sys.stderr)
        sys.exit(0)

    print(f"[CI_CHECK] Comparing {args.base}..{args.head}", file=sys.stderr)
    diff_text = get_diff_text(args.base, args.head)
    if not diff_text:
        print("[CI_CHECK] WARNING: Empty diff — nothing to check.", file=sys.stderr)
        sys.exit(0)

    changed_files = get_changed_files(diff_text)
    print(f"[CI_CHECK] Changed files: {changed_files}", file=sys.stderr)

    # Import the guard rules checker (stdlib only inside it)
    try:
        from backend.engine.guard_rules import check_diff_against_guard_rules_with_report
    except ImportError as e:
        print(f"[CI_CHECK] ERROR importing guard_rules: {e}", file=sys.stderr)
        sys.exit(2)

    report = check_diff_against_guard_rules_with_report(rules, changed_files, diff_text)
    violations = report.get("violations", [])
    errors = report.get("errors", [])

    if errors:
        print(f"\n[CI_CHECK] INCOMPLETE: {len(errors)} guard rule(s) encountered evaluation errors:\n", file=sys.stderr)
        for err in errors:
            print(f"  RULE: {err.get('rule_id')} — {err.get('error_type')}: {err.get('message')}", file=sys.stderr)
        if violations:
            print(f"\n[CI_CHECK] Also detected {len(violations)} violation(s).", file=sys.stderr)
        sys.exit(2)

    if violations:
        print(f"\n[CI_CHECK] FAIL: {len(violations)} guard rule violation(s) found!\n")
        for v in violations:
            print(f"  RULE: {v.get('rule_id')} ({v.get('rule_type')})")
            print(f"  FILE: {v.get('file')}")
            print(f"  LINE: {v.get('line', '').strip()}")
            print(f"  MESSAGE: {v.get('message', '')}")
            print(f"  CITATION: {v.get('citation', '')}")
            print()
        sys.exit(1)
    else:
        print(f"[CI_CHECK] PASS: No guard rule violations in {len(changed_files)} file(s).")
        sys.exit(0)

if __name__ == "__main__":
    main()
