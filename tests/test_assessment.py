"""
Tests for Step 3.2: Evidence Assessment and Abstention
Verifies:
1. Deterministic label boundaries:
   - contradicted: at least one contradicting relation from an active source.
   - strong: >= 2 independent source groups with direct support.
   - moderate: 1 direct group + >= 1 other group, or >= 2 independent indirect groups.
   - weak: exactly 1 source group.
   - insufficient: no evidence, or only 1 indirect group.
2. Acceptance criteria:
   - A decision with a single copied source cannot be labelled strong.
   - A contradicted decision is assessed as 'contradicted' (never strong/moderate).
3. Review routing:
   - Labels weak, insufficient, contradicted create review-queue items with explicit reasons.
4. Abstention:
   - /api/explain and explain_artifact return status: 'insufficient_evidence' when assessment is insufficient.
5. Recomputation:
   - Recomputing assessment updates decisions.evidence_assessment in database.
"""
import os
import tempfile
import unittest

from backend.models import Event, Decision, DecisionClaim, ClaimEvidence, Entity
from backend.db import Database
from backend.api import APIHandler
from backend.engine.evidence import assess
from backend.engine.explanation import ExplanationGenerator
from backend.engine.independence import link_claim_to_event


class TestEvidenceAssessment(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)
        self.api = APIHandler(self.db)
        self.repo = "acme/framework"

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            try:
                os.remove(self.tmp.name)
            except Exception:
                pass

    def test_boundary_strong(self):
        """strong: >= 2 independent source groups with direct support (e.g. ADR + PR)."""
        adr_ev = Event(
            event_id="ev_adr_1",
            source_type="adr",
            source_id="docs/adr/001.md",
            source_url="https://github.com/acme/framework/blob/main/docs/adr/001.md",
            repo=self.repo,
            title="ADR 001: SQLite WAL mode",
            body="We choose SQLite WAL mode because of zero external service dependencies.",
            raw_metadata={"file_path": "docs/adr/001.md"}
        )
        pr_ev = Event(
            event_id="ev_pr_1",
            source_type="github_pr",
            source_id="101",
            source_url="https://github.com/acme/framework/pull/101",
            repo=self.repo,
            title="PR #101: Configure SQLite storage engine",
            body="Configures connection pooling, pragmas, and checkpoint handlers for SQLite WAL mode.",
            raw_metadata={"pr_number": 101}
        )
        self.db.upsert_event(adr_ev)
        self.db.upsert_event(pr_ev)

        dec = Decision(
            decision_id="dec_strong_1",
            title="Adopt SQLite WAL",
            state="accepted",
            evidence_assessment="strong",
            rationale="We choose SQLite WAL mode because of zero external service dependencies.",
            evidence_event_ids=["ev_adr_1", "ev_pr_1"],
            repo=self.repo
        )
        self.db.save_decision(dec)

        res = assess(dec, db=self.db)
        self.assertEqual(res["label"], "strong")
        self.assertEqual(res["independent_sources"], 2)
        self.assertGreaterEqual(len(res["direct_support"]), 2)
        self.assertEqual(len(res["contradicting"]), 0)

    def test_boundary_moderate_direct_plus_indirect(self):
        """moderate: 1 direct group plus >= 1 other group (e.g. 1 direct + 1 indirect)."""
        adr_ev = Event(
            event_id="ev_adr_2",
            source_type="adr",
            source_id="docs/adr/002.md",
            source_url="https://github.com/acme/framework/blob/main/docs/adr/002.md",
            repo=self.repo,
            title="ADR 002: Memory Caching",
            body="We adopt in-memory LRU cache to eliminate redis network roundtrips.",
            raw_metadata={"file_path": "docs/adr/002.md"}
        )
        issue_ev = Event(
            event_id="ev_issue_5",
            source_type="github_issue",
            source_id="5",
            source_url="https://github.com/acme/framework/issues/5",
            repo=self.repo,
            title="Issue #5: Discussing caching options",
            body="General thread discussing overall cache layer design and potential options.",
            raw_metadata={"issue_number": 5}
        )
        self.db.upsert_event(adr_ev)
        self.db.upsert_event(issue_ev)

        dec = Decision(
            decision_id="dec_mod_1",
            title="In-Memory Cache",
            state="accepted",
            evidence_assessment="moderate",
            rationale="We adopt in-memory LRU cache to eliminate redis network roundtrips.",
            evidence_event_ids=["ev_adr_2", "ev_issue_5"],
            repo=self.repo
        )
        self.db.save_decision(dec)

        res = assess(dec, db=self.db)
        self.assertEqual(res["label"], "moderate")
        self.assertEqual(res["independent_sources"], 2)
        self.assertEqual(len(res["direct_support"]), 1)
        self.assertEqual(len(res["indirect_support"]), 1)

    def test_boundary_moderate_two_indirect(self):
        """moderate: >= 2 independent indirect groups."""
        issue_a = Event(
            event_id="ev_iss_a",
            source_type="github_issue",
            source_id="21",
            source_url="https://github.com/acme/framework/issues/21",
            repo=self.repo,
            title="General architecture notes",
            body="Unrelated conversation without matching sentences.",
            raw_metadata={"issue_number": 21}
        )
        issue_b = Event(
            event_id="ev_iss_b",
            source_type="github_issue",
            source_id="22",
            source_url="https://github.com/acme/framework/issues/22",
            repo=self.repo,
            title="Telemetry updates",
            body="Telemetry logging overhaul conversation.",
            raw_metadata={"issue_number": 22}
        )
        self.db.upsert_event(issue_a)
        self.db.upsert_event(issue_b)

        dec = Decision(
            decision_id="dec_mod_ind",
            title="Telemetry Decision",
            state="accepted",
            evidence_assessment="moderate",
            rationale="Adopt distributed trace context propagation.",
            evidence_event_ids=["ev_iss_a", "ev_iss_b"],
            repo=self.repo
        )
        self.db.save_decision(dec)

        res = assess(dec, db=self.db)
        self.assertEqual(res["label"], "moderate")
        self.assertEqual(res["independent_sources"], 2)
        self.assertEqual(len(res["direct_support"]), 0)
        self.assertGreaterEqual(len(res["indirect_support"]), 2)

    def test_boundary_weak_single_source_group(self):
        """weak: exactly 1 source group (e.g. 1 direct source group without independent corroboration)."""
        adr_ev = Event(
            event_id="ev_adr_solo",
            source_type="adr",
            source_id="docs/adr/003.md",
            source_url="https://github.com/acme/framework/blob/main/docs/adr/003.md",
            repo=self.repo,
            title="ADR 003: Auth Middleware",
            body="We use JWT tokens signed with Ed25519 for session authentication.",
            raw_metadata={"file_path": "docs/adr/003.md"}
        )
        self.db.upsert_event(adr_ev)

        dec = Decision(
            decision_id="dec_weak_1",
            title="Ed25519 JWT Auth",
            state="accepted",
            evidence_assessment="weak",
            rationale="We use JWT tokens signed with Ed25519 for session authentication.",
            evidence_event_ids=["ev_adr_solo"],
            repo=self.repo
        )
        self.db.save_decision(dec)

        res = assess(dec, db=self.db)
        self.assertEqual(res["label"], "weak")
        self.assertEqual(res["independent_sources"], 1)
        self.assertIn("no independent source besides the ADR", res["missing_corroboration"])

    def test_copy_vs_independent_sources_cannot_be_strong(self):
        """
        Acceptance criterion: A decision with a single copied source (>80% token overlap)
        cannot be labelled strong; counts as 1 source group and is labelled weak.
        """
        orig_ev = Event(
            event_id="ev_orig_doc",
            source_type="doc",
            source_id="design/storage.md",
            source_url="https://github.com/acme/framework/blob/main/design/storage.md",
            repo=self.repo,
            title="Storage Spec",
            body="We decide to use SQLite WAL mode because of zero external service dependencies.",
            raw_metadata={"file_path": "design/storage.md"}
        )
        # Copied into wiki with identical token overlap
        copy_ev = Event(
            event_id="ev_copy_doc",
            source_type="doc",
            source_id="wiki/copied_spec.md",
            source_url="https://github.com/acme/framework/blob/main/wiki/copied_spec.md",
            repo=self.repo,
            title="Copied Spec",
            body="Quoted from storage spec: We decide to use SQLite WAL mode because of zero external service dependencies.",
            raw_metadata={"file_path": "wiki/copied_spec.md"}
        )
        self.db.upsert_event(orig_ev)
        self.db.upsert_event(copy_ev)

        dec = Decision(
            decision_id="dec_copy_test",
            title="Copied Decision",
            state="accepted",
            evidence_assessment="weak",
            rationale="We decide to use SQLite WAL mode because of zero external service dependencies.",
            evidence_event_ids=["ev_orig_doc", "ev_copy_doc"],
            repo=self.repo
        )
        self.db.save_decision(dec)

        res = assess(dec, db=self.db)
        # Even though there are 2 events, they collapse to 1 independent source group
        self.assertNotEqual(res["label"], "strong", "Single copied source cannot be labelled strong!")
        self.assertEqual(res["label"], "weak")
        self.assertEqual(res["independent_sources"], 1)

    def test_boundary_contradicted(self):
        """contradicted: at least one contradicting relation from an active source."""
        good_ev = Event(
            event_id="ev_good_adr",
            source_type="adr",
            source_id="docs/adr/004.md",
            source_url="https://github.com/acme/framework/blob/main/docs/adr/004.md",
            repo=self.repo,
            title="ADR 004: Redis Caching",
            body="We propose Redis cluster for caching layer.",
            raw_metadata={"file_path": "docs/adr/004.md"}
        )
        bad_ev = Event(
            event_id="ev_bad_perf",
            source_type="github_issue",
            source_id="404",
            source_url="https://github.com/acme/framework/issues/404",
            repo=self.repo,
            title="Issue #404: Benchmark results",
            body="Performance testing proved Redis cluster was rejected because it caused high memory bottlenecks and operational failure.",
            raw_metadata={"issue_number": 404}
        )
        self.db.upsert_event(good_ev)
        self.db.upsert_event(bad_ev)

        dec = Decision(
            decision_id="dec_contra_1",
            title="Redis Cluster",
            state="accepted",
            evidence_assessment="contradicted",
            rationale="We propose Redis cluster for caching layer.",
            evidence_event_ids=["ev_good_adr", "ev_bad_perf"],
            repo=self.repo
        )
        self.db.save_decision(dec)

        res = assess(dec, db=self.db)
        self.assertEqual(res["label"], "contradicted")
        self.assertGreaterEqual(len(res["contradicting"]), 1)
        self.assertGreaterEqual(len(res["conflicting_evidence"]), 1)

    def test_boundary_insufficient(self):
        """insufficient: 0 evidence events, or only 1 indirect group."""
        # 0 evidence events
        dec_empty = Decision(
            decision_id="dec_zero_ev",
            title="Empty Proposed Decision",
            state="proposed",
            evidence_assessment="insufficient",
            rationale="Unsubstantiated proposal.",
            evidence_event_ids=[],
            repo=self.repo
        )
        res_zero = assess(dec_empty, db=self.db)
        self.assertEqual(res_zero["label"], "insufficient")
        self.assertEqual(res_zero["independent_sources"], 0)

        # Only 1 indirect group
        ev_ind = Event(
            event_id="ev_single_ind",
            source_type="github_issue",
            source_id="999",
            source_url="https://github.com/acme/framework/issues/999",
            repo=self.repo,
            title="Random chat",
            body="Completely unrelated conversation without any matching sentence.",
            raw_metadata={"issue_number": 999}
        )
        self.db.upsert_event(ev_ind)
        dec_single_ind = Decision(
            decision_id="dec_ind_only",
            title="Indirect Only Proposal",
            state="proposed",
            evidence_assessment="insufficient",
            rationale="Something completely different that never appears in issue 999.",
            evidence_event_ids=["ev_single_ind"],
            repo=self.repo
        )
        self.db.save_decision(dec_single_ind)
        res_ind = assess(dec_single_ind, db=self.db)
        self.assertEqual(res_ind["label"], "insufficient")

    def test_review_routing_for_weak_insufficient_contradicted(self):
        """Labels weak, insufficient, and contradicted route to /api/review-queue."""
        # Create 3 decisions with weak, insufficient, and contradicted labels
        # 1. Weak
        ev_w = Event(event_id="ev_rw_w", source_type="adr", source_id="w.md", source_url="https://github.com/a/b/blob/main/w.md", repo=self.repo, body="Decision A body.", raw_metadata={"file_path": "w.md"})
        self.db.upsert_event(ev_w)
        d_weak = Decision(decision_id="dec_rq_weak", title="Weak Decision", state="proposed", evidence_assessment="weak", rationale="Decision A body.", evidence_event_ids=["ev_rw_w"], repo=self.repo, confidence=0.95, review_status="pending_review")
        self.db.save_decision(d_weak)

        # 2. Insufficient
        d_insuff = Decision(decision_id="dec_rq_insuff", title="Insuff Decision", state="proposed", evidence_assessment="insufficient", rationale="Unsubstantiated.", evidence_event_ids=[], repo=self.repo, confidence=0.95, review_status="pending_review")
        self.db.save_decision(d_insuff)

        # 3. Contradicted
        ev_c = Event(event_id="ev_rw_c", source_type="github_issue", source_id="111", source_url="https://github.com/a/b/issues/111", repo=self.repo, body="Redis cluster was rejected due to bottlenecks.", raw_metadata={"issue_number": 111})
        self.db.upsert_event(ev_c)
        d_contra = Decision(decision_id="dec_rq_contra", title="Contra Decision", state="proposed", evidence_assessment="contradicted", rationale="We propose Redis cluster.", evidence_event_ids=["ev_rw_c"], repo=self.repo, confidence=0.95, review_status="pending_review")
        self.db.save_decision(d_contra)

        # Fetch review queue via API
        rq_res = self.api.handle_get("/api/review-queue", {})
        self.assertEqual(rq_res["status"], "success")
        items = rq_res["data"]
        item_ids = {it.get("decision_id") for it in items}

        self.assertIn("dec_rq_weak", item_ids)
        self.assertIn("dec_rq_insuff", item_ids)
        self.assertIn("dec_rq_contra", item_ids)

        # Verify reasons are set
        weak_item = [it for it in items if it.get("decision_id") == "dec_rq_weak"][0]
        self.assertIn("weak", weak_item["queue_reason"])
        contra_item = [it for it in items if it.get("decision_id") == "dec_rq_contra"][0]
        self.assertIn("contradicted", contra_item["queue_reason"])

    def test_abstention_on_insufficient_evidence(self):
        """
        When evidence assessment is insufficient and no stronger source exists,
        /api/explain and explain_artifact return status: 'insufficient_evidence'.
        """
        # Register entity and insufficient decision
        ent_path = "src/payment/gateway.py::process_charge"
        self.db.upsert_entity(Entity(
            entity_id="ent_gateway_charge",
            entity_type="function",
            canonical_path=ent_path,
            repo=self.repo
        ))

        dec = Decision(
            decision_id="dec_unsupported_arch",
            title="Unsupported Payment Scheme",
            state="proposed",
            evidence_assessment="insufficient",
            rationale="Untested payment gateway design.",
            artifacts_affected=[ent_path],
            evidence_event_ids=[],
            repo=self.repo
        )
        self.db.save_decision(dec)

        # 1. Test explain_artifact directly
        exp_gen = ExplanationGenerator(self.db)
        art_res = exp_gen.explain_artifact(ent_path)
        self.assertEqual(art_res["status"], "insufficient_evidence")
        self.assertIn("Insufficient evidence", art_res["message"])

        # 2. Test /api/explain endpoint
        api_res = self.api.handle_get("/api/explain", {"artifact": [ent_path]})
        self.assertEqual(api_res["status"], "insufficient_evidence")
        self.assertIn("Insufficient evidence", api_res["message"])

        # 3. Test explain_decision directly
        dec_res = exp_gen.explain_decision("dec_unsupported_arch")
        self.assertEqual(dec_res["status"], "insufficient_evidence")

    def test_recompute_evidence_assessment(self):
        """recompute_evidence_assessment updates decisions.evidence_assessment in DB."""
        adr_ev = Event(
            event_id="ev_recomp_adr",
            source_type="adr",
            source_id="docs/adr/099.md",
            source_url="https://github.com/acme/framework/blob/main/docs/adr/099.md",
            repo=self.repo,
            title="ADR 099: Microservices",
            body="We adopt event sourcing architecture for payment state tracking.",
            raw_metadata={"file_path": "docs/adr/099.md"}
        )
        self.db.upsert_event(adr_ev)

        dec = Decision(
            decision_id="dec_recomp",
            title="Event Sourcing",
            state="accepted",
            evidence_assessment="strong",  # initially claimed strong
            rationale="We adopt event sourcing architecture for payment state tracking.",
            evidence_event_ids=["ev_recomp_adr"],  # but only 1 source group!
            repo=self.repo
        )
        self.db.save_decision(dec)

        # Recompute should deterministically downgrade it to 'weak' because it has only 1 source group
        label = self.db.recompute_evidence_assessment("dec_recomp")
        self.assertEqual(label, "weak")

        # Verify DB column was updated
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT evidence_assessment FROM decisions WHERE decision_id = 'dec_recomp'")
            row = c.fetchone()
            self.assertEqual(row["evidence_assessment"], "weak")


if __name__ == "__main__":
    unittest.main()
