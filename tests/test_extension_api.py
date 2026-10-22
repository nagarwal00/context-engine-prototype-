"""
Unit and integration tests for Extension API Contract (Phase 8 / Step 8.0).
Verifies:
1. Stable JSON schemas and schema_version for /api/pr-analysis, /api/file-context, /api/repos/status, /api/findings/feedback.
2. Per-repository isolation (Rule R3).
3. Caching by head SHA on PR analysis.
4. Decision and rejected-alternative context on file/entity queries.
5. Absolute absence of GitHub tokens in any API response (Rule R4).
6. Non-exception responses for unadded repositories ({ "status": "not_added" }).
"""
import os
import shutil
import tempfile
import unittest
import json
from backend.db import Database
from backend.api import APIHandler
from backend.auth.sessions import create_session
from backend.migrations.runner import run_migrations
from tests.helpers_time import iso_z


class TestExtensionAPI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_ext_api.db")
        self.db = Database(self.db_path)

        # Seed users
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO users (user_id, github_id, login, avatar_url, created_at, last_login_at) VALUES (1, 1001, 'alice', 'https://avatar.alice', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
            )
            conn.execute(
                "INSERT INTO users (user_id, github_id, login, avatar_url, created_at, last_login_at) VALUES (2, 1002, 'bob', 'https://avatar.bob', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
            )

            # Seed demo repository
            conn.execute(
                "INSERT INTO repos (repo_full_name, visibility, added_by_user_id, added_at) VALUES ('acme/demo-repo', 'demo', 1, '2026-01-01T00:00:00Z')"
            )

            # Seed private repository for Alice
            conn.execute(
                "INSERT INTO repos (repo_full_name, visibility, added_by_user_id, added_at) VALUES ('alice/secret-vault', 'private', 1, '2026-01-01T00:00:00Z')"
            )
            conn.execute(
                "INSERT INTO repo_access (user_id, repo_full_name, level, verified_at) VALUES (?, ?, ?, ?)",
                (1, 'alice/secret-vault', 'admin', iso_z())
            )

            # Seed decisions
            conn.execute("""
            INSERT INTO decisions (decision_id, repo, title, state, rationale, made_by, made_at, confidence, review_status)
            VALUES ('dec_cache_1', 'acme/demo-repo', 'Use In-Memory LRU Cache', 'accepted',
                    'Avoid external dependency overhead', 'alice', '2026-02-01T00:00:00Z', 0.95, 'confirmed')
            """)
            conn.execute("""
            INSERT INTO decisions (decision_id, repo, title, state, rationale, made_by, made_at, confidence, review_status)
            VALUES ('dec_cache_2', 'acme/demo-repo', 'Reject Redis Cluster', 'rejected',
                    'Redis introduces unacceptable operational latency and memory overhead', 'alice', '2026-02-02T00:00:00Z', 0.90, 'confirmed')
            """)
            conn.execute("""
            INSERT INTO decisions (decision_id, repo, title, state, rationale, made_by, made_at, confidence, review_status)
            VALUES ('dec_vault_1', 'alice/secret-vault', 'Use Hardware HSM for Keys', 'accepted',
                    'FIPS 140-2 Level 3 compliance required', 'alice', '2026-03-01T00:00:00Z', 0.99, 'confirmed')
            """)

            # Seed entities
            conn.execute("""
            INSERT INTO entities (entity_id, entity_type, canonical_path, repo)
            VALUES ('ent_file_1', 'file', 'src/cache.py', 'acme/demo-repo')
            """)
            conn.execute("""
            INSERT INTO entities (entity_id, entity_type, canonical_path, repo)
            VALUES ('ent_func_1', 'function', 'src/cache.py::get_cached_item', 'acme/demo-repo')
            """)
            conn.execute("""
            INSERT INTO entities (entity_id, entity_type, canonical_path, repo)
            VALUES ('ent_vault_file', 'file', 'src/crypto.py', 'alice/secret-vault')
            """)

            # Seed decision artifacts
            conn.execute("""
            INSERT INTO decision_artifacts (decision_id, entity_id, repo_full_name)
            VALUES ('dec_cache_1', 'ent_file_1', 'acme/demo-repo')
            """)
            conn.execute("""
            INSERT INTO decision_artifacts (decision_id, entity_id, repo_full_name)
            VALUES ('dec_cache_2', 'ent_file_1', 'acme/demo-repo')
            """)
            conn.execute("""
            INSERT INTO decision_artifacts (decision_id, entity_id, repo_full_name)
            VALUES ('dec_vault_1', 'ent_vault_file', 'alice/secret-vault')
            """)

            # Seed PR event
            conn.execute("""
            INSERT INTO events (event_id, repo, source_type, source_id, source_url, author, ts, title, body, raw_metadata)
            VALUES ('ev_pr_42', 'acme/demo-repo', 'github_pr', '42', 'https://github.com/acme/demo-repo/pull/42', 'alice',
                    '2026-02-10T12:00:00Z', 'Add high performance caching',
                    'We want to use Redis cache cluster for all operations.',
                    '{"title": "Add Redis caching support", "head_sha": "head_sha_1", "body": "We want to use Redis cache cluster for all operations."}')
            """)

        # Create session tokens for Alice and Bob
        self.alice_raw_token, _ = create_session(self.db, user_id=1, client="extension")
        self.bob_raw_token, _ = create_session(self.db, user_id=2, client="extension")
        self.alice_headers = {"Authorization": f"Bearer {self.alice_raw_token}"}
        self.bob_headers = {"Authorization": f"Bearer {self.bob_raw_token}"}

        self.api = APIHandler(self.db)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_unadded_repo_returns_not_added_status(self):
        """Unadded repository returns clean JSON { status: 'not_added' } without exception."""
        res_pr = self.api.handle_get(
            "/api/pr-analysis",
            {"repo": ["nonexistent/repo"], "number": ["99"]},
            headers=self.alice_headers
        )
        self.assertEqual(res_pr.get("schema_version"), "1.0")
        self.assertEqual(res_pr.get("status"), "not_added")
        self.assertEqual(res_pr.get("repo"), "nonexistent/repo")

        res_file = self.api.handle_get(
            "/api/file-context",
            {"repo": ["nonexistent/repo"], "path": ["src/index.js"]},
            headers=self.alice_headers
        )
        self.assertEqual(res_file.get("schema_version"), "1.0")
        self.assertEqual(res_file.get("status"), "not_added")

    def test_demo_repo_readable_anonymously(self):
        """Demo repository analysis is accessible anonymously without auth headers."""
        res = self.api.handle_get(
            "/api/pr-analysis",
            {"repo": ["acme/demo-repo"], "number": ["42"]},
            headers={}
        )
        self.assertEqual(res.get("schema_version"), "1.0")
        self.assertEqual(res.get("status"), "ready")
        self.assertEqual(res.get("repo"), "acme/demo-repo")
        self.assertEqual(res.get("number"), 42)
        self.assertIn("findings", res)

    def test_per_repo_isolation_rule_r3(self):
        """User B cannot access User A's private repository data."""
        # Alice can access her vault
        alice_res = self.api.handle_get(
            "/api/file-context",
            {"repo": ["alice/secret-vault"], "path": ["src/crypto.py"]},
            headers=self.alice_headers
        )
        self.assertEqual(alice_res.get("status"), "ready")
        self.assertEqual(len(alice_res.get("decisions", [])), 1)
        self.assertEqual(alice_res["decisions"][0]["decision_id"], "dec_vault_1")

        # Bob is denied access to Alice's vault
        bob_res = self.api.handle_get(
            "/api/file-context",
            {"repo": ["alice/secret-vault"], "path": ["src/crypto.py"]},
            headers=self.bob_headers
        )
        self.assertEqual(bob_res.get("status_code"), 403)
        self.assertEqual(bob_res.get("status"), "error")

        # Anonymous caller is prompted to login
        anon_res = self.api.handle_get(
            "/api/file-context",
            {"repo": ["alice/secret-vault"], "path": ["src/crypto.py"]},
            headers={}
        )
        self.assertEqual(anon_res.get("status"), "needs_relogin")

    def test_pr_analysis_caching_by_head_sha(self):
        """PR analysis is cached deterministically by head SHA."""
        # First call with head_sha_1
        res1 = self.api.handle_get(
            "/api/pr-analysis",
            {"repo": ["acme/demo-repo"], "number": ["42"], "head_sha": ["head_sha_1"]},
            headers=self.alice_headers
        )
        self.assertEqual(res1.get("status"), "ready")
        self.assertEqual(res1.get("head_sha"), "head_sha_1")
        self.assertFalse(res1.get("cached", False))

        # Second call with identical head SHA should be cached
        res2 = self.api.handle_get(
            "/api/pr-analysis",
            {"repo": ["acme/demo-repo"], "number": ["42"], "head_sha": ["head_sha_1"]},
            headers=self.alice_headers
        )
        self.assertEqual(res2.get("status"), "ready")
        self.assertTrue(res2.get("cached", False))

        # Third call with new head SHA (head_sha_2) invalidates/bypasses cache
        res3 = self.api.handle_get(
            "/api/pr-analysis",
            {"repo": ["acme/demo-repo"], "number": ["42"], "head_sha": ["head_sha_2"]},
            headers=self.alice_headers
        )
        self.assertEqual(res3.get("status"), "ready")
        self.assertEqual(res3.get("head_sha"), "head_sha_2")
        self.assertFalse(res3.get("cached", False))

    def test_file_context_returns_decisions_and_alternatives(self):
        """File context endpoint returns active decisions and rejected alternatives."""
        res = self.api.handle_get(
            "/api/file-context",
            {"repo": ["acme/demo-repo"], "path": ["src/cache.py"], "line": ["15"]},
            headers=self.alice_headers
        )
        self.assertEqual(res.get("schema_version"), "1.0")
        self.assertEqual(res.get("status"), "ready")
        self.assertEqual(res.get("file"), "src/cache.py")

        decisions = res.get("decisions", [])
        self.assertTrue(any(d["decision_id"] == "dec_cache_1" for d in decisions))
        lru_dec = next(d for d in decisions if d["decision_id"] == "dec_cache_1")
        self.assertEqual(lru_dec["state"], "accepted")
        self.assertEqual(lru_dec["freshness"], "fresh")
        self.assertEqual(lru_dec.get("affected_function"), "get_cached_item")

        rejected = res.get("rejected_alternatives", [])
        self.assertTrue(any(r["decision_id"] == "dec_cache_2" for r in rejected))
        redis_rej = next(r for r in rejected if r["decision_id"] == "dec_cache_2")
        self.assertEqual(redis_rej["state"], "rejected")
        self.assertIn("latency", redis_rej["rejection_reason"])

    def test_feedback_action_confirms_and_dismisses(self):
        """POST /api/findings/feedback accepts dismiss and confirm actions with schema_version."""
        dismiss_res = self.api.handle_post(
            "/api/findings/feedback",
            {
                "finding_id": "find_test_101",
                "action": "dismiss",
                "decision_id": "dec_cache_2",
                "pr_id": "42",
                "reason": "Temporary load test only"
            },
            headers=self.alice_headers
        )
        self.assertEqual(dismiss_res.get("schema_version"), "1.0")
        self.assertEqual(dismiss_res.get("status"), "success")

        confirm_res = self.api.handle_post(
            "/api/findings/feedback",
            {
                "finding_id": "find_test_102",
                "action": "confirm",
                "decision_id": "dec_cache_2",
                "pr_id": "42",
                "reason": "Violates architectural decision"
            },
            headers=self.alice_headers
        )
        self.assertEqual(confirm_res.get("schema_version"), "1.0")
        self.assertEqual(confirm_res.get("status"), "success")

    def test_no_github_tokens_in_any_response_rule_r4(self):
        """Responses never contain GitHub tokens or raw session credentials."""
        secret_patterns = ["ghp_", "gho_", "ghu_", "ghs_", "ghr_", "bearer", "cif_session="]

        endpoints = [
            ("/api/pr-analysis", {"repo": ["acme/demo-repo"], "number": ["42"]}),
            ("/api/file-context", {"repo": ["acme/demo-repo"], "path": ["src/cache.py"]}),
            ("/api/repos/status", {"repo": ["acme/demo-repo"]}),
        ]

        for path, params in endpoints:
            res = self.api.handle_get(path, params, headers=self.alice_headers)
            serialized = json.dumps(res).lower()
            for pattern in secret_patterns:
                self.assertNotIn(pattern, serialized, f"Secret pattern '{pattern}' leaked in {path}")


if __name__ == "__main__":
    unittest.main()
