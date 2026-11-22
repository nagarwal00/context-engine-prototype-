"""
Extractor precision regressions (audit fixes ALG-01, ALG-02, ALG-03).
Examples are synthetic and written for this test — not taken from WhyBench.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import Database
from backend.engine.extractor import DecisionExtractor
from backend.ingestion.adr_adapter import ADRAdapter
from backend.ingestion.identity import IdentityResolver
from backend.models import Event


class ExtractorPrecisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.tmp.name, "x.db"))
        self.ex = DecisionExtractor(self.db)
        self.n = 0

    def tearDown(self):
        self.tmp.cleanup()

    def _extract(self, title, body="", source_type="git_commit"):
        self.n += 1
        ev = Event(event_id=f"e{self.n}", source_type=source_type, source_id=f"s{self.n}", repo="t/r",
                   author="a", timestamp="2026-01-01T00:00:00Z", title=title, body=body,
                   artifacts_touched=["src/app.py"])
        return self.ex.extract_from_event_bundle("b", [ev], "t/r", [])

    def test_cosmetic_changes_are_not_architectural_decisions(self):
        for msg in ("feat: change login button color to blue", "Implement tooltip on hover",
                    "support dark mode toggle in settings page"):
            self.assertEqual(self._extract(msg), [], msg)

    def test_architectural_changes_are_still_extracted(self):
        for msg in ("Implement exponential backoff with jitter for payment API retries",
                    "feat: add Redis cache layer for session lookups",
                    "We decided to drop the XML exporter"):
            decs = self._extract(msg)
            self.assertEqual(len(decs), 1, msg)
            self.assertEqual(decs[0].state, "accepted")

    def test_approval_comment_mentioning_reject_is_not_a_rejection(self):
        decs = self._extract("Review on PR #3: looks good",
                             "LGTM. The validator correctly rejects empty strings.", "pr_review_comment")
        self.assertFalse(any(d.state == "rejected" for d in decs))

    def test_explicit_rejection_comment_is_rejected(self):
        decs = self._extract("Review on PR #4: polling",
                             "We reject this approach: polling every second burns the API quota.",
                             "pr_review_comment")
        self.assertEqual([d.state for d in decs], ["rejected"])


class ADRStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db = Database(os.path.join(self.tmp.name, "x.db"))
        self.adapter = ADRAdapter(db, IdentityResolver(db))

    def tearDown(self):
        self.tmp.cleanup()

    def _status(self, text):
        md = f"# ADR 9: Thing\n\n## Status\n{text}\n\n## Context\nc\n\n## Decision\nd\n"
        return self.adapter.parse_nygard_adr(md)["status"]

    def test_status_parsing(self):
        self.assertEqual(self._status("Accepted"), "accepted")
        self.assertEqual(self._status("Not accepted"), "rejected")
        self.assertEqual(self._status("Rejected"), "rejected")
        self.assertEqual(self._status("Superseded by ADR 12 (previously accepted)"), "superseded")


if __name__ == "__main__":
    unittest.main()
