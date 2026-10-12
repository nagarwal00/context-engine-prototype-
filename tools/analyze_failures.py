"""
WhyBench Failure Analysis Tool (Step 4.3)
Classifies every missed ground-truth item into exactly one category:
  1. not_ingested   - Expected evidence event absent from DB
  2. no_candidate   - Event present, no decision extracted from bundle
  3. filtered       - Candidate produced/event present but removed by noise/quality filter
  4. wrong_evidence - Decision exists for topic/entity but cites different events
  5. wrong_state    - Found with shared evidence, but lifecycle state differs
Also lists wrongly-extracted system decisions (false positives) with short reasons.
Outputs structured JSON and Markdown summary table.
"""
import os
import sys
import json
import argparse
from typing import Dict, Any, List, Set, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db import Database
from backend.models import Event
from backend.evaluation.benchmark import compute_decision_matching
from backend.evaluation.baselines import tokenize, STOP_WORDS
from backend.engine.extractor import is_decision_candidate
from tools.ingest_whybench import build_whybench_db

CATEGORY_ORDER = ["not_ingested", "no_candidate", "filtered", "wrong_evidence", "wrong_state"]

def classify_missed_item(
    q: Dict[str, Any],
    db_events: Dict[str, Event],
    system_decisions: List[Dict[str, Any]],
    decision_to_evidence: Dict[str, Set[str]],
    found_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Classifies a missed or failed ground-truth item into exactly one category
    in the strict priority order defined by Step 4.3.
    """
    q_id = q["id"]
    repo = q.get("repo", "")
    expected_events = set(q.get("evidence_event_ids", []) or q.get("expected_evidence_contains", []))
    expected_state = q.get("expected_state")

    # If the item was matched with shared evidence but state was wrong
    if found_info and not found_info.get("state_match", True):
        return {
            "category": "wrong_state",
            "reason": f"Found decision '{found_info.get('decision_id')}' sharing evidence, but system state '{found_info.get('system_state')}' != expected '{expected_state}'",
            "matched_decision_id": found_info.get("decision_id"),
            "system_state": found_info.get("system_state"),
            "expected_state": expected_state,
            "evidence_events": list(expected_events)
        }

    # 1. not_ingested: expected evidence event(s) absent from DB
    ingested_events = [eid for eid in expected_events if eid in db_events]
    if not ingested_events:
        return {
            "category": "not_ingested",
            "reason": f"Expected evidence event(s) {list(expected_events)} absent from database events table",
            "missing_events": list(expected_events),
            "ingested_events": []
        }

    # 2. filtered: event present, but pre-filtered by noise/trivial heuristic
    for eid in ingested_events:
        ev = db_events[eid]
        if not is_decision_candidate(ev):
            return {
                "category": "filtered",
                "reason": f"Event '{eid}' ({ev.source_type}) pre-filtered as noise/trivial commit by is_decision_candidate",
                "filtered_event": eid,
                "event_source_type": ev.source_type
            }

    # 3. wrong_evidence: a decision exists in the same repository for this topic/entity, but cites different events
    q_tokens = set(tokenize((q.get("title") or "") + " " + (q.get("question") or "")))
    repo_decisions = [d for d in system_decisions if d.get("repo") == repo]
    topic_match_decision = None
    for d in repo_decisions:
        d_tokens = set(tokenize((d.get("title") or "") + " " + (d.get("rationale") or "")))
        overlap = len(q_tokens.intersection(d_tokens))
        if overlap >= 3:
            topic_match_decision = d
            break

    if topic_match_decision is not None:
        cites = list(decision_to_evidence.get(topic_match_decision["decision_id"], set()))
        return {
            "category": "wrong_evidence",
            "reason": f"Decision '{topic_match_decision['decision_id']}' exists for overlapping topic, but cites {cites} instead of expected {list(expected_events)}",
            "existing_decision_id": topic_match_decision["decision_id"],
            "existing_evidence": cites,
            "expected_evidence": list(expected_events)
        }

    # 4. no_candidate: event present and passed candidate check, but no decision extracted from its bundle
    return {
        "category": "no_candidate",
        "reason": f"Event(s) {ingested_events} present in DB, but extractor extracted 0 decision candidates from its bundle",
        "ingested_events": ingested_events
    }

def analyze_failures(
    split: str = "dev",
    db_path: Optional[str] = None,
    output_json: Optional[str] = None,
    output_md: Optional[str] = None
) -> Dict[str, Any]:
    whybench_dir = os.path.join(PROJECT_ROOT, "backend", "evaluation", "whybench")
    questions_file = os.path.join(whybench_dir, "questions.json")

    if db_path is None:
        db_path = os.path.join(PROJECT_ROOT, "whybench.db")

    if not os.path.exists(db_path):
        print(f"[INFO] Initializing and building WhyBench database at: {db_path}...")
        db = build_whybench_db(db_path)
    else:
        db = Database(db_path)

    with open(questions_file, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    split_questions = [q for q in all_questions if q.get("split") == split and q.get("verified") is True]
    standard_questions = [q for q in split_questions if q.get("expected_state") != "unresolved"]
    refusal_questions = [q for q in split_questions if q.get("expected_state") == "unresolved"]

    # Fetch DB events
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events")
        db_events = {}
        for r in cursor.fetchall():
            row = dict(r)
            arts = json.loads(row["artifacts_touched"]) if isinstance(row["artifacts_touched"], str) else row["artifacts_touched"]
            ev = Event(
                event_id=row["event_id"],
                source_type=row["source_type"],
                source_id=row["source_id"],
                source_url=row["source_url"],
                repo=row["repo"],
                author=row.get("author", ""),
                timestamp=row.get("ts", ""),
                title=row.get("title", ""),
                body=row.get("body", ""),
                artifacts_touched=arts or []
            )
            db_events[row["event_id"]] = ev

        cursor.execute("SELECT * FROM decisions WHERE review_status != 'human_rejected'")
        system_decisions = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT decision_id, event_id FROM decision_evidence")
        decision_to_evidence: Dict[str, Set[str]] = {}
        for r in cursor.fetchall():
            decision_to_evidence.setdefault(r["decision_id"], set()).add(r["event_id"])

    # Run matching
    match_results = compute_decision_matching(standard_questions, system_decisions, decision_to_evidence)
    strict = match_results["strict"]
    found_map = {f["gt_id"]: f for f in strict["found"]}
    wrong_state_map = {f["gt_id"]: f for f in strict["wrong_state"]}

    # Classify failures
    classified_failures = []
    repo_stats: Dict[str, Dict[str, int]] = {}
    category_totals = {cat: 0 for cat in CATEGORY_ORDER}

    for q in standard_questions:
        q_id = q["id"]
        repo = q["repo"]
        repo_stats.setdefault(repo, {cat: 0 for cat in CATEGORY_ORDER})

        found_info = found_map.get(q_id)
        if found_info and found_info.get("state_match", True) and q_id not in wrong_state_map:
            continue  # Correctly extracted True Positive

        # Classify this failure
        ws_info = wrong_state_map.get(q_id)
        info = ws_info if ws_info else found_info
        classification = classify_missed_item(q, db_events, system_decisions, decision_to_evidence, info)
        cat = classification["category"]

        category_totals[cat] = category_totals.get(cat, 0) + 1
        repo_stats[repo][cat] = repo_stats[repo].get(cat, 0) + 1

        classified_failures.append({
            "id": q_id,
            "repo": repo,
            "question": q["question"],
            "expected_state": q.get("expected_state"),
            "expected_evidence": q.get("evidence_event_ids", []),
            "category": cat,
            "reason": classification["reason"],
            "details": classification
        })

    # Evaluate False Positives
    false_positives = []
    matched_sd_ids = set(strict["matched_system_ids"])

    # (a) Refusal False Positives: System decision matched against a refusal question
    for q in refusal_questions:
        expected_events = set(q.get("evidence_event_ids", []))
        repo = q.get("repo")
        for sd in system_decisions:
            if repo and sd.get("repo") != repo:
                continue
            sd_events = decision_to_evidence.get(sd["decision_id"], set())
            if expected_events.intersection(sd_events):
                false_positives.append({
                    "type": "refusal_false_positive",
                    "decision_id": sd["decision_id"],
                    "repo": repo,
                    "title": sd["title"],
                    "state": sd["state"],
                    "question_id": q["id"],
                    "reason": f"Decision was extracted on negative refusal question '{q['id']}' (system should have abstained)"
                })

    # (b) Unmatched System Decisions in DB
    for sd in system_decisions:
        if sd["decision_id"] not in matched_sd_ids:
            cites = list(decision_to_evidence.get(sd["decision_id"], set()))
            false_positives.append({
                "type": "unmatched_decision",
                "decision_id": sd["decision_id"],
                "repo": sd["repo"],
                "title": sd["title"],
                "state": sd["state"],
                "cites": cites,
                "reason": "System decision extracted from repository history does not match any evaluated ground-truth question"
            })

    report = {
        "split": split,
        "standard_questions_total": len(standard_questions),
        "found_strictly": strict["matched_gt_count"],
        "total_failures": len(classified_failures),
        "category_totals": category_totals,
        "repo_breakdown": repo_stats,
        "failures": classified_failures,
        "false_positives_total": len(false_positives),
        "false_positives": false_positives
    }

    # Format Markdown
    md_lines = []
    md_lines.append(f"# WhyBench Failure Analysis Report — Split: `{split}`")
    md_lines.append("")
    md_lines.append(f"- **Standard Questions Evaluated**: {len(standard_questions)}")
    md_lines.append(f"- **Successfully Extracted (Strict 1-to-1)**: {strict['matched_gt_count']}")
    md_lines.append(f"- **Total Misses & State Mismatches**: {len(classified_failures)}")
    md_lines.append(f"- **False Positive Decisions**: {len(false_positives)}")
    md_lines.append("")
    md_lines.append("## 1. Failure Counts by Category")
    md_lines.append("")
    md_lines.append("| Category | Total Count | Description |")
    md_lines.append("|---|:---:|---|")
    md_lines.append(f"| `not_ingested` | **{category_totals.get('not_ingested', 0)}** | Expected evidence event is absent from DB `events` table |")
    md_lines.append(f"| `no_candidate` | **{category_totals.get('no_candidate', 0)}** | Event present in DB, but no decision was extracted from bundle |")
    md_lines.append(f"| `filtered` | **{category_totals.get('filtered', 0)}** | Candidate event removed by pre-filter or noise filter |")
    md_lines.append(f"| `wrong_evidence` | **{category_totals.get('wrong_evidence', 0)}** | Decision exists for topic/entity, but cites different events |")
    md_lines.append(f"| `wrong_state` | **{category_totals.get('wrong_state', 0)}** | Decision matched with evidence, but state differs from expected |")
    md_lines.append("")
    md_lines.append("## 2. Failure Breakdown by Repository")
    md_lines.append("")
    md_lines.append("| Repository | not_ingested | no_candidate | filtered | wrong_evidence | wrong_state | Total Missed |")
    md_lines.append("|---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for r, stats in repo_stats.items():
        tot = sum(stats.values())
        md_lines.append(f"| `{r}` | {stats.get('not_ingested',0)} | {stats.get('no_candidate',0)} | {stats.get('filtered',0)} | {stats.get('wrong_evidence',0)} | {stats.get('wrong_state',0)} | **{tot}** |")
    md_lines.append("")
    md_lines.append("## 3. Itemized Failure Analysis")
    md_lines.append("")
    for f_item in classified_failures:
        md_lines.append(f"### `{f_item['id']}` ({f_item['repo']}) — `{f_item['category']}`")
        md_lines.append(f"- **Question**: {f_item['question']}")
        md_lines.append(f"- **Expected State**: `{f_item['expected_state']}`")
        md_lines.append(f"- **Expected Events**: `{f_item['expected_evidence']}`")
        md_lines.append(f"- **Failure Reason**: {f_item['reason']}")
        md_lines.append("")

    md_lines.append("## 4. Wrongly-Extracted System Decisions (False Positives)")
    md_lines.append("")
    md_lines.append(f"Total false positive / unlinked decisions identified: **{len(false_positives)}**")
    md_lines.append("")
    for fp in false_positives[:10]:
        md_lines.append(f"- **`{fp['decision_id']}`** (`{fp['repo']}`): *{fp['title']}* — {fp['reason']}")
    if len(false_positives) > 10:
        md_lines.append(f"- *... and {len(false_positives) - 10} more unlinked decisions*")
    md_lines.append("")

    markdown_content = "\n".join(md_lines)

    # Save files if requested or default locations
    if output_json is None:
        results_dir = os.path.join(PROJECT_ROOT, "results")
        os.makedirs(results_dir, exist_ok=True)
        output_json = os.path.join(results_dir, f"{split}_failure_analysis.json")

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if output_md is None:
        docs_dir = os.path.join(PROJECT_ROOT, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        output_md = os.path.join(docs_dir, f"{split}_failure_analysis.md")

    with open(output_md, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    # Terminal output
    print("\n" + "=" * 70)
    print(f"  WHYBENCH FAILURE ANALYSIS [{split.upper()} SPLIT]")
    print("=" * 70)
    print(f"  Standard Questions Evaluated:  {len(standard_questions)}")
    print(f"  Strict True Positives:         {strict['matched_gt_count']}")
    print(f"  Total Missed / State Mismatch: {len(classified_failures)}")
    print("-" * 70)
    print("  CATEGORY BREAKDOWN (PRIORITY ORDER):")
    print(f"    1. not_ingested:             {category_totals.get('not_ingested', 0)}")
    print(f"    2. no_candidate:             {category_totals.get('no_candidate', 0)}")
    print(f"    3. filtered:                 {category_totals.get('filtered', 0)}")
    print(f"    4. wrong_evidence:           {category_totals.get('wrong_evidence', 0)}")
    print(f"    5. wrong_state:              {category_totals.get('wrong_state', 0)}")
    print("-" * 70)
    print("  PER-REPOSITORY BREAKDOWN:")
    for r, stats in repo_stats.items():
        print(f"    {r[:32]:<32} | missed: {sum(stats.values())} (no_cand: {stats['no_candidate']}, not_ingest: {stats['not_ingested']})")
    print("-" * 70)
    print(f"  False Positive Decisions:      {len(false_positives)}")
    print(f"  [SAVED JSON] {output_json}")
    print(f"  [SAVED MD]   {output_md}")
    print("=" * 70 + "\n")

    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WhyBench Failure Analysis Tool (Step 4.3)")
    parser.add_argument("--split", choices=["dev", "test"], default="dev", help="Split to analyze (default: dev)")
    parser.add_argument("--db", default=None, help="Path to whybench database")
    parser.add_argument("--output-json", default=None, help="Path to write JSON failure report")
    parser.add_argument("--output-md", default=None, help="Path to write Markdown failure report")

    args = parser.parse_args()
    analyze_failures(split=args.split, db_path=args.db, output_json=args.output_json, output_md=args.output_md)
