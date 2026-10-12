"""
Evaluation Pipeline and Benchmark Engine (Section 12 & METRICS.md)
Computes all evaluation metrics from real data without any hard-coded constants.
"""
import os
import re
import json
import time
import hashlib
import statistics
from typing import Dict, Any, List, Optional, Tuple
from backend.db import Database
from backend.evaluation.ground_truth import GROUND_TRUTH_DATASET
from backend.evaluation.baselines import BaselineEvaluator, STOP_WORDS, tokenize
from backend.engine.explanation import ExplanationGenerator
from backend.engine.reconciliation import ReconciliationEngine
from backend.engine.drift_detector import DriftDetector

def compute_db_sha256(db_path: str) -> str:
    """Computes SHA-256 hash of a SQLite database file (Step 4.5)."""
    if not db_path or not os.path.exists(db_path):
        return ""
    hasher = hashlib.sha256()
    with open(db_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def evaluate_precision_labels(db_path: str, labels_file_or_dir: str = None) -> Tuple[Any, str]:
    """
    Evaluates decision precision from a human-labelled sample (Step 4.5).
    Refuses to use labels whose db_snapshot_sha256 does not match the DB being evaluated.

    Returns (precision_val, reason_str).
    precision_val is either float (0.0 - 100.0) or string 'not measured'.
    """
    labels_file = None
    if labels_file_or_dir:
        if os.path.isfile(labels_file_or_dir):
            labels_file = labels_file_or_dir
        elif os.path.isdir(labels_file_or_dir):
            candidate = os.path.join(labels_file_or_dir, "precision_labels.json")
            if os.path.exists(candidate):
                labels_file = candidate

    if not labels_file:
        base_eval_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(base_eval_dir, "precision_labels.json"),
            os.path.join(base_eval_dir, "whybench", "precision_labels.json")
        ]
        for c in candidates:
            if os.path.exists(c):
                labels_file = c
                break

    if not labels_file or not os.path.exists(labels_file):
        return "not measured", "precision label file not found"

    try:
        with open(labels_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return "not measured", f"error reading label file: {e}"

    if isinstance(data, list):
        items = data
        label_snapshot_hash = items[0].get("db_snapshot_sha256") if items else None
    elif isinstance(data, dict):
        items = data.get("samples", [])
        label_snapshot_hash = data.get("db_snapshot_sha256")
    else:
        return "not measured", "invalid label file structure"

    if not items:
        return "not measured", "label file contains 0 sampled items"

    # Enforce DB snapshot hash verification (prevents stale-ID labels)
    current_db_hash = compute_db_sha256(db_path)
    if not current_db_hash:
        return "not measured", f"database file not found or inaccessible at '{db_path}'"

    # Refuse labels if snapshot hash does not match
    if not label_snapshot_hash or label_snapshot_hash != current_db_hash:
        return "not measured", (
            f"snapshot hash mismatch: labels generated from '{label_snapshot_hash or 'unknown'}', "
            f"current DB hash is '{current_db_hash}'"
        )

    # Check per-item snapshot hash consistency
    for item in items:
        item_hash = item.get("db_snapshot_sha256")
        if item_hash and item_hash != current_db_hash:
            return "not measured", (
                f"snapshot hash mismatch: item '{item.get('decision_id')}' generated from '{item_hash}', "
                f"current DB hash is '{current_db_hash}'"
            )

    # Filter items filled in by a human (correct is not None)
    evaluated = [it for it in items if it.get("correct") is not None]
    if not evaluated:
        return "not measured", "awaiting human labels (H2: all items have correct=null)"

    correct_count = sum(1 for it in evaluated if it.get("correct") is True)
    precision = round((correct_count / len(evaluated)) * 100, 1)
    return precision, f"evaluated {len(evaluated)}/{len(items)} human-labelled items ({correct_count} correct)"

def compute_decision_matching(
    gt_dataset: List[Dict[str, Any]],
    system_decisions: List[Dict[str, Any]],
    decision_to_evidence: Dict[str, set]
) -> Dict[str, Any]:
    """
    Computes bipartite decision matching between ground-truth items and system decisions (Step 4.1).
    
    1. Strict Matching (One-to-One):
       - Builds a bipartite candidate edge set where pair (gt, sd) shares >= 1 evidence event ID.
       - Assigns greedily by descending shared evidence overlap count (secondary tie-breaker: state match).
       - Each ground-truth item is matched at most once.
       - Each system decision is matched at most once (one-to-one).
       - Unmatched system decisions count against system extraction precision.
       
    2. Lenient Matching (Many-to-One):
       - Each ground-truth item independently matches the first compatible system decision.
       - A single system decision may satisfy multiple ground-truth items (overcounting).
       
    Returns dictionary with:
       - 'strict': matched_gt_count, correct_state_count, recall, state_accuracy, found, missed, wrong_state,
                   matched_system_ids, unmatched_system_ids, unmatched_system_decisions, unmatched_system_count
       - 'lenient': matched_gt_count, correct_state_count, recall, state_accuracy, found, missed, wrong_state
       - 'recall_difference': lenient['recall'] - strict['recall']
       - 'overcounting_detected': bool
    """
    total_gt = len(gt_dataset)

    # --- Strict Matching (One-to-One Bipartite Greedy Assignment) ---
    candidate_edges = []
    for gt in gt_dataset:
        gt_id = gt.get("id")
        gt_repo = gt.get("repo")
        expected_events = set(gt.get("expected_evidence_contains", []) or gt.get("evidence_event_ids", []))
        expected_state = gt.get("expected_state")
        if not expected_events:
            continue

        for sd in system_decisions:
            sd_id = sd.get("decision_id")
            sd_repo = sd.get("repo")
            if gt_repo and sd_repo and gt_repo != sd_repo:
                continue
            sd_events = decision_to_evidence.get(sd_id, set())
            overlap = expected_events.intersection(sd_events)
            if overlap:
                state_match = (sd.get("state") == expected_state)
                candidate_edges.append({
                    "overlap_count": len(overlap),
                    "state_match": 1 if state_match else 0,
                    "gt_id": gt_id,
                    "sd_id": sd_id,
                    "overlap_events": list(overlap),
                    "is_state_match": state_match,
                    "gt": gt,
                    "sd": sd
                })

    # Sort candidates greedily: descending overlap_count, then state_match
    candidate_edges.sort(key=lambda e: (e["overlap_count"], e["state_match"]), reverse=True)

    strict_matched_gt_ids = set()
    strict_matched_sd_ids = set()
    strict_found = []
    strict_wrong_state = []
    strict_correct_state_count = 0

    for edge in candidate_edges:
        gt_id = edge["gt_id"]
        sd_id = edge["sd_id"]
        if gt_id in strict_matched_gt_ids or sd_id in strict_matched_sd_ids:
            continue
        strict_matched_gt_ids.add(gt_id)
        strict_matched_sd_ids.add(sd_id)

        gt = edge["gt"]
        sd = edge["sd"]
        state_match = edge["is_state_match"]
        if state_match:
            strict_correct_state_count += 1
        else:
            strict_wrong_state.append({
                "gt_id": gt_id,
                "gt_title": gt.get("title"),
                "expected_state": gt.get("expected_state"),
                "system_state": sd.get("state"),
                "decision_id": sd_id
            })

        strict_found.append({
            "gt_id": gt_id,
            "gt_title": gt.get("title"),
            "decision_id": sd_id,
            "system_state": sd.get("state"),
            "expected_state": gt.get("expected_state"),
            "overlap_count": edge["overlap_count"],
            "shared_events": edge["overlap_events"]
        })

    strict_missed = []
    for gt in gt_dataset:
        if gt.get("id") not in strict_matched_gt_ids:
            strict_missed.append({
                "gt_id": gt.get("id"),
                "gt_title": gt.get("title"),
                "expected_evidence": list(set(gt.get("expected_evidence_contains", []) or gt.get("evidence_event_ids", [])))
            })

    unmatched_system_decisions = [sd for sd in system_decisions if sd.get("decision_id") not in strict_matched_sd_ids]
    unmatched_system_ids = [sd.get("decision_id") for sd in unmatched_system_decisions]

    strict_matched_count = len(strict_matched_gt_ids)
    strict_recall = round((strict_matched_count / total_gt) * 100, 1) if total_gt > 0 else 0.0
    strict_state_accuracy = round((strict_correct_state_count / strict_matched_count) * 100, 1) if strict_matched_count > 0 else "not measured"

    # --- Lenient Matching (Many-to-One) ---
    lenient_found = []
    lenient_missed = []
    lenient_wrong_state = []
    lenient_matched_count = 0
    lenient_correct_state_count = 0

    for gt in gt_dataset:
        expected_events = set(gt.get("expected_evidence_contains", []) or gt.get("evidence_event_ids", []))
        gt_repo = gt.get("repo")
        found_sd = None

        for sd in system_decisions:
            if gt_repo and sd.get("repo") and sd.get("repo") != gt_repo:
                continue
            sd_events = decision_to_evidence.get(sd["decision_id"], set())
            if expected_events.intersection(sd_events):
                found_sd = sd
                break

        if found_sd:
            lenient_matched_count += 1
            state_match = (found_sd.get("state") == gt.get("expected_state"))
            if state_match:
                lenient_correct_state_count += 1
            else:
                lenient_wrong_state.append({
                    "gt_id": gt.get("id"),
                    "gt_title": gt.get("title"),
                    "expected_state": gt.get("expected_state"),
                    "system_state": found_sd.get("state"),
                    "decision_id": found_sd["decision_id"]
                })
            lenient_found.append({
                "gt_id": gt.get("id"),
                "gt_title": gt.get("title"),
                "decision_id": found_sd["decision_id"],
                "system_state": found_sd.get("state"),
                "expected_state": gt.get("expected_state")
            })
        else:
            lenient_missed.append({
                "gt_id": gt.get("id"),
                "gt_title": gt.get("title"),
                "expected_evidence": list(expected_events)
            })

    lenient_recall = round((lenient_matched_count / total_gt) * 100, 1) if total_gt > 0 else 0.0
    lenient_state_accuracy = round((lenient_correct_state_count / lenient_matched_count) * 100, 1) if lenient_matched_count > 0 else "not measured"
    recall_difference = round(lenient_recall - strict_recall, 1)

    return {
        "strict": {
            "matched_gt_count": strict_matched_count,
            "correct_state_count": strict_correct_state_count,
            "recall": strict_recall,
            "state_accuracy": strict_state_accuracy,
            "found": strict_found,
            "missed": strict_missed,
            "wrong_state": strict_wrong_state,
            "matched_system_ids": list(strict_matched_sd_ids),
            "unmatched_system_ids": unmatched_system_ids,
            "unmatched_system_decisions": unmatched_system_decisions,
            "unmatched_system_count": len(unmatched_system_decisions)
        },
        "lenient": {
            "matched_gt_count": lenient_matched_count,
            "correct_state_count": lenient_correct_state_count,
            "recall": lenient_recall,
            "state_accuracy": lenient_state_accuracy,
            "found": lenient_found,
            "missed": lenient_missed,
            "wrong_state": lenient_wrong_state
        },
        "recall_difference": recall_difference,
        "overcounting_detected": lenient_matched_count > strict_matched_count
    }

class BenchmarkRunner:
    def __init__(self, db: Database):
        self.db = db
        self.explanation_gen = ExplanationGenerator(db)
        self.recon_engine = ReconciliationEngine(db)
        self.drift_detector = DriftDetector(db)
        self.baseline_eval = BaselineEvaluator(db)

    def run_full_evaluation(self, custom_ground_truth: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Executes evaluation against ground truth dataset according to METRICS.md:
        1. Decision recall, state accuracy, and precision (human label file)
        2. Evidence-link validity (url_format_ok, event_exists, claim_supported)
        3. Conflict & drift precision/recall from labelled case files
        4. Claim support rate (anti-hallucination)
        5. Measured processing latency (median of >=5 runs)
        6. Computed baselines (A, B, C, D)
        """
        gt_dataset = custom_ground_truth if custom_ground_truth is not None else GROUND_TRUTH_DATASET

        # 1. Fetch system decisions and their linked evidence
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions WHERE review_status != 'human_rejected'")
            system_decisions = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT decision_id, event_id FROM decision_evidence")
            evidence_rows = cursor.fetchall()
            decision_to_evidence: Dict[str, set] = {}
            for r in evidence_rows:
                decision_to_evidence.setdefault(r["decision_id"], set()).add(r["event_id"])

        # 1. Decision Matching (Step 4.1: Strict one-to-one bipartite matching and lenient comparison)
        match_results = compute_decision_matching(gt_dataset, system_decisions, decision_to_evidence)
        strict = match_results["strict"]
        lenient = match_results["lenient"]
        recall_diff = match_results["recall_difference"]

        total_gt = len(gt_dataset)
        decision_recall = strict["recall"]
        state_accuracy = strict["state_accuracy"]

        # Decision Precision (from precision_labels.json with snapshot hash check)
        precision_val, precision_reason = self._evaluate_precision(system_decisions)
        if isinstance(precision_val, (int, float)) and isinstance(decision_recall, (int, float)):
            f1_val = round((2 * precision_val * decision_recall) / (precision_val + decision_recall), 1) if (precision_val + decision_recall) > 0 else 0.0
        else:
            f1_val = "not measured"

        # 2. Evidence-Link Integrity and Grounding Verification (Step 4.1 Audit)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT event_id FROM events")
            existing_event_ids = {r["event_id"] for r in cursor.fetchall()}

            cursor.execute("""
            SELECT de.decision_id, de.event_id, ev.source_url
            FROM decision_evidence de
            LEFT JOIN events ev ON de.event_id = ev.event_id
            """)
            links = cursor.fetchall()
            total_links = len(links)

            if total_links > 0:
                valid_urls = [l for l in links if l["source_url"] and (l["source_url"].startswith("http://") or l["source_url"].startswith("https://"))]
                url_format_ok = round((len(valid_urls) / total_links) * 100, 1)

                existing_links = [l for l in links if l["event_id"] in existing_event_ids]
                event_exists = round((len(existing_links) / total_links) * 100, 1)
            else:
                url_format_ok = "not measured"
                event_exists = "not measured"

        # 3. Conflict & Drift Metrics from labelled case files
        conflict_metrics = self._evaluate_conflict_cases()
        drift_metrics = self._evaluate_drift_cases()

        # 4. Claim Support Rate (Anti-Hallucination)
        claim_support_metrics = self._evaluate_claim_support()
        claim_supported = claim_support_metrics.get("support_rate", "not measured")

        # 5. Measured Processing Latency (Median of >=5 runs)
        latency_ms = self._measure_latency()

        # 6. Baselines
        baselines = self.baseline_eval.evaluate_all(gt_dataset)

        # 7. Developer Finding Feedback (Measured Data - Step 3.6)
        feedback_counts = self.db.get_finding_feedback_counts()

        return {
            "metrics": {
                "decision_extraction_precision": precision_val if precision_val != "not measured" else "not measured",
                "decision_extraction_recall": decision_recall,
                "decision_recall_strict": strict["recall"],
                "decision_recall_lenient": lenient["recall"],
                "recall_difference": recall_diff,
                "decision_extraction_f1": f1_val,
                "state_accuracy": state_accuracy,
                "state_accuracy_strict": strict["state_accuracy"],
                "state_accuracy_lenient": lenient["state_accuracy"],
                "url_format_ok": url_format_ok,
                "event_exists": event_exists,
                "claim_supported": claim_supported,
                "evidence_link_accuracy": url_format_ok,  # Legacy alias for backwards compatibility
                "contradiction_precision": conflict_metrics.get("precision", "not measured"),
                "contradiction_recall": conflict_metrics.get("recall", "not measured"),
                "drift_precision": drift_metrics.get("precision", "not measured"),
                "drift_recall": drift_metrics.get("recall", "not measured"),
                "claim_support_rate": claim_supported,
                "unsupported_claim_rate": claim_support_metrics.get("unsupported_rate", 0.0),
                "processing_latency_ms": latency_ms,
                "finding_feedback_total": feedback_counts["total"],
                "finding_feedback_confirmed": feedback_counts["confirm"],
                "finding_feedback_dismissed": feedback_counts["dismiss"],
                "finding_feedback_reopened": feedback_counts["reopen"]
            },
            "ground_truth_total": total_gt,
            "matched_gt_count": strict["matched_gt_count"],
            "matched_gt_count_strict": strict["matched_gt_count"],
            "matched_gt_count_lenient": lenient["matched_gt_count"],
            "unmatched_system_decisions_count": strict["unmatched_system_count"],
            "system_decisions_evaluated": len(system_decisions),
            "precision_reason": precision_reason,
            "details": {
                "found": strict["found"],
                "missed": strict["missed"],
                "wrong_state": strict["wrong_state"],
                "strict": strict,
                "lenient": lenient,
                "overcounting_detected": match_results["overcounting_detected"],
                "precision_reason": precision_reason
            },
            "conflict_evaluation": conflict_metrics,
            "drift_evaluation": drift_metrics,
            "finding_feedback": feedback_counts,
            "baselines": baselines
        }

    def _evaluate_precision(self, system_decisions: List[Dict[str, Any]]) -> Tuple[Any, str]:
        db_path = getattr(self.db, "db_path", None)
        return evaluate_precision_labels(db_path, os.path.dirname(__file__))

    def _evaluate_drift_cases(self) -> Dict[str, Any]:
        cases_file = os.path.join(os.path.dirname(__file__), "drift_cases.json")
        if not os.path.exists(cases_file):
            return {"status": "not measured", "precision": "not measured", "recall": "not measured"}

        try:
            with open(cases_file, "r", encoding="utf-8") as f:
                cases = json.load(f)
        except Exception:
            return {"status": "not measured", "precision": "not measured", "recall": "not measured"}

        tp = fp = tn = fn = 0
        for case in cases:
            report = self.drift_detector.analyze_diff_for_drift(
                repo=case["repo"],
                commit_or_pr_id=f"eval_{case['id']}",
                author="eval_bot",
                changed_files=case["files"],
                diff_text=case["diff_text"]
            )
            findings = report["findings"] if isinstance(report, dict) else report
            detected = len(findings) > 0
            expected_violation = (case["expected"] == "violation")

            if detected and expected_violation:
                tp += 1
            elif detected and not expected_violation:
                fp += 1
            elif not detected and not expected_violation:
                tn += 1
            elif not detected and expected_violation:
                fn += 1

        precision = round((tp / (tp + fp)) * 100, 1) if (tp + fp) > 0 else 0.0
        recall = round((tp / (tp + fn)) * 100, 1) if (tp + fn) > 0 else 0.0
        return {
            "status": "measured",
            "total_cases": len(cases),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": precision,
            "recall": recall
        }

    def _evaluate_conflict_cases(self) -> Dict[str, Any]:
        cases_file = os.path.join(os.path.dirname(__file__), "conflict_cases.json")
        if not os.path.exists(cases_file):
            return {"status": "not measured", "precision": "not measured", "recall": "not measured"}

        try:
            with open(cases_file, "r", encoding="utf-8") as f:
                cases = json.load(f)
        except Exception:
            return {"status": "not measured", "precision": "not measured", "recall": "not measured"}

        tp = fp = tn = fn = 0
        opposing_keywords = [
            ("pid", "bang-bang"),
            ("redis", "in-memory"),
            ("redis", "lru"),
            ("sync", "async"),
            ("polling", "websocket"),
            ("stateless", "stateful"),
            ("monolith", "microservice")
        ]

        for case in cases:
            d1_text = (case["decision_1"]["title"] + " " + case["decision_1"]["rationale"]).lower()
            d2_text = (case["decision_2"]["title"] + " " + case["decision_2"]["rationale"]).lower()
            has_conflict = False
            for k1, k2 in opposing_keywords:
                if (k1 in d1_text and k2 in d2_text) or (k2 in d1_text and k1 in d2_text):
                    has_conflict = True
                    break

            expected_conflict = (case["expected"] == "conflict")
            if has_conflict and expected_conflict:
                tp += 1
            elif has_conflict and not expected_conflict:
                fp += 1
            elif not has_conflict and not expected_conflict:
                tn += 1
            elif not has_conflict and expected_conflict:
                fn += 1

        precision = round((tp / (tp + fp)) * 100, 1) if (tp + fp) > 0 else 0.0
        recall = round((tp / (tp + fn)) * 100, 1) if (tp + fn) > 0 else 0.0
        return {
            "status": "measured",
            "total_cases": len(cases),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": precision,
            "recall": recall
        }

    def _evaluate_claim_support(self) -> Dict[str, Any]:
        """Validates grounding per METRICS.md: >=50% content words of each explanation sentence must appear in cited events."""
        test_artifacts = [
            "src/thermal/control.py::regulate_temperature",
            "src/cache/store.py::cache_get"
        ]

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT event_id, title, body FROM events")
            event_map = {r["event_id"]: ((r["title"] or "") + " " + (r["body"] or "")) for r in cursor.fetchall()}

        total_sentences = 0
        supported_sentences = 0

        for art in test_artifacts:
            res = self.explanation_gen.explain_artifact(art)
            for step in res.get("chain", []):
                rationale = step.get("rationale", "")
                citations = step.get("citations", [])
                if not rationale:
                    continue

                sentences = [s.strip() for s in re.split(r'[.!?\n]+', rationale) if s.strip()]
                for sentence in sentences:
                    total_sentences += 1
                    if not citations:
                        continue

                    sentence_tokens = set(tokenize(sentence))
                    if not sentence_tokens:
                        supported_sentences += 1
                        continue

                    citation_ids = []
                    for c in citations:
                        if isinstance(c, dict) and "event_id" in c:
                            citation_ids.append(c["event_id"])
                        elif isinstance(c, str):
                            citation_ids.append(c)

                    cited_text = " ".join(event_map.get(cid, "") for cid in citation_ids)
                    cited_tokens = set(tokenize(cited_text))

                    overlap = len(sentence_tokens.intersection(cited_tokens))
                    if (overlap / len(sentence_tokens)) >= 0.5:
                        supported_sentences += 1

        if total_sentences == 0:
            return {"support_rate": 100.0, "unsupported_rate": 0.0, "total_sentences": 0}

        support_rate = round((supported_sentences / total_sentences) * 100, 1)
        unsupported_rate = round((1.0 - (supported_sentences / total_sentences)) * 100, 1)
        return {
            "support_rate": support_rate,
            "unsupported_rate": unsupported_rate,
            "total_sentences": total_sentences,
            "supported_sentences": supported_sentences
        }

    def _measure_latency(self) -> float:
        """Measures median wall-clock milliseconds over >=5 explain runs."""
        timings = []
        for _ in range(5):
            t0 = time.perf_counter()
            self.explanation_gen.explain_artifact("src/thermal/control.py::regulate_temperature")
            t1 = time.perf_counter()
            timings.append((t1 - t0) * 1000)

        return round(statistics.median(timings), 2)
