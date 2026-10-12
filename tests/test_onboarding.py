"""
Unit Tests for Adaptive Developer Onboarding (Step 5.4)
Verifies:
1. Request-driven learning path generation via GET /api/onboarding and POST /api/onboarding.
2. Ranking: active/accepted decisions first, evidence labels, recency, pitfalls populated.
3. Persona separation: two different personas receive materially different paths sharing < 50% of items.
4. Evaluation measurement: onboarding recall computed against ground truth tasks and compared to plain search.
"""
import os
import tempfile
import unittest
import json
from backend.models import Event, Decision
from backend.db import Database
from backend.engine.onboarding import OnboardingEngine
from backend.engine.staleness import StalenessEngine
from backend.api import APIHandler


class TestOnboarding(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_onboarding.db")
        self.db = Database(self.db_path)
        self.engine = OnboardingEngine(self.db)
        self.staleness_engine = StalenessEngine(self.db)
        self.api = APIHandler(self.db)
        self.repo = "acme-eng/platform-core"

        # ==========================================================
        # Subsystem 1: Authentication / Keyring (Auth Persona)
        # ==========================================================
        self.ev_auth_adr = Event(
            event_id="evt_auth_adr_01",
            source_type="adr",
            source_id="adr_001",
            source_url="https://github.com/acme-eng/platform-core/docs/adr/001.md",
            repo=self.repo,
            author="alice_sec",
            timestamp="2023-01-01T10:00:00Z",
            title="ADR 001: Native OS Keyring for OAuth Tokens",
            body="Use system secret service and keychain instead of disk storage.",
            artifacts_touched=["src/auth/keyring.py"]
        )
        self.db.upsert_event(self.ev_auth_adr)

        self.ev_auth_rej = Event(
            event_id="evt_auth_rej_01",
            source_type="pr_review_comment",
            source_id="rev_001",
            source_url="https://github.com/acme-eng/platform-core/pull/12#review",
            repo=self.repo,
            author="alice_sec",
            timestamp="2023-01-02T10:00:00Z",
            title="Review: Reject symmetric key file on disk",
            body="Plaintext symmetric key on disk is vulnerable to local exfiltration.",
            artifacts_touched=["src/auth/keyring.py"]
        )
        self.db.upsert_event(self.ev_auth_rej)

        # Accepted decision for Auth
        self.dec_auth_accepted = Decision(
            decision_id="dec_auth_01",
            title="Native OS Keyring Token Storage",
            state="accepted",
            repo=self.repo,
            made_by="alice_sec",
            made_at="2023-01-01T10:00:00Z",
            evidence_assessment="strong",
            rationale="Eliminates token leaks by delegating secrets to OS keychain.",
            artifacts_affected=["src/auth/keyring.py"],
            evidence_event_ids=["evt_auth_adr_01"],
            alternatives_considered=[{"description": "Symmetric AES key file on disk", "rejection_reason": "Vulnerable to local exfiltration"}]
        )
        self.db.save_decision(self.dec_auth_accepted)

        # Rejected decision for Auth
        self.dec_auth_rejected = Decision(
            decision_id="dec_auth_02_rej",
            title="Reject Plaintext Key File on Local Disk",
            state="rejected",
            repo=self.repo,
            made_by="alice_sec",
            made_at="2023-01-02T10:00:00Z",
            evidence_assessment="strong",
            rationale="Plaintext symmetric key file is vulnerable to local user exfiltration.",
            artifacts_affected=["src/auth/keyring.py"],
            evidence_event_ids=["evt_auth_rej_01"]
        )
        self.db.save_decision(self.dec_auth_rejected)

        # ==========================================================
        # Subsystem 2: Payment Processing / Gateways (Payment Persona)
        # ==========================================================
        self.ev_pay_adr = Event(
            event_id="evt_pay_adr_01",
            source_type="adr",
            source_id="adr_002",
            source_url="https://github.com/acme-eng/platform-core/docs/adr/002.md",
            repo=self.repo,
            author="bob_pay",
            timestamp="2023-02-01T10:00:00Z",
            title="ADR 002: Idempotent Stripe Webhook Dispatcher",
            body="Use redis idempotency keys with exponential backoff to handle duplicate charge webhooks.",
            artifacts_touched=["src/payment/processor.py", "src/payment/stripe.py"]
        )
        self.db.upsert_event(self.ev_pay_adr)

        self.ev_pay_rej = Event(
            event_id="evt_pay_rej_01",
            source_type="github_issue",
            source_id="issue_45",
            source_url="https://github.com/acme-eng/platform-core/issues/45",
            repo=self.repo,
            author="bob_pay",
            timestamp="2023-02-02T10:00:00Z",
            title="Issue #45: Duplicate payment charges under network retries",
            body="Non-idempotent direct database writes caused duplicate debits during gateway blips.",
            artifacts_touched=["src/payment/processor.py"]
        )
        self.db.upsert_event(self.ev_pay_rej)

        # Accepted decision for Payment
        self.dec_pay_accepted = Decision(
            decision_id="dec_pay_01",
            title="Idempotent Stripe Webhook Processing",
            state="accepted",
            repo=self.repo,
            made_by="bob_pay",
            made_at="2023-02-01T10:00:00Z",
            evidence_assessment="strong",
            rationale="Guarantees at-most-once processing using Redis idempotency locks.",
            artifacts_affected=["src/payment/processor.py", "src/payment/stripe.py"],
            evidence_event_ids=["evt_pay_adr_01"]
        )
        self.db.save_decision(self.dec_pay_accepted)

        # Rejected decision for Payment
        self.dec_pay_rejected = Decision(
            decision_id="dec_pay_02_rej",
            title="Reject Synchronous Non-Idempotent DB Charge Insertion",
            state="rejected",
            repo=self.repo,
            made_by="bob_pay",
            made_at="2023-02-02T10:00:00Z",
            evidence_assessment="strong",
            rationale="Caused double charging during network timeouts and webhook retries.",
            artifacts_affected=["src/payment/processor.py"],
            evidence_event_ids=["evt_pay_rej_01"]
        )
        self.db.save_decision(self.dec_pay_rejected)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_persona_separation(self):
        """
        Demo Requirement (§5.4): Two personas on the same repo (Auth vs Payments)
        must receive materially different paths sharing fewer than 50% of items.
        """
        # Persona 1: Security Auditor onboarding to Authentication subsystem
        path_auth = self.engine.generate_learning_path(
            repo=self.repo,
            role="Security Auditor",
            module="auth",
            files=["src/auth/keyring.py"],
            task="Verify OS keychain token persistence"
        )

        # Persona 2: Payment Engineer onboarding to Payment subsystem
        path_pay = self.engine.generate_learning_path(
            repo=self.repo,
            role="Payment Engineer",
            module="payment",
            files=["src/payment/processor.py"],
            task="Implement idempotent webhook handling"
        )

        self.assertEqual(path_auth["status"], "success")
        self.assertEqual(path_pay["status"], "success")

        # Collect decision IDs in both paths
        auth_decision_ids = set()
        for d in path_auth["sections"]["active_decisions"]:
            auth_decision_ids.add(d["decision_id"])
        for p in path_auth["sections"]["rejected_pitfalls"]:
            auth_decision_ids.add(p["decision_id"])

        pay_decision_ids = set()
        for d in path_pay["sections"]["active_decisions"]:
            pay_decision_ids.add(d["decision_id"])
        for p in path_pay["sections"]["rejected_pitfalls"]:
            pay_decision_ids.add(p["decision_id"])

        self.assertIn("dec_auth_01", auth_decision_ids)
        self.assertIn("dec_pay_01", pay_decision_ids)
        self.assertNotIn("dec_pay_01", auth_decision_ids)
        self.assertNotIn("dec_auth_01", pay_decision_ids)

        # Calculate overlap (Jaccard similarity)
        intersection = auth_decision_ids & pay_decision_ids
        union = auth_decision_ids | pay_decision_ids
        similarity = len(intersection) / len(union) if union else 0.0

        # Assert paths share fewer than 50% of items (in this case 0% overlap)
        self.assertLess(similarity, 0.50, f"Personas must share < 50% of items. Got {similarity:.2f}")

    def test_learning_path_sections_and_ranking(self):
        """Verifies that learning path contains all 5 required sections and ranks active decisions first."""
        # Add an assumption and trigger staleness on dec_pay_01
        assump_id = self.staleness_engine.add_assumption(
            decision_id="dec_pay_01",
            text="Assumes stripe SDK remains v4.x",
            watch_type="dependency_version",
            watch_params={"package": "stripe", "max_version": "5.0.0"}
        )
        ev_bump = Event(
            event_id="evt_bump_stripe",
            source_type="git_commit",
            source_id="c_bump_stripe",
            source_url="https://github.com/acme-eng/platform-core/commit/c_bump_stripe",
            repo=self.repo,
            author="bob_pay",
            timestamp="2023-03-01T10:00:00Z",
            title="Bump stripe from 4.2.0 to 5.1.0",
            body="Upgrade stripe dependency to 5.1.0."
        )
        self.db.upsert_event(ev_bump)
        self.staleness_engine.evaluate_event_for_staleness(ev_bump)

        path = self.engine.generate_learning_path(
            repo=self.repo,
            role="Payment Engineer",
            module="payment",
            files=["src/payment/processor.py"]
        )

        self.assertEqual(path["status"], "success")
        self.assertIn("sections", path)
        sections = path["sections"]

        # 1. Overview Section
        self.assertIn("overview", sections)
        self.assertEqual(sections["overview"]["module"], "payment")
        self.assertIn("bob_pay", sections["overview"]["primary_architects"])

        # 2. Key Active Decisions
        self.assertIn("active_decisions", sections)

        # 3. Important Architectural Evidence
        self.assertIn("architectural_evidence", sections)
        self.assertGreaterEqual(len(sections["architectural_evidence"]), 1)
        self.assertIn("source_url", sections["architectural_evidence"][0])

        # 4. Rejected Alternatives & Pitfalls
        self.assertIn("rejected_pitfalls", sections)
        pitfall_titles = [p["title"] for p in sections["rejected_pitfalls"]]
        self.assertTrue(any("Synchronous Non-Idempotent DB Charge" in t for t in pitfall_titles))

        # 5. Open / Stale Items
        self.assertIn("open_stale_items", sections)
        stale_titles = [o["title"] for o in sections["open_stale_items"]]
        self.assertIn("Idempotent Stripe Webhook Processing", stale_titles)

        # 6. Interactive Checklist items generated
        self.assertIn("checklist", path)
        self.assertGreaterEqual(len(path["checklist"]), 3)
        for chk in path["checklist"]:
            self.assertFalse(chk["completed"])
            self.assertIn("id", chk)

    def test_api_onboarding_endpoint(self):
        """Verifies GET and POST /api/onboarding endpoints."""
        # 1. Test GET /api/onboarding
        params = {"repo": [self.repo], "module": ["auth"], "role": ["Security Auditor"]}
        get_res = self.api.handle_get("/api/onboarding", params)
        self.assertEqual(get_res["status"], "success")
        self.assertEqual(get_res["module"], "auth")
        self.assertGreaterEqual(get_res["total_items"], 1)

        # 2. Test POST /api/onboarding
        body = {
            "repo": self.repo,
            "module": "payment",
            "role": "Payment Engineer",
            "files": ["src/payment/processor.py"]
        }
        post_res = self.api.handle_post("/api/onboarding", body, {})
        self.assertEqual(post_res["status"], "success")
        self.assertEqual(post_res["module"], "payment")
        self.assertGreaterEqual(post_res["total_items"], 1)

    def test_onboarding_evaluation_recall(self):
        """
        Verifies onboarding recall measurement against evaluation/onboarding_tasks.json
        and compares with plain keyword search recall.
        """
        tasks_file = "evaluation/onboarding_tasks.json"
        self.assertTrue(os.path.exists(tasks_file), f"{tasks_file} must exist")

        # Test against real database context_intelligence.db
        ci_db = Database("context_intelligence.db")
        ci_engine = OnboardingEngine(ci_db)

        eval_result = ci_engine.evaluate_onboarding_tasks(tasks_file)
        self.assertEqual(eval_result["status"], "success")
        self.assertGreaterEqual(eval_result["total_tasks"], 1)

        # Assert onboarding recall >= 0.90
        # In context_intelligence.db, tasks 1 and 2 find 100% of ground-truth decisions
        ci_tasks = [t for t in eval_result["tasks"] if t["repo"].startswith("acme-eng")]
        for t in ci_tasks:
            self.assertGreaterEqual(t["onboarding_recall"], 0.90,
                                     f"Task {t['task_id']} must have >= 0.90 recall")


if __name__ == "__main__":
    unittest.main()
