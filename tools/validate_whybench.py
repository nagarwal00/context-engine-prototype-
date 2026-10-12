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
        if expected_state not in ("accepted", "rejected", "proposed", "superseded", "unresolved", "none"):
            errors.append(f"Question {qid} has invalid expected_state: '{expected_state}'.")

        # Refusal / negative cases (unresolved or none)
        is_negative = expected_state in ("unresolved", "none")
        if is_negative:
            neg_type = q.get("negative_type")
            if not neg_type or neg_type not in ("unrecorded", "mention_without_decision"):
                errors.append(f"Negative question {qid} ({expected_state}) must declare negative_type as 'unrecorded' or 'mention_without_decision'.")
            for u in q.get("evidence_urls", []):
                if not (u.startswith("http://") or u.startswith("https://")):
                    errors.append(f"Question {qid} has invalid URL: '{u}'.")
        else:
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
        elif split in ("test", "test_v2"):
            test_count += 1
        else:
            errors.append(f"Question {qid} has invalid split: '{split}'. Must be 'dev', 'test', or 'test_v2'.")

    # Check minimum per-repo counts (Acceptance criteria: >= 20 verified questions per repo)
    for r, count in repo_counts.items():
        if count < 20:
            errors.append(f"Repository '{r}' only has {count} questions (minimum 20 required by handoff spec).")

    # Step 4.6: Check representative negative cases mix (>= 15 negatives per repo, at least half of type b)
    neg_stats = defaultdict(lambda: defaultdict(lambda: {"total": 0, "type_a": 0, "type_b": 0}))
    for q in questions:
        if q.get("expected_state") in ("unresolved", "none"):
            s = q.get("split")
            r = q.get("repo")
            nt = q.get("negative_type", "unrecorded")
            neg_stats[s][r]["total"] += 1
            if nt == "mention_without_decision":
                neg_stats[s][r]["type_b"] += 1
            else:
                neg_stats[s][r]["type_a"] += 1

    for s in ("dev", "test_v2") if "test_v2" in neg_stats else ("dev", "test"):
        for r in sorted(repo_counts.keys()):
            counts = neg_stats[s][r]
            tot = counts["total"]
            tb = counts["type_b"]
            if tot < 15:
                errors.append(f"Repository '{r}' in split '{s}' has only {tot} negative cases (minimum 15 required by Step 4.6).")
            if tb < (tot / 2):
                errors.append(f"Repository '{r}' in split '{s}' has {tb}/{tot} type (b) negatives (at least half required by Step 4.6).")

    # Step 4.9: Check frozen test split test_v2 requirements (>= 20 questions per repo & frozen hash check)
    v2_questions = [q for q in questions if q.get("split") == "test_v2"]
    if v2_questions:
        v2_repo_counts = defaultdict(int)
        for q in v2_questions:
            v2_repo_counts[q.get("repo")] += 1
        for r in sorted(repo_counts.keys()):
            c = v2_repo_counts[r]
            if c < 20:
                errors.append(f"Repository '{r}' in 'test_v2' split has only {c} verified questions (minimum 20 required by Step 4.9).")

    frozen_file = os.path.join(PROJECT_ROOT, "backend", "evaluation", "whybench", "FROZEN.md")
    if os.path.exists(frozen_file):
        import hashlib
        with open(file_path, "rb") as f:
            actual_q_hash = hashlib.sha256(f.read()).hexdigest()
        with open(frozen_file, "r", encoding="utf-8") as f:
            frozen_content = f.read()
        if actual_q_hash not in frozen_content:
            errors.append(f"questions.json SHA-256 ({actual_q_hash}) does not match frozen hash recorded in FROZEN.md!")

    total = len(questions)
    dev_ratio = round((dev_count / total) * 100, 1) if total > 0 else 0
    test_ratio = round((test_count / total) * 100, 1) if total > 0 else 0

    print("=" * 65)
    print("  WHYBENCH DATASET VALIDATION REPORT")
    print("=" * 65)
    print(f"  Total Questions:      {total}")
    print(f"  Dev Split:            {dev_count} ({dev_ratio}%)")
    print(f"  Test Split:           {test_count} ({test_ratio}%)")
    print(f"  Verified Items:       {total - unverified_count}/{total}")
    print("  Per-Repository Breakdown:")
    for r, c in sorted(repo_counts.items()):
        print(f"    - {r}: {c} questions")
    print("-" * 65)
    print("  REPRESENTATIVE NEGATIVE CASES MIX (STEP 4.6):")
    for s in ("dev", "test_v2") if "test_v2" in neg_stats else ("dev", "test"):
        print(f"    Split '{s}':")
        for r in sorted(repo_counts.keys()):
            c = neg_stats[s][r]
            pct_b = round((c['type_b'] / c['total']) * 100, 1) if c['total'] > 0 else 0.0
            print(f"      * {r}: {c['total']} negatives (type_a: {c['type_a']}, type_b: {c['type_b']} [{pct_b}%])")
    print("-" * 65)
    print(f"  Validation Errors:    {len(errors)}")
    print("=" * 65)

    if errors:
        for err in errors:
            print(f"  [ERROR] {err}")
        return False

    if unverified_count > 0:
        print(f"  [WARN] {unverified_count} questions are not marked 'verified: true'.")
        return False

    print("  [SUCCESS] WhyBench questions dataset schema & negative mix are 100% valid!")
    return True

if __name__ == "__main__":
    valid = validate_whybench_questions()
    sys.exit(0 if valid else 1)
