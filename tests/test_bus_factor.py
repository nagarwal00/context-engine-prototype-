"""
Unit Tests for Bus Factor & Knowledge Concentration (Step 5.3)
Verifies:
1. Module with quiet architect (1 commit, but all important ADRs/decisions) has bus factor = 1 and high concentration risk.
2. Module with prolific committer (50 commits, but distributed collaborative decisions) has low/medium risk.
3. Module B (quiet architect) ranks higher in concentration risk than Module A (prolific committer).
4. Raw commits do NOT inflate knowledge scores.
5. GET /api/bus-factor returns correct structure, doc coverage, and onboarding hints.
"""
import os
import tempfile
import unittest
from backend.models import Event, Decision
from backend.db import Database
from backend.engine.bus_factor import BusFactorEngine
from backend.api import APIHandler


class TestBusFactor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_bus_factor.db")
        self.db = Database(self.db_path)
        self.engine = BusFactorEngine(self.db)
        self.api = APIHandler(self.db)
        self.repo = "org/core-infra"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_prolific_committer_vs_quiet_architect(self):
        """
        Tests key requirement: A prolific committer pushing 50 commits with distributed collaborative
        decisions must have lower concentration risk than a quiet architect pushing 1 commit who
        authored all critical ADRs and decisions alone.
        """
        # ==========================================================
        # Module A: 'analytics' (Prolific Committer: alice_committer)
        # alice pushed 50 commits to src/analytics/collector.py
        # BUT decisions are collaboratively shared:
        # dec_a1 authored by bob_dev, reviewed by dave_reviewer
        # dec_a2 authored by charlie_dev, reviewed by dave_reviewer
        # ==========================================================
        # 50 commits by alice_committer
        for i in range(50):
            ev = Event(
                event_id=f"evt_a_commit_{i}",
                source_type="git_commit",
                source_id=f"c_a_{i}",
                source_url=f"https://github.com/org/core-infra/commit/c_a_{i}",
                repo=self.repo,
                author="alice_committer",
                timestamp=f"2023-01-01T{i%24:02d}:00:00Z",
                title=f"Analytics cleanup commit {i}",
                body="Minor refactor / whitespace cleanup in analytics engine",
                artifacts_touched=["src/analytics/collector.py"]
            )
            self.db.upsert_event(ev)

        # Evidence events for Module A decisions (PRs + Reviewers)
        ev_a_pr1 = Event(
            event_id="evt_a_pr_1",
            source_type="github_pr",
            source_id="pr_a_1",
            source_url="https://github.com/org/core-infra/pull/1",
            repo=self.repo,
            author="bob_dev",
            timestamp="2023-01-02T10:00:00Z",
            title="Analytics PR 1",
            body="Architectural design discussion for streaming analytics engine",
            artifacts_touched=["src/analytics/collector.py", "src/analytics/aggregator.py"]
        )
        self.db.upsert_event(ev_a_pr1)

        ev_a_rev1 = Event(
            event_id="evt_a_rev_1",
            source_type="pr_review_comment",
            source_id="rev_a_1",
            source_url="https://github.com/org/core-infra/pull/1#review-1",
            repo=self.repo,
            author="dave_reviewer",
            timestamp="2023-01-02T11:00:00Z",
            title="Review of PR 1",
            body="LGTM, validated buffering thresholds.",
            artifacts_touched=["src/analytics/collector.py"]
        )
        self.db.upsert_event(ev_a_rev1)

        ev_a_pr2 = Event(
            event_id="evt_a_pr_2",
            source_type="github_pr",
            source_id="pr_a_2",
            source_url="https://github.com/org/core-infra/pull/2",
            repo=self.repo,
            author="charlie_dev",
            timestamp="2023-01-03T10:00:00Z",
            title="Analytics PR 2",
            body="Architectural design discussion for analytics buffering system",
            artifacts_touched=["src/analytics/collector.py", "src/analytics/aggregator.py"]
        )
        self.db.upsert_event(ev_a_pr2)

        ev_a_rev2 = Event(
            event_id="evt_a_rev_2",
            source_type="pr_review_comment",
            source_id="rev_a_2",
            source_url="https://github.com/org/core-infra/pull/2#review-2",
            repo=self.repo,
            author="dave_reviewer",
            timestamp="2023-01-03T11:00:00Z",
            title="Review of PR 2",
            body="Approved, good fault isolation.",
            artifacts_touched=["src/analytics/collector.py"]
        )
        self.db.upsert_event(ev_a_rev2)

        # 2 accepted decisions in analytics with multiple participants
        dec_a1 = Decision(
            decision_id="dec_a_01",
            title="Streaming Analytics Pipeline",
            state="accepted",
            repo=self.repo,
            made_by="bob_dev",
            evidence_assessment="strong",
            artifacts_affected=["src/analytics/collector.py", "src/analytics/aggregator.py"],
            evidence_event_ids=["evt_a_pr_1", "evt_a_rev_1"]
        )
        self.db.save_decision(dec_a1)

        dec_a2 = Decision(
            decision_id="dec_a_02",
            title="Batch Buffer Mechanism",
            state="accepted",
            repo=self.repo,
            made_by="charlie_dev",
            evidence_assessment="strong",
            artifacts_affected=["src/analytics/collector.py", "src/analytics/aggregator.py"],
            evidence_event_ids=["evt_a_pr_2", "evt_a_rev_2"]
        )
        self.db.save_decision(dec_a2)

        # ==========================================================
        # Module B: 'security' (Quiet Architect: quinn_architect)
        # quinn pushed only 1 commit, BUT authored all important ADRs and decisions alone
        # ==========================================================
        ev_b_commit = Event(
            event_id="evt_b_commit_01",
            source_type="git_commit",
            source_id="c_b_01",
            source_url="https://github.com/org/core-infra/commit/c_b_01",
            repo=self.repo,
            author="quinn_architect",
            timestamp="2023-01-05T12:00:00Z",
            title="Security enclave initial commit",
            body="Bootstrap security enclave",
            artifacts_touched=["src/security/enclave.py"]
        )
        self.db.upsert_event(ev_b_commit)

        ev_b_adr1 = Event(
            event_id="evt_b_adr_01",
            source_type="adr",
            source_id="adr_001",
            source_url="https://github.com/org/core-infra/docs/adr/001.md",
            repo=self.repo,
            author="quinn_architect",
            timestamp="2023-01-05T12:00:00Z",
            title="ADR 001: Zero-Trust Cryptographic Enclave",
            body="ADR document detailing the strict enclave protocol and key isolation.",
            artifacts_touched=["src/security/enclave.py", "src/security/crypto.py"]
        )
        self.db.upsert_event(ev_b_adr1)

        ev_b_adr2 = Event(
            event_id="evt_b_adr_02",
            source_type="adr",
            source_id="adr_002",
            source_url="https://github.com/org/core-infra/docs/adr/002.md",
            repo=self.repo,
            author="quinn_architect",
            timestamp="2023-01-06T12:00:00Z",
            title="ADR 002: HSM Key Rotation Policy",
            body="ADR document specifying automated hardware security module rotation.",
            artifacts_touched=["src/security/enclave.py", "src/security/crypto.py"]
        )
        self.db.upsert_event(ev_b_adr2)

        dec_b1 = Decision(
            decision_id="dec_b_01",
            title="Zero-Trust Enclave Isolation",
            state="accepted",
            repo=self.repo,
            made_by="quinn_architect",
            evidence_assessment="strong",
            artifacts_affected=["src/security/enclave.py", "src/security/crypto.py"],
            evidence_event_ids=["evt_b_adr_01"]
        )
        self.db.save_decision(dec_b1)

        dec_b2 = Decision(
            decision_id="dec_b_02",
            title="Automated HSM Key Rotation",
            state="accepted",
            repo=self.repo,
            made_by="quinn_architect",
            evidence_assessment="strong",
            artifacts_affected=["src/security/enclave.py", "src/security/crypto.py"],
            evidence_event_ids=["evt_b_adr_02"]
        )
        self.db.save_decision(dec_b2)

        # --- Run Analysis ---
        result = self.engine.analyze_repository(self.repo)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_modules"], 2)

        modules = {m["module"]: m for m in result["modules"]}
        self.assertIn("analytics", modules)
        self.assertIn("security", modules)

        mod_analytics = modules["analytics"]
        mod_security = modules["security"]

        # 1. Assert raw commits did NOT inflate alice_committer's knowledge score
        # alice_committer had 50 commits, but 0 decision authoring or substantive review
        analytics_contributors = {c["contributor"]: c["knowledge_score"] for c in mod_analytics["contributors"]}
        self.assertNotIn("alice_committer", analytics_contributors,
                         "Raw commits must NOT inflate contributor knowledge scores")

        # 2. Quiet architect module has bus factor = 1 and high risk
        self.assertEqual(mod_security["bus_factor"], 1)
        self.assertEqual(mod_security["risk_level"], "high")
        self.assertEqual(mod_security["top_contributor"], "quinn_architect")
        self.assertEqual(mod_security["top_contributor_share"], 1.0)
        self.assertEqual(mod_security["documentation_coverage"], 1.0)
        self.assertEqual(mod_security["single_contributor_share"], 1.0)

        # 3. Analytics module has distributed knowledge across multiple contributors
        self.assertGreaterEqual(mod_analytics["bus_factor"], 1)
        self.assertIn(mod_analytics["risk_level"], ("medium", "low"))
        self.assertLess(mod_analytics["top_contributor_share"], 0.70)
        self.assertEqual(mod_analytics["single_contributor_share"], 0.0)

        # 4. Critical invariant: Module B (quiet architect) must rank ABOVE Module A in concentration risk
        first_module = result["modules"][0]["module"]
        self.assertEqual(first_module, "security",
                         "Quiet architect module with concentrated knowledge must rank higher in risk than prolific committer module")

        # 5. Onboarding transfer hint must be populated for high risk module
        self.assertIn("quinn_architect", mod_security["onboarding_hint"])
        self.assertIn("Concentration risk", mod_security["onboarding_hint"])

    def test_bus_factor_api_endpoint(self):
        """Verifies GET /api/bus-factor authorization and response structure."""
        # Check authorization (default deny / role enforcement)
        ok, code, msg = self.api.check_authorization(
            "GET", "/api/bus-factor", {"authorization": "Bearer viewer_token"}
        )
        self.assertTrue(ok)
        self.assertEqual(code, 200)

        # Insert a single decision
        ev = Event(
            event_id="evt_test_01",
            source_type="adr",
            source_id="adr_test",
            source_url="https://github.com/org/core-infra/docs/adr/test.md",
            repo=self.repo,
            author="lead_dev",
            timestamp="2023-01-01T10:00:00Z",
            title="ADR Test",
            body="ADR documentation",
            artifacts_touched=["src/core/main.py", "src/core/config.py"]
        )
        self.db.upsert_event(ev)

        dec = Decision(
            decision_id="dec_core_01",
            title="Core Architecture",
            state="accepted",
            repo=self.repo,
            made_by="lead_dev",
            evidence_assessment="strong",
            artifacts_affected=["src/core/main.py", "src/core/config.py"],
            evidence_event_ids=["evt_test_01"]
        )
        self.db.save_decision(dec)

        data = self.api.handle_get("/api/bus-factor", {"repo": [self.repo]})
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["repo"], self.repo)
        self.assertGreaterEqual(len(data["modules"]), 1)
        self.assertEqual(data["modules"][0]["module"], "core")
        self.assertEqual(data["modules"][0]["bus_factor"], 1)
        self.assertIn("documentation_coverage", data["modules"][0])
        self.assertIn("onboarding_hint", data["modules"][0])


if __name__ == "__main__":
    unittest.main()
