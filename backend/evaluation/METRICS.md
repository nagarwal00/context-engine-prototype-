# Evaluation Metrics Specification

This document formally defines the metrics computed by the Context Intelligence Framework (CIF) evaluation suite. All metrics reported by the system are derived deterministically from real data and labelled evaluation sets; no metric values are hard-coded.

---

## 1. Ground Truth Matching Rule (GT Decision ↔ System Decision)

A ground-truth (GT) decision is considered **found** if and only if:
1. There exists at least one system decision in the same repository that does not have `review_status == "human_rejected"`.
2. The system decision shares at least one event ID with the GT item's `expected_evidence_contains` list.

*Note:* Title word overlap or semantic substring matching is explicitly **not** used for matching due to fragility and false positives.

---

## 2. Decision Recall

$$\text{Decision Recall} = \frac{\text{Count of found GT decisions}}{\text{Total count of GT decisions}}$$

- If total GT decisions is 0, recall is reported as `not measured` or `0.0`.
- The benchmark output must list detailed item IDs for `found` and `missed` GT decisions.

---

## 3. State Accuracy

$$\text{State Accuracy} = \frac{\text{Count of found GT decisions where system } \texttt{state} == \text{GT } \texttt{expected\_state}}{\text{Count of found GT decisions}}$$

- If count of found GT decisions is 0, state accuracy is reported as `not measured` or `0.0`.
- The benchmark output must list detailed item IDs for `wrong_state` decisions.

---

## 4. Decision Precision

$$\text{Decision Precision} = \frac{\text{Count of sampled system decisions labeled as correct}}{\text{Total count of sampled system decisions evaluated}}$$

- Grounded validity labels are loaded from `backend/evaluation/precision_labels.json`.
- If the label file is missing, empty, or all entries have `correct: null`, precision is reported as `"not measured"`.
- Precision must never be fabricated or assigned an unmeasured default.

---

## 5. Evidence-Link Validity

$$\text{Evidence-Link Validity} = \frac{\text{Count of decision evidence links where event exists in } \texttt{events} \text{ and has non-empty http(s) } \texttt{source\_url}}{\text{Total count of decision evidence links in DB}}$$

- This metric mechanically validates link integrity and provenance availability (i.e., that the referenced event exists and links to a valid external URL).
- It checks that the link exists and is well-formed, not subjective human correctness.

---

## 6. Claim Support Rate (Grounding Invariant)

For each sentence in every generated explanation:
1. The sentence must cite $\ge 1$ evidence event ID.
2. The sentence is considered **supported** if at least 50% of its content words (lower-cased, stop-words removed, words with length $> 3$ characters) appear in the concatenated title and body of the cited evidence events.
3. Unsupported Claim Rate is defined as:

$$\text{Claim Support Rate} = \frac{\text{Count of supported explanation sentences}}{\text{Total count of explanation sentences}}$$

$$\text{Unsupported Claim Rate} = 1.0 - \text{Claim Support Rate}$$

The standard English stop-word list used for token filtering is defined centrally in `backend.evaluation.benchmark.STOP_WORDS`.

---

## 7. Conflict Precision, Drift Precision & Recall

Computed against standardized labelled evaluation suites (`conflict_cases.json` and `drift_cases.json`):
- **Conflict Precision** = True Positive Conflicts / (True Positive Conflicts + False Positive Conflicts)
- **Conflict Recall** = True Positive Conflicts / (True Positive Conflicts + False Negative Conflicts)
- **Drift Precision** = True Positive Drifts / (True Positive Drifts + False Positive Drifts)
- **Drift Recall** = True Positive Drifts / (True Positive Drifts + False Negative Drifts)

If case files are missing, these are reported as `"not measured"`.

---

## 8. Latency

Wall-clock processing latency measured in milliseconds using `time.perf_counter()`:
1. **Ingestion Latency**: Wall-clock duration to ingest and index a repository bundle.
2. **Explanation Latency**: Wall-clock duration to answer an `explain` query.
- Reported as the median value of >= 5 measured runs.

---
89: 
90: ## 9. Evidence Assessment Deterministic Rule (Step 3.2)
91: 
92: Evaluates corroboration and evidentiary quality for decisions deterministically using claim-level passage links and source group clustering.
93: 
94: **Design Choice Statement:** The thresholds defined below are explicit architectural design choices, not statistical probabilities or sample estimates.
95: 
96: | Label | Deterministic Rule Definition |
97: |---|---|
98: | `contradicted` | At least one `contradicting` relation from an active evidence source (not superseded by later evidence). |
99: | `strong` | $\ge 2$ independent source groups with direct support ($\ge 2$ direct groups). |
100: | `moderate` | 1 direct group plus $\ge 1$ other group of any relation (e.g. 1 direct + 1 indirect), OR $\ge 2$ independent indirect groups. |
101: | `weak` | Exactly 1 source group (e.g. 1 direct source without corroboration, or a single thread with multiple comments/copies). |
102: | `insufficient` | No evidence events recorded, or only 1 indirect group. |
103: 
104: ### Missing Corroboration & Review Routing:
105: - Decisions assessed as `weak`, `insufficient`, or `contradicted` automatically generate review-queue items (`/api/review-queue`) with human-readable rationale (e.g., "no independent source besides the ADR", "no outcome/test evidence linked").
106: - Explanation endpoints (`/api/explain`) abstain with `{ "status": "insufficient_evidence", "message": "..." }` when the governing decision has `evidence_assessment == "insufficient"` and no stronger source exists.
107: - Legacy extraction confidence scores are displayed as **"Heuristic score (uncalibrated)"** until calibration is proven.
