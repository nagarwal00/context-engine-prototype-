"""
WhyBench Evaluation Runner (Section 2.4 & Section 3.4)
Runs the Context Intelligence Framework and Baselines A-D against the WhyBench corpus.
"""
import os
import sys
import json
import hashlib
import subprocess
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db import Database
from backend.evaluation.baselines import BaselineEvaluator, STOP_WORDS, tokenize
from backend.evaluation.benchmark import BenchmarkRunner, compute_decision_matching, evaluate_precision_labels
from backend.evaluation.calibration import compute_calibration, format_calibration_markdown
from tools.ingest_whybench import build_whybench_db
from tools.generate_evaluation_report import generate_evaluation_report


def compute_file_sha256(filepath: str) -> str:
    """Computes SHA-256 hash of a file for reproducible manifest."""
    if not filepath or not os.path.exists(filepath):
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_git_metadata() -> Dict[str, Any]:
    """Retrieves current git commit HEAD and clean/dirty working tree flag."""
    commit = "unknown"
    clean = False
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, stderr=subprocess.DEVNULL)
        commit = out.decode("utf-8").strip()
        status_out = subprocess.check_output(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, stderr=subprocess.DEVNULL)
        clean = (len(status_out.strip()) == 0)
    except Exception:
        pass
    return {"git_commit": commit, "git_clean": clean}


