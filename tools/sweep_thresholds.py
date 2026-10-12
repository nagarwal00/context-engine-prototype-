"""
Threshold Sweep Evaluation for CIF Decision Extraction (Step 4.4)
Computes precision, recall, and F1 curve across confidence thresholds on dev split.
"""
import os
import sys
import json
import sqlite3

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.evaluation.benchmark import compute_decision_matching

def run_threshold_sweep(db_path: str = None):
    if db_path is None:
        db_path = os.path.join(PROJECT_ROOT, "whybench.db")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Load all decisions
    c.execute("""
        SELECT decision_id, repo, title, state, confidence, review_status
        FROM decisions
    """)
    all_decisions = [dict(row) for row in c.fetchall()]

    # Load evidence mapping
    c.execute("SELECT decision_id, event_id FROM decision_evidence")
    decision_to_evidence = {}
    for row in c.fetchall():
        d_id = row["decision_id"]
        e_id = row["event_id"]
        if d_id not in decision_to_evidence:
            decision_to_evidence[d_id] = set()
        decision_to_evidence[d_id].add(e_id)

    # Load dev ground truth questions
    q_file = os.path.join(PROJECT_ROOT, "backend", "evaluation", "whybench", "questions.json")
    with open(q_file, "r", encoding="utf-8") as f:
        all_qs = json.load(f)

    dev_standard = [q for q in all_qs if q.get("split") == "dev" and q.get("expected_state") != "unresolved"]
    total_gt = len(dev_standard)

    thresholds = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95]
    results = []

    print("=" * 78)
    print("  CONFIDENCE THRESHOLD SWEEP (DEV SPLIT) — STEP 4.4")
    print("=" * 78)
    print(f"{'Threshold (theta)':<18} | {'Decisions':<10} | {'TP':<5} | {'FP':<5} | {'Recall':<8} | {'Precision':<10} | {'F1':<8}")
    print("-" * 78)

    for th in thresholds:
        filtered_decs = [d for d in all_decisions if (d.get("confidence") or 0.0) >= th]
        m = compute_decision_matching(dev_standard, filtered_decs, decision_to_evidence)
        strict = m["strict"]
        tp = strict["matched_gt_count"]
        fp = strict["unmatched_system_count"]
        total_sys = len(filtered_decs)

        recall = round((tp / total_gt) * 100, 1) if total_gt > 0 else 0.0
        precision = round((tp / total_sys) * 100, 1) if total_sys > 0 else 0.0
        f1 = round(2 * (precision * recall) / (precision + recall), 1) if (precision + recall) > 0 else 0.0

        print(f"  theta >= {th:<10.2f} | {total_sys:<10} | {tp:<5} | {fp:<5} | {recall:>5.1f}% | {precision:>8.1f}% | {f1:>5.1f}%")

        results.append({
            "threshold": th,
            "total_system_decisions": total_sys,
            "true_positives": tp,
            "false_positives": fp,
            "recall": recall,
            "precision": precision,
            "f1": f1
        })

    print("=" * 78)
    return results

if __name__ == "__main__":
    run_threshold_sweep()
