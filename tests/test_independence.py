"""
Tests for Step 3.1: Source Independence and Claim-Level Evidence
Verifies:
1. Same-thread: 5 comments/reviews in one PR thread count as 1 independent source.
2. ADR + PR: An ADR file plus a separate PR discussion count as 2 independent sources.
3. Commit + PR: A commit belonging to a PR and the PR count as 1 independent source; standalone commit is commit:<sha>.
4. Duplicate-copy: Body with identical normalized text or >80% token overlap maps to original event's source group (1 source).
5. Passage extraction: exact offsets slice equality, threshold cutoff, contradiction cues.
6. DB persistence: migration 003, DecisionClaim, ClaimEvidence, foreign key cascading, and CHECK constraints.
"""
import os
import tempfile
import unittest
import sqlite3

from backend.models import Event, Decision, DecisionClaim, ClaimEvidence
from backend.db import Database
from backend.engine.independence import (
    independence_key,
    extract_best_passage,
    extract_claims_from_decision,
    link_claim_to_event,
    calculate_independent_sources,
    get_independent_source_count,
    tokenize_content_words
)


class TestSourceIndependence(unittest.TestCase):

    def test_same_thread_counts_as_one_source(self):
        """5 comments in one PR thread count as 1 independent source, regardless of different authors."""
        repo = "acme/backend"
        events = [
            Event(
                event_id=f"evt_comment_{i}",
                source_type="pr_review_comment",
                source_id=f"comm_{i}",
                source_url=f"https://github.com/{repo}/pull/42#discussion_r{100+i}",
                repo=repo,
                author=f"engineer_{i}",
                title=f"Review on PR #42 by engineer_{i}",
                body=f"Comment {i}: SQLite WAL mode provides sufficient write concurrency for our current load.",
                raw_metadata={"pr_number": 42, "comment_id": f"comm_{i}"}
            )
            for i in range(1, 6)
        ]

        claim = DecisionClaim(
            claim_id="clm_wal_1",
            decision_id="dec_wal",
            claim_type="rationale",
            text="SQLite WAL mode provides sufficient write concurrency."
        )

        claim_evidences = [link_claim_to_event(claim, ev, all_events=events) for ev in events]

        # All 5 comments must map to the same source group
        for ce in claim_evidences:
            self.assertEqual(ce.source_group, f"thread:{repo}#42")

        groups = calculate_independent_sources(claim_evidences)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups, {f"thread:{repo}#42"})
        self.assertEqual(get_independent_source_count(claim_evidences), 1)

    def test_adr_plus_pr_counts_as_two_sources(self):
        """An ADR plus a separate PR discussion count as 2 independent sources."""
        repo = "acme/core"
        adr_event = Event(
            event_id="evt_adr_001",
            source_type="adr",
            source_id="docs/adr/0001-storage.md",
            source_url=f"https://github.com/{repo}/blob/main/docs/adr/0001-storage.md",
            repo=repo,
            author="lead_arch",
            title="ADR 0001: SQLite storage architecture",
            body="We use SQLite as embedded database to minimize operational complexity.",
            raw_metadata={"file_path": "docs/adr/0001-storage.md"}
        )

        pr_event = Event(
            event_id="evt_pr_55",
            source_type="github_pr",
            source_id="55",
            source_url=f"https://github.com/{repo}/pull/55",
            repo=repo,
            author="contributor_1",
            title="PR #55: Implement embedded storage engine",
            body="Switching backend to SQLite database to eliminate external daemon dependencies.",
            raw_metadata={"pr_number": 55}
        )

        events = [adr_event, pr_event]
        claim = DecisionClaim(
            claim_id="clm_storage_1",
            decision_id="dec_storage",
            claim_type="rationale",
            text="Use SQLite embedded storage to minimize operational dependencies."
        )

        claim_evidences = [link_claim_to_event(claim, ev, all_events=events) for ev in events]

        self.assertEqual(claim_evidences[0].source_group, f"doc:{repo}:docs/adr/0001-storage.md")
        self.assertEqual(claim_evidences[1].source_group, f"thread:{repo}#55")

        groups = calculate_independent_sources(claim_evidences)
        self.assertEqual(len(groups), 2)
        self.assertEqual(get_independent_source_count(claim_evidences), 2)

    def test_commit_and_pr_counts_as_one_source(self):
        """A commit belonging to PR #77 and PR #77 itself count as 1 independent source."""
        repo = "acme/service"
        pr_event = Event(
            event_id="evt_pr_77",
            source_type="github_pr",
            source_id="77",
            source_url=f"https://github.com/{repo}/pull/77",
            repo=repo,
            author="dev_a",
            title="PR #77: Use token bucket rate limiting",
            body="Implements token bucket algorithm for API throttling.",
            raw_metadata={"pr_number": 77, "commit_shas": ["a1b2c3d4e5"]}
        )

        commit_event = Event(
            event_id="evt_git_a1b2c3",
            source_type="git_commit",
            source_id="a1b2c3d4e5",
            source_url=f"https://github.com/{repo}/commit/a1b2c3d4e5",
            repo=repo,
            author="dev_a",
            title="Add token bucket limiter (#77)",
            body="Commit message mentioning PR #77 for throttling.",
            raw_metadata={"pr_number": 77}
        )

        events = [pr_event, commit_event]
        claim = DecisionClaim(
            claim_id="clm_rate_1",
            decision_id="dec_rate",
            claim_type="rationale",
            text="Token bucket rate limiting algorithm for throttling."
        )

        ce_pr = link_claim_to_event(claim, pr_event, all_events=events)
        ce_commit = link_claim_to_event(claim, commit_event, all_events=events)

        self.assertEqual(ce_pr.source_group, f"thread:{repo}#77")
        self.assertEqual(ce_commit.source_group, f"thread:{repo}#77")

        groups = calculate_independent_sources([ce_pr, ce_commit])
        self.assertEqual(len(groups), 1)

        # Standalone commit without PR keys by commit:<sha>
        standalone_commit = Event(
            event_id="evt_git_solo",
            source_type="git_commit",
            source_id="f9e8d7c6b5",
            source_url=f"https://github.com/{repo}/commit/f9e8d7c6b5",
            repo=repo,
            author="dev_b",
            title="Refactor auth headers without PR",
            body="Quick fix directly committed to main."
        )
        self.assertEqual(independence_key(standalone_commit), "commit:f9e8d7c6b5")

    def test_duplicate_copy_maps_to_original_source_group(self):
        """Quoted or copied text (>80% token overlap) maps to original event's source group."""
        repo = "acme/platform"
        original_event = Event(
            event_id="evt_issue_10",
            source_type="github_issue",
            source_id="10",
            source_url=f"https://github.com/{repo}/issues/10",
            repo=repo,
            author="alice",
            title="Issue #10: Database migration strategy",
            body="We decided to adopt SQLite WAL mode because of zero external service dependencies and predictable performance.",
            raw_metadata={"issue_number": 10}
        )

        # Copied verbatim into a doc or wiki by someone else
        copied_event = Event(
            event_id="evt_doc_copy",
            source_type="doc",
            source_id="wiki/architecture_notes.md",
            source_url=f"https://github.com/{repo}/blob/main/wiki/architecture_notes.md",
            repo=repo,
            author="bob",
            title="Wiki architecture notes",
            body="Quote from Alice: We decided to adopt SQLite WAL mode because of zero external service dependencies and predictable performance.",
            raw_metadata={"file_path": "wiki/architecture_notes.md"}
        )

        all_events = [original_event, copied_event]
        orig_key = independence_key(original_event, all_events=all_events)
        copy_key = independence_key(copied_event, all_events=all_events)

        self.assertEqual(orig_key, f"thread:{repo}#10")
        self.assertEqual(copy_key, orig_key)

        claim = DecisionClaim(
            claim_id="clm_1",
            decision_id="dec_1",
            claim_type="rationale",
            text="SQLite WAL mode zero external service dependencies."
        )
        ce1 = link_claim_to_event(claim, original_event, all_events=all_events)
        ce2 = link_claim_to_event(claim, copied_event, all_events=all_events)

        self.assertEqual(calculate_independent_sources([ce1, ce2]), {f"thread:{repo}#10"})
        self.assertEqual(get_independent_source_count([ce1, ce2]), 1)


