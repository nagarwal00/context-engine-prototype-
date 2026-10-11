"""
Tests for Historical Point-in-Time ('as of') Queries & Counterfactual Explorer (Step 2.6)
Verifies:
- Query before any decision returns empty result.
- A query for 1 March never shows a decision made on 15 March as active.
- A supersession dated 10 March is shown as accepted on 5 March and superseded on 12 March.
- Evidence appearing after cutoff is segregated into later_evidence.
- A decision with only reconstructed history is flagged.
- Documented alternatives show recorded rejection reasons or untried disclaimer (no speculation).
- Endpoint GET /api/as-of returns expected structures and handles error cases.
"""
import os
import tempfile
import unittest
from backend.db import Database
from backend.models import Decision, Event, Entity, Edge
from backend.engine.lifecycle import transition
from backend.engine.as_of import as_of
from backend.api import APIHandler


class TestAsOf(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_as_of.db")
        self.db = Database(self.db_path)

        # 1. Setup entities
        ent_file = Entity(
            entity_id="ent_cache_store",
            canonical_path="src/cache/store.py",
            entity_type="file",
            repo="test-repo"
        )
        self.db.upsert_entity(ent_file)

        # 2. Setup events
        # Evt 1: 2026-02-01
        ev_1 = Event(
            event_id="evt_01",
            source_type="github_issue",
            source_id="1",
            source_url="https://github.com/test-repo/issues/1",
            repo="test-repo",
            author="alice",
            timestamp="2026-02-01T08:00:00Z",
            title="Initial issue",
            body="Cache design discussion",
            artifacts_touched=["src/cache/store.py"]
        )
        self.db.upsert_event(ev_1)

        # Evt 2 (Later evidence): 2026-03-25
        ev_later = Event(
            event_id="evt_later",
            source_type="github_pr",
            source_id="50",
            source_url="https://github.com/test-repo/pull/50",
            repo="test-repo",
            author="charlie",
            timestamp="2026-03-25T14:00:00Z",
            title="Late verification telemetry",
            body="Post-hoc verification run",
            artifacts_touched=["src/cache/store.py"]
        )
        self.db.upsert_event(ev_later)

        # 3. Decision A (Alpha): made 2026-02-01, accepted 2026-02-04, superseded 2026-03-10
        dec_alpha = Decision(
            decision_id="dec_alpha",
            title="Alpha: In-memory dictionary cache",
            state="proposed",
            made_by="alice",
            made_at="2026-02-01T10:00:00Z",
            repo="test-repo",
            artifacts_affected=["ent_cache_store"],
            evidence_event_ids=["evt_01", "evt_later"],
            alternatives_considered=[
                {
                    "description": "SQLite in-process store",
                    "rejection_reason": "High lock contention under concurrency",
                    "evidence_event_ids": ["evt_01"]
                },
                {
                    "description": "Memcached cluster",
                    "rejection_reason": ""  # Untried / unrecorded outcome
                }
            ],
            rationale="Fast simple local dictionary"
        )
        self.db.save_decision(dec_alpha)

        # Transition Alpha to accepted on 2026-02-04
        transition(
            self.db,
            "dec_alpha",
            "accepted",
            actor="alice",
            reason="Benchmarked sufficient for phase 1",
            at="2026-02-04T12:00:00Z"
        )

        # 4. Decision B (Beta): made 2026-03-10, superseding Alpha
        dec_beta = Decision(
            decision_id="dec_beta",
            title="Beta: Distributed Redis cluster",
            state="accepted",
            made_by="bob",
            made_at="2026-03-10T14:00:00Z",
            repo="test-repo",
            artifacts_affected=["ent_cache_store"],
            evidence_event_ids=["evt_01"],
            supersedes_decision_id="dec_alpha",
            rationale="Replaces in-memory cache to solve multi-replica cache stampede"
        )
        self.db.save_decision(dec_beta)

        # Transition Alpha to superseded on 2026-03-10
        transition(
            self.db,
            "dec_alpha",
            "superseded",
            actor="bob",
            reason="Superseded by Redis cluster decision dec_beta",
            at="2026-03-10T14:00:00Z",
            superseded_by_id="dec_beta"
        )

        # 5. Decision C (Gamma): made 2026-03-15
        dec_gamma = Decision(
            decision_id="dec_gamma",
            title="Gamma: Global TLS rate limiting",
            state="accepted",
            made_by="carol",
            made_at="2026-03-15T09:00:00Z",
            repo="test-repo",
            artifacts_affected=["ent_cache_store"],
            evidence_event_ids=["evt_01"],
            rationale="Adds upstream rate limiting"
        )
        self.db.save_decision(dec_gamma)

        # 6. Decision D (Delta): only reconstructed history
        dec_delta = Decision(
            decision_id="dec_delta",
            title="Delta: Legacy config loader",
            state="accepted",
            made_by="system",
            made_at="2026-01-15T00:00:00Z",
            repo="test-repo",
            artifacts_affected=["ent_cache_store"],
            evidence_event_ids=["evt_01"],
            rationale="Legacy configuration subsystem"
        )
        self.db.save_decision(dec_delta)

        # Overwrite delta's state_history to simulate reconstructed-only legacy row
        with self.db.get_connection() as conn:
            conn.execute("""
            UPDATE state_history
            SET changed_by = 'system:backfill', notes = 'reconstructed from current state at backfill', reconstructed = 1
            WHERE decision_id = 'dec_delta'
            """)
            conn.commit()

        # 7. Add edge with validity
        edge = Edge(
            edge_id="edge_alpha_affects",
            edge_type="affects",
            from_id="dec_alpha",
            from_type="decision",
            to_id="ent_cache_store",
            to_type="entity",
            valid_from="2026-02-01T10:00:00Z",
            valid_to="2026-03-10T14:00:00Z"
        )
        self.db.upsert_edge(edge)

        self.handler = APIHandler(self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_query_before_any_decision_returns_empty(self):
        """Fixture: before any decision (empty result)."""
        res = as_of(self.db, repo="test-repo", cutoff="2026-01-01T00:00:00Z")
        self.assertEqual(res["status"], "success")
        data = res["data"]
        self.assertEqual(len(data["decisions"]), 0)
        self.assertIn("no architectural decisions", data["explanation"].lower())

    def test_query_1_march_never_shows_15_march_decision(self):
        """
        Acceptance criterion:
        A query for 1 March never shows a decision made on 15 March (dec_gamma) as active.
        """
        res = as_of(self.db, repo="test-repo", cutoff="2026-03-01")
        data = res["data"]
        dec_ids = [d["decision_id"] for d in data["decisions"]]

        self.assertIn("dec_alpha", dec_ids)
        self.assertNotIn("dec_gamma", dec_ids)
        self.assertNotIn("dec_beta", dec_ids)

        alpha = next(d for d in data["decisions"] if d["decision_id"] == "dec_alpha")
        # On 1 March, Alpha was accepted (transitioned 4 Feb, superseded 10 March)
        self.assertEqual(alpha["state_as_of_cutoff"], "accepted")

    def test_supersession_on_5_march_vs_12_march(self):
        """
        Acceptance criterion:
        A supersession dated 10 March is shown as accepted on 5 March and superseded on 12 March.
        """
        # Query on 5 March: Alpha must be accepted
        res_5 = as_of(self.db, repo="test-repo", cutoff="2026-03-05")
        alpha_5 = next(d for d in res_5["data"]["decisions"] if d["decision_id"] == "dec_alpha")
        self.assertEqual(alpha_5["state_as_of_cutoff"], "accepted")

        # Beta (made 10 March) must NOT be present on 5 March
        self.assertFalse(any(d["decision_id"] == "dec_beta" for d in res_5["data"]["decisions"]))

        # Changed afterwards on 5 March includes the 10 March transition
        changed_5 = res_5["data"]["changed_afterwards"]
        self.assertTrue(any(
            c.get("decision_id") == "dec_alpha" and c.get("to_state") == "superseded"
            for c in changed_5
        ))

        # Query on 12 March: Alpha must be superseded
        res_12 = as_of(self.db, repo="test-repo", cutoff="2026-03-12")
        alpha_12 = next(d for d in res_12["data"]["decisions"] if d["decision_id"] == "dec_alpha")
        self.assertEqual(alpha_12["state_as_of_cutoff"], "superseded")

        # Beta must now be present on 12 March
        beta_12 = next(d for d in res_12["data"]["decisions"] if d["decision_id"] == "dec_beta")
        self.assertEqual(beta_12["state_as_of_cutoff"], "accepted")

    def test_evidence_appearing_after_cutoff_segregated(self):
        """Fixture: evidence appearing after the cutoff is segregated into later_evidence."""
        res = as_of(self.db, repo="test-repo", cutoff="2026-02-15")
        data = res["data"]

        # evt_01 is from 2026-02-01 (<= cutoff) -> in evidence
        known_eids = [e["event_id"] for e in data["evidence"]]
        self.assertIn("evt_01", known_eids)

        # evt_later is from 2026-03-25 (> cutoff) -> in later_evidence
        later_eids = [e["event_id"] for e in data["later_evidence"]]
        self.assertIn("evt_later", later_eids)
        self.assertNotIn("evt_later", known_eids)

    def test_decision_with_only_reconstructed_history_flagged(self):
        """Fixture: a decision with only reconstructed history is flagged."""
        res = as_of(self.db, repo="test-repo", cutoff="2026-01-20")
        data = res["data"]

        delta = next(d for d in data["decisions"] if d["decision_id"] == "dec_delta")
        self.assertTrue(delta["has_reconstructed_history_only"])

    def test_counterfactual_rules_and_no_speculation(self):
        """
        Counterfactual rules:
        - Documented alternative with recorded reason shows that reason.
        - Untried alternative shows 'no recorded outcome — consequences of the untried alternative are unknown.'
        - Explanation generator does not write speculative text.
        """
        res = as_of(self.db, repo="test-repo", cutoff="2026-03-01")
        alts = res["data"]["documented_alternatives"]

        sqlite_alt = next(a for a in alts if "SQLite" in a["description"])
        self.assertIn("High lock contention", sqlite_alt["rejection_reason"])

        memcached_alt = next(a for a in alts if "Memcached" in a["description"])
        self.assertEqual(
            memcached_alt["rejection_reason"],
            "no recorded outcome — consequences of the untried alternative are unknown."
        )

        explanation = res["data"]["explanation"]
        self.assertIn("Documented alternatives considered:", explanation)
        self.assertIn("no recorded outcome", explanation)

    def test_edge_validity_at_cutoff(self):
        """Edges valid at cutoff: valid_from <= cutoff and (valid_to is null or valid_to > cutoff)."""
        # On 2026-02-15, edge_alpha_affects (valid 2026-02-01 to 2026-03-10) is active
        res_active = as_of(self.db, repo="test-repo", cutoff="2026-02-15")
        edge_ids = [e["edge_id"] for e in res_active["data"]["edges"]]
        self.assertIn("edge_alpha_affects", edge_ids)

        # On 2026-03-15, edge_alpha_affects has expired (valid_to = 2026-03-10 <= 2026-03-15)
        res_expired = as_of(self.db, repo="test-repo", cutoff="2026-03-15")
        edge_ids_expired = [e["edge_id"] for e in res_expired["data"]["edges"]]
        self.assertNotIn("edge_alpha_affects", edge_ids_expired)

    def test_api_endpoint_as_of(self):
        """Endpoint GET /api/as-of integration."""
        # Valid query
        res = self.handler.handle_get("/api/as-of", {"date": ["2026-03-05"], "repo": ["test-repo"]})
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res["data"]["cutoff_input"], "2026-03-05")

        # Missing date
        res_err = self.handler.handle_get("/api/as-of", {})
        self.assertEqual(res_err.get("status"), "error")
        self.assertEqual(res_err.get("status_code"), 400)

        # Invalid date
        res_inv = self.handler.handle_get("/api/as-of", {"date": ["not-a-date"]})
        self.assertEqual(res_inv.get("status"), "error")
        self.assertEqual(res_inv.get("status_code"), 400)

    def test_artifact_filtering(self):
        """Artifact parameter filters decisions affecting that specific artifact."""
        res = as_of(self.db, repo="test-repo", cutoff="2026-03-01", artifact="src/cache/store.py")
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(len(res["data"]["decisions"]), 1)

        # Query for non-existent artifact yields 0 decisions
        res_none = as_of(self.db, repo="test-repo", cutoff="2026-03-01", artifact="src/unrelated/file.py")
        self.assertEqual(len(res_none["data"]["decisions"]), 0)


if __name__ == "__main__":
    unittest.main()
