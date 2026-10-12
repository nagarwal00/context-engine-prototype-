# CIF Documentation Changelog: Extraction Refinements

This document tracks empirical performance and extraction precision improvements across iterations.

---

## Step 3.1: Trivial Commit Filtering & Noise Reduction

### Motivation
In initial prototypes, mechanical commits (e.g., "Added README", "Added requirements.txt", "bump version", "fix typo") were ingested as architectural decisions whenever keywords occurred, resulting in false-positive architectural records.

### Implementation
- Added `is_decision_candidate(event)` in `backend/engine/extractor.py`.
- Enforces strict rejection patterns:
  1. Conventional trivial commit prefixes (`added (readme|license|requirements.txt)`, `updated docs`, `fix typo`, `merge branch`, `bump version`, `chore: ...`).
  2. Non-code artifact filtering (events touching purely `.md`, `.txt`, `.lock`, or config files are excluded unless explicit architectural decision markers like `"decided to"`, `"opted for"`, or `"instead of"` appear).
  3. Short empty messages (<5 title chars, <15 body chars).
- ADR events are always preserved as authoritative.

### Verification & Empirical Impact
- **Unit Testing**: Verified in `tests/test_extractor.py` with 10 positive architectural candidates (10/10 accepted) and 10 negative trivial commits (10/10 rejected).
- **WhyBench Dev Split Recall**:
  - Before filtering: 55.6% recall with false-positive noise from trivial commits.
  - After filtering: 55.6% recall with 0% trivial commit pollution in the indexed decision space.
  - State Accuracy: 100.0% on verified architectural decisions.
  - Refusal Accuracy: 100.0% on undocumented / negative decision questions.

---

## Step 4.4: Recall Improvement from Failure Analysis (Dev Split Only)

### Motivation & Error Category Diagnosis
In Step 4.3 failure analysis (`tools/analyze_failures.py --split dev`), 8 ground-truth items were missed:
1. **`wrong_evidence` (5 misses)**:
   - Root causes:
     - Events missing narrow keywords fell through to a fallback placeholder decision with `evidence_event_ids=[]`, generating 47 false-positive decisions and empty evidence citations (`WB_PAY_02`, `WB_PAY_05`, `WB_CH_02`, `WB_CH_04`, `WB_CLI_02`).
     - PR decisions closing issues did not link closed issues into decision evidence (`ev.parent_event_ids` ignored).
     - `git_commit` source type was omitted from decision extraction (`WB_PAY_05`).
2. **`no_candidate` (3 misses)**:
   - Root causes:
     - PR review comments containing explicit rejection cues (`reject`, `rejected`, `must reject`) were unparsed (`WB_PAY_03`, `WB_CH_02`, `WB_CLI_02`).
     - Standard architectural action verbs in PR titles (`Implement`, `Add`, `Pinning`) were not covered by the narrow keyword list (`WB_CH_06`, `WB_CLI_04`).

### Implementation
- **Source Type Expansion**: Supported `git_commit` and `github_issue` alongside `github_pr` and `pr_review_comment` in `backend/engine/extractor.py`.
- **Rejection Signal Detection & State Classification**:
  - Implemented `REJECTION_PATTERNS` (`reject`, `rejected`, `must reject`, `cannot use`, `not viable`, `abandoned`).
  - PR review comments containing rejection cues extract decisions with `state="rejected"` and record the rejected proposal under `alternatives_considered`.
- **Affirmative Architectural Intent Markers**:
  - Broadened signals (`implement`, `adopt`, `migrat*`, `switch to`, `enable`, `introduce`, `support`, `isolate`, `batch`, `pinning`, `feat:`, `refactor:`).
- **Parent Event ID Propagation**:
  - PR decisions closing issues now attach `[ev.event_id] + list(ev.parent_event_ids)` into `evidence_event_ids`, grounding the decision in both the PR implementation and the underlying issue.
- **Noise Elimination**:
  - Trivial events without architectural intent return `[]` rather than polluting the database with empty-evidence dummy records.

### Empirical Performance Comparison on Dev Split

| Metric | Pre-Improvement (Step 4.3) | Post-Improvement (Step 4.4) | Change |
|---|:---:|:---:|:---:|
| **Standard Questions Evaluated** | 18 | 18 | - |
| **Strict True Positives (TP)** | 10 | **18** | **+8 (+80.0%)** |
| **Strict Decision Recall** | 55.6% | **100.0%** | **+44.4%** |
| **Strict State Accuracy** | 100.0% (10/10) | **100.0% (18/18)** | **Maintained** |
| **Task 1 Evidence Hit Rate** | 55.6% | **100.0% (18/18)** | **+44.4%** |
| **Refusal Accuracy** | 100.0% (6/6) | **100.0% (6/6)** | **Maintained** |
| **Total Failure Count** | 8 | **0** | **-8 (-100%)** |
| *— `not_ingested`* | 0 | 0 | 0 |
| *— `no_candidate`* | 3 | **0** | **-3** |
| *— `filtered`* | 0 | 0 | 0 |
| *— `wrong_evidence`* | 5 | **0** | **-5** |
| *— `wrong_state`* | 0 | 0 | 0 |
| **False Positive Decisions** | 47 | **22** | **-25 (-53.2%)** |

### Confidence Threshold Sweep & Precision/Recall Curve (Dev Split)
Evaluated via `tools/sweep_thresholds.py` across confidence thresholds $\theta \in [0.50, 0.95]$:

| Threshold ($\theta$) | Decisions Kept | True Positives (TP) | False Positives (FP) | Recall | Precision | F1 Score |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| $\theta \ge 0.50$ | 40 | 18 | 22 | 100.0% | 45.0% | 62.1% |
| $\theta \ge 0.60$ | 40 | 18 | 22 | 100.0% | 45.0% | 62.1% |
| $\theta \ge 0.70$ | 39 | 18 | 21 | 100.0% | 46.2% | 63.2% |
| $\theta \ge 0.80$ | 39 | 18 | 21 | 100.0% | 46.2% | 63.2% |
| $\theta \ge 0.85$ | 39 | 18 | 21 | 100.0% | 46.2% | 63.2% |
| $\theta \ge 0.90$ | 16 | 10 | 6 | 55.6% | 62.5% | 58.8% |
| $\theta \ge 0.95$ | 15 | 9 | 6 | 50.0% | 60.0% | 54.5% |

*Tuning was conducted strictly on the `dev` split; `test_v1` and `test_v2` were not accessed.*
