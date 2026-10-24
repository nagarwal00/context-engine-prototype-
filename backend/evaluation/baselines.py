"""
Baseline Evaluation Implementations (Section 1.4 & 12.3)
Implements honest, runnable baselines:
- Baseline A: Keyword search (BM25/token overlap over all events)
- Baseline B: Docs-only search (restricted to ADR / doc events)
- Baseline C: Plain LLM (only if env vars configured; else 'not measured')
- Baseline D: Copilot CSV loader (only if manual evaluations logged; else 'not measured')
"""
import csv
import io
import json
import logging
import math
import os
import re
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.db import Database
from backend.ingestion.sanitizer import sanitize_text

logger = logging.getLogger("cif.evaluation.baselines")
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def compute_wilson_interval(k: int, n: int, z: float = 1.96) -> Optional[Tuple[float, float]]:
    """Computes Wilson score 95% confidence interval for binomial proportions."""
    if n == 0:
        return None
    p = k / n
    d = 1.0 + (z * z) / n
    c = (p + (z * z) / (2.0 * n)) / d
    h = (z * math.sqrt((p * (1.0 - p)) / n + (z * z) / (4.0 * n * n))) / d
    return (round(c - h, 4), round(c + h, 4))


def parse_llm_json_response(raw_text: str) -> Dict[str, Any]:
    """Safely extracts JSON dictionary from LLM completion text, tolerating markdown code fences."""
    if not raw_text:
        return {}
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if m:
            try:
                data = json.loads(m.group(0))
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
    return {}


STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's",
    "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we",
    "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours"
}

def tokenize(text: str) -> List[str]:
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Z0-9_\-\./]+\b', text.lower())
    return [w for w in words if len(w) > 3 and w not in STOP_WORDS]

