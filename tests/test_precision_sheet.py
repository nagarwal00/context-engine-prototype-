"""
tests/test_precision_sheet.py
Unit tests for precision labelling sheet export and import bound to DB snapshot hash (Step 4.3).

Verifies:
1. Export writes valid CSV with correct headers and blank label columns.
2. Export queries cited events from edges correctly.
3. Import successfully updates labels with boolean True/False and notes.
4. Import rejects snapshot hash mismatch with ValueError.
5. Import rejects invalid non-binary label with ValueError.
6. Import rejects unknown decision ID with ValueError.
"""
import csv
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.precision_sheet import (
    compute_db_sha256,
    export_precision_sheet,
    import_precision_sheet
)


class TestPrecisionSheet(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.tmp_dir) / "test_precision.db"

        # Create minimal SQLite database with decisions, events, and edges
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE decisions (
            decision_id TEXT PRIMARY KEY,
            repo TEXT,
            title TEXT,
            state TEXT,
            confidence REAL,
            rationale TEXT,
            review_status TEXT
        );
        """)
        cur.execute("""
        CREATE TABLE events (
            event_id TEXT PRIMARY KEY,
            source_type TEXT,
            source_id TEXT,
            title TEXT,
            body TEXT,
            repo TEXT,
            ts TEXT
        );
        """)
        cur.execute("""
        CREATE TABLE edges (
            edge_id TEXT PRIMARY KEY,
            edge_type TEXT,
            from_id TEXT,
            from_type TEXT,
            to_id TEXT,
            to_type TEXT,
            valid_from TEXT,
            valid_to TEXT,
            repo_full_name TEXT
        );
        """)

        cur.execute("""
        INSERT INTO decisions VALUES 
          ('dec_01', 'repo/test', 'Adopt Rust', 'accepted', 0.9, 'Memory safety', 'approved'),
          ('dec_02', 'repo/test', 'Use SQLite', 'accepted', 0.85, 'Local persistence', 'approved');
        """)
        cur.execute("""
        INSERT INTO events VALUES 
          ('evt_01', 'adr', '001', 'RFC: Rust Migration', 'Body text', 'repo/test', '2026-01-01T00:00:00Z'),
          ('evt_02', 'pr', '42', 'Implement SQLite Storage', 'Body text', 'repo/test', '2026-01-02T00:00:00Z');
        """)
        cur.execute("""
        INSERT INTO edges VALUES 
          ('ed_01', 'evidenced_by', 'dec_01', 'decision', 'evt_01', 'event', '2026-01-01T00:00:00Z', NULL, 'repo/test'),
          ('ed_02', 'evidenced_by', 'dec_02', 'decision', 'evt_02', 'event', '2026-01-02T00:00:00Z', NULL, 'repo/test');
        """)
        conn.commit()
        conn.close()

        self.db_hash = compute_db_sha256(self.db_path)

        self.labels_path = Path(self.tmp_dir) / "precision_labels.json"
        self.csv_path = Path(self.tmp_dir) / "precision_sheet.csv"

        labels = [
            {
                "dataset_version": "whybench_v1",
                "db_snapshot_sha256": self.db_hash,
                "repo": "repo/test",
                "decision_id": "dec_01",
                "title": "Adopt Rust",
                "state": "accepted",
                "confidence": 0.9,
                "rationale": "Memory safety",
                "correct": None,
                "note": ""
            },
            {
                "dataset_version": "whybench_v1",
                "db_snapshot_sha256": self.db_hash,
                "repo": "repo/test",
                "decision_id": "dec_02",
                "title": "Use SQLite",
                "state": "accepted",
                "confidence": 0.85,
                "rationale": "Local persistence",
                "correct": None,
                "note": ""
            }
        ]
        with open(self.labels_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(labels, f, indent=2)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_export_creates_csv_with_blank_labels(self):
        export_precision_sheet(self.labels_path, self.csv_path, self.db_path)
        self.assertTrue(self.csv_path.exists())

        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))

        self.assertEqual(len(reader), 2)
        self.assertEqual(reader[0]["id"], "dec_01")
        self.assertEqual(reader[0]["decision_title"], "Adopt Rust")
        self.assertIn("evt_01", reader[0]["cited_events"])
        self.assertEqual(reader[0]["correct"], "")
        self.assertEqual(reader[0]["reason"], "")

        self.assertEqual(reader[1]["id"], "dec_02")
        self.assertIn("evt_02", reader[1]["cited_events"])

    def test_import_updates_labels(self):
        export_precision_sheet(self.labels_path, self.csv_path, self.db_path)

        # Simulate human filling in labels
        rows = [
            {"id": "dec_01", "decision_title": "Adopt Rust", "rationale": "Memory safety", "cited_events": "evt_01", "correct": "true", "reason": "Accurate"},
            {"id": "dec_02", "decision_title": "Use SQLite", "rationale": "Local persistence", "cited_events": "evt_02", "correct": "false", "reason": "Hallucinated rationale"}
        ]
        with open(self.csv_path, "w", encoding="utf-8", newline="\n") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "decision_title", "rationale", "cited_events", "correct", "reason"])
            writer.writeheader()
            writer.writerows(rows)

        updated_count = import_precision_sheet(self.csv_path, self.labels_path, self.db_path)
        self.assertEqual(updated_count, 2)

        with open(self.labels_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIs(data[0]["correct"], True)
        self.assertEqual(data[0]["note"], "Accurate")
        self.assertIs(data[1]["correct"], False)
        self.assertEqual(data[1]["note"], "Hallucinated rationale")

    def test_import_hash_mismatch_raises_error(self):
        export_precision_sheet(self.labels_path, self.csv_path, self.db_path)

        # Alter database file so hash changes
        with open(self.db_path, "ab") as f:
            f.write(b"modified_data_at_end")

        with self.assertRaises(ValueError) as ctx:
            import_precision_sheet(self.csv_path, self.labels_path, self.db_path)
        self.assertIn("Snapshot hash mismatch", str(ctx.exception))

    def test_import_invalid_label_raises_error(self):
        export_precision_sheet(self.labels_path, self.csv_path, self.db_path)

        rows = [
            {"id": "dec_01", "decision_title": "Adopt Rust", "rationale": "", "cited_events": "", "correct": "maybe", "reason": ""}
        ]
        with open(self.csv_path, "w", encoding="utf-8", newline="\n") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "decision_title", "rationale", "cited_events", "correct", "reason"])
            writer.writeheader()
            writer.writerows(rows)

        with self.assertRaises(ValueError) as ctx:
            import_precision_sheet(self.csv_path, self.labels_path, self.db_path)
        self.assertIn("Invalid label", str(ctx.exception))

    def test_import_unknown_decision_id_raises_error(self):
        export_precision_sheet(self.labels_path, self.csv_path, self.db_path)

        rows = [
            {"id": "dec_unknown_99", "decision_title": "Unknown", "rationale": "", "cited_events": "", "correct": "true", "reason": ""}
        ]
        with open(self.csv_path, "w", encoding="utf-8", newline="\n") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "decision_title", "rationale", "cited_events", "correct", "reason"])
            writer.writeheader()
            writer.writerows(rows)

        with self.assertRaises(ValueError) as ctx:
            import_precision_sheet(self.csv_path, self.labels_path, self.db_path)
        self.assertIn("Unknown decision ID", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