def run_whybench(split: str = "dev", is_final: bool = False, force: bool = False, extractor_mode: str = "heuristic", run_id: Optional[str] = None, rebuild_db: bool = True) -> Dict[str, Any]:
    whybench_dir = os.path.join(PROJECT_ROOT, "backend", "evaluation", "whybench")
    questions_file = os.path.join(whybench_dir, "questions.json")
    results_date_str = datetime.now().strftime("%Y%m%d")
    if not run_id:
        run_id = f"{split}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Guard test split run per Section 2.4 & Step 4.9
    if split in ("test", "test_v2") and not is_final:
        print(f"[ERROR] The '{split}' split may only be evaluated with the explicit '--final' flag.")
        print("        Use '--split dev' for development and tuning.")
        sys.exit(1)

    existing_results = [f for f in os.listdir(whybench_dir) if f.startswith(f"results_{split}_")]
    if split in ("test", "test_v2") and existing_results and not force:
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
    db = build_whybench_db(db_path, extractor_mode=extractor_mode, rebuild=rebuild_db)

    with open(questions_file, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    # Filter for target split and verified items
    split_questions = [q for q in all_questions if (q.get("split") == split or (split == "test" and q.get("split") == "test_v2")) and q.get("verified") is True]
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
    standard_questions = [q for q in split_questions if q.get("expected_state") not in ("unresolved", "none")]
    refusal_questions = [q for q in split_questions if q.get("expected_state") in ("unresolved", "none")]

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

    # 2. Refusal / negative questions (Step 4.6 unrecorded & mention_without_decision mix)
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

        # Check for unrecorded tech false positives (type a)
        if matched_decision is None and not expected_events:
            q_text = q.get("question", "").lower()
            q_tokens = set(tokenize(q_text)) - STOP_WORDS
            for sd in system_decisions:
                if repo and sd.get("repo") != repo:
                    continue
                sd_title_tokens = set(tokenize(sd.get("title", ""))) - STOP_WORDS
                sd_problem_tokens = set(tokenize(sd.get("problem_statement", ""))) - STOP_WORDS
                sd_all = sd_title_tokens | sd_problem_tokens
                if any(w in sd_all for w in q_tokens if len(w) > 5 and w in ("mongodb", "dynamodb", "elasticsearch", "cassandra", "memcached", "spanner", "vault", "consul", "istio", "envoy", "traefik")):
                    matched_decision = sd
                    break

        outcome = {
            "id": q["id"],
            "repo": q["repo"],
            "question": q["question"],
            "expected_state": q.get("expected_state", "none"),
            "negative_type": q.get("negative_type", "unrecorded"),
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

    # Evaluate Baselines (fair comparison: positive/standard questions only)
    baseline_evaluator = BaselineEvaluator(db)
    baselines_out = baseline_evaluator.evaluate_all(standard_questions)

    # Evaluate Human-Labelled Precision (Step 4.5) & Calibration (Step 4.7)
    precision_val, precision_reason = evaluate_precision_labels(db.db_path, whybench_dir)

    labels_file = os.path.join(whybench_dir, "precision_labels.json")
    labelled_items = []
    if os.path.exists(labels_file):
        try:
            with open(labels_file, "r", encoding="utf-8") as f:
                raw_labels = json.load(f)
                if isinstance(raw_labels, list):
                    labelled_items = raw_labels
                elif isinstance(raw_labels, dict):
                    labelled_items = raw_labels.get("samples", [])
        except Exception:
            labelled_items = []

    calibration_res = compute_calibration(labelled_items, num_bins=5, min_labels_for_ece=100)

    # Per-Repository Metrics Computation (Step 4.8)
    repos = sorted(list(set(q.get("repo") for q in split_questions if q.get("repo"))))
    per_repo_metrics = {}

    for r in repos:
        repo_split_qs = [q for q in split_questions if q.get("repo") == r]
        repo_std_qs = [q for q in standard_questions if q.get("repo") == r]
        repo_ref_qs = [q for q in refusal_questions if q.get("repo") == r]
        r_std_tot = len(repo_std_qs)
        r_ref_tot = len(repo_ref_qs)

        # Task 1 CIF hits
        r_cif_hits = 0
        for q in repo_std_qs:
            expected_events = set(q.get("evidence_event_ids", []))
            m_id = strict_found_map.get(q["id"], {}).get("decision_id")
            if m_id and expected_events.intersection(decision_to_evidence.get(m_id, set())):
                r_cif_hits += 1
        r_cif_hit_rate = round((r_cif_hits / r_std_tot) * 100, 1) if r_std_tot > 0 else 0.0

        # Task 1 Baselines (fair comparison: positive/standard questions only)
        r_kw = baseline_evaluator.run_baseline_keyword(repo_std_qs)
        r_doc = baseline_evaluator.run_baseline_docs_only(repo_std_qs)

        # Task 2 Strict & Lenient Matching
        r_strict_found = [f for f in strict_match["found"] if f.get("gt_id") in {q["id"] for q in repo_std_qs}]
        r_lenient_found = [f for f in lenient_match["found"] if f.get("gt_id") in {q["id"] for q in repo_std_qs}]
        r_strict_cnt = len(r_strict_found)
        r_lenient_cnt = len(r_lenient_found)
        r_strict_recall = round((r_strict_cnt / r_std_tot) * 100, 1) if r_std_tot > 0 else 0.0
        r_lenient_recall = round((r_lenient_cnt / r_std_tot) * 100, 1) if r_std_tot > 0 else 0.0

        # State accuracy
        r_state_corr = sum(1 for f in r_strict_found if any(q["id"] == f["gt_id"] and q.get("expected_state") == f["system_state"] for q in repo_std_qs))
        r_state_acc = round((r_state_corr / r_strict_cnt) * 100, 1) if r_strict_cnt > 0 else 0.0

        # Refusal accuracy
        r_ref_corr = sum(1 for q in question_results if q.get("repo") == r and q.get("is_refusal_case") and q.get("status") == "correct_refusal")
        r_ref_acc = round((r_ref_corr / r_ref_tot) * 100, 1) if r_ref_tot > 0 else 100.0

        per_repo_metrics[r] = {
            "questions_total": len(repo_split_qs),
            "standard_questions": r_std_tot,
            "refusal_questions": r_ref_tot,
            "task_1_cif_hits": r_cif_hits,
            "task_1_cif_hit_rate": r_cif_hit_rate,
            "baseline_keyword_hit_rate": r_kw.get("task_1_hit_rate", 0.0),
            "baseline_docs_only_hit_rate": r_doc.get("task_1_hit_rate", 0.0),
            "strict_matched_gt_count": r_strict_cnt,
            "lenient_matched_gt_count": r_lenient_cnt,
            "decision_recall_strict": r_strict_recall,
            "decision_recall_lenient": r_lenient_recall,
            "state_correct_count": r_state_corr,
            "state_accuracy": r_state_acc,
            "refusal_correct_count": r_ref_corr,
            "refusal_accuracy": r_ref_acc,
            "decision_precision": precision_val,
            "decision_precision_reason": precision_reason
        }

    overall_metrics = {
        "task_1_cif_hit_rate": cif_task1_hit_rate,
        "task_1_cif_hits": cif_task1_hits,
        "task_1_cif_metric_label": "Decision-evidence hit rate",
        "task_1_cif_metric_definition": "single strictly-matched decision cites >=1 expected evidence event; not a ranked top-5 retrieval",
        "decision_recall_strict": decision_recall_strict,
        "strict_matched_gt_count": strict_match["matched_gt_count"],
        "decision_recall_lenient": decision_recall_lenient,
        "lenient_matched_gt_count": lenient_match["matched_gt_count"],
        "recall_difference": recall_difference,
        "state_accuracy": state_accuracy,
        "state_correct_count": strict_match["correct_state_count"],
        "refusal_accuracy": refusal_accuracy,
        "refusal_correct_count": refusal_correct_count,
        "decision_precision": precision_val,
        "decision_precision_reason": precision_reason,
        "calibration": calibration_res,
        "baseline_keyword": baselines_out["baseline_keyword"],
        "baseline_docs_only": baselines_out["baseline_docs_only"],
        "baseline_llm": baselines_out["baseline_llm"],
        "baseline_copilot": baselines_out["baseline_copilot"]
    }

    # Step 4.8 Manifest Compilation
    git_meta = get_git_metadata()
    dataset_hashes = {
        "dataset_version": "whybench_v1",
        "questions_sha256": compute_file_sha256(questions_file),
        "precision_labels_sha256": compute_file_sha256(os.path.join(whybench_dir, "precision_labels.json")),
        "drift_cases_sha256": compute_file_sha256(os.path.join(PROJECT_ROOT, "backend", "evaluation", "drift_cases.json")),
        "conflict_cases_sha256": compute_file_sha256(os.path.join(PROJECT_ROOT, "backend", "evaluation", "conflict_cases.json")),
        "db_snapshot_sha256": compute_file_sha256(db_path)
    }

    manifest = {
        "manifest_version": "1.0",
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "split": split,
        "questions_evaluated": len(split_questions),
        "standard_questions": total_standard_questions,
        "refusal_questions": refusal_total,
        "environment": {
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
            "git_commit": git_meta["git_commit"],
            "git_clean": git_meta["git_clean"]
        },
        "configurations": {
            "extractor_mode": extractor_mode,
            "llm_model": os.environ.get("CIF_LLM_MODEL", "none"),
            "decision_threshold": float(os.environ.get("CIF_DECISION_THRESHOLD", "0.85")),
            "random_seed": 1234
        },
        "dataset_hashes": dataset_hashes,
        "metrics": {
            "overall": overall_metrics,
            "per_repository": per_repo_metrics
        },
        "predictions": question_results
    }

    # Write Manifests
    run_dir = os.path.join(PROJECT_ROOT, "results", run_id)
    os.makedirs(run_dir, exist_ok=True)
    manifest_path = os.path.join(run_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    latest_manifest_path = os.path.join(PROJECT_ROOT, "results", "latest_manifest.json")
    with open(latest_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Legacy results JSON for backwards compatibility
    out_filename = f"results_{split}_{results_date_str}.json"
    out_filepath = os.path.join(whybench_dir, out_filename)
    with open(out_filepath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Automatically generate evaluation_results.md dynamically from latest manifest (Step 4.8)
    try:
        generate_evaluation_report(manifest_path, os.path.join(PROJECT_ROOT, "evaluation_results.md"))
    except Exception as e:
        print(f"  [WARN] Failed to regenerate evaluation_results.md from manifest: {e}")

    print("\n" + "=" * 65)
    print(f"  WHYBENCH RESULTS [{split.upper()} SPLIT] (Run ID: {run_id})")
    print("=" * 65)
    print(f"  Total Questions:              {len(split_questions)}")
    print("-" * 65)
    print("  TASK 1 — EVIDENCE RETRIEVAL (Decision-Evidence Hit Rate):")
    print(f"    CIF Decision-Evidence Hit Rate: {cif_task1_hit_rate}% ({cif_task1_hits}/{total_standard_questions})")
    print(f"    Baseline A (Keyword BM25):  {baselines_out['baseline_keyword']['task_1_hit_rate']}% hit rate")
    print(f"    Baseline B (Docs-only):     {baselines_out['baseline_docs_only']['task_1_hit_rate']}% hit rate")
    print("-" * 65)
    print("  TASK 2 — DECISION RECONSTRUCTION:")
    print(f"    CIF Decision Recall (Strict): {decision_recall_strict}% ({strict_match['matched_gt_count']}/{total_standard_questions})")
    print(f"    CIF Decision Recall (Lenient):{decision_recall_lenient}% ({lenient_match['matched_gt_count']}/{total_standard_questions})")
    if recall_difference > 0:
        print(f"    Overcounting Gap:             +{recall_difference}%")
    print(f"    CIF State Accuracy:           {state_accuracy}% ({strict_match['correct_state_count']}/{strict_match['matched_gt_count']})")
    print(f"    CIF Refusal Accuracy:         {refusal_accuracy}% ({refusal_correct_count}/{refusal_total})")
    print(f"    CIF Decision Precision:       {precision_val} ({precision_reason})")
    cal_reason = calibration_res.get('reason') or f"ECE={calibration_res.get('ece_pct')}%"
    print(f"    CIF Calibration (ECE):        {calibration_res['status']} ({cal_reason})")
    print("-" * 65)
    print("  PER-REPOSITORY BREAKDOWN:")
    for r, rdata in sorted(per_repo_metrics.items()):
        print(f"    * {r}:")
        print(f"        T1 Hit Rate: {rdata['task_1_cif_hit_rate']}% ({rdata['task_1_cif_hits']}/{rdata['standard_questions']})")
        print(f"        T2 Strict Recall: {rdata['decision_recall_strict']}% ({rdata['strict_matched_gt_count']}/{rdata['standard_questions']})")
        print(f"        T2 Refusal Acc: {rdata['refusal_accuracy']}% ({rdata['refusal_correct_count']}/{rdata['refusal_questions']})")
    print("=" * 65)
    print(f"  [SAVED MANIFEST] {manifest_path}")
    print(f"  [SAVED LATEST]   {latest_manifest_path}\n")

    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WhyBench Evaluation Runner")
    parser.add_argument("--split", choices=["dev", "test", "test_v2"], default="dev", help="Dataset split to evaluate (dev, test, or test_v2)")
    parser.add_argument("--final", action="store_true", help="Required flag to evaluate the test split")
    parser.add_argument("--force", action="store_true", help="Force re-evaluation of test split")
    parser.add_argument("--extractor", choices=["heuristic", "llm", "both"], default="heuristic", help="Extraction engine")
    parser.add_argument("--run-id", type=str, default=None, help="Explicit run ID identifier for manifest")
    parser.add_argument("--no-rebuild", action="store_true", help="Reuse existing DB snapshot if present")

    args = parser.parse_args()
    run_whybench(split=args.split, is_final=args.final, force=args.force, extractor_mode=args.extractor, run_id=args.run_id, rebuild_db=not args.no_rebuild)

