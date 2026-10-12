"""
Unit Tests for Offline Slack Export Adapter (Step 5.5)
Verifies:
1. Parsing of Slack export structure (users.json, channels.json, YYYY-MM-DD.json).
2. Author identity resolution via IdentityResolver.
3. Thread grouping and independence key assignment.
4. Privacy sanitizer execution BEFORE persistence (zero raw secrets reach SQLite).
5. Source independence engine grouping across threads.
"""
import os
import tempfile
import json
import unittest
from backend.models import Event, Decision
from backend.db import Database
from backend.ingestion.identity import IdentityResolver
from backend.ingestion.slack_adapter import SlackExportAdapter
from backend.engine.independence import independence_key, count_independent_sources


class TestSlackAdapter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_slack.db")
        self.db = Database(self.db_path)
        self.identity_resolver = IdentityResolver(self.db)
        self.adapter = SlackExportAdapter(self.db, self.identity_resolver)
        self.repo = "acme-eng/platform-core"

        # Setup synthetic Slack workspace export folder
        self.export_dir = os.path.join(self.temp_dir.name, "slack_export")
        os.makedirs(self.export_dir, exist_ok=True)

        # 1. users.json
        users = [
            {
                "id": "U01SARAH",
                "name": "sarahc",
                "real_name": "Sarah Chen",
                "profile": {"email": "sarah.chen@acme.org"}
            },
            {
                "id": "U02MARCUS",
                "name": "marcusv",
                "real_name": "Marcus Vance",
                "profile": {"email": "marcus.vance@techcorp.io"}
            }
        ]
        with open(os.path.join(self.export_dir, "users.json"), "w", encoding="utf-8") as f:
            json.dump(users, f)

        # 2. channels.json
        channels = [
            {
                "id": "C01ARCH",
                "name": "architecture"
            }
        ]
        with open(os.path.join(self.export_dir, "channels.json"), "w", encoding="utf-8") as f:
            json.dump(channels, f)

        # 3. Channel message files
        arch_dir = os.path.join(self.export_dir, "architecture")
        os.makedirs(arch_dir, exist_ok=True)

        messages = [
            {
                "type": "message",
                "user": "U01SARAH",
                "text": "Thread 1 Root: Proposing Redis cluster migration over local memory cache.",
                "ts": "1673344800.000100",
                "thread_ts": "1673344800.000100"
            },
            {
                "type": "message",
                "user": "U02MARCUS",
                "text": "Thread 1 Reply: Concur. Also check secret config: AKIAIOSFODNN7EXAMPLE",
                "ts": "1673344860.000200",
                "thread_ts": "1673344800.000100"
            },
            {
                "type": "message",
                "user": "U01SARAH",
                "text": "Thread 2 Root: Separate discussion on DB migration exponential backoff.",
                "ts": "1673348400.000300",
                "thread_ts": "1673348400.000300"
            }
        ]
        with open(os.path.join(arch_dir, "2023-01-10.json"), "w", encoding="utf-8") as f:
            json.dump(messages, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_slack_export_ingestion_and_privacy(self):
        """Verifies parsing, identity mapping, and secret redaction."""
        result = self.adapter.ingest_export(self.export_dir, self.repo)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["messages_ingested"], 3)
        self.assertEqual(result["threads_count"], 2)
        self.assertIn("architecture", result["channels"])

        # Verify messages in SQLite
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM events WHERE repo = ? ORDER BY ts ASC", (self.repo,))
            rows = [dict(r) for r in cur.fetchall()]

        self.assertEqual(len(rows), 3)

        # 1. Verify Identity Resolution:
        # U01SARAH email matches sarah.chen@acme.org -> canonical_id sarah_chen
        # U02MARCUS email matches marcus.vance@techcorp.io -> canonical_id marcus_vance
        self.assertEqual(rows[0]["author"], "sarah_chen")
        self.assertEqual(rows[1]["author"], "marcus_vance")
        self.assertEqual(rows[2]["author"], "sarah_chen")

        # 2. Verify Privacy Sanitization:
        # AKIAIOSFODNN7EXAMPLE must NEVER be stored raw in the database
        for r in rows:
            self.assertNotIn("AKIAIOSFODNN7EXAMPLE", r["body"])
        self.assertIn("[REDACTED:AWS_KEY]", rows[1]["body"])

        # 3. Verify Source URLs
        for r in rows:
            self.assertTrue(r["source_url"].startswith("https://slack.com/archives/C01ARCH/p"))

        # 4. Verify Parent linkage for thread replies
        ev_reply = rows[1]
        parent_ids = json.loads(ev_reply["parent_event_ids"])
        self.assertEqual(len(parent_ids), 1)
        self.assertEqual(parent_ids[0], rows[0]["event_id"])

    def test_slack_thread_independence_grouping(self):
        """Verifies that messages in the same Slack thread share independence_key."""
        result = self.adapter.ingest_export(self.export_dir, self.repo)
        events = result["events"]

        ev_thread1_root = events[0]
        ev_thread1_reply = events[1]
        ev_thread2_root = events[2]

        key1 = independence_key(ev_thread1_root, events)
        key2 = independence_key(ev_thread1_reply, events)
        key3 = independence_key(ev_thread2_root, events)

        # Root and reply in Thread 1 must share the SAME independence key
        self.assertEqual(key1, key2)
        self.assertTrue(key1.startswith("slack:acme-eng/platform-core:architecture#1673344800.000100"))

        # Thread 2 must have a DIFFERENT independence key
        self.assertNotEqual(key1, key3)
        self.assertTrue(key3.startswith("slack:acme-eng/platform-core:architecture#1673348400.000300"))

        # Two events in the same thread count as 1 independent source
        sources_same_thread = count_independent_sources([ev_thread1_root, ev_thread1_reply])
        self.assertEqual(sources_same_thread, 1, "Two messages in the same thread must count as 1 source")

        # Two events in different threads count as 2 independent sources
        sources_diff_threads = count_independent_sources([ev_thread1_root, ev_thread2_root])
        self.assertEqual(sources_diff_threads, 2, "Messages in different threads must count as 2 sources")


if __name__ == "__main__":
    unittest.main()
