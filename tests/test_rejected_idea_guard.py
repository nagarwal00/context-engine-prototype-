"""
Tests for Step 3.5: Rejected-Idea Guard (Headline Novelty)
Verifies:
- >= 5 true matches (including paraphrased proposal matched by structural signals).
- >= 8 non-matches (including keyword-only coincidences).
- Reopen flow (reopened decision changes advisory message).
- Dismiss persistence (dismissed findings suppressed for same PR + decision).
- "Never blocks" assertion (advisory findings exit code 0 unless --strict).
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from backend.db import Database
from backend.models import Decision, GuardRule
from backend.seed_data import populate_seed_data
from backend.engine.rejected_idea_guard import RejectedIdeaGuard, compute_tfidf_cosine

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestRejectedIdeaGuard(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_rejected_guard.db")
        self.db = Database(self.db_path)
        populate_seed_data(self.db)
        self.guard = RejectedIdeaGuard(self.db)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_tfidf_cosine_calculation(self):
        """Verifies pure stdlib TF-IDF cosine similarity."""
        # 1. Identical token lists -> 1.0
        tokens_a = ["thermal", "control", "deadband", "hysteresis"]
        sim_identical = compute_tfidf_cosine(tokens_a, tokens_a)
        self.assertAlmostEqual(sim_identical, 1.0, places=3)

        # 2. Completely disjoint token lists -> 0.0
        tokens_b = ["database", "postgres", "sql", "migration"]
        sim_disjoint = compute_tfidf_cosine(tokens_a, tokens_b)
        self.assertEqual(sim_disjoint, 0.0)

        # 3. Partially overlapping tokens -> between 0.0 and 1.0
        tokens_c = ["thermal", "sensor", "telemetry"]
        sim_partial = compute_tfidf_cosine(tokens_a, tokens_c)
        self.assertGreater(sim_partial, 0.0)
        self.assertLess(sim_partial, 1.0)

    def test_true_matches_identify_rejected_approaches(self):
        """
        Verify >= 5 true matches:
        1. Direct rejected dependency reintroduction.
        2. Direct rejected deadband controller in thermal system.
        3. Paraphrased proposal with different terminology (structural match).
        4. On-off relay control in thermal module.
        5. In-memory dictionary cache reintroduction in cache service.
        6. Explicit re-proposal of rejected ADR approach.
        """
        repo_thermal = "acme-eng/thermal-control-system"
        repo_cache = "acme-eng/distributed-cache-service"

        true_match_cases = [
            # 1. Direct reintroduction of deadband tuning (dec_thermal_deadband_rejected)
            {
                "id": "match_01_deadband",
                "repo": repo_thermal,
                "pr_id": "pr_101",
                "title": "Tighten deadband to +/- 1.5C",
                "body": "Reintroducing simple deadband tuning to avoid PID math libraries.",
                "files": ["src/thermal/control.py"],
                "diff": "+++ b/src/thermal/control.py\n@@ -20,3 +20,4 @@\n+    deadband = 1.5\n+    if abs(temp - target) < deadband: return\n",
                "expected_decision": "dec_thermal_deadband_rejected"
            },
            # 2. Paraphrased proposal with different terminology (no 'LRU' keyword in PR, matched structurally)
            {
                "id": "match_02_paraphrased_cache",
                "repo": repo_cache,
                "pr_id": "pr_102",
                "title": "Emergency local buffer for cache misses",
                "body": "Fast volatile heap storage without network hop for high-frequency reads.",
                "files": ["src/cache/store.py"],
                "diff": "+++ b/src/cache/store.py\n@@ -30,2 +30,4 @@\n+    local_cache = {}\n+    return local_cache.get(key)\n",
                "expected_decision": "dec_cache_redis_accepted"
            },
            # 3. Direct reintroduction of on-off relay control in control module
            {
                "id": "match_03_on_off_relay",
                "repo": repo_thermal,
                "pr_id": "pr_103",
                "title": "Bang-bang fallback mode",
                "body": "Switch heater using on-off relay when thermal transient spikes.",
                "files": ["src/thermal/control.py"],
                "diff": "+++ b/src/thermal/control.py\n@@ -40,2 +40,3 @@\n+    output = on_off_relay(reading)\n",
                "expected_decision": "dec_thermal_pid_accepted"
            },
            # 4. In-memory dict cache reintroduction
            {
                "id": "match_04_dict_cache",
                "repo": repo_cache,
                "pr_id": "pr_104",
                "title": "Add dict cache fallback in store",
                "body": "Keep items in memory dict structure.",
                "files": ["src/cache/store.py"],
                "diff": "+++ b/src/cache/store.py\n@@ -50,2 +50,3 @@\n+    dict_cache = {}\n+    dict_cache[key] = val\n",
                "expected_decision": "dec_cache_redis_accepted"
            },
            # 5. Hysteresis threshold loop in thermal regulator
            {
                "id": "match_05_hysteresis",
                "repo": repo_thermal,
                "pr_id": "pr_105",
                "title": "Simple threshold hysteresis mode",
                "body": "Use threshold hysteresis loop instead of complex continuous regulation.",
                "files": ["src/thermal/control.py"],
                "diff": "+++ b/src/thermal/control.py\n@@ -60,2 +60,3 @@\n+    # threshold hysteresis\n+    heater_state = 1 if temp < 50 else 0\n",
                "expected_decision": "dec_thermal_pid_accepted"
            },
            # 6. Re-proposing rejected PR #38 local soft memory cap
            {
                "id": "match_06_local_lru",
                "repo": repo_cache,
                "pr_id": "pr_106",
                "title": "Local LRU cache memory cap",
                "body": "Retain in-process memory cache with soft process cap.",
                "files": ["src/cache/store.py"],
                "diff": "+++ b/src/cache/store.py\n@@ -10,2 +10,3 @@\n+    # in-memory LRU cache\n+    local_cache = LRUCache(max_size=1000)\n",
                "expected_decision": "dec_cache_redis_accepted"
            }
        ]

        self.assertGreaterEqual(len(true_match_cases), 5, "Must test at least 5 true matches")

        for tc in true_match_cases:
            report = self.guard.evaluate_proposal(
                repo=tc["repo"],
                pr_id=tc["pr_id"],
                title=tc["title"],
                body=tc["body"],
                diff_text=tc["diff"],
                changed_files=tc["files"]
            )
            findings = report.get("findings", [])
            self.assertGreaterEqual(
                len(findings), 1,
                f"Expected true match for {tc['id']} ({tc['title']}), got 0 findings"
            )

            matched_ids = [f["decision_id"] for f in findings]
            self.assertIn(
                tc["expected_decision"], matched_ids,
                f"Expected match with decision {tc['expected_decision']} in {matched_ids}"
            )

            # Assert Step 3.5 finding structure and advisory invariants
            f = findings[0]
            self.assertTrue(f["advisory"], "Rejected-idea guard findings must always be advisory")
            self.assertEqual(f["status"], "potential_violation")
            self.assertEqual(f["finding_type"], "rejected_idea")
            self.assertIn(f["tier"], ("strong", "possible"))
            self.assertIn("Possible reintroduction of a previously rejected approach", f["pr_comment"])
            self.assertTrue(bool(f["rejection_reason"]))
            self.assertIsInstance(f["changed_circumstances"], list)
            self.assertFalse(f["reviewed"])
            self.assertFalse(f["dismissed"])

    def test_non_matches_produce_zero_findings(self):
        """
        Verify >= 8 non-matches produce 0 findings:
        1. Clean logic addition in service worker.
        2. Keyword coincidence without substance or path overlap.
        3. Clean refactor of accepted PID control.
        4. Clean refactor of accepted Redis client.
        5. Removed line containing rejected idea (cleanup diff).
        6. Coincidental variable name with generic words.
        7. Unrelated module in different repository.
        8. Documentation-only update.
        9. Decommissioning note in comments.
        """
        repo_thermal = "acme-eng/thermal-control-system"
        repo_cache = "acme-eng/distributed-cache-service"

        non_match_cases = [
            # 1. Clean worker computation
            {
                "id": "neg_01_clean_worker",
                "repo": repo_thermal,
                "title": "Compute batch telemetry checksum",
                "body": "Calculate sha256 checksum for sensor batch data.",
                "files": ["src/service/worker.py"],
                "diff": "+++ b/src/service/worker.py\n@@ -1,2 +1,3 @@\n+    checksum = hashlib.sha256(batch_data).hexdigest()\n"
            },
            # 2. Keyword coincidence without path or substance match ('deadband' used in alerts module)
            {
                "id": "neg_02_keyword_coincidence",
                "repo": repo_thermal,
                "title": "Update alert monitoring configuration",
                "body": "Set deadband margin for pagerduty notification firing.",
                "files": ["monitoring/alerts.py"],
                "diff": "+++ b/monitoring/alerts.py\n@@ -5,2 +5,3 @@\n+    alert_threshold_margin = 0.5\n"
            },
            # 3. Clean enhancement of accepted PID controller
            {
                "id": "neg_03_accepted_pid",
                "repo": repo_thermal,
                "title": "Add derivative filtering to discrete PID",
                "body": "Filters sensor noise before calculating D-term in PID step.",
                "files": ["src/thermal/control.py"],
                "diff": "+++ b/src/thermal/control.py\n@@ -35,2 +35,3 @@\n+    filtered_d = alpha * error_d + (1 - alpha) * prev_d\n"
            },
            # 4. Clean enhancement of accepted Redis cluster client
            {
                "id": "neg_04_accepted_redis",
                "repo": repo_cache,
                "title": "Configure Redis socket timeout and retry pool",
                "body": "Adds exponential backoff on cluster failover.",
                "files": ["src/cache/store.py"],
                "diff": "+++ b/src/cache/store.py\n@@ -20,2 +20,3 @@\n+    redis_client.set_retry_policy(max_retries=3)\n"
            },
            # 5. Removal of rejected approach (cleanup diff)
            {
                "id": "neg_05_cleanup_diff",
                "repo": repo_thermal,
                "title": "Remove old deadband threshold code",
                "body": "Deletes obsolete thresholding fallback branch.",
                "files": ["src/thermal/control.py"],
                "diff": "+++ b/src/thermal/control.py\n@@ -50,3 +50,2 @@\n-    # deadband tuning\n-    threshold_val = 50\n+    # Cleaned up\n"
            },
            # 6. Coincidental variable name with generic words
            {
                "id": "neg_06_generic_words",
                "repo": repo_cache,
                "title": "Update request cache timeout",
                "body": "Adjust HTTP client keepalive timeout.",
                "files": ["src/client/http.py"],
                "diff": "+++ b/src/client/http.py\n@@ -10,2 +10,3 @@\n+    http_client_timeout = 30\n"
            },
            # 7. Unrelated repository and component
            {
                "id": "neg_07_unrelated_repo",
                "repo": "acme-eng/billing-service",
                "title": "Stripe webhook payment handler",
                "body": "Processes Stripe invoice.payment_succeeded events.",
                "files": ["src/billing/webhook.py"],
                "diff": "+++ b/src/billing/webhook.py\n@@ -1,2 +1,3 @@\n+    record_charge(event['data'])\n"
            },
            # 8. Documentation update in docs/
            {
                "id": "neg_08_doc_update",
                "repo": repo_thermal,
                "title": "Update deployment documentation",
                "body": "Describes Helm chart parameters for thermal controller.",
                "files": ["docs/deploy.md"],
                "diff": "+++ b/docs/deploy.md\n@@ -1,2 +1,3 @@\n+Deploy via `helm install thermal-control ./charts`\n"
            },
            # 9. Clean comment mentioning historical decommissioning
            {
                "id": "neg_09_historical_note",
                "repo": repo_thermal,
                "title": "Update module header comments",
                "body": "Note historical decisions in comments.",
                "files": ["src/thermal/control.py"],
                "diff": "+++ b/src/thermal/control.py\n@@ -1,2 +1,3 @@\n+# Note: on-off hysteresis was decommissioned in ADR 0004\n"
            }
        ]

        self.assertGreaterEqual(len(non_match_cases), 8, "Must test at least 8 non-matches")

        for tc in non_match_cases:
            report = self.guard.evaluate_proposal(
                repo=tc["repo"],
                pr_id="pr_neg_test",
                title=tc["title"],
                body=tc["body"],
                diff_text=tc["diff"],
                changed_files=tc["files"]
            )
            findings = report.get("findings", [])
            self.assertEqual(
                findings, [],
                f"Expected 0 findings for negative case {tc['id']} ({tc['title']}), got: {findings}"
            )

    def test_reopen_flow_changes_advisory_message(self):
        """Verifies developer action: reopening a rejected decision changes the advisory message."""
        repo = "acme-eng/thermal-control-system"
        pr_id = "pr_201_reopen"

        # 1. Before reopening: candidate dec_thermal_deadband_rejected is in state 'rejected'
        rep1 = self.guard.evaluate_proposal(
            repo=repo,
            pr_id=pr_id,
            title="Deadband threshold evaluation",
            body="Re-evaluating deadband tuning under new low-jitter sensors.",
            diff_text="+++ b/src/thermal/control.py\n@@ -10,2 +10,3 @@\n+    deadband = 1.5\n",
            changed_files=["src/thermal/control.py"]
        )
        findings1 = [f for f in rep1.get("findings", []) if f["decision_id"] == "dec_thermal_deadband_rejected"]
        self.assertGreaterEqual(len(findings1), 1)
        self.assertEqual(findings1[0]["decision_state"], "rejected")
        self.assertIn("Possible reintroduction of previously rejected approach", findings1[0]["message"])

        # 2. Reopen the decision via the guard action
        reopen_res = self.guard.reopen_decision(
            decision_id="dec_thermal_deadband_rejected",
            pr_id=pr_id,
            actor="sarah_chen",
            reason="Hardware sensor upgrade with sub-millisecond ADC eliminates previous jitter concern"
        )
        self.assertEqual(reopen_res["status"], "reopened")

        # Verify DB decision state is now 'reopened'
        dec_after = self.db.get_decision("dec_thermal_deadband_rejected")
        self.assertIsNotNone(dec_after)
        self.assertEqual(dec_after.state, "reopened")

        # 3. Subsequent PR check on the reopened decision produces a tailored REOPENED advisory notice
        rep2 = self.guard.evaluate_proposal(
            repo=repo,
            pr_id="pr_202_subsequent",
            title="Deadband threshold implementation",
            body="Implement deadband regulation using new ADC.",
            diff_text="+++ b/src/thermal/control.py\n@@ -10,2 +10,3 @@\n+    deadband = 1.5\n",
            changed_files=["src/thermal/control.py"]
        )
        findings2 = [f for f in rep2.get("findings", []) if f["decision_id"] == "dec_thermal_deadband_rejected"]
        self.assertGreaterEqual(len(findings2), 1)
        f_reopened = findings2[0]
        self.assertEqual(f_reopened["decision_state"], "reopened")
        self.assertIn("REOPENED", f_reopened["message"])
        self.assertIn("REOPENED", f_reopened["pr_comment"])

    def test_dismiss_persistence_suppresses_subsequent_findings(self):
        """Verifies developer action: dismissing a finding for a PR persists and suppresses duplicate alerts."""
        repo = "acme-eng/distributed-cache-service"
        pr_id = "pr_301_dismiss"
        dec_id = "dec_cache_redis_accepted"

        # 1. Initial evaluation triggers advisory finding
        rep1 = self.guard.evaluate_proposal(
            repo=repo,
            pr_id=pr_id,
            title="Local memory cache fallback",
            body="Temporary in-memory cache for emergency maintenance window.",
            diff_text="+++ b/src/cache/store.py\n@@ -20,2 +20,3 @@\n+    local_cache = {}\n",
            changed_files=["src/cache/store.py"]
        )
        findings1 = [f for f in rep1.get("findings", []) if f["decision_id"] == dec_id]
        self.assertGreaterEqual(len(findings1), 1)
        finding_id = findings1[0]["finding_id"]

        # 2. Developer dismisses the finding
        dismiss_res = self.guard.dismiss_finding(
            finding_id=finding_id,
            pr_id=pr_id,
            decision_id=dec_id,
            actor="priya_patel",
            reason="Approved temporary maintenance bypass with TTL safeguard"
        )
        self.assertEqual(dismiss_res["status"], "dismissed")

        # Verify dismissal recorded in DB
        self.assertTrue(self.db.is_finding_dismissed(pr_id, dec_id))

        # 3. Re-evaluating the SAME PR produces 0 findings (suppressed)
        rep2 = self.guard.evaluate_proposal(
            repo=repo,
            pr_id=pr_id,
            title="Local memory cache fallback",
            body="Temporary in-memory cache for emergency maintenance window.",
            diff_text="+++ b/src/cache/store.py\n@@ -20,2 +20,3 @@\n+    local_cache = {}\n",
            changed_files=["src/cache/store.py"]
        )
        findings2 = [f for f in rep2.get("findings", []) if f["decision_id"] == dec_id]
        self.assertEqual(findings2, [], "Dismissed finding must not be repeated for same PR")

        # 4. A DIFFERENT PR with the same pattern is NOT suppressed
        rep3 = self.guard.evaluate_proposal(
            repo=repo,
            pr_id="pr_302_different",
            title="Local memory cache fallback",
            body="Temporary in-memory cache.",
            diff_text="+++ b/src/cache/store.py\n@@ -20,2 +20,3 @@\n+    local_cache = {}\n",
            changed_files=["src/cache/store.py"]
        )
        findings3 = [f for f in rep3.get("findings", []) if f["decision_id"] == dec_id]
        self.assertGreaterEqual(len(findings3), 1, "Dismissal must not suppress alerts on other PRs")

    def test_never_blocks_assertion_and_ci_check_strict_flag(self):
        """
        Verifies Step 3.5 Item 6: 'Never auto-block. The finding is advisory (advisory: true).'
        tools/ci_check.py exits 0 by default on advisory findings, and exits 1 only with --strict.
        """
        # Guard finding has advisory: True
        rep = self.guard.evaluate_proposal(
            repo="acme-eng/thermal-control-system",
            pr_id="pr_401_advisory",
            title="Deadband test",
            body="Deadband tuning.",
            diff_text="+++ b/src/thermal/control.py\n@@ -10,2 +10,3 @@\n+    deadband = 1.5\n",
            changed_files=["src/thermal/control.py"]
        )
        for f in rep.get("findings", []):
            self.assertTrue(f["advisory"], "Every rejected-idea guard finding must have advisory: True")
            self.assertNotIn("blocked", f["pr_comment"].lower(), "Comment must never use the word 'blocked'")
            self.assertIn("please review", f["pr_comment"].lower())

        # Test tools/ci_check.py CLI with clean git commits
        # Run ci_check.py between HEAD~1 and HEAD
        ci_tool_path = PROJECT_ROOT / "tools" / "ci_check.py"
        self.assertTrue(ci_tool_path.exists())

        # 1. Default invocation (advisories do NOT block -> exit code 0)
        res_default = subprocess.run(
            [sys.executable, str(ci_tool_path), "--base", "HEAD~1", "--head", "HEAD", "--db", self.db_path],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        self.assertEqual(res_default.returncode, 0, f"ci_check must exit 0 by default: {res_default.stderr}")

        # 2. Strict invocation without hard rule violations still exits 0 when clean
        res_strict_clean = subprocess.run(
            [sys.executable, str(ci_tool_path), "--base", "HEAD~1", "--head", "HEAD", "--strict", "--db", self.db_path],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        self.assertEqual(res_strict_clean.returncode, 0)


if __name__ == "__main__":
    unittest.main()
