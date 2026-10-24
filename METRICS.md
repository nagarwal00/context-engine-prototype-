# Evaluation Metrics Specification

This document formally defines the metrics computed by the Context Intelligence Framework (CIF) evaluation suite. All metrics reported by the system are derived deterministically from real data and labelled evaluation sets; no metric values are hard-coded.

---

## 1. Ground Truth Matching Rule (GT Decision ↔ System Decision)

Matching between ground-truth (GT) labels and system decisions is performed strictly via shared evidence event IDs (never via fragile title keywords or substrings):

### 1.1 Strict Matching (One-to-One Bipartite Matching — Primary Metric)
1. **Bipartite Candidate Graph**: Construct candidate edges for any pair $(\text{GT}_i, \text{System}_j)$ within the same repository that share $\ge 1$ evidence event ID.
2. **Greedy Overlap Assignment**: Candidate edges are sorted in descending order of shared evidence overlap count (with state match as secondary tie-breaker).
3. **Mutual Exclusion**: Edges are assigned greedily such that each ground-truth item is matched at most once, and each system decision is matched at most once.
4. **Precision Accountability**: System decisions not matched to any ground-truth item count against extraction precision.

### 1.2 Lenient Matching (Many-to-One Comparison)
Each ground-truth item independently matches the first compatible system decision without mutual exclusion. Under lenient matching, a single system decision may satisfy multiple ground-truth items.

### 1.3 Overcounting Gap
$$\text{Recall Difference} = \text{Decision Recall}_{\text{lenient}} - \text{Decision Recall}_{\text{strict}}$$

Reporting both strict and lenient recall exposes any previous overcounting where one system decision satisfied multiple benchmark questions.

---

## 2. Decision Recall

$$\text{Decision Recall (Strict)} = \frac{\text{Count of uniquely matched GT decisions (One-to-One)}}{\text{Total count of GT decisions}}$$

- Strict recall is the canonical reported recall metric.
- If total GT decisions is 0, recall is reported as `not measured` or `0.0`.
- The benchmark output lists detailed item IDs for `found`, `missed`, and unmatched system decisions.

---

## 3. State Accuracy

$$\text{State Accuracy} = \frac{\text{Count of strictly matched GT decisions where system } \texttt{state} == \text{GT } \texttt{expected\_state}}{\text{Count of strictly matched GT decisions}}$$

- If count of found GT decisions is 0, state accuracy is reported as `not measured` or `0.0`.
- The benchmark output lists detailed item IDs for `wrong_state` decisions.

---

## 4. Decision Precision

$$\text{Decision Precision} = \frac{\text{Count of sampled system decisions labeled as correct}}{\text{Total count of sampled system decisions evaluated}}$$

- Grounded validity labels are loaded from `backend/evaluation/precision_labels.json`.
- If the label file is missing, empty, or all entries have `correct: null`, precision is reported as `"not measured"`.
- Precision must never be fabricated or assigned an unmeasured default.

---

## 5. Evidence-Link Integrity and Grounding Verification (Replaces Legacy Validity)

Legacy "Evidence-Link Validity" checked only string syntax. Step 4.1 replaces this with three distinct, explicit integrity checks:

