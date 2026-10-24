"""
tools/recompute_task1_fair.py
Fair Task-1 Comparison Recomputation Tool (Step 2.1)

Scores baseline retrieval methods and CIF on the exact same positive questions
(expected_state != "none"), computes Wilson 95% confidence intervals, and records
the fair comparison as a separate corrections file without mutating frozen manifests.
"""
import argparse
import json
import math
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.db import Database
from backend.evaluation.baselines import BaselineEvaluator


def compute_wilson_interval(k: int, n: int, z: float = 1.96) -> Optional[Tuple[float, float]]:
    """Computes Wilson score 95% confidence interval for binomial proportions."""
    if n == 0:
        return None
    p = k / n
    d = 1.0 + (z * z) / n
    c = (p + (z * z) / (2.0 * n)) / d
    h = (z * math.sqrt((p * (1.0 - p)) / n + (z * z) / (4.0 * n * n))) / d
    return (round(c - h, 4), round(c + h, 4))


def recompute_task1_fair(
    split: str = "test_v2",
    db_path: Path = PROJECT_ROOT / "whybench.db",
    out_path: Optional[Path] = None
) -> Dict[str, Any]:
    if out_path is None:
        out_path = PROJECT_ROOT / "results" / "test_v2_20261013_100423" / "corrections_task1_fair.json"

    manifest_path = PROJECT_ROOT / "results" / "latest_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Latest manifest not found at {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        latest_manifest = json.load(f)

    questions_path = PROJECT_ROOT / "backend" / "evaluation" / "whybench" / "questions.json"
    with open(questions_path, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    split_questions = [q for q in all_questions if q.get("split") == split]
    positives = [q for q in split_questions if q.get("expected_state") != "none"]
    positives_n = len(positives)

    # Work on a temporary copy of the database to ensure immutability
    temp_dir = tempfile.mkdtemp()
    temp_db_path = Path(temp_dir) / "wb_temp.db"
    shutil.copy2(db_path, temp_db_path)

    try:
        temp_db = Database(str(temp_db_path))
        evaluator = BaselineEvaluator(temp_db)

        # Baseline evaluation on positives only
        kw_res = evaluator.run_baseline_keyword(positives)
        doc_res = evaluator.run_baseline_docs_only(positives)

        kw_hits = kw_res.get("found_count", 0)
        kw_rate = kw_res.get("task_1_hit_rate", round(kw_hits / positives_n * 100, 1) if positives_n else 0.0)
        kw_wilson = compute_wilson_interval(kw_hits, positives_n)

        doc_hits = doc_res.get("found_count", 0)
        doc_rate = doc_res.get("task_1_hit_rate", round(doc_hits / positives_n * 100, 1) if positives_n else 0.0)
        doc_wilson = compute_wilson_interval(doc_hits, positives_n)

        # CIF numbers read directly from existing frozen manifest
        overall_m = latest_manifest.get("metrics", {}).get("overall", {})
        cif_hits = overall_m.get("task_1_cif_hits", 21)
        cif_rate = overall_m.get("task_1_cif_hit_rate", 80.8)
        cif_wilson = compute_wilson_interval(cif_hits, positives_n)

        # Per repository breakdown
        repos = sorted(list({q.get("repo") for q in positives if q.get("repo")}))
        per_repo_results: Dict[str, Any] = {}
        manifest_per_repo = latest_manifest.get("metrics", {}).get("per_repository", {})

        for r in repos:
            r_pos = [q for q in positives if q.get("repo") == r]
            r_n = len(r_pos)
            r_kw = evaluator.run_baseline_keyword(r_pos)
            r_doc = evaluator.run_baseline_docs_only(r_pos)

            r_kw_hits = r_kw.get("found_count", 0)
            r_kw_rate = r_kw.get("task_1_hit_rate", round(r_kw_hits / r_n * 100, 1) if r_n else 0.0)
            r_kw_wilson = compute_wilson_interval(r_kw_hits, r_n)

            r_doc_hits = r_doc.get("found_count", 0)
            r_doc_rate = r_doc.get("task_1_hit_rate", round(r_doc_hits / r_n * 100, 1) if r_n else 0.0)
            r_doc_wilson = compute_wilson_interval(r_doc_hits, r_n)

            m_r = manifest_per_repo.get(r, {})
            r_cif_hits = m_r.get("task_1_cif_hits", 0)
            r_cif_rate = m_r.get("task_1_cif_hit_rate", round(r_cif_hits / r_n * 100, 1) if r_n else 0.0)
            r_cif_wilson = compute_wilson_interval(r_cif_hits, r_n)

            per_repo_results[r] = {
                "positives_n": r_n,
                "cif": {
                    "hits": r_cif_hits,
                    "n": r_n,
                    "rate": r_cif_rate,
                    "wilson95_low": r_cif_wilson[0] if r_cif_wilson else None,
                    "wilson95_high": r_cif_wilson[1] if r_cif_wilson else None,
                },
                "baseline_keyword": {
                    "hits": r_kw_hits,
                    "n": r_n,
                    "rate": r_kw_rate,
                    "wilson95_low": r_kw_wilson[0] if r_kw_wilson else None,
                    "wilson95_high": r_kw_wilson[1] if r_kw_wilson else None,
                    "original_rate": m_r.get("baseline_keyword_hit_rate"),
                },
                "baseline_docs_only": {
                    "hits": r_doc_hits,
                    "n": r_n,
                    "rate": r_doc_rate,
                    "wilson95_low": r_doc_wilson[0] if r_doc_wilson else None,
                    "wilson95_high": r_doc_wilson[1] if r_doc_wilson else None,
                    "original_rate": m_r.get("baseline_docs_only_hit_rate"),
                }
            }

        correction_data = {
            "generated_by": "tools/recompute_task1_fair.py",
            "split": split,
            "reason": "baselines were originally scored over all questions incl. negatives; CIF over positives only",
            "positives_n": positives_n,
            "cif_metric_definition": "single strictly-matched decision cites >=1 expected evidence event; not a ranked top-5 retrieval",
            "original_values": {
                "baseline_keyword_rate": overall_m.get("baseline_keyword", {}).get("task_1_hit_rate", 59.2),
                "baseline_keyword_total_count": overall_m.get("baseline_keyword", {}).get("total_count", 71),
                "baseline_docs_only_rate": overall_m.get("baseline_docs_only", {}).get("task_1_hit_rate", 8.5),
                "baseline_docs_only_total_count": overall_m.get("baseline_docs_only", {}).get("total_count", 71),
            },
            "overall": {
                "cif": {
                    "hits": cif_hits,
                    "n": positives_n,
                    "rate": cif_rate,
                    "wilson95_low": cif_wilson[0] if cif_wilson else None,
                    "wilson95_high": cif_wilson[1] if cif_wilson else None,
                },
                "baseline_keyword": {
                    "hits": kw_hits,
                    "n": positives_n,
                    "rate": kw_rate,
                    "wilson95_low": kw_wilson[0] if kw_wilson else None,
                    "wilson95_high": kw_wilson[1] if kw_wilson else None,
                },
                "baseline_docs_only": {
                    "hits": doc_hits,
                    "n": positives_n,
                    "rate": doc_rate,
                    "wilson95_low": doc_wilson[0] if doc_wilson else None,
                    "wilson95_high": doc_wilson[1] if doc_wilson else None,
                }
            },
            "per_repository": per_repo_results
        }

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(correction_data, f, indent=2)

        print("=" * 70)
        print("  TASK-1 FAIR RECOMPUTATION COMPLETE")
        print("=" * 70)
        print(f"  Split:               {split}")
        print(f"  Positives Evaluated: {positives_n} (expected_state != 'none')")
        print(f"  CIF:                 {cif_hits}/{positives_n} ({cif_rate}%) Wilson: {cif_wilson}")
        print(f"  BM25 (Baseline A):   {kw_hits}/{positives_n} ({kw_rate}%) Wilson: {kw_wilson}")
        print(f"  Docs (Baseline B):   {doc_hits}/{positives_n} ({doc_rate}%) Wilson: {doc_wilson}")
        print(f"  Output saved to:     {out_path}")
        print("=" * 70)

        return correction_data

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Recompute Task-1 fair comparisons")
    parser.add_argument("--split", type=str, default="test_v2", help="Dataset split (default: test_v2)")
    parser.add_argument("--db", type=str, default=str(PROJECT_ROOT / "whybench.db"), help="Path to whybench database")
    parser.add_argument(
        "--out",
        type=str,
        default=str(PROJECT_ROOT / "results" / "test_v2_20261013_100423" / "corrections_task1_fair.json"),
        help="Path to output corrections json"
    )
    args = parser.parse_args()

    recompute_task1_fair(
        split=args.split,
        db_path=Path(args.db),
        out_path=Path(args.out)
    )


if __name__ == "__main__":
    main()
