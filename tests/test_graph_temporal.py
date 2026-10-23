"""
Tests for Temporal Edge Defaults and Validation (P1-c / Step 1.5)
"""
import os
import tempfile
import unittest
from pathlib import Path

from backend.db import Database
from backend.models import Edge, Decision, Event
from backend.engine.graph import TemporalGraph
from tools.repair_edge_validity import repair_edges


class TestGraphTemporal(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_temporal.db")
        self.db = Database(self.db_path)
        self.graph = TemporalGraph(self.db)

        # Seed dummy endpoint rows so edge repo resolution succeeds
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO decisions (decision_id, repo, repo_full_name, title, state, made_at, confidence) "
                "VALUES ('dec_01', 'acme/test', 'acme/test', 'D1', 'accepted', '2025-01-01T00:00:00Z', 1.0), "
                "       ('dec_02', 'acme/test', 'acme/test', 'D2', 'accepted', '2025-01-01T00:00:00Z', 1.0), "
                "       ('dec_pid_01', 'acme/test', 'acme/test', 'D PID', 'accepted', '2025-01-01T00:00:00Z', 1.0)"
            )
            conn.execute(
                "INSERT INTO entities (entity_id, entity_type, canonical_path, repo, repo_full_name) "
                "VALUES ('ent_01', 'file', 'src/file.py', 'acme/test', 'acme/test')"
            )
            conn.execute(
                "INSERT INTO events (event_id, repo, repo_full_name, source_type, source_id, source_url, ts) "
                "VALUES ('evt_commit_01', 'acme/test', 'acme/test', 'git_commit', 'c1', 'https://example.com', '2025-06-01T12:00:00Z')"
            )
            conn.commit()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_missing_valid_from_raises_value_error(self):
        """Calling add_edge without a valid_from timestamp must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.graph.add_edge(
                edge_type="affects",
                from_id="dec_01",
                from_type="decision",
                to_id="ent_01",
                to_type="entity"
            )
        self.assertIn("valid_from is required", str(ctx.exception))

        # Edge object with empty valid_from must also raise
        edge_empty = Edge(
            edge_id="e_test_empty",
            edge_type="affects",
            from_id="dec_01",
            to_id="ent_01",
            valid_from=""
        )
        with self.assertRaises(ValueError):
            self.graph.add_edge(edge_empty)

    def test_invalid_iso_format_raises_value_error(self):
        """Non-ISO timestamp strings must raise ValueError."""
        with self.assertRaises(ValueError):
            self.graph.add_edge(
                edge_type="affects",
                from_id="dec_01",
                to_id="ent_01",
                valid_from="not-a-timestamp"
            )

    def test_valid_to_earlier_than_valid_from_raises_value_error(self):
        """If valid_to is set it must be >= valid_from, else raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.graph.add_edge(
                edge_type="affects",
                from_id="dec_01",
                to_id="ent_01",
                valid_from="2025-06-01T00:00:00Z",
                valid_to="2025-05-31T23:59:59Z"
            )
        self.assertIn("must be >= valid_from", str(ctx.exception))

        # Edge object with invalid range must also raise
        edge_invalid = Edge(
            edge_id="e_invalid_range",
            edge_type="affects",
            from_id="dec_01",
            to_id="ent_01",
            valid_from="2025-06-01T00:00:00Z",
            valid_to="2025-05-31T00:00:00Z"
        )
        with self.assertRaises(ValueError):
            self.graph.add_edge(edge_invalid)

    def test_edge_created_from_event_has_correct_valid_from(self):
        """An edge created from an event at 2025-06-01 has valid_from 2025-06-01."""
        target_timestamp = "2025-06-01T12:00:00Z"
        edge = self.graph.add_edge(
            edge_type="evidenced_by",
            from_id="dec_pid_01",
            from_type="decision",
            to_id="evt_commit_01",
            to_type="event",
            valid_from=target_timestamp
        )
        self.assertEqual(edge.valid_from, target_timestamp)

        # Verify edge in database
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT valid_from FROM edges WHERE edge_id = ?", (edge.edge_id,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["valid_from"], target_timestamp)

    def test_valid_to_greater_or_equal_succeeds(self):
        """Equal or subsequent valid_to values must be accepted."""
        edge = self.graph.add_edge(
            edge_type="affects",
            from_id="dec_01",
            to_id="ent_01",
            valid_from="2025-06-01T00:00:00Z",
            valid_to="2025-06-01T00:00:00Z"
        )
        self.assertIsNotNone(edge)

        edge2 = self.graph.add_edge(
            edge_type="supersedes",
            from_id="dec_02",
            to_id="dec_01",
            valid_from="2025-06-01T00:00:00Z",
            valid_to="2025-08-01T00:00:00Z"
        )
        self.assertIsNotNone(edge2)

    def test_repair_edge_validity_tool_reports_and_applies(self):
        """Verify tools/repair_edge_validity.py dry-run and apply modes."""
        placeholder_ts = "2026-01-01T00:00:00Z"
        dec_ts = "2025-03-15T10:00:00Z"
        earlier_event_ts = "2025-03-10T08:00:00Z"

        # Insert decision
        dec = Decision(
            decision_id="dec_repair_test",
            title="Test Decision",
            state="accepted",
            made_at=dec_ts,
            artifacts_affected=["src/file.py"],
            evidence_event_ids=["evt_repair_test"]
        )
        ev = Event(
            event_id="evt_repair_test",
            source_type="git_commit",
            source_url="https://github.com/acme/repo/commit/1",
            timestamp=earlier_event_ts
        )
        self.db.upsert_event(ev)
        self.db.save_decision(dec)

        # Directly insert edge with placeholder
        with self.db.get_connection() as conn:
            conn.execute("""
            INSERT INTO edges (edge_id, edge_type, from_id, from_type, to_id, to_type, valid_from, valid_to)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "edge_placeholder_test",
                "affects",
                dec.decision_id,
                "decision",
                "ent_file",
                "entity",
                placeholder_ts,
                None
            ))
            conn.commit()

        # 1. Test Dry-Run: reports candidate, does not write changes, no backup
        res_dry = repair_edges(self.db_path, apply_changes=False)
        self.assertEqual(res_dry["edges_scanned"], 1)
        self.assertEqual(res_dry["edges_repaired"], 1)
        self.assertIsNone(res_dry["backup_path"])

        # Check DB unchanged after dry-run
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT valid_from FROM edges WHERE edge_id = 'edge_placeholder_test'")
            row = cursor.fetchone()
            self.assertEqual(row["valid_from"], placeholder_ts)

        # 2. Test Apply: writes changes and creates backup
        res_apply = repair_edges(self.db_path, apply_changes=True)
        self.assertEqual(res_apply["edges_repaired"], 1)
        self.assertIsNotNone(res_apply["backup_path"])
        self.assertTrue(os.path.exists(res_apply["backup_path"]))

        # Check DB has earliest relevant timestamp (earlier_event_ts)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT valid_from FROM edges WHERE edge_id = 'edge_placeholder_test'")
            row = cursor.fetchone()
            self.assertEqual(row["valid_from"], earlier_event_ts)


if __name__ == "__main__":
    unittest.main()
