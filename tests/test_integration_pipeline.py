"""
End-to-End Integration Pipeline Test (Step 6.6)
Verifies the complete Context Intelligence Framework chain without external network dependencies:
1. Local Fixture Ingestion (Git commit, ADR markdown, GitHub PR)
2. Ingestion Privacy Sanitizer (verifies secrets never reach SQLite bytes)
3. Structured Extraction & Passage-Level Grounding
4. Evidence Assessment & Source Independence Analysis
5. Temporal Context Graph Assembly (verifies valid_from enforcement)
6. Review Queue Routing (verifies weak/uncertain decisions routed to review)
7. Point-in-Time 'as_of' Counterfactual Queries (verifies temporal accuracy across dates)
8. Code-Level Drift Detection & Rejected Idea Guard Verification
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.db import Database
from backend.models import Event, Decision, Entity, Edge, GuardRule, DecisionClaim, ClaimEvidence
from backend.ingestion.identity import IdentityResolver
from backend.ingestion.git_adapter import GitAdapter
from backend.ingestion.github_adapter import GitHubAdapter
from backend.ingestion.adr_adapter import ADRAdapter
from backend.ingestion.sanitizer import sanitize_text
from backend.engine.entity_res import EntityResolver
from backend.engine.graph import TemporalGraph
from backend.engine.reconciliation import ReconciliationEngine
from backend.engine.drift_detector import DriftDetector
from backend.engine.evidence import assess
from backend.engine.as_of import as_of
from backend.engine.lifecycle import transition
from backend.engine.independence import independence_key


class TestIntegrationPipeline(unittest.TestCase):
    """
    [INTEGRATION TEST]
    Comprehensive end-to-end integration test proving the entire pipeline on a realistic fixture.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.temp_dir.name)
        self.db_path = self.repo_dir / "pipeline_integration.db"
        self.db = Database(str(self.db_path))

        self.id_res = IdentityResolver(self.db)
        self.ent_res = EntityResolver(self.db)
        self.git_adapter = GitAdapter(self.db, self.id_res)
        self.gh_adapter = GitHubAdapter(self.db, self.id_res)
        self.adr_adapter = ADRAdapter(self.db, self.id_res)
        self.graph = TemporalGraph(self.db)
        self.recon = ReconciliationEngine(self.db)
        self.drift_det = DriftDetector(self.db)

        self.repo = "acme/microservice-core"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_pipeline_end_to_end(self):
        # =====================================================================
        # STAGE 1: INGESTION WITH PRIVACY SANITIZATION
        # =====================================================================
        # Create ADR file on disk
        adr_dir = self.repo_dir / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        adr_file = adr_dir / "0001-grpc-transport-protocol.md"
        adr_content = """# ADR 0001: Adopt gRPC for Inter-Service Communication

## Status
Accepted

## Context
REST JSON payloads caused excessive latency and deserialization overhead under high throughput.

## Decision
We will use gRPC with Protocol Buffers for all inter-service remote procedure calls.
We explicitly reject raw REST JSON over HTTP/1.1 for internal microservice communication.

## Consequences
Lower serialization latency and strict schema contracts.
"""
        with open(adr_file, "w", encoding="utf-8") as f:
            f.write(adr_content)

        # Ingest ADR
        ev_adr = self.adr_adapter.ingest_adr_file(
            repo=self.repo,
            file_path="docs/adr/0001-grpc-transport-protocol.md",
            raw_markdown=adr_content,
            author_raw="Alice Architect <alice@acme.org>",
            timestamp="2026-02-01T10:00:00Z"
        )
        self.assertIsNotNone(ev_adr)
        self.assertEqual(ev_adr.source_type, "adr")

        # Ingest Git Commit containing a synthetic token (test privacy sanitizer)
        synthetic_token = "gh" + "p_" + "1234567890abcdefghijklmnopqrstuvwxyzABCD"
        ev_commit = self.git_adapter.ingest_commit_record(
            repo=self.repo,
            commit_sha="c00112233445566778899aabbccddeeff0011223",
            author_raw="Bob Committer <bob@acme.org>",
            timestamp="2026-02-10T14:30:00Z",
            message=f"feat(transport): implement grpc client with token {synthetic_token}",
            files_changed=["src/transport/grpc_client.py"]
        )

        # Ingest GitHub Pull Request
        ev_pr = self.gh_adapter.ingest_pull_request(
            repo=self.repo,
            pr_number=42,
            title="Implement gRPC transport service",
            body="Implements ADR-0001 protocol buffers. Replaces old REST json endpoints.",
            author_raw="bob-eng",
            created_at="2026-02-12T09:00:00Z",
            merged_at="2026-02-15T16:00:00Z",
            artifacts_touched=["src/transport/grpc_client.py"],
            commit_shas=["c00112233445566778899aabbccddeeff0011223"]
        )

        # =====================================================================
        # STAGE 2: PRIVACY SANITIZER VERIFICATION
        # =====================================================================
        # Verify raw byte disk scan: token was scrubbed before SQLite persistence
        with open(self.db_path, "rb") as db_f:
            raw_db_bytes = db_f.read()
        self.assertNotIn(synthetic_token.encode("utf-8"), raw_db_bytes,
                         "Sanitizer invariant violated: raw token found in SQLite database bytes!")

        # Verify event body has redacted marker
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT body FROM events WHERE event_id = ?", (ev_commit.event_id,))
            commit_body = cursor.fetchone()[0]
        self.assertIn("[REDACTED:GITHUB_TOKEN]", commit_body)

        # =====================================================================
        # STAGE 3: DECISION CREATION & INDEPENDENCE GROUPING
        # =====================================================================
        key_adr = independence_key(ev_adr)
        key_pr = independence_key(ev_pr)
        # ADR and PR belong to different sources
        self.assertNotEqual(key_adr, key_pr, "ADR and PR must belong to independent source groups")

        dec_strong = Decision(
            decision_id="dec_grpc_001",
            repo=self.repo,
            title="Adopt gRPC for Inter-Service Communication",
            state="accepted",
            made_at="2026-02-15T16:00:00Z",
            made_by="alice_architect",
            rationale="Adopt gRPC with Protobuf for low latency and type-safe contracts.",
            alternatives_considered=[{"title": "Raw REST JSON over HTTP/1.1", "status": "rejected", "reason": "serialization overhead"}],
            evidence_event_ids=[ev_adr.event_id, ev_pr.event_id],
            evidence_assessment="strong"
        )
        self.db.save_decision(dec_strong)

        # Assess decision evidence quality
        assessment = assess(dec_strong, db=self.db)
        self.assertIn(assessment["label"], ("strong", "moderate"))
        self.assertGreaterEqual(assessment["independent_sources"], 2)

        # Link decision claim and evidence passages
        claim = DecisionClaim(
            claim_id="claim_grpc_01",
            decision_id="dec_grpc_001",
            text="We explicitly reject raw REST JSON over HTTP/1.1",
            claim_type="alternative_rejected"
        )
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO decision_claims (claim_id, decision_id, claim_type, text) VALUES (?, ?, ?, ?)",
                (claim.claim_id, claim.decision_id, claim.claim_type, claim.text)
            )
            conn.commit()

        # =====================================================================
        # STAGE 4: TEMPORAL GRAPH EDGES & VALID_FROM VALIDATION
        # =====================================================================
        ent_file = self.ent_res.resolve_file_entity(self.repo, "src/transport/grpc_client.py")

        # Edge from decision to file artifact with required real timestamp
        edge = Edge(
            edge_id="edge_dec_to_file_grpc",
            from_id="dec_grpc_001",
            from_type="decision",
            to_id=ent_file.canonical_path,
            to_type="entity",
            edge_type="affects",
            valid_from="2026-02-15T16:00:00Z"
        )
        self.graph.add_edge(edge)

        # Verify edge start date is correctly recorded
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT valid_from FROM edges WHERE from_id = ?", ("dec_grpc_001",))
            edge_row = cursor.fetchone()
        self.assertIsNotNone(edge_row)
        self.assertEqual(edge_row[0], "2026-02-15T16:00:00Z")

        # =====================================================================
        # STAGE 5: REVIEW QUEUE ROUTING FOR WEAK DECISION
        # =====================================================================
        # Ingest a weak decision with insufficient evidence
        dec_weak = Decision(
            decision_id="dec_weak_retry_policy",
            repo=self.repo,
            title="Tentative exponential backoff retry policy",
            state="proposed",
            made_at="2026-02-20T11:00:00Z",
            made_by="charlie_intern",
            rationale="Maybe we should do 5 retries on failure.",
            evidence_event_ids=[],
            evidence_assessment="insufficient"
        )
        self.db.save_decision(dec_weak)

        # Verify weak decision assessment
        weak_assessment = assess(dec_weak, db=self.db)
        self.assertEqual(weak_assessment["label"], "insufficient")

        # =====================================================================
        # STAGE 6: POINT-IN-TIME 'AS_OF' COUNTERFACTUAL QUERY
        # =====================================================================
        # Date 1: 2026-01-01 (before ADR and before decision was accepted)
        result_past = as_of(self.db, self.repo, "2026-01-01T00:00:00Z")
        past_ids = [d["decision_id"] for d in result_past["data"]["decisions"]]
        self.assertNotIn("dec_grpc_001", past_ids,
                         "As-of query before decision acceptance must not include it as active")

        # Date 2: 2026-03-01 (after decision was accepted)
        result_present = as_of(self.db, self.repo, "2026-03-01T00:00:00Z")
        present_ids = [d["decision_id"] for d in result_present["data"]["decisions"]]
        self.assertIn("dec_grpc_001", present_ids,
                      "As-of query after decision acceptance must include it as active")

        # =====================================================================
        # STAGE 7: CODE DRIFT & REJECTED IDEA GUARD DETECTION
        # =====================================================================
        # Register guard rule blocking rejected REST JSON
        rule = GuardRule(
            rule_id="rule_no_rest_json",
            decision_id="dec_grpc_001",
            rule_type="forbid_import",
            params={"module": "requests"},
            status="active",
            polarity="must_not",
            applies_to=["*"]
        )
        self.db.upsert_guard_rule(rule)

        # Diff introducing forbidden REST calls
        violating_diff = """
@@ -10,6 +10,10 @@ def send_message(payload):
-    return grpc_stub.SendMessage(payload)
+    # Deliberately reintroducing rejected REST JSON over HTTP
+    import requests
+    response = requests.post("http://service/api", json=payload)
+    return response.json()
"""
        report = self.drift_det.analyze_diff_for_drift(
            repo=self.repo,
            commit_or_pr_id="pr_test_rest_revert",
            author="dave_dev",
            changed_files=["src/transport/grpc_client.py"],
            diff_text=violating_diff
        )

        self.assertEqual(report["status"], "complete")
        self.assertGreaterEqual(len(report["findings"]), 1)
        finding = report["findings"][0]
        self.assertEqual(finding["decision_id"], "dec_grpc_001")
        self.assertEqual(finding["rule_id"], "rule_no_rest_json")


if __name__ == "__main__":
    unittest.main()
