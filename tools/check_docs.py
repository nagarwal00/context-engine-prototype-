#!/usr/bin/env python3
"""
tools/check_docs.py - Documentation consistency and integrity checker.

Validates:
1. Reuses tools/print_facts.py to verify and print live factual metrics.
2. Checks for banned historical drift strings:
   - 'bbackend'
   - '61 labelled'
   - '169+'
   - '6 core surfaces'
   - 'v001-v006'
3. Validates markdown links and repo-relative references exist on disk.
4. Checks for TODO(human) markers (fails only when --strict is passed).
"""
import argparse
import os
import re
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.print_facts import get_question_facts, get_test_count, get_migration_facts, get_ui_surface_facts

BANNED_STRINGS = [
    "bbackend",
    "61 labelled",
    "169+",
    "6 core surfaces",
    "v001-v006",
]

# Files allowed to mention banned strings (e.g., historical review audit logs)
BANNED_STRINGS_ALLOWLIST = {
    "docs/process/ANTIGRAVITY_HANDOFF_V4_FIXES.md",
    "ANTIGRAVITY_HANDOFF_V4_FIXES.md",
}

# Directories and root files belonging to the actual repository
REPO_TOP_DIRS = {
    "backend",
    "docs",
    "extension",
    "results",
    "tests",
    "tools",
    "user_study",
    "vscode-extension",
    "web",
    ".github",
}

# Synthetic / demo repository paths that exist in event streams, not repository disk
SYNTHETIC_PREFIXES = (
    "src/thermal/",
    "src/cache/",
    "src/transport/",
    "docs/adr/",
    "docs/designs/",
    "docs/rfc/",
    "tools/_repro_",
)


