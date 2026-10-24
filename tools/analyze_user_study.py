"""
tools/analyze_user_study.py
Analyzes empirical user study results for the Context Intelligence Framework (Step 4.4).

Calculates per-condition:
- Mean and median completion time (seconds)
- Decision correctness rate (%) with Wilson 95% confidence intervals
- Subjective confidence ratings (1-5 Likert scale)
- Within-subject paired differences (time saved, accuracy delta)

Refuses to print statistical conclusions when participant count N < 5
to maintain strict scientific and academic integrity (no fabricated rows).
"""
import argparse
import csv
import math
import os
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def compute_wilson_interval(k: int, n: int, z: float = 1.96) -> Optional[Tuple[float, float]]:
    if n == 0:
        return None
    p = k / n
    d = 1.0 + (z * z) / n
    c = (p + (z * z) / (2.0 * n)) / d
    h = (z * math.sqrt((p * (1.0 - p)) / n + (z * z) / (4.0 * n * n))) / d
    return (round(c - h, 4), round(c + h, 4))


def parse_and_validate_row(row: Dict[str, str], row_idx: int) -> Dict[str, Any]:
    pid = (row.get("participant_id") or "").strip()
    if not pid:
        raise ValueError(f"Row {row_idx}: missing participant_id")

    tool = (row.get("tool") or "").strip().lower()
    if tool in ("cif", "cif_tool", "context_intelligence"):
        normalized_tool = "cif"
    elif tool in ("baseline", "baseline_search", "github", "github_search", "grep"):
        normalized_tool = "baseline"
    else:
        raise ValueError(f"Row {row_idx} ({pid}): invalid tool '{tool}' (must be 'cif' or 'baseline')")

    raw_time = (row.get("time_seconds") or "").strip()
    try:
        time_sec = float(raw_time)
        if time_sec < 0:
            raise ValueError()
    except Exception:
        raise ValueError(f"Row {row_idx} ({pid}): invalid time_seconds '{raw_time}' (must be >= 0)")

    raw_correct = (row.get("correct") or "").strip()
    if raw_correct in ("1", "1.0", "true", "yes"):
        correct = 1
    elif raw_correct in ("0", "0.0", "false", "no"):
        correct = 0
    else:
        raise ValueError(f"Row {row_idx} ({pid}): invalid correct '{raw_correct}' (must be 0 or 1)")

    raw_conf = (row.get("confidence") or "").strip()
    try:
        conf = float(raw_conf)
        if not (1.0 <= conf <= 5.0):
            raise ValueError()
    except Exception:
        raise ValueError(f"Row {row_idx} ({pid}): invalid confidence '{raw_conf}' (must be between 1 and 5)")

    return {
        "participant_id": pid,
        "task_id": (row.get("task_id") or "").strip(),
        "tool": normalized_tool,
        "time_seconds": time_sec,
        "correct": correct,
        "confidence": conf,
        "notes": (row.get("notes") or "").strip()
    }


