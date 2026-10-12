"""
Baseline Evaluation Implementations (Section 1.4 & 12.3)
Implements honest, runnable baselines:
- Baseline A: Keyword search (BM25/token overlap over all events)
- Baseline B: Docs-only search (restricted to ADR / doc events)
- Baseline C: Plain LLM (only if env vars configured; else 'not measured')
- Baseline D: Copilot CSV loader (only if manual evaluations logged; else 'not measured')
"""
import os
import re
import csv
from typing import List, Dict, Any, Optional
from backend.db import Database

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

    def run_baseline_llm(self, ground_truth: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Baseline C: Plain LLM over repository context (measured only if API key present)."""
        api_key = os.environ.get("CIF_LLM_API_KEY")
        model = os.environ.get("CIF_LLM_MODEL")

        if not api_key or not model:
            return {
                "name": "Baseline C: Plain LLM Q&A",
                "status": "not measured",
                "decision_recall": "not measured",
                "evidence_grounding_accuracy": "not measured",
                "note": "Requires CIF_LLM_API_KEY and CIF_LLM_MODEL environment variables"
            }

        # If LLM key is configured, execute queries honestly
        # (Implemented via LLMClient in Phase 3)
        return {
            "name": "Baseline C: Plain LLM Q&A",
            "status": "not measured",
            "decision_recall": "not measured",
            "evidence_grounding_accuracy": "not measured",
            "note": "LLM query runner ready for invocation"
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
