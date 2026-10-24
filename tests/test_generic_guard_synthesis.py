"""
Tests for Generic Guard Rule Synthesis (Step 3.2b)
Table-driven unit tests on neutral text (zero domain words) covering:
- Extraction patterns: backticks, import statements, snake_case, CamelCase
- Word-boundary regex behavior
- Path derivation from affected artifacts
- Prevention of rules generated from accepted-only concepts
- Explicit 'must use `X`' require_import extraction
- Invariant: all synthesized rules have status='proposed' and source='synthesized'
"""
import re
import unittest
from backend.models import Decision
from backend.engine.guard_rules import propose_rules_from_decision
from backend.engine.identifiers import (
    extract_identifiers,
    derive_paths_from_artifacts,
    extract_require_import_modules,
    is_module_like
)


class TestGenericGuardSynthesis(unittest.TestCase):

    def test_backticked_spans_in_rejected_alternatives(self):
        """Backticked spans in rejected alternatives synthesize forbid_pattern and forbid_import."""
        dec = Decision(
            decision_id="dec_neutral_compress_01",
            title="Standardize on LZ4 stream framing",
            state="accepted",
            made_by="arch_lead",
            made_at="2026-03-01T12:00:00Z",
            artifacts_affected=["src/storage/stream.py"],
            alternatives_considered=[{
                "description": "Considered using `zstandard` frame dictionary",
                "rejection_reason": "High initialization memory overhead in micro-workers"
            }],
            rationale="Adopt `lz4` for near-zero decompression latency",
            repo="org/neutral-storage"
        )

        rules = propose_rules_from_decision(dec)
        forbid_patterns = [r for r in rules if r.rule_type == "forbid_pattern"]
        forbid_imports = [r for r in rules if r.rule_type == "forbid_import"]

        # Expect zstandard forbidden pattern and import
        self.assertTrue(any("zstandard" in r.rule_id for r in forbid_patterns))
        self.assertTrue(any(r.params.get("module") == "zstandard" for r in forbid_imports))

        for r in rules:
            self.assertEqual(r.status, "proposed", "All synthesized rules must be proposed")
            self.assertEqual(r.source, "synthesized", "Source must be synthesized")

    def test_import_and_require_syntax_extraction(self):
        """Statements like 'from xml_parser import ...' or 'import xml_parser' synthesize forbid_import."""
        dec = Decision(
            decision_id="dec_neutral_xml_02",
            title="Adopt JSON Schema parser",
            state="accepted",
            made_by="eng_dev",
            made_at="2026-03-02T10:00:00Z",
            artifacts_affected=["src/parser/handler.py"],
            alternatives_considered=[{
                "description": "Evaluated from xml_parser import parse_tree",
                "rejection_reason": "Vulnerable to XXE expansion attacks"
            }],
            rationale="Use strict json schema validation for payload safety",
            repo="org/neutral-parser"
        )

        rules = propose_rules_from_decision(dec)
        import_rules = [r for r in rules if r.rule_type == "forbid_import"]
        modules = [r.params.get("module") for r in import_rules]
        self.assertIn("xml_parser", modules)

    def test_snake_case_and_camel_case_concept_extraction(self):
        """snake_case (>=5 chars) and CamelCase tokens in rejected text become forbidden patterns."""
        dec = Decision(
            decision_id="dec_neutral_naming_03",
            title="Clean architecture boundaries",
            state="accepted",
            made_by="eng_dev",
            made_at="2026-03-03T10:00:00Z",
            artifacts_affected=["src/net/router.py"],
            alternatives_considered=[{
                "description": "Rejected custom legacy_encoder and RawSocketTransport wrapper",
                "rejection_reason": "Bypasses TLS encryption boundary"
            }],
            rationale="Route all requests via unified GatewayClient",
            repo="org/neutral-net"
        )

        rules = propose_rules_from_decision(dec)
        pattern_rules = [r for r in rules if r.rule_type == "forbid_pattern"]
        rule_ids = [r.rule_id for r in pattern_rules]

        self.assertTrue(any("legacy_encoder" in rid for rid in rule_ids))
        self.assertTrue(any("RawSocketTransport" in rid for rid in rule_ids))

    def test_word_boundary_regex_behavior(self):
        """Synthesized forbid_pattern regexes have strict \\b word boundaries."""
        dec = Decision(
            decision_id="dec_neutral_boundary_04",
            title="Adopt structured telemetry",
            state="accepted",
            made_by="eng_dev",
            made_at="2026-03-04T10:00:00Z",
            artifacts_affected=["src/telemetry/stats.py"],
            alternatives_considered=[{
                "description": "Reject raw `datadog` statsd metric emissions",
                "rejection_reason": "Vendor lock-in"
            }],
            rationale="Adopt OpenTelemetry standard",
            repo="org/neutral-telemetry"
        )

        rules = propose_rules_from_decision(dec)
        datadog_rule = next((r for r in rules if "datadog" in r.rule_id), None)
        self.assertIsNotNone(datadog_rule)

        regex_pattern = datadog_rule.params["regex"]
        compiled = re.compile(regex_pattern)

        # Whole word matches
        self.assertTrue(compiled.search("import datadog"))
        self.assertTrue(compiled.search("client = datadog.Client()"))
        self.assertTrue(compiled.search("# use datadog here"))

        # Substrings of different tokens do NOT match
        self.assertFalse(compiled.search("datadog_gateway_helper = 1"))
        self.assertFalse(compiled.search("import my_datadog_proxy"))
        self.assertFalse(compiled.search("undatadogged()"))

    def test_path_derivation_from_artifacts(self):
        """Paths are derived from affected artifacts directory and extension, falling back to **/*."""
        # 1. Single artifact
        paths = derive_paths_from_artifacts(["src/auth/token.go"])
        self.assertIn("src/auth/**/*.go", paths)
        self.assertIn("src/auth/*.go", paths)
        self.assertIn("**/token.go", paths)

        # 2. Function entity syntax (split on ::)
        paths_fn = derive_paths_from_artifacts(["src/storage/db.py::connect_pool"])
        self.assertIn("src/storage/**/*.py", paths_fn)
        self.assertIn("**/db.py", paths_fn)

        # 3. None or empty artifacts
        paths_empty = derive_paths_from_artifacts([])
        self.assertEqual(paths_empty, ["**/*"])
        paths_none = derive_paths_from_artifacts(None)
        self.assertEqual(paths_none, ["**/*"])

    def test_no_rule_from_accepted_only_words(self):
        """Tokens present ONLY in accepted title/rationale must NEVER generate forbidden rules."""
        dec = Decision(
            decision_id="dec_neutral_accepted_05",
            title="Adopt snappy compression codec for block chunks",
            state="accepted",
            made_by="eng_dev",
            made_at="2026-03-05T10:00:00Z",
            artifacts_affected=["src/storage/blocks.py"],
            alternatives_considered=[{
                "description": "Rejected `gzip_compressor`",
                "rejection_reason": "High CPU serialization cost"
            }],
            rationale="Snappy achieves optimal throughput on commodity NVMe drives",
            repo="org/neutral-storage"
        )

        rules = propose_rules_from_decision(dec)
        for r in rules:
            # Accepted words must not be forbidden
            self.assertNotIn("snappy", r.rule_id.lower())
            self.assertNotIn("nvme", r.rule_id.lower())

        # Rejected word MUST be forbidden
        self.assertTrue(any("gzip_compressor" in r.rule_id.lower() for r in rules))

    def test_require_import_only_from_explicit_must_use_phrase(self):
        """require_import rules are only synthesized from explicit phrases like 'must use `X`'."""
        # Case A: Explicit phrase
        dec_explicit = Decision(
            decision_id="dec_neutral_must_06",
            title="Crypto standard update",
            state="accepted",
            made_by="sec_officer",
            made_at="2026-03-06T10:00:00Z",
            artifacts_affected=["src/crypto/cipher.py"],
            alternatives_considered=[],
            rationale="All signature verification must use `cryptography` library",
            repo="org/neutral-sec"
        )
        rules_exp = propose_rules_from_decision(dec_explicit)
        req_rules = [r for r in rules_exp if r.rule_type == "require_import"]
        self.assertEqual(len(req_rules), 1)
        self.assertEqual(req_rules[0].params.get("module"), "cryptography")
        self.assertEqual(req_rules[0].polarity, "must")
        self.assertEqual(req_rules[0].source, "synthesized")

        # Case B: Casual mention without 'must use `X`'
        dec_casual = Decision(
            decision_id="dec_neutral_casual_07",
            title="Crypto discussion",
            state="accepted",
            made_by="sec_officer",
            made_at="2026-03-07T10:00:00Z",
            artifacts_affected=["src/crypto/cipher.py"],
            alternatives_considered=[],
            rationale="We discussed cryptography principles with the team",
            repo="org/neutral-sec"
        )
        rules_cas = propose_rules_from_decision(dec_casual)
        req_cas = [r for r in rules_cas if r.rule_type == "require_import"]
        self.assertEqual(len(req_cas), 0, "Casual mention must not synthesize require_import")


if __name__ == "__main__":
    unittest.main()
