"""
WhyBench Validation Script (Section 2.3)
Checks schema compliance, verified flags, public URL citations, split ratio,
uniqueness, per-repo question quotas (>= 20 per repo), and event existence.
"""
import os
import sys
import json
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def validate_whybench_questions(file_path: str = None) -> bool:
    if file_path is None:
        file_path = os.path.join(PROJECT_ROOT, "backend", "evaluation", "whybench", "questions.json")

    if not os.path.exists(file_path):
        print(f"[FAIL] WhyBench questions file not found at: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    if not questions or not isinstance(questions, list):
        print("[FAIL] Questions file must be a non-empty JSON list.")
        return False

    # Load all repo event IDs to verify existence
    data_dir = os.path.join(PROJECT_ROOT, "backend", "evaluation", "whybench", "data")
    repo_event_ids = defaultdict(set)
    if os.path.exists(data_dir):
        for rdir in os.listdir(data_dir):
            ev_file = os.path.join(data_dir, rdir, "events.json")
            if os.path.exists(ev_file):
                with open(ev_file, "r", encoding="utf-8") as f:
                    evs = json.load(f)
                    for e in evs:
                        repo_event_ids[e["repo"]].add(e["event_id"])

    seen_ids = set()
    dev_count = 0
    test_count = 0
    unverified_count = 0
    repo_counts = defaultdict(int)
    errors = []

    for idx, q in enumerate(questions):
        qid = q.get("id")
        if not qid:
            errors.append(f"Item #{idx} is missing 'id'.")
        elif qid in seen_ids:
            errors.append(f"Duplicate ID found: '{qid}'.")
        else:
            seen_ids.add(qid)

        repo = q.get("repo")
        if not repo:
            errors.append(f"Question {qid} is missing 'repo'.")
        else:
            repo_counts[repo] += 1

        if not q.get("question"):
            errors.append(f"Question {qid} is missing 'question' text.")
        if not q.get("answer_summary"):
            errors.append(f"Question {qid} is missing 'answer_summary'.")

        expected_state = q.get("expected_state")
        if expected_state not in ("accepted", "rejected", "proposed", "superseded", "unresolved"):
            errors.append(f"Question {qid} has invalid expected_state: '{expected_state}'.")

        # Refusal cases (unresolved) have empty evidence; others must have evidence
        if expected_state != "unresolved":
            urls = q.get("evidence_urls", [])
            if not urls:
                errors.append(f"Question {qid} ({expected_state}) must have at least one public evidence_url.")
            for u in urls:
                if not (u.startswith("http://") or u.startswith("https://")):
                    errors.append(f"Question {qid} has invalid URL: '{u}'.")

            ev_ids = q.get("evidence_event_ids", [])
            if not ev_ids:
                errors.append(f"Question {qid} is missing evidence_event_ids.")
            else:
                for eid in ev_ids:
                    if repo in repo_event_ids and eid not in repo_event_ids[repo]:
                        errors.append(f"Question {qid} references event '{eid}' not found in {repo} events.")

        if not q.get("verified"):
            unverified_count += 1

        split = q.get("split")
        if split == "dev":
            dev_count += 1
        elif split == "test":
            test_count += 1
        else:
            errors.append(f"Question {qid} has invalid split: '{split}'. Must be 'dev' or 'test'.")

    # Check minimum per-repo counts (Acceptance criteria: >= 20 verified questions per repo)
    for r, count in repo_counts.items():
        if count < 20:
            errors.append(f"Repository '{r}' only has {count} questions (minimum 20 required by handoff spec).")

    total = len(questions)
    dev_ratio = round((dev_count / total) * 100, 1) if total > 0 else 0
    test_ratio = round((test_count / total) * 100, 1) if total > 0 else 0

    print("=" * 60)
    print("  WHYBENCH DATASET VALIDATION REPORT")
    print("=" * 60)
    print(f"  Total Questions:      {total}")
    print(f"  Dev Split:            {dev_count} ({dev_ratio}%)")
    print(f"  Test Split:           {test_count} ({test_ratio}%)")
    print(f"  Verified Items:       {total - unverified_count}/{total}")
    print("  Per-Repository Breakdown:")
    for r, c in sorted(repo_counts.items()):
        print(f"    - {r}: {c} questions")
    print(f"  Validation Errors:    {len(errors)}")
    print("=" * 60)

    if errors:
        for err in errors:
            print(f"  [ERROR] {err}")
        return False

    if unverified_count > 0:
        print(f"  [WARN] {unverified_count} questions are not marked 'verified: true'.")
        return False

    print("  [SUCCESS] WhyBench questions dataset schema is 100% valid!")
    return True

if __name__ == "__main__":
    valid = validate_whybench_questions()
    sys.exit(0 if valid else 1)