class TestPassageExtraction(unittest.TestCase):

    def test_passage_extraction_exact_offsets(self):
        claim_text = "We chose SQLite because it has zero external dependencies."
        event_text = (
            "Architecture Review Summary.\n"
            "We evaluated several storage layers including PostgreSQL and Redis.\n"
            "We chose SQLite because it has zero external dependencies and runs in-process.\n"
            "Deployment will proceed next week."
        )

        passage, start, end, relation = extract_best_passage(claim_text, event_text, threshold=0.25)
        self.assertIsNotNone(passage)
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertEqual(relation, "direct")

        # Mechanical verification: event_text[start:end] must exactly equal passage
        self.assertEqual(event_text[start:end], passage)
        self.assertIn("We chose SQLite because it has zero external dependencies", passage)

    def test_passage_extraction_below_threshold_returns_indirect(self):
        claim_text = "Implement quantum entanglement encryption for inter-pod RPC."
        event_text = "Refactored CSS stylesheet margins and button colors for the navbar."

        passage, start, end, relation = extract_best_passage(claim_text, event_text, threshold=0.25)
        self.assertIsNone(passage)
        self.assertIsNone(start)
        self.assertIsNone(end)
        self.assertEqual(relation, "indirect")

    def test_contradiction_detection(self):
        claim_text = "We adopted Redis caching for low latency lookup."
        event_text = "Performance benchmarks showed Redis caching was rejected because it caused high memory bottlenecks and operational failure."

        passage, start, end, relation = extract_best_passage(claim_text, event_text, threshold=0.2)
        self.assertIsNotNone(passage)
        self.assertEqual(relation, "contradicting")


