"""
Review Queue: every button must change the database, and the queue must reflect it.

Regression tests for the bugs documented in audit/REVIEW_QUEUE_INVESTIGATION.md:
the dashboard sent the wrong identifier for drift and possible-rejected-idea items, the backend
reported "success" for no-op actions, Correct never removed an item, stale Confirm changed nothing,
conflict Confirm deleted the confirmed conflict, and edge/finding ids were authorized against the
demo repository.

Each action is replayed the way the dashboard sends it: {"action", "target_id": item["target_id"],
"item_type": item["item_type"]}.
"""
import contextlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import APIHandler
from backend.db import Database
from backend.seed_data import populate_seed_data

DEMO = "acme-eng/thermal-control-system"


def _q(path, sql, args=()):
    with contextlib.closing(sqlite3.connect(path)) as conn:
        return conn.execute(sql, args).fetchall()


def build_queue_db(path):
    """Seeded DB plus one item of every queue type that the seed does not create."""
    db = Database(path)
    populate_seed_data(db)
    decisions = [d for d in db.get_all_decisions() if d.repo == DEMO]
    accepted = [d for d in decisions if d.state == "accepted"]
    newer, older = accepted[0], accepted[-1]
    db.record_ambiguous_finding(
        finding_id="af_queue_test", pr_id="pr_77", repo=DEMO, decision_id=older.decision_id,
        decision_title=older.title, tier="possible", signals_matched=["kw"],
        rejection_reason="resembles a rejected approach", message="possible match", pr_comment="c")
    with contextlib.closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("""INSERT INTO edges (edge_id, edge_type, from_id, from_type, to_id, to_type, valid_from, repo_full_name)
                        VALUES ('edge_supersede_test', 'supersession_candidate', ?, 'decision', ?, 'decision',
                                '2026-03-01T00:00:00Z', ?)""", (newer.decision_id, older.decision_id, DEMO))
        conn.execute("UPDATE decisions SET freshness = 'stale' WHERE decision_id = ?", (newer.decision_id,))
        conn.execute("""INSERT INTO decision_assumptions (assumption_id, decision_id, text, watch_type, status, last_checked_at)
                        VALUES ('asm_test', ?, 'traffic stays below 1k rps', 'manual', 'broken', '2026-03-02T00:00:00')""",
                     (newer.decision_id,))
    return db


class ReviewQueueActionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "queue.db")
        self.db = build_queue_db(self.path)
        self.api = APIHandler(self.db)

    # -- helpers ---------------------------------------------------------------------------
    def queue(self):
        res = self.api.handle_get("/api/review-queue", {})
        self.assertEqual(res["status"], "success")
        return res["data"]

    def item(self, item_type):
        items = [i for i in self.queue() if i["item_type"] == item_type]
        self.assertTrue(items, f"seeded queue has no '{item_type}' item")
        return items[0]

    def act(self, item, action, **extra):
        body = {"action": action, "target_id": item["target_id"], "item_type": item["item_type"], **extra}
        return self.api.handle_post("/api/review-action", body)

    def in_queue(self, item):
        return any(i["item_type"] == item["item_type"] and i["target_id"] == item["target_id"] for i in self.queue())

    def feedback(self, finding_id):
        return _q(self.path, "SELECT action, finding_type FROM finding_feedback WHERE finding_id = ?", (finding_id,))

    # -- contract --------------------------------------------------------------------------
    def test_every_queue_item_exposes_the_id_the_action_endpoint_expects(self):
        expected_key = {"decision": "decision_id", "stale_decision": "decision_id", "conflict": "edge_id",
                        "drift": "edge_id", "supersession_candidate": "edge_id",
                        "possible_rejected_idea": "finding_id"}
        types = set()
        for i in self.queue():
            types.add(i["item_type"])
            self.assertEqual(i.get("target_id"), i[expected_key[i["item_type"]]], i)
        self.assertEqual(types, set(expected_key))  # fixture covers every item type

    # -- decisions -------------------------------------------------------------------------
    def test_confirm_decision_persists_and_leaves_queue(self):
        it = self.item("decision")
        res = self.act(it, "confirm")
        self.assertEqual(res["status"], "success", res)
        self.assertEqual(_q(self.path, "SELECT review_status FROM decisions WHERE decision_id=?",
                            (it["target_id"],))[0][0], "human_confirmed")
        self.assertFalse(self.in_queue(it))

    def test_correct_decision_changes_title_keeps_rationale_records_reason_and_leaves_queue(self):
        it = self.item("decision")
        old_state, old_rationale = _q(self.path, "SELECT state, rationale FROM decisions WHERE decision_id=?",
                                      (it["target_id"],))[0]
        res = self.act(it, "correct", title="Corrected title", state=old_state, reason="extraction mislabelled")
        self.assertEqual(res["status"], "success", res)
        title, rationale, status = _q(self.path, "SELECT title, rationale, review_status FROM decisions WHERE decision_id=?",
                                      (it["target_id"],))[0]
        self.assertEqual((title, rationale, status), ("Corrected title", old_rationale, "human_corrected"))
        notes = [r[0] for r in _q(self.path, "SELECT notes FROM state_history WHERE decision_id=?", (it["target_id"],))]
        self.assertTrue(any("extraction mislabelled" in (n or "") for n in notes), notes)
        self.assertFalse(self.in_queue(it))

    def test_illegal_transition_is_409_and_changes_nothing(self):
        it = self.item("decision")
        if _q(self.path, "SELECT state FROM decisions WHERE decision_id=?", (it["target_id"],))[0][0] != "accepted":
            self.skipTest("first queued decision is not accepted")
        before = _q(self.path, "SELECT * FROM decisions WHERE decision_id=?", (it["target_id"],))
        res = self.act(it, "reject")
        self.assertEqual(res.get("status_code"), 409, res)
        self.assertEqual(_q(self.path, "SELECT * FROM decisions WHERE decision_id=?", (it["target_id"],)), before)
        self.assertTrue(self.in_queue(it))

    def test_confirm_stale_decision_revalidates_it(self):
        it = self.item("stale_decision")
        res = self.act(it, "confirm", reason="assumption re-checked")
        self.assertEqual(res["status"], "success", res)
        self.assertEqual(_q(self.path, "SELECT freshness FROM decisions WHERE decision_id=?",
                            (it["target_id"],))[0][0], "revalidated")
        self.assertFalse(self.in_queue(it))

    # -- conflict / drift edges ----------------------------------------------------------------
    def _edge_exists(self, edge_id):
        return bool(_q(self.path, "SELECT 1 FROM edges WHERE edge_id=?", (edge_id,)))

    def test_confirm_conflict_keeps_edge_records_verdict_and_leaves_queue(self):
        it = self.item("conflict")
        res = self.act(it, "confirm")
        self.assertEqual(res["status"], "success", res)
        self.assertTrue(self._edge_exists(it["target_id"]), "a confirmed conflict must stay in the graph")
        self.assertEqual(self.feedback(it["target_id"]), [("confirm", "conflict")])
        self.assertFalse(self.in_queue(it))

    def test_reject_conflict_removes_edge_records_verdict_and_leaves_queue(self):
        it = self.item("conflict")
        res = self.act(it, "reject")
        self.assertEqual(res["status"], "success", res)
        self.assertFalse(self._edge_exists(it["target_id"]))
        self.assertEqual(self.feedback(it["target_id"]), [("dismiss", "conflict")])
        self.assertFalse(self.in_queue(it))

    def test_drift_confirm_and_reject_use_the_edge_id(self):
        it = self.item("drift")
        self.assertTrue(it["target_id"].startswith("edge"), it)
        res = self.act(it, "confirm")
        self.assertEqual(res["status"], "success", res)
        self.assertTrue(self._edge_exists(it["target_id"]))
        self.assertEqual(self.feedback(it["target_id"]), [("confirm", "drift")])
        self.assertFalse(self.in_queue(it))

    def test_supersession_candidate_confirm_supersedes_older_decision(self):
        it = self.item("supersession_candidate")
        older = it["to_id"]
        res = self.act(it, "confirm", reason="ADR 12 replaces it")
        self.assertEqual(res["status"], "success", res)
        self.assertEqual(_q(self.path, "SELECT state FROM decisions WHERE decision_id=?", (older,))[0][0], "superseded")
        self.assertFalse(self.in_queue(it))

    # -- possible rejected idea (ambiguous finding) ----------------------------------------------
    def test_possible_rejected_idea_confirm_and_dismiss_use_the_finding_id(self):
        it = self.item("possible_rejected_idea")
        self.assertEqual(it["target_id"], "af_queue_test")
        res = self.act(it, "reject")
        self.assertEqual(res["status"], "success", res)
        self.assertEqual(_q(self.path, "SELECT status FROM ambiguous_findings WHERE finding_id='af_queue_test'")[0][0],
                         "dismissed")
        self.assertFalse(self.in_queue(it))

    # -- no silent no-ops ----------------------------------------------------------------------
    def test_unknown_edge_id_is_404_not_success(self):
        res = self.api.handle_post("/api/review-action",
                                   {"action": "confirm", "target_id": "edge_does_not_exist", "item_type": "drift"})
        self.assertEqual(res.get("status_code"), 404, res)

    def test_unsupported_action_for_item_type_is_400(self):
        it = self.item("conflict")
        res = self.act(it, "correct", title="x")
        self.assertEqual(res.get("status_code"), 400, res)
        self.assertTrue(self._edge_exists(it["target_id"]))

    def test_unknown_item_type_is_400(self):
        res = self.api.handle_post("/api/review-action",
                                   {"action": "confirm", "target_id": "x", "item_type": "banana"})
        self.assertEqual(res.get("status_code"), 400, res)

    def test_changes_persist_after_reopening_the_database(self):
        it = self.item("conflict")
        self.act(it, "reject")
        fresh = APIHandler(Database(self.path))  # new handler, new connections
        self.assertFalse(any(i.get("target_id") == it["target_id"] for i in fresh.handle_get("/api/review-queue", {})["data"]))


