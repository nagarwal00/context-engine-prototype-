"""
Local-folder ingestion must not invent metadata (audit fixes INT-04 / ALG-05).

The previous implementation stamped every issue file as issue #5 by "sarah_chen", every ADR
as written by "alex_rodriguez", produced https://github.com/local/... links that 404, and
linked each ADR to every function in the repository.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import Database
from backend.ingestion.live_github import LiveGitHubIngestor

ADR = """# ADR 0007: Use PostgreSQL for the ledger

## Status
Accepted

## Context
SQLite locks under concurrent writers in src/ledger.py.

## Decision
We decided to migrate the ledger store to PostgreSQL.

## Consequences
Operations must run a database server.
"""

ISSUE = """# Issue #42: Ledger writes time out under load

Writers in ledger.py block each other. Proposal: introduce a connection pool.
"""


def _make_repo(root, with_git):
    os.makedirs(os.path.join(root, "src"))
    os.makedirs(os.path.join(root, "docs", "adr"))
    os.makedirs(os.path.join(root, "docs", "issues"))
    with open(os.path.join(root, "src", "ledger.py"), "w") as f:
        f.write("def post_entry(x):\n    return x\n")
    with open(os.path.join(root, "src", "unrelated.py"), "w") as f:
        f.write("def helper():\n    return 1\n")
    with open(os.path.join(root, "docs", "adr", "0007-postgres.md"), "w") as f:
        f.write(ADR)
    with open(os.path.join(root, "docs", "issues", "issue_42_ledger.md"), "w") as f:
        f.write(ISSUE)
    if with_git:
        env = dict(os.environ, GIT_AUTHOR_NAME="Real Author", GIT_AUTHOR_EMAIL="ra@example.com",
                   GIT_COMMITTER_NAME="Real Author", GIT_COMMITTER_EMAIL="ra@example.com",
                   GIT_AUTHOR_DATE="2025-03-04T05:06:07+00:00", GIT_COMMITTER_DATE="2025-03-04T05:06:07+00:00")
        for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "commit", "-q", "-m", "feat: adopt PostgreSQL ledger store instead of SQLite"]):
            subprocess.run(cmd, cwd=root, env=env, check=True, capture_output=True)
    else:
        with open(os.path.join(root, "commits.json"), "w") as f:
            json.dump([
                {"sha": "a" * 40, "author": "fixture_dev", "date": "2025-01-01T00:00:00Z",
                 "message": "feat: switch to PostgreSQL ledger", "files": ["src/ledger.py"]},
                {"sha": "b" * 40, "message": "incomplete entry without author/date"},
            ], f)


class LocalIngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = Database(os.path.join(self.tmp, "t.db"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ingest(self, with_git):
        root = os.path.join(self.tmp, "ledger_service")
        _make_repo(root, with_git)
        return LiveGitHubIngestor(self.db).ingest_local_directory(root)

    def _rows(self, sql, *args):
        with self.db.get_connection() as conn:
            return [dict(r) for r in conn.execute(sql, args)]

    def test_fixture_mode_uses_only_declared_data(self):
        stats = self._ingest(with_git=False)
        self.assertEqual(stats["commit_source"], "commits.json")
        self.assertEqual(stats["commits_ingested"], 1, "incomplete fixture entries must be skipped")
        issue = self._rows("SELECT * FROM events WHERE source_type = 'github_issue'")
        self.assertEqual([e["source_id"] for e in issue], ["42"])
        self.assertEqual(issue[0]["author"], "unknown")
        authors = {e["author"] for e in self._rows("SELECT author FROM events")}
        self.assertFalse(authors & {"sarah_chen", "alex_rodriguez"}, authors)

    def test_git_mode_reads_real_authors_and_dates(self):
        if shutil.which("git") is None:
            self.skipTest("git not installed")
        stats = self._ingest(with_git=True)
        self.assertEqual(stats["commit_source"], "git")
        adr = self._rows("SELECT author, ts FROM events WHERE source_type = 'adr'")[0]
        self.assertEqual(adr["ts"][:10], "2025-03-04")
        self.assertIn("real", adr["author"].lower())

    def test_local_citations_are_not_fake_github_links(self):
        self._ingest(with_git=False)
        urls = [e["source_url"] for e in self._rows("SELECT source_url FROM events")]
        self.assertTrue(urls)
        for u in urls:
            self.assertFalse(u.startswith("https://github.com/local/"), u)
            self.assertTrue(u.startswith("local://ledger_service/"), u)

    def test_adr_is_linked_only_to_files_it_mentions(self):
        self._ingest(with_git=False)
        rows = self._rows("""SELECT e.canonical_path FROM decisions d
                             JOIN decision_artifacts da ON da.decision_id = d.decision_id
                             JOIN entities e ON e.entity_id = da.entity_id
                             WHERE d.title LIKE '%PostgreSQL for the ledger%'""")
        paths = {r["canonical_path"] for r in rows}
        self.assertIn("src/ledger.py", paths)  # the file the ADR names
        self.assertNotIn("src/unrelated.py", paths)
        self.assertFalse(any("helper" in p for p in paths), paths)

    def test_reingest_is_idempotent_and_grounded(self):
        self._ingest(with_git=False)
        first = self._rows("SELECT COUNT(*) AS n FROM decisions")[0]["n"]
        LiveGitHubIngestor(self.db).ingest_local_directory(os.path.join(self.tmp, "ledger_service"), clear_existing=False)
        self.assertEqual(self._rows("SELECT COUNT(*) AS n FROM decisions")[0]["n"], first)
        self.assertEqual(self._rows("SELECT COUNT(*) AS n FROM v_ungrounded_decisions")[0]["n"], 0)


if __name__ == "__main__":
    unittest.main()
