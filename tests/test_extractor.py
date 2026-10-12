import os
import unittest
from backend.models import Event, Decision
from backend.engine.extractor import is_decision_candidate
from backend.engine.llm_extractor import validate_grounding, LLMDecisionExtractor
from backend.engine.llm_client import LLMClient

class MockLLMClient(LLMClient):
    def __init__(self, canned_response: str = None, is_avail: bool = True):
        super().__init__()
        self.canned_response = canned_response
        self._is_avail = is_avail

    def available(self) -> bool:
        return self._is_avail

    def complete_json(self, prompt: str, system_prompt: str = "") -> str:
        return self.canned_response

class TestExtractor(unittest.TestCase):
    def test_is_decision_candidate_positive_and_negative_examples(self):
        """Tests 10 positive architectural candidates and 10 negative trivial commits."""
        positives = [
            Event("e_p1", "adr", "0001", "http://x", "r", "a", "2026-01-01", "ADR 0001: Stripe Migration", "Migrate to stripe"),
            Event("e_p2", "github_pr", "12", "http://x", "r", "a", "2026-01-01", "feat: migrate to distributed Redis cache", "Replaces local memory cache with Redis cluster", ["src/cache.py"]),
            Event("e_p3", "git_commit", "c1", "http://x", "r", "a", "2026-01-01", "refactor: adopt async event bus instead of sync polling", "Decided to replace polling with event emitter", ["src/bus.py"]),
            Event("e_p4", "github_pr", "15", "http://x", "r", "a", "2026-01-01", "perf: implement connection pooling for PostgreSQL", "Opted for PgBouncer connection pool", ["src/db.py"]),
            Event("e_p5", "pr_review_comment", "r1", "http://x", "r", "a", "2026-01-01", "Review on PR #15", "We should use exponential backoff instead of constant sleep", ["src/net.py"]),
            Event("e_p6", "github_adr", "0002", "http://x", "r", "a", "2026-01-01", "RFC: Use WebSocket stream for invalidation", "Persistent socket connection"),
            Event("e_p7", "git_commit", "c2", "http://x", "r", "a", "2026-01-01", "feat(auth): integrate native OS keyring credentials", "Eliminates plaintext tokens on disk", ["src/auth.py"]),
            Event("e_p8", "github_pr", "20", "http://x", "r", "a", "2026-01-01", "feat: migrate to KVM dirty ring live migration", "Replaces userfaultfd dirty page capture", ["src/vmm.rs"]),
            Event("e_p9", "git_commit", "c3", "http://x", "r", "a", "2026-01-01", "feat: implement vhost-user-net DPDK shared queues", "Agreed to use shared memory queues for line rate packet throughput", ["src/net.rs"]),
            Event("e_p10", "github_pr", "33", "http://x", "r", "a", "2026-01-01", "feat(ext): subprocess isolation for third-party extensions", "Executes extensions in sandboxed subprocess", ["src/ext.go"])
        ]

        negatives = [
            Event("e_n1", "git_commit", "n1", "http://x", "r", "a", "2026-01-01", "Added README", "Added README", ["README.md"]),
            Event("e_n2", "git_commit", "n2", "http://x", "r", "a", "2026-01-01", "Added requirements.txt", "Added requirements.txt", ["requirements.txt"]),
            Event("e_n3", "git_commit", "n3", "http://x", "r", "a", "2026-01-01", "Fix typo in comment", "Fixed spelling typo", ["src/main.py"]),
            Event("e_n4", "git_commit", "n4", "http://x", "r", "a", "2026-01-01", "Merge branch 'main' into feature", "Merge remote-tracking branch", ["src/main.py"]),
            Event("e_n5", "git_commit", "n5", "http://x", "r", "a", "2026-01-01", "Initial commit", "Initial commit", ["README.md"]),
            Event("e_n6", "git_commit", "n6", "http://x", "r", "a", "2026-01-01", "bump version to 1.2.1", "Bump version", ["package.json"]),
            Event("e_n7", "git_commit", "n7", "http://x", "r", "a", "2026-01-01", "Updated .gitignore", "ignore *.pyc", [".gitignore"]),
            Event("e_n8", "git_commit", "n8", "http://x", "r", "a", "2026-01-01", "chore: formatting and lint cleanup", "Run black formatter", ["src/main.py"]),
            Event("e_n9", "git_commit", "n9", "http://x", "r", "a", "2026-01-01", "Update LICENSE", "Update copyright year", ["LICENSE"]),
            Event("e_n10", "git_commit", "n10", "http://x", "r", "a", "2026-01-01", "up", "up", [])
        ]

        self.assertEqual(len(positives), 10)
        self.assertEqual(len(negatives), 10)

        for p in positives:
            self.assertTrue(is_decision_candidate(p), f"Expected positive for: {p.title}")

        for n in negatives:
            self.assertFalse(is_decision_candidate(n), f"Expected negative rejection for: {n.title}")

    def test_validate_grounding_anti_hallucination(self):
        """Asserts that an invented or hallucinated rationale is downgraded to proposed with evidence_assessment=insufficient."""
        events = [
            Event(
                event_id="evt_valid_01",
                source_type="adr",
                source_id="0001",
                source_url="http://example.com/adr1",
                repo="org/repo",
                author="alice",
                timestamp="2026-01-01T00:00:00Z",
                title="Adopt PostgreSQL relational storage",
                body="We require ACID transactional safety for database persistence."
            )
        ]

        # Valid candidate grounded in event
        valid_cand = {
            "title": "Adopt PostgreSQL",
            "state": "accepted",
            "rationale": "We require ACID transactional safety for database persistence.",
            "evidence_event_ids": ["evt_valid_01"],
            "confidence": 0.95
        }
        res_valid = validate_grounding(valid_cand, events)
        self.assertEqual(res_valid["state"], "accepted")

        # Hallucinated candidate with invented rationale not in event
        hallucinated_cand = {
            "title": "Migrate to Cassandra NoSQL",
            "state": "accepted",
            "rationale": "Cassandra provides peer-to-peer gossip protocol with tunable eventual consistency across worldwide datacenter clusters.",
            "evidence_event_ids": ["evt_valid_01"],
            "confidence": 0.95
        }
        res_hal = validate_grounding(hallucinated_cand, events)
        self.assertEqual(res_hal["state"], "proposed", "Hallucinated claim must be downgraded to proposed")
        self.assertEqual(res_hal["evidence_assessment"], "insufficient")
        self.assertLessEqual(res_hal["confidence"], 0.3)
        self.assertEqual(res_hal["review_status"], "pending_review")

        # Candidate with nonexistent event ID
        bad_id_cand = {
            "title": "Unknown decision",
            "state": "accepted",
            "rationale": "Some rationale",
            "evidence_event_ids": ["evt_nonexistent_99"],
            "confidence": 0.95
        }
        res_bad = validate_grounding(bad_id_cand, events)
        self.assertEqual(res_bad["state"], "proposed")
        self.assertEqual(res_bad["evidence_assessment"], "insufficient")
        self.assertEqual(res_bad["review_status"], "pending_review")

    def test_extractor_rejection_cues_from_pr_review(self):
        """Step 4.4: PR review comments with rejection cues must be extracted with state='rejected'."""
        from backend.engine.extractor import DecisionExtractor
        extractor = DecisionExtractor(None)
        rev_ev = Event(
            event_id="evt_rev_01",
            source_type="pr_review_comment",
            source_id="c101",
            source_url="https://github.com/org/repo/pull/1#discussion_r101",
            repo="org/repo",
            author="reviewer_bob",
            timestamp="2026-01-05T12:00:00Z",
            title="Review on PR #1: Reject fixed interval retries",
            body="Fixed 500ms sleep creates thundering herd. We must reject fixed sleep in favor of exponential backoff with full jitter.",
            artifacts_touched=["src/retry.py"]
        )
        decs = extractor.extract_from_event_bundle("Review Bundle", [rev_ev], "org/repo", ["src/retry.py"])
        self.assertEqual(len(decs), 1)
        dec = decs[0]
        self.assertEqual(dec.state, "rejected")
        self.assertIn("evt_rev_01", dec.evidence_event_ids)
        self.assertEqual(dec.confidence, 0.85)
        self.assertIn("Reject fixed interval retries", dec.title)
        self.assertEqual(len(dec.alternatives_considered), 1)

    def test_extractor_pr_and_commit_with_parent_events(self):
        """Step 4.4: Architectural PRs and git commits link parent event IDs into evidence."""
        from backend.engine.extractor import DecisionExtractor
        extractor = DecisionExtractor(None)
        pr_ev = Event(
            event_id="evt_pr_14",
            source_type="github_pr",
            source_id="14",
            source_url="https://github.com/org/repo/pull/14",
            repo="org/repo",
            author="author_alice",
            timestamp="2026-01-06T14:00:00Z",
            title="PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8)",
            body="Adds decorator with decorator-level exponential backoff with full jitter algorithm.",
            artifacts_touched=["src/payments.py"],
            parent_event_ids=["evt_issue_08"]
        )
        decs = extractor.extract_from_event_bundle("PR 14", [pr_ev], "org/repo", ["src/payments.py"])
        self.assertEqual(len(decs), 1)
        dec = decs[0]
        self.assertEqual(dec.state, "accepted")
        self.assertIn("evt_pr_14", dec.evidence_event_ids)
        self.assertIn("evt_issue_08", dec.evidence_event_ids)
        self.assertEqual(dec.confidence, 0.85)

    def test_extractor_filters_trivial_events(self):
        """Step 4.4: Trivial non-decision events return empty extraction and do not invent dummy decisions."""
        from backend.engine.extractor import DecisionExtractor
        extractor = DecisionExtractor(None)
        trivial_ev = Event(
            event_id="evt_triv_01",
            source_type="git_commit",
            source_id="c_triv",
            source_url="https://github.com/org/repo/commit/123",
            repo="org/repo",
            author="dev",
            timestamp="2026-01-07T10:00:00Z",
            title="fix typo in comments",
            body="fix minor spelling typo",
            artifacts_touched=["README.md"]
        )
        decs = extractor.extract_from_event_bundle("Trivial Commit", [trivial_ev], "org/repo", [])
        self.assertEqual(len(decs), 0)

if __name__ == "__main__":
    unittest.main()