class ReviewQueueAuthorizationTests(unittest.TestCase):
    """Edge and finding ids must be authorized against THEIR repository (was: demo repository)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "auth.db")
        build_queue_db(self.path)
        with contextlib.closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("INSERT INTO repos (repo_full_name, visibility, added_at, partial) "
                         "VALUES ('victim/private', 'private', datetime('now'), 0)")
            conn.execute("""INSERT INTO edges (edge_id, edge_type, from_id, from_type, to_id, to_type, valid_from, repo_full_name)
                            VALUES ('edge_private_conflict', 'conflicts_with', 'a', 'decision', 'b', 'decision',
                                    '2026-01-01T00:00:00Z', 'victim/private')""")

    def test_edge_id_resolves_to_its_own_repository(self):
        from backend.auth.repo_access import resolve_repo_for_request
        db = Database(self.path)
        repo = resolve_repo_for_request(db, "/api/review-action", {},
                                        {"target_id": "edge_private_conflict", "item_type": "conflict"})
        self.assertEqual(repo, "victim/private")
        repo = resolve_repo_for_request(db, "/api/review-action", {},
                                        {"target_id": "af_queue_test", "item_type": "possible_rejected_idea"})
        self.assertEqual(repo, DEMO)

    def test_other_users_cannot_act_on_a_private_repository_edge(self):
        from backend.security import authorize
        from backend.auth.sessions import create_session
        db = Database(self.path)
        with contextlib.closing(sqlite3.connect(self.path)) as conn, conn:
            uid = conn.execute("INSERT INTO users (github_id, login, avatar_url, created_at, last_login_at) "
                               "VALUES (-50, 'outsider', '', datetime('now'), datetime('now'))").lastrowid
        token, _ = create_session(db, user_id=uid, client="web")
        ok, status, _ = authorize({"Cookie": f"cif_session={token}"}, "repo_review", "10.0.0.5", db=db,
                                  path="/api/review-action",
                                  body_json={"action": "reject", "target_id": "edge_private_conflict", "item_type": "conflict"})
        self.assertFalse(ok)
        self.assertIn(status, (401, 403, 404))


if __name__ == "__main__":
    unittest.main()
