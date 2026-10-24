"""
tests/test_llm_baseline.py
Tests for Baseline C: Plain LLM Evaluation (Step 4.1)
Verifies:
1. Local-only short circuit (CIF_LOCAL_ONLY=1 -> 'not measured').
2. Missing env vars short circuit (CIF_LLM_API_KEY / CIF_LLM_MODEL missing -> 'not measured').
3. OpenAI provider mock transport: scoring, positive/negative partitioning, Wilson intervals, and audit log.
4. Anthropic provider mock transport: headers, payload structure.
5. Retries on HTTP error with exponential backoff.
6. Garbled JSON and markdown code fences parsing.
7. Key never present in audit logs or warning messages.
"""
import json
import logging
import os
import shutil
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from backend.db import Database
from backend.models import Event
from backend.evaluation.baselines import (
    BaselineEvaluator,
    compute_wilson_interval,
    parse_llm_json_response
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestLLMBaseline(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_llm_baseline.db")
        self.db = Database(self.db_path)
        self.evaluator = BaselineEvaluator(self.db)

        # Seed sample events for repository 'org/repo-a'
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO events (event_id, repo, source_type, source_id, title, body, source_url, ts)
            VALUES 
              ('ev_001', 'org/repo-a', 'commit', 'c1', 'Use Redis for distributed caching', 'Adopt redis cluster for shared sessions', 'https://github.com/org/repo-a/commit/c1', '2026-01-01T00:00:00Z'),
              ('ev_002', 'org/repo-a', 'issue', 'i1', 'Performance issues with memory', 'In-memory cache exhausted heap', 'https://github.com/org/repo-a/issues/1', '2026-01-02T00:00:00Z'),
              ('ev_003', 'org/repo-a', 'pr', 'pr1', 'Merge Redis client integration', 'Switched to redis-py driver', 'https://github.com/org/repo-a/pull/1', '2026-01-03T00:00:00Z')
            """)
            conn.commit()

        self.sample_ground_truth = [
            # 1. Positive question (expected_state='accepted', expects ev_001)
            {
                "question_id": "q_pos_1",
                "repo": "org/repo-a",
                "question": "Why did we adopt Redis?",
                "expected_state": "accepted",
                "evidence_event_ids": ["ev_001"]
            },
            # 2. Positive question (expected_state='accepted', expects ev_003)
            {
                "question_id": "q_pos_2",
                "repo": "org/repo-a",
                "question": "Which PR merged the Redis driver?",
                "expected_state": "accepted",
                "evidence_event_ids": ["ev_003"]
            },
            # 3. Negative question (expected_state='none', unrecorded topic)
            {
                "question_id": "q_neg_1",
                "repo": "org/repo-a",
                "question": "Why did we migrate to DynamoDB?",
                "expected_state": "none",
                "evidence_event_ids": []
            },
            # 4. Negative question (expected_state='none', unrecorded topic)
            {
                "question_id": "q_neg_2",
                "repo": "org/repo-a",
                "question": "Why did we adopt Kafka?",
                "expected_state": "none",
                "evidence_event_ids": []
            }
        ]

        self.created_audit_files = []

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        # Clean up any audit files generated during testing
        results_dir = PROJECT_ROOT / "results"
        for f in self.created_audit_files:
            p = results_dir / f
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass

    def test_local_only_mode_returns_not_measured(self):
        """Verifies Step 4.1: CIF_LOCAL_ONLY=1 disables LLM calls."""
        with patch.dict(os.environ, {
            "CIF_LOCAL_ONLY": "1",
            "CIF_LLM_API_KEY": "synthetic_key_12345",
            "CIF_LLM_MODEL": "gpt-4o"
        }):
            res = self.evaluator.run_baseline_llm(self.sample_ground_truth)
            self.assertEqual(res["status"], "not measured")
            self.assertIn("CIF_LOCAL_ONLY", res["note"])

    def test_missing_env_vars_returns_not_measured(self):
        """Verifies Step 4.1: Missing API key or model name returns 'not measured'."""
        with patch.dict(os.environ, {
            "CIF_LOCAL_ONLY": "0"
        }, clear=True):
            res = self.evaluator.run_baseline_llm(self.sample_ground_truth)
            self.assertEqual(res["status"], "not measured")
            self.assertIn("Requires CIF_LLM_API_KEY", res["note"])

    def test_openai_mock_transport_scoring_and_audit(self):
        """Verifies Step 4.1: OpenAI provider evaluation, scoring, intervals, and audit log."""
        test_key = "test_sk_secret_12345"

        def mock_transport(url, headers, payload, attempt):
            self.assertIn("Bearer " + test_key, headers.get("Authorization", ""))
            self.assertEqual(payload["model"], "gpt-4o")
            user_msg = payload["messages"][1]["content"]

            if "Why did we adopt Redis?" in user_msg:
                # True positive match
                return json.dumps({
                    "decision_found": True,
                    "state": "accepted",
                    "evidence_event_ids": ["ev_001"],
                    "answer": "Adopted Redis for distributed caching."
                })
            elif "Which PR merged the Redis driver?" in user_msg:
                # Miss: wrong evidence cited
                return json.dumps({
                    "decision_found": True,
                    "state": "rejected",
                    "evidence_event_ids": ["ev_002"],
                    "answer": "Found memory discussion."
                })
            elif "Why did we migrate to DynamoDB?" in user_msg:
                # Correct refusal on negative
                return json.dumps({
                    "decision_found": False,
                    "state": "none",
                    "evidence_event_ids": [],
                    "answer": "No decision found in event stream."
                })
            elif "Why did we adopt Kafka?" in user_msg:
                # Hallucination on negative citing an invented event ID
                return json.dumps({
                    "decision_found": True,
                    "state": "accepted",
                    "evidence_event_ids": ["ev_invented_999"],
                    "answer": "Invented kafka claim."
                })
            return json.dumps({"decision_found": False})

        with patch.dict(os.environ, {
            "CIF_LOCAL_ONLY": "0",
            "CIF_LLM_API_KEY": test_key,
            "CIF_LLM_MODEL": "gpt-4o",
            "CIF_LLM_PROVIDER": "openai"
        }):
            res = self.evaluator.run_baseline_llm(
                self.sample_ground_truth,
                transport_fn=mock_transport
            )

            self.assertEqual(res["status"], "measured")
            self.assertEqual(res["model"], "gpt-4o")
            self.assertEqual(res["provider"], "openai")

            # Positives = 2, hits = 1 (50.0%)
            self.assertEqual(res["task_1_hits"], 1)
            self.assertEqual(res["task_1_n"], 2)
            self.assertEqual(res["task_1_hit_rate"], 50.0)
            self.assertIsNotNone(res["task_1_wilson_95"])

            # State accuracy: 2 positive candidates found, 1 state matched ('accepted' vs 'rejected') -> 50.0%
            self.assertEqual(res["task_2_state_hits"], 1)
            self.assertEqual(res["task_2_state_n"], 2)
            self.assertEqual(res["task_2_state_accuracy"], 50.0)

            # Refusal accuracy: 2 negatives, 1 correctly refused -> 50.0%
            self.assertEqual(res["task_2_refusal_hits"], 1)
            self.assertEqual(res["task_2_refusal_n"], 2)
            self.assertEqual(res["task_2_refusal_accuracy"], 50.0)

            # Unsupported claim rate: 1 response had invented id 'ev_invented_999' out of 4 total -> 25.0%
            self.assertEqual(res["unsupported_claim_hits"], 1)
            self.assertEqual(res["unsupported_claim_n"], 4)
            self.assertEqual(res["unsupported_claim_rate"], 25.0)

            # Audit log file verification
            audit_path_str = res.get("audit_log", "")
            self.assertTrue(audit_path_str, "audit_log path must be returned")
            audit_file = PROJECT_ROOT / audit_path_str
            self.assertTrue(audit_file.exists(), f"Audit log file must exist at {audit_file}")
            self.created_audit_files.append(audit_file.name)

            with open(audit_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 4)

            # Verify no secret key is in audit file
            audit_text = "".join(lines)
            self.assertNotIn(test_key, audit_text)

    def test_anthropic_headers_and_payload_format(self):
        """Verifies Step 4.1: Anthropic provider uses x-api-key and messages payload."""
        test_key = "test_anthropic_sk_secret_67890"

        captured_requests = []
        def mock_transport(url, headers, payload, attempt):
            captured_requests.append((url, headers, payload))
            return json.dumps({
                "content": [{"text": '{"decision_found": false, "state": "none", "evidence_event_ids": []}'}]
            })

        with patch.dict(os.environ, {
            "CIF_LOCAL_ONLY": "0",
            "CIF_LLM_API_KEY": test_key,
            "CIF_LLM_MODEL": "claude-3-5-sonnet",
            "CIF_LLM_PROVIDER": "anthropic"
        }):
            res = self.evaluator.run_baseline_llm(
                self.sample_ground_truth[:1],
                transport_fn=mock_transport
            )
            self.assertEqual(res["status"], "measured")
            self.assertEqual(len(captured_requests), 1)

            url, headers, payload = captured_requests[0]
            self.assertIn("https://api.anthropic.com/v1/messages", url)
            self.assertEqual(headers.get("x-api-key"), test_key)
            self.assertEqual(headers.get("anthropic-version"), "2023-06-01")
            self.assertEqual(payload["model"], "claude-3-5-sonnet")
            self.assertIn("system", payload)

            if res.get("audit_log"):
                self.created_audit_files.append(Path(res["audit_log"]).name)

    def test_retries_on_http_error(self):
        """Verifies Step 4.1: 2 retries with exponential backoff on HTTP/transport errors."""
        attempts_seen = []

        def failing_then_succeeding_transport(url, headers, payload, attempt):
            attempts_seen.append(attempt)
            if attempt < 2:
                raise urllib.error.HTTPError(url, 500, "Internal Server Error", hdrs=None, fp=None)
            return json.dumps({
                "choices": [{"message": {"content": '{"decision_found": false, "state": "none", "evidence_event_ids": []}'}}]
            })

        with patch("time.sleep") as mock_sleep:
            with patch.dict(os.environ, {
                "CIF_LOCAL_ONLY": "0",
                "CIF_LLM_API_KEY": "dummy_key",
                "CIF_LLM_MODEL": "gpt-4o"
            }):
                raw = self.evaluator._call_llm_api(
                    provider="openai",
                    api_key="dummy_key",
                    model="gpt-4o",
                    base_url=None,
                    user_prompt="test",
                    system_prompt="sys",
                    timeout=60,
                    transport_fn=failing_then_succeeding_transport
                )
                self.assertIsNotNone(raw)
                self.assertEqual(attempts_seen, [0, 1, 2])
                self.assertEqual(mock_sleep.call_count, 2)

    def test_garbled_json_handled_without_crash(self):
        """Verifies Step 4.1: Markdown code fences, malformed text, or invalid JSON are handled gracefully."""
        # 1. Markdown code block
        fence_text = "```json\n{\"decision_found\": true, \"state\": \"accepted\", \"evidence_event_ids\": [\"e1\"]}\n```"
        p1 = parse_llm_json_response(fence_text)
        self.assertTrue(p1.get("decision_found"))
        self.assertEqual(p1.get("evidence_event_ids"), ["e1"])

        # 2. Text with embedded JSON block
        embedded = "Here is your response:\n{\"decision_found\": false, \"state\": \"none\"}\nHope this helps!"
        p2 = parse_llm_json_response(embedded)
        self.assertFalse(p2.get("decision_found"))

        # 3. Completely garbled text
        garbled = "I cannot fulfill this request as an AI language model."
        p3 = parse_llm_json_response(garbled)
        self.assertEqual(p3, {})

    def test_key_never_in_logs_or_audit(self):
        """Verifies Step 4.1: Secret key is never logged to system logs."""
        secret_key = "super_secret_never_leak_this_key_9999"

        def error_transport(url, headers, payload, attempt):
            raise urllib.error.HTTPError(url, 401, "Unauthorized", hdrs=None, fp=None)

        with self.assertLogs("cif.evaluation.baselines", level="WARNING") as cm:
            with patch.dict(os.environ, {
                "CIF_LOCAL_ONLY": "0",
                "CIF_LLM_API_KEY": secret_key,
                "CIF_LLM_MODEL": "gpt-4o"
            }):
                raw = self.evaluator._call_llm_api(
                    provider="openai",
                    api_key=secret_key,
                    model="gpt-4o",
                    base_url=None,
                    user_prompt="prompt",
                    system_prompt="sys",
                    timeout=60,
                    transport_fn=error_transport
                )
                self.assertIsNone(raw)

        log_output = " ".join(cm.output)
        self.assertNotIn(secret_key, log_output)


if __name__ == "__main__":
    unittest.main()
