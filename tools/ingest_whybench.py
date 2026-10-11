"""
WhyBench Ingestion Tool (Section 2.2)
Rebuilds a clean, reproducible WhyBench SQLite database (whybench.db)
from offline exports in backend/evaluation/whybench/data/.
"""
import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db import Database
from backend.models import Event, Decision, Entity, Edge
from backend.ingestion.identity import IdentityResolver
from backend.engine.entity_res import EntityResolver
from backend.engine.extractor import DecisionExtractor
from backend.engine.llm_extractor import LLMDecisionExtractor
from backend.engine.graph import TemporalGraph

def build_whybench_db(db_path: str = None, extractor_mode: str = "heuristic") -> Database:
    if db_path is None:
        db_path = os.path.join(PROJECT_ROOT, "whybench.db")

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = Database(db_path)
    ident_resolver = IdentityResolver(db)
    ent_resolver = EntityResolver(db)
    if extractor_mode == "llm":
        extractor = LLMDecisionExtractor(db)
    else:
        extractor = DecisionExtractor(db)
    graph = TemporalGraph(db)

    data_dir = os.path.join(PROJECT_ROOT, "backend", "evaluation", "whybench", "data")
    repo_dirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]

    total_events = 0
    total_entities = 0
    total_decisions = 0

    for rdir in repo_dirs:
        events_file = os.path.join(data_dir, rdir, "events.json")
        if not os.path.exists(events_file):
            continue

        with open(events_file, "r", encoding="utf-8") as f:
            raw_events = json.load(f)

        for rev in raw_events:
            ev = Event(
                event_id=rev["event_id"],
                source_type=rev["source_type"],
                source_id=rev["source_id"],
                source_url=rev["source_url"],
                repo=rev["repo"],
                author=rev.get("author", "contributor"),
                timestamp=rev.get("timestamp", "2026-01-01T00:00:00Z"),
                title=rev.get("title", ""),
                body=rev.get("body", ""),
                artifacts_touched=rev.get("artifacts_touched", []),
                parent_event_ids=rev.get("parent_event_ids", []),
                raw_metadata=rev.get("raw_metadata", {})
            )
            db.upsert_event(ev)
            total_events += 1

            # Resolve entities
            entity_ids = []
            for art in ev.artifacts_touched:
                ent = ent_resolver.resolve_file_entity(ev.repo, art, f"Indexed file {art}")
                entity_ids.append(ent.entity_id)
                total_entities += 1

            # Extract decisions from ADRs and PRs
            extracted_decs = extractor.extract_from_event_bundle(
                bundle_name=ev.title or "bundle",
                events=[ev],
                repo=ev.repo,
                target_entities=entity_ids
            )
            for dec in extracted_decs:
                db.save_decision(dec)
                graph.link_decision_to_artifacts_and_evidence(dec)
                total_decisions += 1

    print("=" * 60)
    print("  WHYBENCH INGESTION COMPLETE")
    print("=" * 60)
    print(f"  Database path:       {db_path}")
    print(f"  Events ingested:     {total_events}")
    print(f"  Entities resolved:   {total_entities}")
    print(f"  Decisions indexed:   {total_decisions}")
    print("=" * 60)
    return db

if __name__ == "__main__":
    build_whybench_db()