1. **`url_format_ok` (Format Only)**:
   $$\text{url\_format\_ok} = \frac{\text{Count of decision evidence links with well-formed } \texttt{http(s)://} \text{ URL}}{\text{Total count of decision evidence links in DB}}$$
   *Explicitly designated as a format check only, never described as correctness or accuracy.*
2. **`event_exists` (Referential Integrity)**:
   $$\text{event\_exists} = \frac{\text{Count of decision evidence links where } \texttt{event\_id} \text{ exists in } \texttt{events} \text{ table}}{\text{Total count of decision evidence links in DB}}$$
3. **`claim_supported` (Substantive Grounding)**:
   Sentence-level support verification rate from Section 6. Legacy `evidence_link_accuracy` is retained only as an alias pointing to `url_format_ok`.

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

## 9. Evidence Assessment Deterministic Rule (Step 3.2)

Evaluates corroboration and evidentiary quality for decisions deterministically using claim-level passage links and source group clustering.

**Design Choice Statement:** The thresholds defined below are explicit architectural design choices, not statistical probabilities or sample estimates.

| Label | Deterministic Rule Definition |
|---|---|
| `contradicted` | At least one `contradicting` relation from an active evidence source (not superseded by later evidence). |
| `strong` | $\ge 2$ independent source groups with direct support ($\ge 2$ direct groups). |
| `moderate` | 1 direct group plus $\ge 1$ other group of any relation (e.g. 1 direct + 1 indirect), OR $\ge 2$ independent indirect groups. |
| `weak` | Exactly 1 source group (e.g. 1 direct source without corroboration, or a single thread with multiple comments/copies). |
| `insufficient` | No evidence events recorded, or only 1 indirect group. |

### Missing Corroboration & Review Routing:
- Decisions assessed as `weak`, `insufficient`, or `contradicted` automatically generate review-queue items (`/api/review-queue`) with human-readable rationale (e.g., "no independent source besides the ADR", "no outcome/test evidence linked").
- Explanation endpoints (`/api/explain`) abstain with `{ "status": "insufficient_evidence", "message": "..." }` when the governing decision has `evidence_assessment == "insufficient"` and no stronger source exists.
- Legacy extraction confidence scores are displayed as **"Heuristic score (uncalibrated)"** until calibration is proven.

---

## 10. Split Benchmark Task Definitions (Step 4.2)

To ensure fair comparisons and eliminate Direct Conflation of Unlike Tasks, the WhyBench evaluation corpus is formally partitioned into two distinct tasks:

### Task 1 — Evidence Retrieval ("Find the sources that explain X")
- **Input**: Natural language question or query regarding an architectural topic, decision, or component.
- **Systems Evaluated**: Comparable across CIF and all retrieval baselines:
  - **Baseline A (Keyword Search / BM25)**: Scores all events (commits, issues, PR discussions, ADRs) by token overlap.
  - **Baseline B (Documentation/ADR Search)**: Scores only documentation and ADR events by token overlap.
  - **CIF (Context Intelligence)**: Traverses the provenance graph to retrieve evidence events linked to relevant decisions.
- **What Each System Receives**: Natural language query string + repository identifier.
- **What Counts as Correct**: Top-$k$ event hit rate ($k=5$). The prediction is correct if $\ge 1$ retrieved event belongs to the question's expected evidence event set (`expected_evidence_contains`).
- **Refusal Scoring**: An unconditional top-$k$ retrieval baseline has no abstention mechanism; when asked about unrecorded decisions, it unconditionally returns top-$k$ noisy hits. Such baselines receive **`n/a (always answers)`** rather than a false 0% score. CIF can abstain with `status: "insufficient_evidence"`.

### Task 2 — Decision Reconstruction (Lifecycle State, Rationale, Alternatives, Supersession)
- **Input**: Raw repository history bundles (commits, PR reviews, issue threads, ADR documents).
- **Systems Evaluated**:
  - **CIF**: Structured candidate extraction, invariant verification, reconciled lifecycle state machine, and context graph.
  - **Baselines C & D (LLM / Copilot)**: Generative synthesis models evaluated when configured or manually labelled.
  - **Baselines A & B (Keyword / Docs Search)**: Cannot extract structured decisions, classify lifecycle states, or identify alternatives. Marked **`n/a`** across Task 2 columns.
- **What Each System Receives**: Full repository event stream and git tree diffs.
- **What Counts as Correct**:
  1. **Strict One-to-One Decision Recall**: Bipartite greedy assignment where candidate decision shares $\ge 1$ evidence event ID with GT label under strict mutual exclusion.
  2. **Decision State Accuracy**: State (`accepted`, `rejected`, `superseded`, `reopened`) strictly matches the ground truth expected state.
  3. **Grounded Rationale & Alternatives**: Rationale validated with $\ge 50\%$ content-token passage support; alternatives correctly preserved.
- **Refusal Scoring**: When evaluated against negative questions regarding unrecorded architectural areas, the system must refuse ("No recorded architectural decision found"). Refusal accuracy measures the percentage of unrecorded cases where the system correctly abstained rather than asserting an ungrounded decision (measured at 64.4% on `test_v2`; see LIMITATIONS). Baselines without refusal capability are marked `n/a (always answers)`.