class TestDatabaseClaimsPersistence(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Database(self.tmp.name)

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            try:
                os.remove(self.tmp.name)
            except Exception:
                pass

    def test_decision_claims_and_evidence_lifecycle(self):
        # 1. Insert event
        ev = Event(
            event_id="evt_test_adr",
            source_type="adr",
            source_id="docs/adr/0002.md",
            source_url="https://github.com/org/repo/blob/main/docs/adr/0002.md",
            repo="org/repo",
            author="architect",
            title="ADR 0002: Storage Layer",
            body="We choose SQLite for local persistence.",
            raw_metadata={"file_path": "docs/adr/0002.md"}
        )
        self.db.upsert_event(ev)

        # 2. Save decision with rationale and alternative
        dec = Decision(
            decision_id="dec_test_claims",
            title="Choose SQLite",
            state="accepted",
            evidence_assessment="strong",
            rationale="We choose SQLite for local persistence.",
            alternatives_considered=[{"description": "Redis", "rejection_reason": "too complex"}],
            evidence_event_ids=["evt_test_adr"],
            repo="org/repo"
        )
        self.db.save_decision(dec)

        # 3. Claims must be automatically extracted and persisted
        claims = self.db.get_claims_for_decision("dec_test_claims")
        self.assertGreaterEqual(len(claims), 2)
        claim_types = {c.claim_type for c in claims}
        self.assertIn("rationale", claim_types)
        self.assertIn("alternative_rejected", claim_types)

        # 4. Check claim evidence records
        all_ce = self.db.get_all_claim_evidence_for_decision("dec_test_claims")
        self.assertGreaterEqual(len(all_ce), 1)
        rat_ce = [r for r in all_ce if r["claim_type"] == "rationale"][0]
        self.assertEqual(rat_ce["event_id"], "evt_test_adr")
        self.assertEqual(rat_ce["source_group"], "doc:org/repo:docs/adr/0002.md")
        self.assertEqual(rat_ce["relation"], "direct")
        self.assertIsNotNone(rat_ce["passage_text"])

    def test_check_constraints_enforced(self):
        # Invalid claim_type
        invalid_claim = DecisionClaim(
            claim_id="clm_bad",
            decision_id="dec_none",
            claim_type="magical_belief",
            text="Non-conforming claim"
        )
        with self.assertRaises(ValueError):
            invalid_claim.validate()

        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO decision_claims (claim_id, decision_id, claim_type, text) VALUES (?, ?, ?, ?)",
                    ("clm_bad", "dec_none", "invalid_type", "Bad text")
                )

        # Invalid claim relation
        invalid_ce = ClaimEvidence(
            claim_id="clm_ok",
            event_id="evt_ok",
            relation="vague_maybe",
            source_group="thread:repo#1"
        )
        with self.assertRaises(ValueError):
            invalid_ce.validate()

        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO claim_evidence (claim_id, event_id, relation, source_group) VALUES (?, ?, ?, ?)",
                    ("clm_ok", "evt_ok", "vague_maybe", "thread:repo#1")
                )


if __name__ == "__main__":
    unittest.main()
