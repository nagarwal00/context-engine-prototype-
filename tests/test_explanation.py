"""
Tests for Evidence-Aware Explanation Output and Sentence Support Verification (Step 3.3)
Verifies:
- Explanation payload structure per decision (decision, lifecycle_state, needs_review, evidence_assessment.label,
  direct_support, indirect_support, missing_corroboration, conflicting_evidence).
- Evidence item structure (source_link, url_format_ok, relevant_passage, author, date, relation, source_group).
- Passage presence in direct support.
- Sentence-level support check flags unsupported statements (claim support rate).
- Decoupled url_format_ok (URL starts with http/https) not conflated with correctness.
- Abstention payload structure on insufficient evidence.
- API endpoints /api/explain and /api/evidence conform to Step 3.3.
"""
import os
import tempfile
import unittest
from pathlib import Path

from backend.db import Database
from backend.models import Decision, Event, Entity, DecisionClaim, ClaimEvidence
from backend.seed_data import populate_seed_data
from backend.api import APIHandler
from backend.engine.explanation import (
    ExplanationGenerator,
    build_decision_evidence_block,
    verify_sentence_support,
    extract_content_tokens,
    split_into_sentences
)


class TestExplanationOutput(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_explanation.db")
        self.db = Database(self.db_path)
        populate_seed_data(self.db)
        self.api = APIHandler(self.db)
        self.gen = ExplanationGenerator(self.db)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_explain_decision_output_structure(self):
        """Verify explain_decision returns the required Step 3.3 structure."""
        res = self.gen.explain_decision("dec_thermal_pid_accepted")
        self.assertEqual(res["status"], "grounded")

        # Top-level required fields
        self.assertIn("decision", res)
        self.assertIn("lifecycle_state", res)
        self.assertIn("needs_review", res)
        self.assertIn("evidence_assessment", res)
        self.assertIn("direct_support", res)
        self.assertIn("indirect_support", res)
        self.assertIn("missing_corroboration", res)
        self.assertIn("conflicting_evidence", res)
        self.assertIn("statements", res)
        self.assertIn("unsupported_sentences", res)
        self.assertIn("claim_support_rate", res)

        # Decision dict structure
        dec = res["decision"]
        self.assertEqual(dec["decision_id"], "dec_thermal_pid_accepted")
        self.assertIn("title", dec)
        self.assertIn("rationale", dec)
        self.assertIn("made_by", dec)
        self.assertIn("made_at", dec)

        # Assessment label
        self.assertIn("label", res["evidence_assessment"])
        self.assertIn(res["evidence_assessment"]["label"], ["strong", "moderate", "weak", "insufficient", "contradicted"])

        # Types
        self.assertIsInstance(res["lifecycle_state"], str)
        self.assertIsInstance(res["needs_review"], bool)
        self.assertIsInstance(res["direct_support"], list)
        self.assertIsInstance(res["indirect_support"], list)
        self.assertIsInstance(res["missing_corroboration"], list)
        self.assertIsInstance(res["conflicting_evidence"], list)

    def test_explain_artifact_output_structure(self):
        """Verify explain_artifact returns the required Step 3.3 structure."""
        res = self.gen.explain_artifact("src/thermal/control.py::regulate_temperature")
        self.assertEqual(res["status"], "grounded")

        self.assertIn("decision", res)
        self.assertIn("lifecycle_state", res)
        self.assertIn("needs_review", res)
        self.assertIn("evidence_assessment", res)
        self.assertIn("direct_support", res)
        self.assertIn("indirect_support", res)
        self.assertIn("missing_corroboration", res)
        self.assertIn("conflicting_evidence", res)
        self.assertIn("statements", res)
        self.assertIn("unsupported_sentences", res)
        self.assertIn("claim_support_rate", res)
        self.assertIn("chain", res)

        # Verify chain blocks have step-level evidence structure
        for step in res["chain"]:
            self.assertIn("decision", step)
            self.assertIn("lifecycle_state", step)
            self.assertIn("needs_review", step)
            self.assertIn("evidence_assessment", step)
            self.assertIn("direct_support", step)
            self.assertIn("indirect_support", step)

    def test_evidence_item_fields_and_passage_presence(self):
        """Verify each evidence item contains source link, passage, author, date, relation, source group."""
        res = self.gen.explain_decision("dec_thermal_pid_accepted")
        self.assertTrue(len(res["direct_support"]) > 0, "Expected direct support evidence items")

        for item in res["direct_support"]:
            self.assertIn("source_link", item)
            self.assertIn("url_format_ok", item)
            self.assertIsInstance(item["url_format_ok"], bool)
            self.assertIn("relevant_passage", item)
            self.assertIn("author", item)
            self.assertIn("date", item)
            self.assertIn("relation", item)
            self.assertEqual(item["relation"], "direct")
            self.assertIn("source_group", item)

            # URL format check: true if starts with http/https, never conflated with truth
            if item["source_link"] and item["source_link"].startswith(("http://", "https://")):
                self.assertTrue(item["url_format_ok"])
            else:
                self.assertFalse(item["url_format_ok"])

            # Passage presence: relevant passage must be a non-empty string for seeded items
            self.assertTrue(bool(item["relevant_passage"]), f"Missing relevant_passage in direct support item {item}")

    def test_sentence_level_support_check_all_supported(self):
        """Verify sentence-level support check passes when text matches evidence passages."""
        evidence_items = [
            {
                "event_id": "ev_01",
                "source_link": "https://github.com/acme-eng/repo/pull/42",
                "relevant_passage": "We replace deadband threshold control with discrete PID control loop for thermal stability.",
                "title": "PR #42: Replace deadband with PID control"
            }
        ]
        text = "We replace deadband control with discrete PID control loop for thermal stability."
        statements, unsupported, rate = verify_sentence_support(text, evidence_items)

        self.assertEqual(len(statements), 1)
        self.assertTrue(statements[0]["supported"])
        self.assertFalse(statements[0]["flagged_unsupported"])
        self.assertEqual(len(unsupported), 0)
        self.assertEqual(rate, 1.0)

    def test_sentence_level_support_flags_unsupported_statement(self):
        """Verify sentence-level support check flags unsupported/hallucinated sentences."""
        evidence_items = [
            {
                "event_id": "ev_01",
                "source_link": "https://github.com/acme-eng/repo/pull/42",
                "relevant_passage": "We replace deadband threshold control with discrete PID control loop.",
                "title": "PR #42: Replace deadband with PID control"
            }
        ]
        # Two sentences: first supported, second fabricated
        text = (
            "We replace deadband control with discrete PID control loop.\n\n"
            "The thermal subsystem now utilizes quantum annealing neural networks for cryogenic cooling."
        )
        statements, unsupported, rate = verify_sentence_support(text, evidence_items)

        self.assertEqual(len(statements), 2)
        # First sentence is supported
        self.assertTrue(statements[0]["supported"])
        self.assertFalse(statements[0]["flagged_unsupported"])

        # Second sentence is flagged unsupported
        self.assertFalse(statements[1]["supported"])
        self.assertTrue(statements[1]["flagged_unsupported"])
        self.assertEqual(len(unsupported), 1)
        self.assertIn("quantum annealing", unsupported[0])

        # Claim support rate should be 1/2 = 0.5
        self.assertEqual(rate, 0.5)

    def test_abstention_output_structure_on_insufficient_evidence(self):
        """Verify abstention response includes required decision context and assessment."""
        # Create a decision with no evidence (insufficient)
        dec_id = "dec_synthetic_unsupported"
        d = Decision(
            decision_id=dec_id,
            title="Synthetic Decision with No Evidence",
            state="proposed",
            rationale="Rationale without corroborating evidence.",
            made_by="developer_test",
            made_at="2026-03-01T10:00:00Z",
            repo="acme-eng/thermal-control-system",
            evidence_event_ids=[]
        )
        self.db.save_decision(d)

        res = self.gen.explain_decision(dec_id)
        self.assertEqual(res["status"], "insufficient_evidence")
        self.assertIn("Insufficient evidence recorded", res["message"])

        # Must still return decision context & evidence assessment
        self.assertIn("decision", res)
        self.assertEqual(res["decision"]["decision_id"], dec_id)
        self.assertEqual(res["lifecycle_state"], "proposed")
        self.assertTrue(res["needs_review"])
        self.assertEqual(res["evidence_assessment"]["label"], "insufficient")
        self.assertEqual(res["direct_support"], [])
        self.assertIn("missing_corroboration", res)

    def test_api_explain_endpoint_returns_step_3_3_payload(self):
        """Verify GET /api/explain returns Step 3.3 payload via APIHandler."""
        res = self.api.handle_get("/api/explain", {"artifact": ["src/thermal/control.py::regulate_temperature"]})
        self.assertEqual(res["status"], "success")
        data = res["data"]

        self.assertIn("lifecycle_state", data)
        self.assertIn("needs_review", data)
        self.assertIn("evidence_assessment", data)
        self.assertIn("direct_support", data)
        self.assertIn("indirect_support", data)
        self.assertIn("missing_corroboration", data)
        self.assertIn("conflicting_evidence", data)
        self.assertIn("claim_support_rate", data)

    def test_api_evidence_endpoint_returns_step_3_3_payload(self):
        """Verify GET /api/evidence returns Step 3.3 payload with direct/indirect support."""
        res = self.api.handle_get("/api/evidence", {"decision_id": ["dec_thermal_pid_accepted"]})
        self.assertEqual(res["status"], "success")
        data = res["data"]

        self.assertIn("decision", data)
        self.assertIn("lifecycle_state", data)
        self.assertIn("needs_review", data)
        self.assertIn("evidence_assessment", data)
        self.assertIn("direct_support", data)
        self.assertIn("indirect_support", data)
        self.assertIn("missing_corroboration", data)
        self.assertIn("conflicting_evidence", data)

        # Legacy backward compatibility checks
        self.assertIn("evidence_events", data)
        self.assertIn("discussion_events", data)


if __name__ == "__main__":
    unittest.main()
