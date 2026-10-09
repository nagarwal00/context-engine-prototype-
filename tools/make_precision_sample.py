"""
Precision Sampling Tool (Section 1.3)
Samples up to 30 system decisions from the database with a fixed random seed (1234)
and generates a template precision_labels.json for human-in-the-loop labeling.
"""
import os
import sys
import json
import random

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db import Database, DB_PATH

def generate_precision_sample(db_path: str = DB_PATH, output_path: str = None, sample_size: int = 30):
    if output_path is None:
        output_path = os.path.join(PROJECT_ROOT, "backend", "evaluation", "precision_labels.json")

    db = Database(db_path)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT decision_id, title, repo, made_by, state, rationale FROM decisions WHERE review_status != 'human_rejected'")
        decisions = [dict(r) for r in cursor.fetchall()]

    if not decisions:
        print(f"[WARN] No decisions found in DB at {db_path}. Writing empty template.")
        samples = []
    else:
        # Fixed random seed for deterministic sampling
        rng = random.Random(1234)
        shuffled = list(decisions)
        rng.shuffle(shuffled)
        sampled = shuffled[:sample_size]

        samples = []
        for d in sampled:
            samples.append({
                "decision_id": d["decision_id"],
                "repo": d["repo"],
                "title": d["title"],
                "state": d["state"],
                "correct": None,
                "note": ""
            })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)

    print(f"[OK] Generated {len(samples)} precision sample items -> {output_path}")

if __name__ == "__main__":
    generate_precision_sample()
