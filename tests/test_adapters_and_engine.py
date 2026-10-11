import os
import tempfile
import unittest
from backend.db import Database
from backend.models import Decision, Event, Entity
from backend.ingestion.git_adapter import GitAdapter
from backend.ingestion.github_adapter import GitHubAdapter
from backend.ingestion.adr_adapter import ADRAdapter
from backend.ingestion.identity import IdentityResolver
from backend.engine.entity_res import EntityResolver
from backend.engine.graph import TemporalGraph
from backend.engine.explanation import ExplanationGenerator
from backend.seed_data import populate_seed_data

class TestAdaptersAndEngine(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_adapters.db")
        self.db = Database(self.db_path)
        self.ident_resolver = IdentityResolver(self.db)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_mechanical_invariant_enforcement(self):
        """Invariant: An accepted decision must have at least one evidence link."""
        dec = Decision(
            decision_id="dec_invalid_01",
            title="Accepted with zero evidence",
            state="accepted",
            made_by="alice",
            made_at="2026-01-01T00:00:00Z",
            artifacts_affected=["src/app.py"],
            alternatives_considered=[],
            rationale="No evidence backing this claim",
            evidence_event_ids=[]
        )
        with self.assertRaises(ValueError):
            self.db.save_decision(dec)

    def test_git_adapter(self):
        """Tests parsing a Git commit and resolving source_url."""
        adapter = GitAdapter(self.db, self.ident_resolver)
        event = adapter.ingest_commit_record(
            repo="acme/service",
            commit_sha="a1b2c3d4e5f67890",
            author_raw="Sarah Chen <sarah.chen@acme.org>",
            timestamp="2026-01-01T12:00:00Z",
            message="feat(core): implement resilient worker loop",
            files_changed=["src/worker.py"]
        )
        self.assertEqual(event.source_type, "git_commit")
        self.assertTrue(event.source_url.startswith("https://github.com/"))
        self.assertEqual(event.artifacts_touched, ["src/worker.py"])
        self.assertEqual(event.author, "sarah_chen")

    def test_github_adapter(self):
        """Tests GitHub issue ingestion and PR parent linkage extraction."""
        adapter = GitHubAdapter(self.db, self.ident_resolver)
        issue_event = adapter.ingest_issue(
            repo="acme/service",
            issue_number=101,
            title="High memory consumption in cache worker",
            body="Investigating memory leaks.",
            author_raw="alex-rodriguez",
            created_at="2026-01-02T10:00:00Z"
        )
        self.assertEqual(issue_event.source_type, "github_issue")
        self.assertEqual(issue_event.source_id, "101")
        self.assertTrue(issue_event.source_url.endswith("/issues/101"))

        pr_event = adapter.ingest_pull_request(
            repo="acme/service",
            pr_number=202,
            title="Fix cache memory leak",
            body="Resolves #101 by flushing periodically. Closes #101",
            author_raw="sarahc-eng",
            created_at="2026-01-03T14:00:00Z",
            merged_at="2026-01-03T16:00:00Z",
            artifacts_touched=["src/cache.py"],
            commit_shas=["a1b2c3d4e5f67890"]
        )
        self.assertEqual(pr_event.source_type, "github_pr")
        self.assertIn("evt_issue_acme_service_101", pr_event.parent_event_ids)

    def test_identity_resolution(self):
        """Tests developer identity alias canonicalization."""
        canonical_1 = self.ident_resolver.resolve("Sarah Chen <sarah.chen@acme.org>")
        canonical_2 = self.ident_resolver.resolve("schen")
        self.assertEqual(canonical_1, canonical_2)
        self.assertEqual(canonical_1, "sarah_chen")

    def test_ast_entity_resolution(self):
        """Tests Python AST function extraction and canonical path naming."""
        code = """def compute_temperature_target(sensor_val, bias=0.5):
    return sensor_val * 1.8 + 32 + bias

def execute_step():
    pass
"""
        resolver = EntityResolver(self.db)
        funcs = resolver.extract_functions_from_python_code(code)
        fn_names = [f[0] for f in funcs]
        self.assertIn("compute_temperature_target", fn_names)
        self.assertIn("execute_step", fn_names)

        ent = resolver.resolve_function_entity(
            repo="acme/service",
            file_path="src/thermal.py",
            function_name="compute_temperature_target"
        )
        self.assertEqual(ent.canonical_path, "src/thermal.py::compute_temperature_target")
        self.assertEqual(ent.entity_type, "function")

    def test_temporal_graph_queries(self):
        """Tests canonical decision chain and evidence trail queries."""
        populate_seed_data(self.db)
        graph = TemporalGraph(self.db)

        # Canonical query 1: decision chain for artifact
        chain = self.db.query_decision_chain_for_artifact(
            "src/thermal/control.py::regulate_temperature"
        )
        self.assertGreaterEqual(len(chain), 2)

        # Canonical query 2: full evidence trail
        trail = self.db.query_full_evidence_trail(chain[0]["decision_id"])
        self.assertIsNotNone(trail["decision"])
        self.assertGreater(len(trail["evidence_events"]), 0)

        # Canonical query 3: timeline slice
        slice_items = self.db.query_timeline_slice("acme-eng/thermal-control-system")
        self.assertGreaterEqual(len(slice_items), 2)

    def test_grounded_explanation_engine(self):
        """Tests synthesis of evidence-grounded explanations and anti-hallucination guarantee."""
        populate_seed_data(self.db)
        engine = ExplanationGenerator(self.db)

        # Known artifact
        result = engine.explain_artifact(
            "src/thermal/control.py::regulate_temperature"
        )
        self.assertEqual(result["status"], "grounded")
        self.assertIn("PID", result["explanation"])
        self.assertGreater(len(result["citations"]), 0)

        # Unknown artifact: Anti-hallucination refusal guarantee
        unknown_res = engine.explain_artifact(
            "src/crypto/quantum_shield.py"
        )
        self.assertEqual(unknown_res["status"], "not_found")
        self.assertIn("No recorded architectural decisions found", unknown_res["explanation"])

if __name__ == "__main__":
    unittest.main()
