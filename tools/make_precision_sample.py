"""
Precision Sampling Tool (Section 1.3 & Step 4.5)
Samples up to 40 system decisions per repository with a fixed random seed (1234)
from a named, hashed DB snapshot and writes a label template.

The label file records dataset_version, db_snapshot_sha256, repo, and decision_id per row,
and correct: null until a human fills it in.
The benchmark refuses to use labels whose snapshot hash does not match the DB being evaluated.
"""
import os
import sys
import json
import random
import argparse
from typing import Dict, Any, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db import Database, DB_PATH
from backend.evaluation.benchmark import compute_db_sha256

def make_precision_sample(
    db_path: str = None,
    output_path: str = None,
    sample_size_per_repo: int = 40,
    dataset_version: str = "whybench_v1",
    seed: int = 1234
) -> List[Dict[str, Any]]:
    if db_path is None:
        # Default to whybench.db if present, else DB_PATH
        whybench_path = os.path.join(PROJECT_ROOT, "whybench.db")
        db_path = whybench_path if os.path.exists(whybench_path) else DB_PATH

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database snapshot not found at: {db_path}")

    # Compute SHA-256 snapshot hash of the database
    snapshot_sha256 = compute_db_sha256(db_path)
    if not snapshot_sha256:
        raise ValueError(f"Failed to compute SHA-256 hash for database at: {db_path}")

    if output_path is None:
        output_path = os.path.join(PROJECT_ROOT, "backend", "evaluation", "precision_labels.json")

    import sqlite3
    db_abs = os.path.abspath(db_path)
    with sqlite3.connect(f"file:{db_abs}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT decision_id, repo, title, state, confidence, rationale
            FROM decisions
            WHERE review_status != 'human_rejected'
            ORDER BY repo, decision_id
        """)
        all_decisions = [dict(r) for r in cursor.fetchall()]

    # Group decisions by repository
    by_repo: Dict[str, List[Dict[str, Any]]] = {}
    for d in all_decisions:
        r = d.get("repo", "unknown")
        by_repo.setdefault(r, []).append(d)

    rng = random.Random(seed)
    sampled_rows = []

    for repo_name in sorted(by_repo.keys()):
        repo_decs = list(by_repo[repo_name])
        # Deterministic shuffle with seed
        rng.shuffle(repo_decs)
        selected = repo_decs[:sample_size_per_repo]
        # Sort selected by decision_id for clean deterministic output
        selected.sort(key=lambda x: x["decision_id"])

        for d in selected:
            sampled_rows.append({
                "dataset_version": dataset_version,
                "db_snapshot_sha256": snapshot_sha256,
                "repo": d["repo"],
                "decision_id": d["decision_id"],
                "title": d.get("title", ""),
                "state": d.get("state", ""),
                "confidence": d.get("confidence", 0.0),
                "rationale": (d.get("rationale") or "")[:250],
                "correct": None,
                "note": ""
            })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(sampled_rows, f, indent=2)
        f.write("\n")

    # Also keep whybench/precision_labels.json synchronized ONLY if output_path is default
    default_output = os.path.join(PROJECT_ROOT, "backend", "evaluation", "precision_labels.json")
    whybench_labels_path = os.path.join(PROJECT_ROOT, "backend", "evaluation", "whybench", "precision_labels.json")
    if os.path.abspath(output_path) == os.path.abspath(default_output):
        try:
            with open(whybench_labels_path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(sampled_rows, f, indent=2)
                f.write("\n")
        except Exception:
            pass

    print("=" * 68)
    print("  PRECISION LABEL TEMPLATE GENERATION COMPLETE (STEP 4.5)")
    print("=" * 68)
    print(f"  Snapshot DB:        {db_path}")
    print(f"  Snapshot SHA-256:   {snapshot_sha256}")
    print(f"  Dataset Version:    {dataset_version}")
    print(f"  Seed:               {seed}")
    print(f"  Repos Sampled:      {len(by_repo)}")
    print(f"  Total Decisions:    {len(all_decisions)}")
    print(f"  Total Sampled:      {len(sampled_rows)}")
    print(f"  Output Template:    {output_path}")
    print("=" * 68)
    return sampled_rows

def generate_precision_sample(db_path: str = None, output_path: str = None, sample_size: int = 40):
    """Backward-compatibility wrapper for existing callers."""
    return make_precision_sample(db_path=db_path, output_path=output_path, sample_size_per_repo=sample_size)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sample system decisions from hashed DB snapshot for precision evaluation.")
    parser.add_argument("--db", default=None, help="Path to SQLite DB snapshot")
    parser.add_argument("--output", default=None, help="Path to output precision_labels.json")
    parser.add_argument("--sample-size", type=int, default=40, help="Max decisions to sample per repository")
    parser.add_argument("--version", default="whybench_v1", help="Dataset version string")
    parser.add_argument("--seed", type=int, default=1234, help="Random seed for sampling determinism")
    args = parser.parse_args()

    make_precision_sample(
        db_path=args.db,
        output_path=args.output,
        sample_size_per_repo=args.sample_size,
        dataset_version=args.version,
        seed=args.seed
    )
