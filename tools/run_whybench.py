"""
WhyBench Evaluation Runner (Section 2.4 & Section 3.4)
Runs the Context Intelligence Framework and Baselines A-D against the WhyBench corpus.
"""
import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db import Database
from backend.evaluation.baselines import BaselineEvaluator, STOP_WORDS, tokenize
from backend.evaluation.benchmark import BenchmarkRunner, compute_decision_matching
from tools.ingest_whybench import build_whybench_db

def run_whybench(split: str = "dev", is_final: bool = False, force: bool = False, extractor_mode: str = "heuristic") -> Dict[str, Any]:
    whybench_dir = os.path.join(PROJECT_ROOT, "backend", "evaluation", "whybench")
    questions_file = os.path.join(whybench_dir, "questions.json")
    results_date_str = datetime.now().strftime("%Y%m%d")

    # Guard test split run per Section 2.4
    if split == "test" and not is_final:
        print("[ERROR] The 'test' split may only be evaluated with the explicit '--final' flag.")
        print("        Use '--split dev' for development and tuning.")
        sys.exit(1)

    existing_results = [f for f in os.listdir(whybench_dir) if f.startswith(f"results_{split}_")]
    if split == "test" and existing_results and not force:
        print(f"[ERROR] Test split results already exist ({existing_results[0]}).")
        print("        Re-running test evaluation is restricted to prevent overfitting. Use --force to override.")
        sys.exit(1)

    if extractor_mode == "both":
        from backend.engine.llm_client import LLMClient
        print(f"\n[INFO] Running dual extractor comparison on split '{split}'...")
        res_heur = run_whybench(split=split, is_final=is_final, force=force, extractor_mode="heuristic")
        llm_client = LLMClient()
        if llm_client.available():
            res_llm = run_whybench(split=split, is_final=is_final, force=True, extractor_mode="llm")
        else:
            res_llm = {
                "status": "not measured",
                "metrics": {
                    "decision_recall": "not measured",
                    "state_accuracy": "not measured",
                    "refusal_accuracy": "not measured"
                }
            }
        print("\n" + "=" * 65)
        print("  EXTRACTOR COMPARISON SUMMARY [DEV SPLIT]")
        print("=" * 65)
        print(f"  Heuristic Recall:        {res_heur['metrics']['decision_recall']}%")
        print(f"  Heuristic State Acc:     {res_heur['metrics']['state_accuracy']}%")
        print(f"  Heuristic Refusal Acc:   {res_heur['metrics']['refusal_accuracy']}%")
        print(f"  LLM Extractor Status:    {res_llm.get('status', 'measured')}")
        if res_llm.get("status") != "not measured":
            print(f"  LLM Recall:              {res_llm['metrics']['decision_recall']}%")
        else:
            print(f"  LLM Recall:              not measured (CIF_LLM_API_KEY unset)")
        print("=" * 65 + "\n")
        return {"heuristic": res_heur, "llm": res_llm}

    # Ingest / Load WhyBench DB
    db_path = os.path.join(PROJECT_ROOT, "whybench.db")
    db = build_whybench_db(db_path, extractor_mode=extractor_mode)

    with open(questions_file, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    # Filter for target split and verified items
    split_questions = [q for q in all_questions if q.get("split") == split and q.get("verified") is True]
    if not split_questions:
        print(f"[ERROR] No verified questions found for split '{split}'.")
        sys.exit(1)

    print(f"\n[INFO] Running WhyBench Evaluation on split: '{split}' ({len(split_questions)} questions) [Extractor: {extractor_mode}]")

    # Fetch system decisions
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM decisions WHERE review_status != 'human_rejected'")
        system_decisions = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT decision_id, event_id FROM decision_evidence")
        evidence_rows = cursor.fetchall()
        decision_to_evidence: Dict[str, set] = {}
        for r in evidence_rows:
            decision_to_evidence.setdefault(r["decision_id"], set()).add(r["event_id"])

    # Evaluate System Predictions (Step 4.1 Strict One-to-One Matching Protocol)
    standard_questions = [q for q in split_questions if q.get("expected_state") != "unresolved"]
    refusal_questions = [q for q in split_questions if q.get("expected_state") == "unresolved"]

    match_results = compute_decision_matching(standard_questions, system_decisions, decision_to_evidence)
    strict_match = match_results["strict"]
    lenient_match = match_results["lenient"]
    recall_difference = match_results["recall_difference"]

    strict_found_map = {f["gt_id"]: f for f in strict_match["found"]}
    question_results = []

    # 1. Standard questions (evaluated via strict one-to-one matching)
    for q in standard_questions:
        q_id = q["id"]
        outcome: Dict[str, Any] = {
            "id": q_id,
            "repo": q["repo"],
            "question": q["question"],
            "expected_state": q.get("expected_state"),
            "is_refusal_case": False
        }
        if q_id in strict_found_map:
            m = strict_found_map[q_id]
            state_match = (m["system_state"] == q.get("expected_state"))
            outcome["status"] = "found"
            outcome["system_decision_id"] = m["decision_id"]
            outcome["system_state"] = m["system_state"]
            outcome["state_match"] = state_match
            outcome["overlap_count"] = m.get("overlap_count", 1)
        else:
            outcome["status"] = "missed"
        question_results.append(outcome)

    # 2. Refusal questions
    refusal_correct_count = 0
    for q in refusal_questions:
        expected_events = set(q.get("evidence_event_ids", []))
        repo = q.get("repo")
        matched_decision = None
        for sd in system_decisions:
            if repo and sd.get("repo") != repo:
                continue
            sd_events = decision_to_evidence.get(sd["decision_id"], set())
            if expected_events and expected_events.intersection(sd_events):
                matched_decision = sd
                break

        outcome = {
            "id": q["id"],
            "repo": q["repo"],
            "question": q["question"],
            "expected_state": "unresolved",
            "is_refusal_case": True
        }
        if matched_decision is None:
            refusal_correct_count += 1
            outcome["status"] = "correct_refusal"
            outcome["system_answer"] = "No recorded architectural decision found (Refused)"
        else:
            outcome["status"] = "false_positive_decision"
            outcome["system_decision_id"] = matched_decision["decision_id"]
        question_results.append(outcome)

    total_standard_questions = len(standard_questions)
    refusal_total = len(refusal_questions)
    decision_recall = strict_match["recall"]
    decision_recall_strict = strict_match["recall"]
    decision_recall_lenient = lenient_match["recall"]
    state_accuracy = strict_match["state_accuracy"]
    state_accuracy_strict = strict_match["state_accuracy"]
    state_accuracy_lenient = lenient_match["state_accuracy"]
    refusal_accuracy = round((refusal_correct_count / refusal_total) * 100, 1) if refusal_total > 0 else 100.0

    # Task 1: Evidence Retrieval Evaluation (CIF top-5 hit rate vs Baselines)
    cif_task1_hits = 0
    for q in standard_questions:
        expected_events = set(q.get("evidence_event_ids", []))
        matched_id = strict_found_map.get(q["id"], {}).get("decision_id") or strict_found_map.get(q["id"], {}).get("system_decision_id")
        if matched_id and expected_events.intersection(decision_to_evidence.get(matched_id, set())):
            cif_task1_hits += 1
    cif_task1_hit_rate = round((cif_task1_hits / total_standard_questions) * 100, 1) if total_standard_questions > 0 else 0.0

    # Evaluate Baselines
    baseline_evaluator = BaselineEvaluator(db)
    baselines_out = baseline_evaluator.evaluate_all(split_questions)

    summary = {
        "benchmark": "WhyBench",
        "split": split,
        "date": datetime.now().isoformat(),
        "extractor_mode": extractor_mode,
        "questions_evaluated": len(split_questions),
        "standard_questions": total_standard_questions,
        "refusal_questions": refusal_total,
        "metrics": {
            "decision_recall": decision_recall,
            "decision_recall_strict": decision_recall_strict,
            "decision_recall_lenient": decision_recall_lenient,
            "recall_difference": recall_difference,
            "state_accuracy": state_accuracy,
            "state_accuracy_strict": state_accuracy_strict,
            "state_accuracy_lenient": state_accuracy_lenient,
            "refusal_accuracy": refusal_accuracy
        },
        "tasks": {
            "task_1_evidence_retrieval": {
                "name": "Task 1 — Evidence Retrieval (Top-5 Event Hit Rate)",
                "description": "Find the sources/events that explain X",
                "cif_hit_rate": cif_task1_hit_rate,
                "baseline_keyword_hit_rate": baselines_out["baseline_keyword"]["task_1_hit_rate"],
                "baseline_docs_only_hit_rate": baselines_out["baseline_docs_only"]["task_1_hit_rate"]
            },
            "task_2_decision_reconstruction": {
                "name": "Task 2 — Decision Reconstruction (State, Rationale, Alternatives)",
                "description": "Reconstruct decision state, rationale, alternatives, supersession, and refusal",
                "cif_strict_recall": decision_recall_strict,
                "cif_lenient_recall": decision_recall_lenient,
                "cif_state_accuracy": state_accuracy,
                "cif_refusal_accuracy": refusal_accuracy,
                "baseline_keyword": {
                    "strict_recall": "n/a",
                    "state_accuracy": "n/a",
                    "refusal_accuracy": "n/a (always answers)"
                },
                "baseline_docs_only": {
                    "strict_recall": "n/a",
                    "state_accuracy": "n/a",
                    "refusal_accuracy": "n/a (always answers)"
                }
            }
        },
        "baselines": baselines_out,
        "question_results": question_results
    }

    # Save results JSON
    out_filename = f"results_{split}_{results_date_str}.json"
    out_filepath = os.path.join(whybench_dir, out_filename)
    with open(out_filepath, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 65)
    print(f"  WHYBENCH RESULTS [{split.upper()} SPLIT]")
    print("=" * 65)
    print(f"  Total Questions:              {len(split_questions)}")
    print("-" * 65)
    print("  TASK 1 — EVIDENCE RETRIEVAL (Top-5 Event Hit Rate):")
    print(f"    CIF Event Hit Rate:         {cif_task1_hit_rate}% ({cif_task1_hits}/{total_standard_questions})")
    print(f"    Baseline A (Keyword BM25):  {baselines_out['baseline_keyword']['task_1_hit_rate']}% hit rate")
    print(f"    Baseline B (Docs-only):     {baselines_out['baseline_docs_only']['task_1_hit_rate']}% hit rate")
    print("-" * 65)
    print("  TASK 2 — DECISION RECONSTRUCTION:")
    print(f"    CIF Decision Recall (Strict): {decision_recall}% ({strict_match['matched_gt_count']}/{total_standard_questions})")
    print(f"    CIF Decision Recall (Lenient):{decision_recall_lenient}% ({lenient_match['matched_gt_count']}/{total_standard_questions})")
    if recall_difference > 0:
        print(f"    Overcounting Gap:             +{recall_difference}%")
    print(f"    CIF State Accuracy:           {state_accuracy}% ({strict_match['correct_state_count']}/{strict_match['matched_gt_count']})")
    print(f"    CIF Refusal Accuracy:         {refusal_accuracy}% ({refusal_correct_count}/{refusal_total})")
    print(f"    Baseline A (Keyword BM25):    n/a (unstructured search only)")
    print(f"    Baseline B (Docs-only):       n/a (unstructured search only)")
    print(f"    Baseline C (Plain LLM):       {baselines_out['baseline_llm']['status']}")
    print(f"    Baseline D (Copilot):         {baselines_out['baseline_copilot']['status']}")
    print("-" * 65)
    print(f"  Baseline A (Keyword):     {baselines_out['baseline_keyword']['decision_recall']}% recall")
    print(f"  Baseline B (Docs-only):   {baselines_out['baseline_docs_only']['decision_recall']}% recall")
    print(f"  Baseline C (Plain LLM):   {baselines_out['baseline_llm']['status']}")
    print(f"  Baseline D (Copilot):     {baselines_out['baseline_copilot']['status']}")
    print("=" * 65)
    print(f"  [SAVED] {out_filepath}\n")

    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WhyBench Evaluation Runner")
    parser.add_argument("--split", choices=["dev", "test"], default="dev", help="Dataset split to evaluate (dev or test)")
    parser.add_argument("--final", action="store_true", help="Required flag to evaluate the test split")
    parser.add_argument("--force", action="store_true", help="Force re-evaluation of test split")
    parser.add_argument("--extractor", choices=["heuristic", "llm", "both"], default="heuristic", help="Extraction engine")

    args = parser.parse_args()
    run_whybench(split=args.split, is_final=args.final, force=args.force, extractor_mode=args.extractor)
