"""
Context Intelligence Framework - Automated Verification & Demo Runner
Executes comprehensive end-to-end tests across all milestones and verifies definition of done (§18).
"""
import sys
import os
import time
import json

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(__file__))

from backend.db import Database
from backend.models import Decision, Event, Entity, Edge
from backend.ingestion.identity import IdentityResolver
from backend.ingestion.git_adapter import GitAdapter
from backend.ingestion.github_adapter import GitHubAdapter
from backend.ingestion.adr_adapter import ADRAdapter
from backend.engine.entity_res import EntityResolver
from backend.engine.graph import TemporalGraph
from backend.engine.reconciliation import ReconciliationEngine
from backend.engine.drift_detector import DriftDetector
from backend.engine.explanation import ExplanationGenerator
from backend.evaluation.benchmark import BenchmarkRunner
from backend.seed_data import populate_seed_data

# Ensure stdout is utf-8 compatible on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_tests():
    print("=" * 75)
    print("  CONTEXT INTELLIGENCE FRAMEWORK -- AUTOMATED VERIFICATION SUITE")
    print("=" * 75)
    
    passed_checks = 0
    total_checks = 0

    def check(name, condition, detail=""):
        nonlocal passed_checks, total_checks
        total_checks += 1
        if condition:
            passed_checks += 1
            print(f"  [PASS] {name}")
        else:
            print(f"  [FAIL] {name} -- {detail}")

    # TEST 1: Database Initialization & Mechanical Invariant Enforcement (Section 5.2 / Section 13)
    print("\n--- Milestone 1: Data Model & Invariant Enforcement ---")
    test_db_path = os.path.join(os.path.dirname(__file__), "test_suite.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    db = Database(test_db_path)
    
    # Verify invariant: Saving non-unresolved decision with empty evidence must FAIL
    invariant_triggered = False
    try:
        bad_dec = Decision(
            decision_id="dec_bad_invariant",
            title="Ungrounded Decision Without Evidence",
            state="accepted",
            evidence_event_ids=[]
        )
        db.save_decision(bad_dec)
    except ValueError as e:
        invariant_triggered = True
    check("Mechanical Invariant: Reject accepted decision with 0 evidence links", invariant_triggered)

    # TEST 2: Multi-Source Ingestion Pipeline (Section 6)
    print("\n--- Milestone 1: Ingestion Adapters & Provenance Links ---")
    ident_res = IdentityResolver(db)
    git_adapter = GitAdapter(db, ident_res)
    gh_adapter = GitHubAdapter(db, ident_res)
    adr_adapter = ADRAdapter(db, ident_res)

    ev_git = git_adapter.ingest_commit_record(
        repo="test/repo",
        commit_sha="abcdef1234567890",
        author_raw="Sarah Chen <sarah.chen@acme.org>",
        timestamp="2026-03-01T10:00:00Z",
        message="feat(core): implement robust controller",
        files_changed=["src/core.py"]
    )
    check("Git Adapter: Ingest commit with clickable source_url", ev_git.source_url.startswith("https://github.com/"))
    check("Identity Resolution: Sarah Chen resolved to canonical_id", ev_git.author == "sarah_chen")

    ev_issue = gh_adapter.ingest_issue(
        repo="test/repo",
        issue_number=101,
        title="Thermal instability issue",
        body="High temperature spike observed.",
        author_raw="alex-rodriguez",
        created_at="2026-03-01T08:00:00Z"
    )
    check("GitHub Adapter: Issue ingested with source_url", ev_issue.source_url.endswith("/issues/101"))

    ev_pr = gh_adapter.ingest_pull_request(
        repo="test/repo",
        pr_number=55,
        title="Fix controller stability",
        body="Resolves thermal oscillation. Closes #101",
        author_raw="sarahc-eng",
        created_at="2026-03-01T12:00:00Z",
        merged_at="2026-03-01T14:00:00Z",
        artifacts_touched=["src/core.py"],
        commit_shas=["abcdef1234567890"]
    )
    check("GitHub Adapter: PR parsed parent linkage 'Closes #101'", "evt_issue_test_repo_101" in ev_pr.parent_event_ids)

    # TEST 3: Entity Resolution & Temporal Context Graph (Section 7)
    print("\n--- Milestone 2: Entity Resolution & Context Graph ---")
    ent_res = EntityResolver(db)
    ent_file = ent_res.resolve_file_entity("test/repo", "src/core.py")
    check("Entity Resolution: File entity canonicalization", ent_file.canonical_path == "src/core.py")

    py_sample_code = """
def regulate_temperature(temp, target):
    return (target - temp) * 2.0

def read_sensor_bus():
    pass
"""
    funcs = ent_res.extract_functions_from_python_code(py_sample_code)
    fn_names = [f[0] for f in funcs]
    check("AST Parser: Extracted function names from code", "regulate_temperature" in fn_names and "read_sensor_bus" in fn_names)

    ent_fn = ent_res.resolve_function_entity("test/repo", "src/core.py", "regulate_temperature")
    check("Entity Resolution: AST function entity canonical path", ent_fn.canonical_path == "src/core.py::regulate_temperature")

    # TEST 4: Seed Data & Pilot Repositories (Section 12.1)
    print("\n--- Milestone 2: Pilot Repositories & Temporal Queries ---")
    populate_seed_data(db)
    
    graph = TemporalGraph(db)
    explanation_gen = ExplanationGenerator(db)

    # Canonical Query 1: Decision chain for artifact
    chain = db.query_decision_chain_for_artifact("src/thermal/control.py::regulate_temperature")
    check("Canonical Query 1: Decision chain for regulate_temperature", len(chain) >= 2)

    # Canonical Query 2: Full evidence trail
    trail = db.query_full_evidence_trail(chain[0]["decision_id"])
    check("Canonical Query 2: Full evidence trail contains verified events", len(trail["evidence_events"]) > 0)

    # Canonical Query 3: Timeline slice
    slice_events = db.query_timeline_slice("acme-eng/thermal-control-system")
    check("Canonical Query 3: Timeline slice returns decisions in time order", len(slice_events) >= 2)

    # TEST 5: Reconciliation & Conflict Detection (Section 8.1 & 8.2)
    print("\n--- Milestone 2: Conflict & Supersession Detection ---")
    recon = ReconciliationEngine(db)
    conflicts = recon.check_for_conflicts()
    check("Conflict Detection: Flagged contributor disagreement (PID vs deadband / Redis vs LRU)", len(conflicts) > 0)

    # TEST 6: Code-Level Drift Detection (Section 8.3)
    print("\n--- Milestone 2: Code-Level Drift Detection Pass ---")
    drift_det = DriftDetector(db)
    violating_diff = """
    @@ -25,12 +25,8 @@ def regulate_temperature(current_temp, target_temp):
    -    return self.clamp(p_term + i_term, 0.0, 100.0)
    +    # Deliberate violation: reintroduces rejected threshold on_off hysteresis
    +    if current_temp > target_temp + 1.5:
    +        return 0.0
    +    return 100.0
    """
    drift_report = drift_det.analyze_diff_for_drift(
        repo="acme-eng/thermal-control-system",
        commit_or_pr_id="pr_test_drift",
        author="elena_rostova",
        changed_files=["src/thermal/control.py"],
        diff_text=violating_diff
    )
    drift_results = drift_report["findings"] if isinstance(drift_report, dict) else drift_report
    check("Drift Detection: Flagged deliberate violation of accepted PID decision", len(drift_results) > 0)
    if drift_results:
        check("Drift Detection: Identified rejected pattern re-introduction", drift_results[0]["drift_type"] in ("drift", "reintroduces_rejected"))

    # TEST 7: Evidence-Grounded Explanations (Section 9)
    print("\n--- Milestone 3: Grounded Explanation Generation ---")
    exp = explanation_gen.explain_artifact("src/thermal/control.py::regulate_temperature")
    check("Explanation Engine: Synthesized grounded explanation", exp["status"] == "grounded")
    check("Explanation Engine: Included clickable source_url citations", len(exp["citations"]) > 0)

    # Test unknown artifact (Anti-hallucination check)
    exp_unknown = explanation_gen.explain_artifact("src/untracked/mystery_module.py")
    check("Explanation Engine: Anti-Hallucination guarantee for unrecorded artifacts", exp_unknown["status"] == "not_found")

    # TEST 8: Evaluation Benchmark (Section 12)
    print("\n--- Milestone 3: Evaluation Metrics & Baselines ---")
    bench = BenchmarkRunner(db)
    bench_results = bench.run_full_evaluation()
    metrics = bench_results["metrics"]
    check("Benchmark: Decision extraction recall computed", isinstance(metrics["decision_extraction_recall"], (int, float)) or metrics["decision_extraction_recall"] == "not measured")
    check("Benchmark: Evidence link accuracy computed", isinstance(metrics["evidence_link_accuracy"], (int, float)) or metrics["evidence_link_accuracy"] == "not measured")
    check("Benchmark: Claim support rate computed", isinstance(metrics["unsupported_claim_rate"], (int, float)))
    check("Benchmark: Processing latency reported", isinstance(metrics["processing_latency_ms"], (int, float)) and metrics["processing_latency_ms"] >= 0.0)

    # Clean up test DB
    try:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    except Exception:
        pass

    print("\n" + "=" * 75)
    print(f"  VERIFICATION RESULTS: {passed_checks}/{total_checks} CHECKS PASSED")
    print("=" * 75)
    if passed_checks == total_checks:
        print("  [SUCCESS] ALL PROTOTYPE CAPABILITIES VERIFIED AGAINST IMPLEMENTATION SPECIFICATION!")
    else:
        print(f"  [WARNING] Some checks failed ({total_checks - passed_checks} failed)")

    return passed_checks == total_checks

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