def analyze_user_study_data(csv_path: Path) -> Dict[str, Any]:
    if not csv_path.exists():
        raise FileNotFoundError(f"User study results CSV not found: {csv_path}")

    raw_rows = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if any(v.strip() for v in r.values() if v):
                raw_rows.append(r)

    if not raw_rows:
        print("=" * 70)
        print("  USER STUDY ANALYSIS (STEP 4.4)")
        print("=" * 70)
        print(f"  Data File:          {csv_path}")
        print("  Status:             AWAITING HUMAN PARTICIPANT DATA (HUMAN TASK H-5)")
        print("  Evaluated Trials:   0")
        print("  Participants Found: 0 / 5 (minimum required)")
        print("=" * 70)
        print("[NOTICE] Statistical conclusions are refused when n < 5 participants.")
        print("To run the study, follow user_study/PROTOCOL.md and fill user_study/results_template.csv.")
        print("=" * 70)
        return {
            "status": "not measured",
            "reason": "awaiting human participant data (0 trials recorded)",
            "participants_n": 0,
            "trials_n": 0
        }

    validated_rows = [parse_and_validate_row(r, idx) for idx, r in enumerate(raw_rows, 2)]
    participants = sorted(list(set(r["participant_id"] for r in validated_rows)))
    num_participants = len(participants)

    if num_participants < 5:
        print("=" * 70)
        print("  USER STUDY ANALYSIS (STEP 4.4)")
        print("=" * 70)
        print(f"  Data File:          {csv_path}")
        print("  Status:             AWAITING HUMAN PARTICIPANT DATA (HUMAN TASK H-5)")
        print(f"  Evaluated Trials:   {len(validated_rows)}")
        print(f"  Participants Found: {num_participants} / 5 (minimum required)")
        print("=" * 70)
        print(f"[NOTICE] Statistical conclusions are REFUSED: sample size (N={num_participants}) is below the required minimum (N >= 5).")
        print("Academic integrity policy: Zero fabricated participant rows.")
        print("To complete Human Task H-5, recruit 5 to 8 participants per user_study/PROTOCOL.md.")
        print("=" * 70)
        return {
            "status": "not measured",
            "reason": f"insufficient sample size (n={num_participants} < 5)",
            "participants_n": num_participants,
            "trials_n": len(validated_rows)
        }

    # Group by tool
    cif_rows = [r for r in validated_rows if r["tool"] == "cif"]
    base_rows = [r for r in validated_rows if r["tool"] == "baseline"]

    def compute_condition_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not rows:
            return {}
        times = [r["time_seconds"] for r in rows]
        corrects = [r["correct"] for r in rows]
        confs = [r["confidence"] for r in rows]
        n = len(rows)
        k_correct = sum(corrects)

        mean_time = round(statistics.mean(times), 1)
        median_time = round(statistics.median(times), 1)
        acc_rate = round((k_correct / n) * 100, 1)
        wilson = compute_wilson_interval(k_correct, n)
        mean_conf = round(statistics.mean(confs), 2)

        return {
            "n": n,
            "mean_time_seconds": mean_time,
            "median_time_seconds": median_time,
            "correct_hits": k_correct,
            "accuracy_rate": acc_rate,
            "accuracy_wilson_95": wilson,
            "mean_confidence": mean_conf
        }

    cif_stats = compute_condition_stats(cif_rows)
    base_stats = compute_condition_stats(base_rows)

    # Compute paired differences
    cif_by_p = {r["participant_id"]: r for r in cif_rows}
    base_by_p = {r["participant_id"]: r for r in base_rows}
    common_pids = sorted(list(set(cif_by_p.keys()).intersection(base_by_p.keys())))

    time_savings = []
    acc_deltas = []
    conf_deltas = []

    for pid in common_pids:
        c_r = cif_by_p[pid]
        b_r = base_by_p[pid]
        # Positive time saving = CIF is faster than baseline
        time_savings.append(b_r["time_seconds"] - c_r["time_seconds"])
        acc_deltas.append(c_r["correct"] - b_r["correct"])
        conf_deltas.append(c_r["confidence"] - b_r["confidence"])

    paired_summary = {}
    if common_pids:
        paired_summary = {
            "paired_participants_n": len(common_pids),
            "mean_time_saved_seconds": round(statistics.mean(time_savings), 1),
            "median_time_saved_seconds": round(statistics.median(time_savings), 1),
            "mean_accuracy_delta": round(statistics.mean(acc_deltas) * 100, 1),
            "mean_confidence_delta": round(statistics.mean(conf_deltas), 2)
        }

    # Print evaluation report
    print("=" * 70)
    print("  USER STUDY STATISTICAL EVALUATION RESULTS (N >= 5)")
    print("=" * 70)
    print(f"  Total Participants (N):  {num_participants}")
    print(f"  Total Executed Trials:   {len(validated_rows)}")
    print(f"  Paired Participants:     {len(common_pids)}")
    print("-" * 70)
    print("  CONDITION COMPARISON:")
    print(f"  Metric                     | CIF (Context Intelligence) | Baseline Code Search")
    print(f"  ---------------------------+----------------------------+---------------------")
    print(f"  Sample Size (Trials)       | {cif_stats.get('n', 0):<26} | {base_stats.get('n', 0)}")
    print(f"  Mean Time (seconds)        | {cif_stats.get('mean_time_seconds', 0.0):<26} | {base_stats.get('mean_time_seconds', 0.0)}")
    print(f"  Median Time (seconds)      | {cif_stats.get('median_time_seconds', 0.0):<26} | {base_stats.get('median_time_seconds', 0.0)}")
    print(f"  Decision Accuracy          | {cif_stats.get('accuracy_rate', 0.0)}% ({cif_stats.get('correct_hits', 0)}/{cif_stats.get('n', 0)}){'':<13} | {base_stats.get('accuracy_rate', 0.0)}% ({base_stats.get('correct_hits', 0)}/{base_stats.get('n', 0)})")
    print(f"  Accuracy Wilson 95% CI     | {str(cif_stats.get('accuracy_wilson_95')):<26} | {str(base_stats.get('accuracy_wilson_95'))}")
    print(f"  Mean Confidence (1-5)      | {cif_stats.get('mean_confidence', 0.0):<26} | {base_stats.get('mean_confidence', 0.0)}")
    print("-" * 70)
    if paired_summary:
        print("  WITHIN-SUBJECT PAIRED DIFFERENCES (CIF vs Baseline):")
        print(f"  Mean Time Saved by CIF:    {paired_summary['mean_time_saved_seconds']} seconds")
        print(f"  Median Time Saved:         {paired_summary['median_time_saved_seconds']} seconds")
        print(f"  Accuracy Difference:       {paired_summary['mean_accuracy_delta']:+0.1f}%")
        print(f"  Confidence Difference:     {paired_summary['mean_confidence_delta']:+0.2f} points (1-5 scale)")
    print("=" * 70)

    return {
        "status": "measured",
        "participants_n": num_participants,
        "trials_n": len(validated_rows),
        "cif": cif_stats,
        "baseline": base_stats,
        "paired": paired_summary
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze empirical user study results.")
    parser.add_argument("--csv", default=str(PROJECT_ROOT / "user_study/results_template.csv"), help="Path to study results CSV")
    args = parser.parse_args()

    analyze_user_study_data(Path(args.csv))


if __name__ == "__main__":
    main()
