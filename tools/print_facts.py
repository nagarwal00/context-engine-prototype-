#!/usr/bin/env python3
"""
tools/print_facts.py - Factual counts derived directly from data.
Prints question counts, test counts, migration count, and UI surfaces.
"""
import glob
import json
import os
import re
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_question_facts():
    q_path = os.path.join(PROJECT_ROOT, "backend", "evaluation", "whybench", "questions.json")
    with open(q_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    total = len(questions)
    by_split = {}
    by_repo = {}
    by_split_repo = {}

    for q in questions:
        split = q.get("split", "unknown")
        repo = q.get("repo") or q.get("repo_full_name", "unknown")

        by_split[split] = by_split.get(split, 0) + 1
        by_repo[repo] = by_repo.get(repo, 0) + 1

        if split not in by_split_repo:
            by_split_repo[split] = {}
        by_split_repo[split][repo] = by_split_repo[split].get(repo, 0) + 1

    return {
        "total": total,
        "by_split": by_split,
        "by_repo": by_repo,
        "by_split_repo": by_split_repo,
    }


def get_test_count():
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(PROJECT_ROOT, "tests"), pattern="test_*.py")
    return suite.countTestCases()


def get_migration_facts():
    mig_dir = os.path.join(PROJECT_ROOT, "backend", "migrations")
    files = glob.glob(os.path.join(mig_dir, "*.py"))
    # Match numbered pattern like 001_... or v001_...
    numbered = [f for f in files if re.search(r"(?:v)?\d{3}_", os.path.basename(f))]
    names = sorted(os.path.basename(f) for f in numbered)
    return {
        "count": len(numbered),
        "files": names,
    }


def get_ui_surface_facts():
    html_path = os.path.join(PROJECT_ROOT, "web", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find unique data-view or data-surface or id="surface-..."
    views = set(re.findall(r'data-view=["\']([^"\']+)["\']', content))
    if not views:
        views = set(re.findall(r'data-surface=["\']([^"\']+)["\']', content))
    if not views:
        views = set(re.findall(r'id=["\']surface-([^"\']+)["\']', content))

    return {
        "count": len(views),
        "views": sorted(views),
    }


def main():
    q_facts = get_question_facts()
    test_count = get_test_count()
    mig_facts = get_migration_facts()
    ui_facts = get_ui_surface_facts()

    print("=" * 60)
    print("  CONTEXT INTELLIGENCE FRAMEWORK — FACTUAL SUMMARY")
    print("=" * 60)
    print(f"1. WhyBench-Synth Questions:")
    print(f"   - Total Questions: {q_facts['total']}")
    for split, cnt in sorted(q_facts['by_split'].items()):
        print(f"     * Split '{split}': {cnt}")
    print(f"   - Per-repository totals:")
    for repo, cnt in sorted(q_facts['by_repo'].items()):
        print(f"     * {repo}: {cnt}")

    print(f"\n2. Automated Unit Tests:")
    print(f"   - Discovered Test Cases: {test_count}")

    print(f"\n3. Database Migrations:")
    print(f"   - Migration Scripts Count: {mig_facts['count']}")
    print(f"   - Range: {mig_facts['files'][0][:3]} to {mig_facts['files'][-1][:3]} ({len(mig_facts['files'])} migrations: {', '.join(mig_facts['files'])})")

    print(f"\n4. Web UI Surfaces:")
    print(f"   - Interactive Surfaces Count: {ui_facts['count']}")
    print(f"   - View IDs: {', '.join(ui_facts['views'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