def get_tracked_markdown_files():
    try:
        proc = subprocess.run(
            ["git", "ls-files", "*.md"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return [f.strip() for f in proc.stdout.splitlines() if f.strip()]
    except Exception:
        md_files = []
        for root, _, files in os.walk(PROJECT_ROOT):
            if any(part in root for part in [".git", "node_modules", "backups", "scratch", ".gemini"]):
                continue
            for f in files:
                if f.endswith(".md"):
                    rel = os.path.relpath(os.path.join(root, f), PROJECT_ROOT).replace("\\", "/")
                    md_files.append(rel)
        return md_files


def check_banned_strings(files):
    errors = []
    for rel_path in files:
        if rel_path in BANNED_STRINGS_ALLOWLIST:
            continue
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        if not os.path.isfile(full_path):
            continue
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                for banned in BANNED_STRINGS:
                    if banned in line:
                        errors.append(f"{rel_path}:{line_no}: Found banned string '{banned}'")
    return errors


def check_markdown_links(files):
    errors = []
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

    for rel_path in files:
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        if not os.path.isfile(full_path):
            continue
        doc_dir = os.path.dirname(full_path)

        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        for match in link_pattern.finditer(content):
            target = match.group(2).strip()

            # Ignore external URLs, anchors, mailto, and legacy file:// links
            if target.startswith(("http://", "https://", "mailto:", "#", "file:///")):
                continue

            # Strip in-page anchors and query parameters
            clean_target = target.split("#")[0].split("?")[0].strip()
            if not clean_target:
                continue

            # Check relative to doc directory OR relative to repo root
            cand1 = os.path.normpath(os.path.join(doc_dir, clean_target))
            cand2 = os.path.normpath(os.path.join(PROJECT_ROOT, clean_target))

            if not (os.path.exists(cand1) or os.path.exists(cand2)):
                errors.append(f"{rel_path}: Broken link '{target}' -> target not found on disk")

    return errors


BACKTICK_ALLOWLIST = {
    "STATUS_AUDIT.md",
    "docs/process/ANTIGRAVITY_HANDOFF_V4_FIXES.md",
}


def check_backticked_paths(files):
    errors = []
    path_pattern = re.compile(r'`([a-zA-Z0-9_\-./]+?\.(?:md|py))`')

    for rel_path in files:
        if rel_path in BACKTICK_ALLOWLIST:
            continue
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        if not os.path.isfile(full_path):
            continue
        doc_dir = os.path.dirname(full_path)

        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        for match in path_pattern.finditer(content):
            target = match.group(1).strip()

            # Ignore wildcards, synthetic prefixes, or patterns
            if "*" in target or target.startswith(SYNTHETIC_PREFIXES) or "<" in target:
                continue

            # Check if this looks like a repo path
            top_dir = target.split("/")[0] if "/" in target else None
            is_repo_path = top_dir in REPO_TOP_DIRS or target.endswith(".md") or "/" in target

            if not is_repo_path:
                continue

            cand1 = os.path.normpath(os.path.join(doc_dir, target))
            cand2 = os.path.normpath(os.path.join(PROJECT_ROOT, target))

            # If it explicitly references a known repo top dir or is in docs, it must exist
            if top_dir in REPO_TOP_DIRS:
                if not (os.path.exists(cand1) or os.path.exists(cand2)):
                    errors.append(f"{rel_path}: Broken backticked path `{target}` -> file not found")

    return errors


def check_todo_human(files):
    todo_items = []
    pattern = re.compile(r'\bTODO\(human\)', re.IGNORECASE)

    for rel_path in files:
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        if not os.path.isfile(full_path):
            continue
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                if pattern.search(line):
                    todo_items.append(f"{rel_path}:{line_no}: {line.strip()}")

    return todo_items


def main():
    parser = argparse.ArgumentParser(description="Check documentation consistency and link integrity.")
    parser.add_argument("--strict", action="store_true", help="Fail if any TODO(human) markers remain.")
    args = parser.parse_args()

    print("=" * 65)
    print("  CONTEXT INTELLIGENCE FRAMEWORK — DOCS CONSISTENCY CHECK")
    print("=" * 65)

    # 1. Print factual summary (reuses print_facts logic)
    print("\n--- Verifying Facts from Live Code & Data ---")
    q_facts = get_question_facts()
    test_cnt = get_test_count()
    mig_facts = get_migration_facts()
    ui_facts = get_ui_surface_facts()
    print(f"  [OK] WhyBench-Synth questions: {q_facts['total']} (dev: {q_facts['by_split'].get('dev', 0)}, test_v2: {q_facts['by_split'].get('test_v2', 0)})")
    print(f"  [OK] Unit tests discovered:     {test_cnt}")
    print(f"  [OK] Database migrations:      {mig_facts['count']}")
    print(f"  [OK] UI surfaces detected:      {ui_facts['count']}")

    files = get_tracked_markdown_files()
    print(f"\n--- Scanning {len(files)} Markdown Documents ---")

    # 2. Check banned strings
    banned_errors = check_banned_strings(files)
    if banned_errors:
        print(f"\n[FAIL] Found {len(banned_errors)} banned string occurrence(s):")
        for err in banned_errors:
            print(f"  - {err}")
    else:
        print("  [PASS] Zero banned strings found.")

    # 3. Check markdown links
    link_errors = check_markdown_links(files)
    if link_errors:
        print(f"\n[FAIL] Found {len(link_errors)} broken markdown link(s):")
        for err in link_errors:
            print(f"  - {err}")
    else:
        print("  [PASS] All repo-relative markdown links point to existing files/dirs.")

    # 4. Check backticked paths
    backtick_errors = check_backticked_paths(files)
    if backtick_errors:
        print(f"\n[FAIL] Found {len(backtick_errors)} broken backticked path(s):")
        for err in backtick_errors:
            print(f"  - {err}")
    else:
        print("  [PASS] All backticked repo-relative file paths exist.")

    # 5. Check TODO(human) markers
    todo_items = check_todo_human(files)
    if todo_items:
        print(f"\n[INFO] Found {len(todo_items)} pending human task marker(s) (TODO(human)):")
        for item in todo_items[:10]:
            print(f"  * {item}")
        if len(todo_items) > 10:
            print(f"  ... and {len(todo_items) - 10} more.")
    else:
        print("  [INFO] No TODO(human) markers found.")

    if args.strict and todo_items:
        print("\n[FAIL] --strict mode active: TODO(human) markers are not permitted.")
        return 1

    if banned_errors or link_errors or backtick_errors:
        print("\n[FAIL] Docs consistency checks FAILED.")
        return 1

    print("\n[SUCCESS] Docs consistency & integrity checks PASSED!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