class BaselineEvaluator:
    def __init__(self, db: Database):
        self.db = db

    def evaluate_all(self, ground_truth: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs all 4 baselines against the provided ground truth dataset."""
        return {
            "baseline_keyword": self.run_baseline_keyword(ground_truth),
            "baseline_docs_only": self.run_baseline_docs_only(ground_truth),
            "baseline_llm": self.run_baseline_llm(ground_truth),
            "baseline_copilot": self.run_baseline_copilot(ground_truth)
        }

    def run_baseline_keyword(self, ground_truth: List[Dict[str, Any]], top_k: int = 5) -> Dict[str, Any]:
        """Baseline A: Token overlap search over all events in the repo (Task 1: Evidence Retrieval)."""
        if not ground_truth:
            return {
                "name": "Baseline A: Keyword Search (Grep/BM25)",
                "status": "not measured",
                "task_1_hit_rate": "not measured",
                "task_1_top_k": top_k,
                "task_2_decision_recall": "n/a",
                "task_2_state_accuracy": "n/a",
                "task_2_refusal_accuracy": "n/a (always answers)",
                "decision_recall": "not measured",
                "found_count": 0,
                "total_count": 0,
                "task_1_applicable": True,
                "task_2_applicable": False,
                "note": "Task 1 (Evidence Retrieval) only; Task 2 (Decision Reconstruction) is n/a."
            }

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT event_id, repo, source_type, title, body FROM events")
            events = [dict(r) for r in cursor.fetchall()]

        found_count = 0
        total_count = len(ground_truth)

        for gt in ground_truth:
            gt_tokens = set(tokenize(gt.get("title", "") + " " + gt.get("question", "")))
            expected_events = set(gt.get("expected_evidence_contains", []) or gt.get("evidence_event_ids", []))
            repo = gt.get("repo")

            repo_events = [e for e in events if not repo or e["repo"] == repo]
            scored_events = []
            for ev in repo_events:
                ev_tokens = set(tokenize((ev.get("title") or "") + " " + (ev.get("body") or "")))
                overlap = len(gt_tokens.intersection(ev_tokens))
                scored_events.append((overlap, ev["event_id"]))

            scored_events.sort(key=lambda x: x[0], reverse=True)
            top_event_ids = {eid for score, eid in scored_events[:top_k] if score > 0}

            if top_event_ids.intersection(expected_events):
                found_count += 1

        recall = round((found_count / total_count) * 100, 1) if total_count > 0 else 0.0
        return {
            "name": "Baseline A: Keyword Search (Grep/BM25)",
            "status": "measured",
            "task_1_hit_rate": recall,
            "task_1_top_k": top_k,
            "task_2_decision_recall": "n/a",
            "task_2_state_accuracy": "n/a",
            "task_2_refusal_accuracy": "n/a (always answers)",
            "decision_recall": recall,  # Backward compatibility alias
            "found_count": found_count,
            "total_count": total_count,
            "top_k": top_k,
            "task_1_applicable": True,
            "task_2_applicable": False,
            "note": "Task 1 (Evidence Retrieval) only; Task 2 (Decision Reconstruction) is n/a."
        }

    def run_baseline_docs_only(self, ground_truth: List[Dict[str, Any]], top_k: int = 5) -> Dict[str, Any]:
        """Baseline B: Token overlap search restricted to ADR/Doc events only (Task 1: Evidence Retrieval)."""
        if not ground_truth:
            return {
                "name": "Baseline B: Documentation/ADRs Only",
                "status": "not measured",
                "task_1_hit_rate": "not measured",
                "task_1_top_k": top_k,
                "task_2_decision_recall": "n/a",
                "task_2_state_accuracy": "n/a",
                "task_2_refusal_accuracy": "n/a (always answers)",
                "decision_recall": "not measured",
                "found_count": 0,
                "total_count": 0,
                "task_1_applicable": True,
                "task_2_applicable": False,
                "note": "Task 1 (Evidence Retrieval) only; Task 2 (Decision Reconstruction) is n/a."
            }

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT event_id, repo, source_type, title, body FROM events WHERE source_type IN ('adr', 'doc', 'github_adr')")
            doc_events = [dict(r) for r in cursor.fetchall()]

        found_count = 0
        total_count = len(ground_truth)

        for gt in ground_truth:
            gt_tokens = set(tokenize(gt.get("title", "") + " " + gt.get("question", "")))
            expected_events = set(gt.get("expected_evidence_contains", []) or gt.get("evidence_event_ids", []))
            repo = gt.get("repo")

            repo_events = [e for e in doc_events if not repo or e["repo"] == repo]
            scored_events = []
            for ev in repo_events:
                ev_tokens = set(tokenize((ev.get("title") or "") + " " + (ev.get("body") or "")))
                overlap = len(gt_tokens.intersection(ev_tokens))
                scored_events.append((overlap, ev["event_id"]))

            scored_events.sort(key=lambda x: x[0], reverse=True)
            top_event_ids = {eid for score, eid in scored_events[:top_k] if score > 0}

            if top_event_ids.intersection(expected_events):
                found_count += 1

        recall = round((found_count / total_count) * 100, 1) if total_count > 0 else 0.0
        return {
            "name": "Baseline B: Documentation/ADRs Only",
            "status": "measured",
            "task_1_hit_rate": recall,
            "task_1_top_k": top_k,
            "task_2_decision_recall": "n/a",
            "task_2_state_accuracy": "n/a",
            "task_2_refusal_accuracy": "n/a (always answers)",
            "decision_recall": recall,  # Backward compatibility alias
            "found_count": found_count,
            "total_count": total_count,
            "top_k": top_k,
            "task_1_applicable": True,
            "task_2_applicable": False,
            "note": "Task 1 (Evidence Retrieval) only; Task 2 (Decision Reconstruction) is n/a."
        }

    def _call_llm_api(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: Optional[str],
        user_prompt: str,
        system_prompt: str,
        timeout: int = 60,
        transport_fn: Optional[Any] = None
    ) -> Optional[str]:
        """Dispatches LLM prompt to OpenAI or Anthropic endpoint with retries and TLS verification."""
        retries = 2
        backoff = 1.0

        if provider == "anthropic":
            url = f"{base_url.rstrip('/') if base_url else 'https://api.anthropic.com/v1'}/messages"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
            payload = {
                "model": model,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
                "max_tokens": 1024,
                "temperature": 0.0
            }
        else:
            url = f"{base_url.rstrip('/') if base_url else 'https://api.openai.com/v1'}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"}
            }

        req_data = json.dumps(payload).encode("utf-8")

        for attempt in range(retries + 1):
            try:
                if transport_fn is not None:
                    return transport_fn(url=url, headers=headers, payload=payload, attempt=attempt)

                ssl_ctx = ssl.create_default_context()
                req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
                    resp_bytes = resp.read()
                    resp_json = json.loads(resp_bytes.decode("utf-8"))
                    if provider == "anthropic":
                        content_arr = resp_json.get("content", [])
                        if content_arr and isinstance(content_arr, list):
                            return content_arr[0].get("text", "")
                    else:
                        choices = resp_json.get("choices", [])
                        if choices and isinstance(choices, list):
                            return choices[0].get("message", {}).get("content", "")
                    return ""
            except urllib.error.HTTPError as e:
                logger.warning("LLM API HTTPError code=%s on attempt %d", e.code, attempt)
                if attempt == retries or e.code in (400, 401, 403):
                    return None
                time.sleep(backoff)
                backoff *= 2.0
            except Exception as e:
                logger.warning("LLM API call error %s on attempt %d", e.__class__.__name__, attempt)
                if attempt == retries:
                    return None
                time.sleep(backoff)
                backoff *= 2.0

        return None

    def run_baseline_llm(
        self,
        ground_truth: List[Dict[str, Any]],
        transport_fn: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Baseline C: Plain LLM over repository context (Step 4.1)."""
        if os.environ.get("CIF_LOCAL_ONLY", "0").strip() == "1":
            return {
                "name": "Baseline C: Plain LLM Q&A",
                "status": "not measured",
                "decision_recall": "not measured",
                "evidence_grounding_accuracy": "not measured",
                "note": "CIF_LOCAL_ONLY is enabled; external network LLM calls disabled"
            }

        api_key = os.environ.get("CIF_LLM_API_KEY", "").strip()
        model = os.environ.get("CIF_LLM_MODEL", "").strip()

        if not api_key or not model:
            return {
                "name": "Baseline C: Plain LLM Q&A",
                "status": "not measured",
                "decision_recall": "not measured",
                "evidence_grounding_accuracy": "not measured",
                "note": "Requires CIF_LLM_API_KEY and CIF_LLM_MODEL environment variables"
            }

        provider = os.environ.get("CIF_LLM_PROVIDER", "openai").lower().strip()
        base_url = os.environ.get("CIF_LLM_BASE_URL", "").strip() or None

        if not ground_truth:
            return {
                "name": f"Baseline C: Plain LLM Q&A ({model})",
                "status": "measured",
                "model": model,
                "provider": provider,
                "task_1_hit_rate": 0.0,
                "task_1_hits": 0,
                "task_1_n": 0,
                "task_1_wilson_95": None,
                "task_2_decision_recall": 0.0,
                "task_2_state_accuracy": 0.0,
                "task_2_state_hits": 0,
                "task_2_state_n": 0,
                "task_2_refusal_accuracy": "n/a",
                "unsupported_claim_rate": 0.0,
                "evaluated_samples": 0
            }

        # Query all events in DB grouped by repo
        events_by_repo: Dict[str, List[Dict[str, Any]]] = {}
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT event_id, repo, source_type, source_id, title, body FROM events ORDER BY ts ASC")
            for r in cursor.fetchall():
                ev = dict(r)
                events_by_repo.setdefault(ev["repo"], []).append(ev)

        # Prepare audit log in results/
        safe_model = re.sub(r"[^a-zA-Z0-9_\-]", "_", model)
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        results_dir = PROJECT_ROOT / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        audit_filename = f"llm_baseline_{safe_model}_{timestamp_str}.jsonl"
        audit_path = results_dir / audit_filename
        audit_records = []

        system_prompt = (
            "You are an architectural decision retrieval engine. "
            "Analyze the provided event stream and answer architectural questions strictly from the recorded events. "
            "Return output strictly in valid JSON format."
        )

        positives = [q for q in ground_truth if q.get("expected_state") != "none"]
        negatives = [q for q in ground_truth if q.get("expected_state") == "none"]

        task_1_hits = 0
        state_hits = 0
        state_candidates = 0
        refusal_hits = 0
        unsupported_claim_count = 0

        for q in ground_truth:
            q_id = q.get("question_id") or q.get("id") or "unknown_q"
            repo = q.get("repo") or q.get("repository") or ""
            expected_state = (q.get("expected_state") or "").lower()
            expected_events = set(q.get("expected_evidence_contains", []) or q.get("evidence_event_ids", []) or [])
            q_text = q.get("question") or q.get("title") or ""

            repo_events = events_by_repo.get(repo, [])
            valid_repo_event_ids = {e["event_id"] for e in repo_events}

            event_lines = []
            for ev in repo_events:
                s_title = sanitize_text(ev.get("title") or "")
                s_body = sanitize_text(ev.get("body") or "")
                st = ev.get("source_type") or "event"
                sid = ev.get("source_id") or ""
                event_lines.append(f"[{ev['event_id']}] ({st}:{sid}) {s_title}: {s_body[:400]}")
            event_stream_text = "\n".join(event_lines)

            user_prompt = (
                f"You are analyzing architectural decisions for repository '{repo}'.\n"
                f"Answer the following question ONLY using evidence from the recorded event stream below.\n"
                f"Do not invent or assume decisions or events not explicitly present.\n\n"
                f"Event Stream:\n{event_stream_text}\n\n"
                f"Question:\n{q_text}\n\n"
                f"Return strict JSON with exact keys:\n"
                f"{{\n"
                f'  "decision_found": <true or false>,\n'
                f'  "state": "<accepted|rejected|superseded|proposed|none>",\n'
                f'  "evidence_event_ids": [<list of event_id strings from the event stream that directly support this decision>],\n'
                f'  "answer": "<brief explanation answering the question>"\n'
                f"}}\n"
                f'If there is no recorded decision or the topic is not covered in the events, set "decision_found": false, "state": "none", and "evidence_event_ids": [].'
            )

            raw_response = self._call_llm_api(
                provider=provider,
                api_key=api_key,
                model=model,
                base_url=base_url,
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                timeout=60,
                transport_fn=transport_fn
            )

            parsed = parse_llm_json_response(raw_response or "")
            decision_found = bool(parsed.get("decision_found", False))
            pred_state = str(parsed.get("state", "none")).lower()
            cited_events = [str(e) for e in parsed.get("evidence_event_ids", []) if isinstance(e, (str, int))]
            cited_set = set(cited_events)

            is_pos = expected_state != "none"
            hit = False
            state_match = False
            if is_pos:
                if decision_found and bool(cited_set.intersection(expected_events)):
                    hit = True
                    task_1_hits += 1
                if decision_found:
                    state_candidates += 1
                    if pred_state == expected_state:
                        state_match = True
                        state_hits += 1

            refusal_correct = False
            if not is_pos:
                if not decision_found or pred_state == "none":
                    refusal_correct = True
                    refusal_hits += 1

            invented_ids = cited_set - valid_repo_event_ids
            has_unsupported = bool(invented_ids)
            if has_unsupported:
                unsupported_claim_count += 1

            audit_records.append({
                "question_id": q_id,
                "repo": repo,
                "expected_state": expected_state,
                "expected_evidence_ids": list(expected_events),
                "decision_found": decision_found,
                "predicted_state": pred_state,
                "cited_evidence_ids": cited_events,
                "task_1_hit": hit,
                "state_match": state_match,
                "refusal_correct": refusal_correct,
                "has_unsupported_claim": has_unsupported,
                "invented_event_ids": list(invented_ids),
                "raw_response": raw_response
            })

        try:
            with open(audit_path, "w", encoding="utf-8") as f:
                for rec in audit_records:
                    f.write(json.dumps(rec) + "\n")
        except Exception as e:
            logger.warning("Failed to write LLM audit log: %s", e)

        pos_n = len(positives)
        neg_n = len(negatives)
        total_n = len(ground_truth)

        task_1_rate = round((task_1_hits / pos_n) * 100, 1) if pos_n > 0 else 0.0
        task_1_wilson = compute_wilson_interval(task_1_hits, pos_n) if pos_n > 0 else None

        state_rate = round((state_hits / state_candidates) * 100, 1) if state_candidates > 0 else 0.0
        state_wilson = compute_wilson_interval(state_hits, state_candidates) if state_candidates > 0 else None

        refusal_rate = round((refusal_hits / neg_n) * 100, 1) if neg_n > 0 else "n/a"
        refusal_wilson = compute_wilson_interval(refusal_hits, neg_n) if neg_n > 0 else None

        unsupported_rate = round((unsupported_claim_count / total_n) * 100, 1) if total_n > 0 else 0.0
        unsupported_wilson = compute_wilson_interval(unsupported_claim_count, total_n) if total_n > 0 else None

        return {
            "name": f"Baseline C: Plain LLM Q&A ({model})",
            "status": "measured",
            "model": model,
            "provider": provider,
            "task_1_hit_rate": task_1_rate,
            "task_1_hits": task_1_hits,
            "task_1_n": pos_n,
            "task_1_wilson_95": task_1_wilson,
            "task_2_decision_recall": task_1_rate,
            "task_2_state_accuracy": state_rate,
            "task_2_state_hits": state_hits,
            "task_2_state_n": state_candidates,
            "task_2_state_wilson_95": state_wilson,
            "task_2_refusal_accuracy": refusal_rate,
            "task_2_refusal_hits": refusal_hits,
            "task_2_refusal_n": neg_n,
            "task_2_refusal_wilson_95": refusal_wilson,
            "unsupported_claim_rate": unsupported_rate,
            "unsupported_claim_hits": unsupported_claim_count,
            "unsupported_claim_n": total_n,
            "unsupported_claim_wilson_95": unsupported_wilson,
            "audit_log": str(audit_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "task_1_applicable": True,
            "task_2_applicable": True,
            "note": f"Scored on {pos_n} positives, {neg_n} negatives. Audit log: results/{audit_filename}"
        }

    def run_baseline_copilot(self, ground_truth: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Baseline D: GitHub Copilot Q&A (loaded from manual_copilot_results.csv)."""
        csv_path = os.path.join(os.path.dirname(__file__), "manual_copilot_results.csv")
        if not os.path.exists(csv_path):
            return {
                "name": "Baseline D: GitHub Copilot",
                "status": "not measured",
                "decision_recall": "not measured",
                "hallucination_rate": "not measured",
                "note": "No manual copilot evaluation records logged in manual_copilot_results.csv"
            }

        rows = []
        try:
            with open(csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if r.get("question_id"):
                        rows.append(r)
        except Exception:
            pass

        if not rows:
            return {
                "name": "Baseline D: GitHub Copilot",
                "status": "not measured",
                "decision_recall": "not measured",
                "hallucination_rate": "not measured",
                "evaluated_samples": 0
            }

        correct_count = sum(1 for r in rows if r.get("answer_correct", "").strip().lower() in ("true", "1", "yes"))
        hallucinated_count = sum(1 for r in rows if r.get("answer_has_invented_reason", "").strip().lower() in ("true", "1", "yes"))
        total = len(rows)

        return {
            "name": "Baseline D: GitHub Copilot",
            "status": "measured",
            "decision_recall": round((correct_count / total) * 100, 1),
            "hallucination_rate": round((hallucinated_count / total) * 100, 1),
            "evaluated_samples": total
        }
