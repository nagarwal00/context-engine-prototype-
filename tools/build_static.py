"""
Static Dataset Snapshot Generator (Phase 8.1)
Runs the CIF APIHandler in-process to export all GET endpoints to web/static_data.js,
then mirrors web/ into docs/ for GitHub Pages static deployment.
Deterministic: running multiple times yields identical output.
"""
import os
import sys
import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.db import Database
from backend.api import APIHandler
from backend.seed_data import populate_seed_data

def build_static():
    db_path = PROJECT_ROOT / "context_intelligence.db"
    db = Database(str(db_path))

    # Ensure DB has seed data if empty
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS c FROM decisions")
        if cursor.fetchone()["c"] == 0:
            populate_seed_data(db)

    api = APIHandler(db)

    endpoints = {}

    # Standard endpoint snapshots
    endpoints["stats"] = api.handle_get("/api/stats", {})
    endpoints["timeline_all"] = api.handle_get("/api/timeline", {})
    endpoints["timeline_thermal"] = api.handle_get("/api/timeline", {"repo": ["acme-eng/thermal-control-system"]})
    endpoints["timeline_cache"] = api.handle_get("/api/timeline", {"repo": ["acme-eng/distributed-cache-service"]})
    endpoints["graph_all"] = api.handle_get("/api/graph", {})
    endpoints["graph_thermal"] = api.handle_get("/api/graph", {"repo": ["acme-eng/thermal-control-system"]})
    endpoints["graph_cache"] = api.handle_get("/api/graph", {"repo": ["acme-eng/distributed-cache-service"]})
    endpoints["artifacts_all"] = api.handle_get("/api/artifacts", {})
    endpoints["artifacts_thermal"] = api.handle_get("/api/artifacts", {"repo": ["acme-eng/thermal-control-system"]})
    endpoints["artifacts_cache"] = api.handle_get("/api/artifacts", {"repo": ["acme-eng/distributed-cache-service"]})
    endpoints["decisions_all"] = api.handle_get("/api/decisions", {})
    endpoints["review_queue"] = api.handle_get("/api/review-queue", {})
    endpoints["benchmark"] = api.handle_get("/api/benchmark", {})

    # Explanations for all artifacts
    explains = {}
    artifacts_list = endpoints["artifacts_all"].get("data", [])
    for art in artifacts_list:
        c_path = art.get("canonical_path")
        if c_path:
            explains[c_path] = api.handle_get("/api/explain", {"artifact": [c_path]})

    # Evidence trails for all decisions
    evidences = {}
    decisions_list = endpoints["decisions_all"].get("data", [])
    for dec in decisions_list:
        d_id = dec.get("decision_id")
        if d_id:
            evidences[d_id] = api.handle_get("/api/evidence", {"decision_id": [d_id]})

    static_bundle = {
        "endpoints": endpoints,
        "explains": explains,
        "evidences": evidences
    }

    # Deterministic JSON serialization
    serialized_json = json.dumps(static_bundle, indent=2, sort_keys=True)
    js_content = f"// Auto-generated static dataset for GitHub Pages deployment\nwindow.__CIF_STATIC_DATA__ = {serialized_json};\n"

    web_dir = PROJECT_ROOT / "web"
    docs_dir = PROJECT_ROOT / "docs"

    target_web_static = web_dir / "static_data.js"
    with open(target_web_static, "w", encoding="utf-8", newline="\n") as f:
        f.write(js_content)

    print(f"[OK] Generated {target_web_static} ({len(js_content)} bytes)")

    # Mirror web/ to docs/
    os.makedirs(docs_dir, exist_ok=True)
    synced_files = []
    for item in os.listdir(web_dir):
        src = web_dir / item
        dst = docs_dir / item
        if src.is_file():
            shutil.copy2(src, dst)
            synced_files.append(item)

    print(f"[OK] Mirrored {len(synced_files)} files to {docs_dir}: {', '.join(synced_files)}")

if __name__ == "__main__":
    build_static()
