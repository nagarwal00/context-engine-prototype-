import os
import tempfile
import unittest
from backend.db import Database
from backend.models import Decision, Event
from backend.engine.reconciliation import ReconciliationEngine
from backend.api import APIHandler


class TestSupersession(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_super.db")
        self.db = Database(self.db_path)
        self.recon = ReconciliationEngine(self.db)
        self.api = APIHandler(self.db)

        # Save valid event to satisfy foreign key in decision_evidence
        ev = Event(
            event_id="evt_mock_evidence",
            source_type="adr",
            source_id="adr_mock",
            source_url="https://github.com/acme/platform/docs/adr/001.md",
            repo="acme/platform",
            author="tester",
            timestamp="2026-01-01T00:00:00Z"
        )
        self.db.upsert_event(ev)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_unrelated_decisions_sharing_generic_word_never_link(self):
        """(a) Two unrelated decisions sharing generic words ('service', 'database') must not link."""
        dec1 = Decision(
            decision_id="dec_auth_db",
            title="Configure authentication database connection pooling",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T10:00:00Z",
            artifacts_affected=["src/auth/db.py"],
            alternatives_considered=[],
            rationale="Improve authentication query throughput",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        dec2 = Decision(
            decision_id="dec_billing_service",
            title="Billing service database sharding strategy",
            state="accepted",
            made_by="bob",
            made_at="2026-02-01T10:00:00Z",
            artifacts_affected=["src/billing/storage.py"],  # completely different entity
            alternatives_considered=[],
            rationale="Scale billing service database independently",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        self.db.save_decision(dec1)
        self.db.save_decision(dec2)

        supersessions = self.recon.detect_supersessions("acme/platform")
        self.assertEqual(len(supersessions), 0, "Unrelated decisions sharing generic words must not link")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state, superseded_by_decision_id FROM decisions WHERE decision_id = 'dec_auth_db'")
            row = cursor.fetchone()
            self.assertEqual(row["state"], "accepted")
            self.assertIsNone(row["superseded_by_decision_id"])

            cursor.execute("SELECT COUNT(*) AS c FROM edges WHERE edge_type = 'supersession_candidate'")
            self.assertEqual(cursor.fetchone()["c"], 0, "No candidate edges should be created for completely unrelated items")

    def test_explicit_reference_auto_links(self):
        """(b) Explicit reference by decision ID or ADR citation links symmetrically."""
        dec_adr3 = Decision(
            decision_id="dec_adr_0003",
            title="ADR-0003: Select synchronous HTTP communication",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T10:00:00Z",
            artifacts_affected=["src/transport/client.py"],
            alternatives_considered=[],
            rationale="Simple request-response protocol",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        dec_adr7 = Decision(
            decision_id="dec_adr_0007",
            title="ADR-0007: Adopt gRPC streaming (supersedes ADR-0003)",
            state="accepted",
            made_by="carol",
            made_at="2026-02-01T10:00:00Z",
            artifacts_affected=["src/transport/grpc.py"],
            alternatives_considered=[],
            rationale="Explicitly supersedes ADR-0003 for high-throughput communication",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.95,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        self.db.save_decision(dec_adr3)
        self.db.save_decision(dec_adr7)

        supersessions = self.recon.detect_supersessions("acme/platform")
        self.assertEqual(len(supersessions), 1)
        self.assertEqual(supersessions[0]["superseded_decision_id"], "dec_adr_0003")
        self.assertEqual(supersessions[0]["new_decision_id"], "dec_adr_0007")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state, superseded_by_decision_id FROM decisions WHERE decision_id = 'dec_adr_0003'")
            row1 = cursor.fetchone()
            self.assertEqual(row1["state"], "superseded")
            self.assertEqual(row1["superseded_by_decision_id"], "dec_adr_0007")

            cursor.execute("SELECT supersedes_decision_id FROM decisions WHERE decision_id = 'dec_adr_0007'")
            row2 = cursor.fetchone()
            self.assertEqual(row2["supersedes_decision_id"], "dec_adr_0003")

            cursor.execute("SELECT * FROM edges WHERE edge_type = 'supersedes' AND from_id = 'dec_adr_0007' AND to_id = 'dec_adr_0003'")
            edge = cursor.fetchone()
            self.assertIsNotNone(edge, "Symmetrical supersedes edge must exist")

    def test_entity_match_and_replacement_cue_auto_links(self):
        """(c) Shared affected entity + later timestamp + replacement cue auto-links."""
        dec_v1 = Decision(
            decision_id="dec_cache_v1",
            title="Memcached distributed cache layer",
            state="accepted",
            made_by="dave",
            made_at="2026-01-10T12:00:00Z",
            artifacts_affected=["src/cache/client.py"],
            alternatives_considered=[],
            rationale="In-memory cache",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        dec_v2 = Decision(
            decision_id="dec_cache_v2",
            title="Redis Cluster cache implementation",
            state="accepted",
            made_by="eve",
            made_at="2026-02-15T12:00:00Z",
            artifacts_affected=["src/cache/client.py"],
            alternatives_considered=[],
            rationale="Replaces memcached cluster to support persistence and pubsub",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.95,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        self.db.save_decision(dec_v1)
        self.db.save_decision(dec_v2)

        supersessions = self.recon.detect_supersessions("acme/platform")
        self.assertEqual(len(supersessions), 1)
        self.assertEqual(supersessions[0]["superseded_decision_id"], "dec_cache_v1")
        self.assertEqual(supersessions[0]["new_decision_id"], "dec_cache_v2")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state, superseded_by_decision_id FROM decisions WHERE decision_id = 'dec_cache_v1'")
            row = cursor.fetchone()
            self.assertEqual(row["state"], "superseded")
            self.assertEqual(row["superseded_by_decision_id"], "dec_cache_v2")

    def test_two_equally_plausible_candidates_route_to_review_queue(self):
        """(d) Two equally plausible candidates sharing an entity do not auto-link and route to review queue."""
        cand_a = Decision(
            decision_id="dec_pipeline_a",
            title="Stream processing engine",
            state="accepted",
            made_by="frank",
            made_at="2026-01-05T08:00:00Z",
            artifacts_affected=["src/pipeline/runner.py"],
            alternatives_considered=[],
            rationale="Initial stream runner",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        cand_b = Decision(
            decision_id="dec_pipeline_b",
            title="Batch computing runtime",
            state="accepted",
            made_by="grace",
            made_at="2026-01-15T08:00:00Z",
            artifacts_affected=["src/pipeline/runner.py"],
            alternatives_considered=[],
            rationale="Batch mode execution scheduler",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        new_dec = Decision(
            decision_id="dec_pipeline_hybrid",
            title="Unified execution runner",
            state="accepted",
            made_by="heidi",
            made_at="2026-02-20T08:00:00Z",
            artifacts_affected=["src/pipeline/runner.py"],
            alternatives_considered=[],
            rationale="Replaces earlier implementation with unified execution",
            evidence_event_ids=["evt_mock_evidence"],
            confidence=0.9,
            review_status="auto_confirmed",
            repo="acme/platform"
        )
        self.db.save_decision(cand_a)
        self.db.save_decision(cand_b)
        self.db.save_decision(new_dec)

        # Neither candidate should be auto-linked because both share the entity and replacement cue applies equally
        supersessions = self.recon.detect_supersessions("acme/platform")
        self.assertEqual(len(supersessions), 0, "Ambiguous supersession must not auto-link")

        # Verify neither older decision was superseded
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state FROM decisions WHERE decision_id IN ('dec_pipeline_a', 'dec_pipeline_b')")
            states = [r["state"] for r in cursor.fetchall()]
            self.assertEqual(states, ["accepted", "accepted"])

            # Verify review queue candidate edges exist
            cursor.execute("SELECT * FROM edges WHERE edge_type = 'supersession_candidate'")
            cand_edges = cursor.fetchall()
            self.assertEqual(len(cand_edges), 2)

        # Check API review queue endpoint contains supersession_candidate items
        resp = self.api.handle_get("/api/review-queue", {})
        queue_items = [it for it in resp["data"] if it["item_type"] == "supersession_candidate"]
        self.assertEqual(len(queue_items), 2)

        # Test human arbitration via API: Confirm one candidate, reject the other
        edge_to_confirm = queue_items[0]["edge_id"]
        confirmed_target = queue_items[0]["to_id"]
        res_confirm = self.api.handle_post("/api/review-action", {
            "action": "confirm",
            "target_id": edge_to_confirm,
            "item_type": "supersession_candidate"
        })
        self.assertEqual(res_confirm["status"], "success")

        # Verify the chosen decision is now superseded
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state, superseded_by_decision_id FROM decisions WHERE decision_id = ?", (confirmed_target,))
            row = cursor.fetchone()
            self.assertEqual(row["state"], "superseded")
            self.assertEqual(row["superseded_by_decision_id"], "dec_pipeline_hybrid")


if __name__ == "__main__":
    unittest.main()
