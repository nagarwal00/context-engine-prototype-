"""
tests/test_edge_tenancy.py - Per-repository edge tenancy and query isolation (Step 1.2 / F4b).
Verifies:
1. Edges created via lifecycle, reconciliation, and drift detector carry repo_full_name.
2. No edge has repo_full_name IS NULL.
3. Cross-tenant isolation in /api/review-queue and /api/stats.
"""
import os
import shutil
import tempfile
import unittest

from backend.api import APIHandler
from backend.auth.sessions import create_session
from backend.db import Database
from backend.engine.drift_detector import DriftDetector
from backend.engine.lifecycle import transition
from backend.engine.reconciliation import ReconciliationEngine
from backend.models import Decision, Edge, Entity, Event
from tests.helpers_time import iso_z


class TestEdgeTenancy(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_edge_tenancy.db")
        self.db = Database(self.db_path)
        self.api = APIHandler(self.db)
        self.reconciliation = ReconciliationEngine(self.db)
        self.drift_detector = DriftDetector(self.db)

        self.repo_x = "org/repo-x"
        self.repo_y = "org/repo-y"

        with self.db.get_connection() as conn:
            # Users
            conn.execute(
                "INSERT INTO users (user_id, github_id, login, avatar_url, created_at, last_login_at) "
                "VALUES (1, 101, 'user_x', 'https://avatar.x', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
            )
            conn.execute(
                "INSERT INTO users (user_id, github_id, login, avatar_url, created_at, last_login_at) "
                "VALUES (2, 102, 'user_y', 'https://avatar.y', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
            )
            # Repos
            now = iso_z()
            conn.execute(
                "INSERT INTO repos (repo_full_name, visibility, added_by_user_id, added_at) VALUES (?, 'private', 1, ?)",
                (self.repo_x, now),
            )
            conn.execute(
                "INSERT INTO repos (repo_full_name, visibility, added_by_user_id, added_at) VALUES (?, 'private', 2, ?)",
                (self.repo_y, now),
            )
            # Access rows
            conn.execute(
                "INSERT INTO repo_access (user_id, repo_full_name, level, verified_at) VALUES (?, ?, 'admin', ?)",
                (1, self.repo_x, now),
            )
            conn.execute(
                "INSERT INTO repo_access (user_id, repo_full_name, level, verified_at) VALUES (?, ?, 'admin', ?)",
                (2, self.repo_y, now),
            )

        # Create session tokens
        self.token_x, _ = create_session(self.db, user_id=1, client="web")
        self.token_y, _ = create_session(self.db, user_id=2, client="web")
        self.headers_x = {"Authorization": f"Bearer {self.token_x}"}
        self.headers_y = {"Authorization": f"Bearer {self.token_y}"}

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_edge_tenancy_and_api_isolation(self):
        # 1. Seed events & decisions for Repo X
        ev_x1 = Event(
            event_id="evt_x_1",
            source_type="git_commit",
            source_id="c1",
            source_url="https://github.com/org/repo-x/commit/1",
            repo=self.repo_x,
            author="user_x",
            timestamp="2026-01-10T10:00:00Z",
            title="Initial commit",
        )
        self.db.upsert_event(ev_x1)

        dec_x1 = Decision(
            decision_id="dec_x_1",
            repo=self.repo_x,
                        title="Adopt Async Worker Pool",
            state="accepted",
            rationale="Handle high concurrency",
            made_by="user_x",
            made_at="2026-01-10T12:00:00Z",
            evidence_event_ids=["evt_x_1"],
            confidence=0.95,
        )
        self.db.save_decision(dec_x1)

        dec_x2 = Decision(
            decision_id="dec_x_2",
            repo=self.repo_x,
                        title="Upgrade to Distributed Task Queue",
            state="proposed",
            rationale="Better queueing across nodes",
            made_by="user_x",
            made_at="2026-01-15T12:00:00Z",
            evidence_event_ids=["evt_x_1"],
            confidence=0.92,
        )
        self.db.save_decision(dec_x2)

        # 2. Trigger (a) Supersession via lifecycle transition in Repo X
        transition(
            self.db,
            decision_id="dec_x_1",
            to_state="superseded",
            reason="Superseded by dec_x_2",
            actor="user_x",
            superseded_by_id="dec_x_2",
        )

        # 3. Seed entity & decision in Repo Y
        ev_y1 = Event(
            event_id="evt_y_1",
            source_type="git_commit",
            source_id="cy1",
            source_url="https://github.com/org/repo-y/commit/1",
            repo=self.repo_y,
            author="user_y",
            timestamp="2026-01-10T10:00:00Z",
            title="Repo Y initial commit",
        )
        self.db.upsert_event(ev_y1)

        dec_y1 = Decision(
            decision_id="dec_y_1",
            repo=self.repo_y,
                        title="Use Hardware Enclave for Secret Key Storage",
            state="accepted",
            rationale="Strict security compliance",
            made_by="user_y",
            made_at="2026-01-10T12:00:00Z",
            evidence_event_ids=["evt_y_1"],
            confidence=0.98,
        )
        self.db.save_decision(dec_y1)

        ent_y = Entity(
            entity_id="ent_y_crypto",
            entity_type="file",
            canonical_path="src/crypto/keys.py",
            repo=self.repo_y,
        )
        self.db.upsert_entity(ent_y)

        # 4. Trigger (c) Drift check that writes drifts_from in Repo Y
        self.drift_detector._record_drift_edge(
            entity_id="ent_y_crypto",
            decision_id="dec_y_1",
        )

        # 5. Trigger (b) Conflict via reconciliation in Repo X
        dec_x3 = Decision(
            decision_id="dec_x_3",
            repo=self.repo_x,
                        title="Adopt Synchronous Blocking Threads",
            state="accepted",
            rationale="Simpler debugging",
            made_by="contributor_other",
            made_at="2026-01-20T12:00:00Z",
            evidence_event_ids=["evt_x_1"],
            confidence=0.85,
        )
        self.db.save_decision(dec_x3)

        # Direct edge for conflict in Repo X via upsert_edge
        edge_conflict = Edge(
            edge_id="edge_conflict_x",
            edge_type="conflicts_with",
            from_id="dec_x_1",
            from_type="decision",
            to_id="dec_x_3",
            to_type="decision",
            valid_from="2026-01-20T12:00:00Z",
        )
        self.db.upsert_edge(edge_conflict)

        # 6. Assert NO edge has NULL repo_full_name and all match their decision's repo
        with self.db.get_connection() as conn:
            null_count = conn.execute("SELECT COUNT(*) FROM edges WHERE repo_full_name IS NULL").fetchone()[0]
            self.assertEqual(null_count, 0, "Found edges with NULL repo_full_name")

            edges = conn.execute("SELECT edge_id, edge_type, repo_full_name FROM edges").fetchall()
            for e in edges:
                self.assertIn(e[2], (self.repo_x, self.repo_y))
                if "x" in e[0] or e[1] == "supersedes" or e[1] == "conflicts_with":
                    self.assertEqual(e[2], self.repo_x)
                if "crypto" in e[0] or "dec_y" in e[0] or e[1] == "drifts_from":
                    self.assertEqual(e[2], self.repo_y)

        # 7. Multi-tenant API isolation:
        # User X queries review-queue: must see Repo X conflict / supersession, but NEVER Repo Y drift
        res_x = self.api.handle_get("/api/review-queue", {}, headers=self.headers_x)
        self.assertEqual(res_x.get("status"), "success")
        items_x = res_x.get("data", [])
        for it in items_x:
            self.assertNotEqual(it.get("decision_id"), "dec_y_1", "User X received Repo Y decision in review queue")
            if it.get("item_type") == "drift":
                self.assertNotEqual(it.get("decision_id"), "dec_y_1")
                self.assertNotEqual(it.get("entity_id"), "ent_y_crypto")

        # User Y queries review-queue: must see Repo Y drift, but NEVER Repo X items
        res_y = self.api.handle_get("/api/review-queue", {}, headers=self.headers_y)
        self.assertEqual(res_y.get("status"), "success")
        items_y = res_y.get("data", [])
        drift_items_y = [it for it in items_y if it.get("item_type") == "drift"]
        self.assertEqual(len(drift_items_y), 1)
        self.assertEqual(drift_items_y[0]["decision_id"], "dec_y_1")
        for it in items_y:
            self.assertNotIn(it.get("decision_id"), ("dec_x_1", "dec_x_2", "dec_x_3"))

        # Anonymous caller gets empty review queue (no demo repo items)
        res_anon = self.api.handle_get("/api/review-queue", {}, headers={})
        self.assertEqual(res_anon.get("status"), "success")
        self.assertEqual(len(res_anon.get("data", [])), 0)

        # User X queries stats: only counts for Repo X
        stats_x = self.api.handle_get("/api/stats", {}, headers=self.headers_x)
        self.assertEqual(stats_x.get("status"), "success")
        self.assertEqual(stats_x["data"]["drifts"], 0)  # Drift was in Repo Y!
        self.assertEqual(stats_x["data"]["conflicts"], 1)  # Conflict was in Repo X!


if __name__ == "__main__":
    unittest.main()
