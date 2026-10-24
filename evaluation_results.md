# Context Intelligence Framework — Empirical Evaluation Results

> **Important**: In accordance with Capstone Project guidelines and `ANTIGRAVITY_HANDOFF_V2.md`, **no metric, percentage, or baseline in this report is fabricated or hand-edited**. All numbers are automatically generated from reproducible run manifests.

---

## 1. WhyBench: Real-World Benchmark Corpus

Evaluated via `tools/run_whybench.py --split test_v2` (Manifest: `results/test_v2_20261013_100423/manifest.json`).

- **Split**: `test_v2`
- **Total Questions Evaluated**: 71
- **Standard Positive Questions**: 26
- **Negative Refusal Questions**: 45
- **Database Snapshot SHA-256**: `26bd603a325232bd25e2e0fce3ef17daf916629f61bc25324b2afdd1ed8cc63d`
- **Git Commit**: `216b7cb08de014daaf7cf932af7f8fb8a1955855` (clean)

### 1.1 Task 1 — Evidence Retrieval ("Find the sources that explain X")
*Comparable across CIF and search baselines evaluated on identical positive questions (`expected_state != 'none'`).*

| System / Baseline | Method | Input Received | Task 1 Hit Rate (Positives) | 95% CI (Wilson) | Refusal (Abstention) | Status |
|---|---|---|:---:|:---:|:---:|:---:|
| **CIF (Context Intelligence)** | Provenance Graph Traversal | Natural language question | **80.8%** (21/26) | [62.1%, 91.5%] | **64.4%** (29/45 abstained) | Measured |
| **Baseline A** | Keyword Token Overlap (BM25) | Natural language question | **92.3%** (24/26) | [75.9%, 97.9%] | *n/a (always answers)* | Measured |
| **Baseline B** | Docs-Only Search (`adr, doc`) | Natural language question | **23.1%** (6/26) | [11.0%, 42.0%] | *n/a (always answers)* | Measured |
| **Baseline C** | Plain LLM over Repo Text | Natural language question | *not measured* | *not measured* | *not measured* | `CIF_LLM_API_KEY` unset |
| **Baseline D** | GitHub Copilot Manual Labels | Natural language question | *not measured* | *not measured* | *not measured* | No manual labels |

> *Footnote: CIF's metric is decision-evidence match, not ranked retrieval; BM25 retrieval is higher. CIF's value is state classification, abstention and guard rules (see Task 2).*

#### Task 1 Per-Repository Breakdown

| Repository | Questions (Std / Refusal) | CIF Event Hit Rate | Baseline A (BM25) | Baseline B (Docs) |
|---|:---:|:---:|:---:|:---:|
| `acme-ecommerce/payment-core` | 10 / 15 | **80.0%** (8/10) | **90.0%** (9/10) | **20.0%** (2/10) |
| `cli/cli` | 8 / 15 | **87.5%** (7/8) | **100.0%** (8/8) | **25.0%** (2/8) |
| `cloud-hypervisor/cloud-hypervisor` | 8 / 15 | **75.0%** (6/8) | **87.5%** (7/8) | **25.0%** (2/8) |

### 1.2 Task 2 — Decision Reconstruction (Lifecycle State, Rationale, Alternatives, Supersession)
*Evaluates structured architectural model extraction and lifecycle fidelity. Search baselines cannot perform this task and are marked `n/a`.*

| System / Baseline | Method | Task 2 Strict Recall (1-to-1) | Task 2 Lenient Recall | State Accuracy | Refusal Accuracy | Status |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **CIF (Context Intelligence)** | Reconciled Lifecycle + Invariants | **80.8%** (21/26) | **80.8%** (21/26) | **100.0%** (21/21, small n) | **64.4%** (29/45) | Measured |
| **Baseline A** | Keyword Search (Grep/BM25) | **n/a** | **n/a** | **n/a** | **n/a (always answers)** | Unstructured search only |
| **Baseline B** | Docs-Only Search | **n/a** | **n/a** | **n/a** | **n/a (always answers)** | Unstructured search only |
| **Baseline C** | Plain LLM over Repo Text | *not measured* | *not measured* | *not measured* | *not measured* | `CIF_LLM_API_KEY` unset |
| **Baseline D** | GitHub Copilot Manual Labels | *not measured* | *not measured* | *not measured* | *not measured* | No manual labels |

#### Task 2 Per-Repository Breakdown

| Repository | Strict Recall (1-to-1) | Lenient Recall | State Accuracy | Refusal Accuracy | Decision Precision |
|---|:---:|:---:|:---:|:---:|:---:|
| `acme-ecommerce/payment-core` | **80.0%** (8/10) | 80.0% | **100.0%** (8/8) | **66.7%** (10/15) | not measured |
| `cli/cli` | **87.5%** (7/8) | 87.5% | **100.0%** (7/7) | **53.3%** (8/15) | not measured |
| `cloud-hypervisor/cloud-hypervisor` | **75.0%** (6/8) | 75.0% | **100.0%** (6/6) | **73.3%** (11/15) | not measured |

#### Honest Task Analysis
1. **Task 1 (Evidence Retrieval)**: On identical positive questions, BM25 achieves **92.3%** (24/26) and Docs-only achieves **23.1%** (6/26) vs CIF's **80.8%** (21/26) decision-evidence match. BM25 raw token retrieval is higher; CIF's contribution is state classification, evidence grounding invariant, and negative abstention (see Task 2).
2. **Task 2 (Decision Reconstruction)**: Baseline A and B cannot classify states (`accepted` vs `rejected`), extract alternatives, or abstain on unrecorded topics (returning 0% refusal). CIF achieves **100.0% (21/21 matched decisions, small n)** State Accuracy and abstains correctly on 29/45 (64.4%) of unrecorded-topic questions; 16/45 receive an unsupported decision — see LIMITATIONS.
3. **Overcounting Gap**: Under audited one-to-one strict matching (Step 4.1), CIF achieves **80.8%** strict recall vs **80.8%** lenient recall (gap: `+0.0%`).

---

### 1.3 Confidence Quality and Calibration (Step 4.7)

> **Status**: *not measured* (not enough labels for calibration).
> Labelled predictions: **0** / 100 required for calibration. Heuristic scores remain explicitly marked as **uncalibrated** in UI and API (`Heuristic score (uncalibrated): XX%`).

---

## 2. Decision Guard Rules Evaluation (Step 3.4 & 3.5)

Evaluated against `backend/evaluation/drift_cases.json` (20 labelled test cases, including 10 violation cases and 10 negative/ok cases):

| Configuration | Test Cases | True Positives (TP) | False Positives (FP) | True Negatives (TN) | False Negatives (FN) | Precision | Recall |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Without Guard Rules** (Heuristic drift only) | 20 | 8 | 1 | 9 | 2 | **88.9%** | **80.0%** |
| **With Active Guard Rules** (`forbid_import`, `pattern`, etc.) | 20 | 10 | 1 | 9 | 0 | **90.9%** | **100.0%** |

### Key Findings
1. **Zero False Negatives in Demo Suite**: Guard rules provide 100.0% recall on forbidden import additions (`forbid_import`) across the 20 authored demo drift cases, ensuring that previously rejected libraries (e.g. `sticky_sessions`, raw synchronous balloon deflaters) cannot be silently reintroduced.
2. **Deterministic Enforcement**: Guard rules execute on added lines (`+`) in pull request diffs using deterministic AST and regex matching.

---

## 3. Synthetic Pilot Repositories (Smoke Test Suite)

Evaluated on synthetic pilot repositories (`acme-eng/thermal-control-system` and `acme-eng/distributed-cache-service`):

| Metric | Measured Value | Target / Interpretation |
|---|:---:|---|
| **Mechanical Invariant Enforcement** | **100.0%** (0 unevidenced decisions) | Non-negotiable database constraint in `backend/db.py` |
| **Evidence Link Validity** | **100.0%** | All links point to valid HTTP/HTTPS GitHub URLs |
| **Claim Support Rate** | **100.0%** (Unsupported: 0.0%) | Sentences in explanation chains cite valid evidence |
| **Processing Latency (Median of 5 runs)** | **12.4 ms** | In-process SQLite + Python graph query |
| **Automated Verification Suite** | **21 / 21 Checks Passed** | Verified via `python run_demo.py` |
| **Full Unit Test Suite** | **169+ Tests Passed** | Verified via `python -m unittest discover -s tests -v` |

---

## 4. Reproducibility Manifest (Step 4.8)

- **Manifest File**: `results/test_v2_20261013_100423/manifest.json`
- **Run Timestamp**: `2026-10-13T10:04:34.739827`
- **Python Version**: `3.11.6`
- **Git Commit HEAD**: `216b7cb08de014daaf7cf932af7f8fb8a1955855`
- **Working Tree Clean**: `True`
- **Extractor Mode**: `heuristic`
- **Decision Threshold**: `0.85`
- **Random Seed**: `1234`
- **Cryptographic Hashes (SHA-256)**:
  * `conflict_cases_sha256`: `80f9337b9e01a7bad2c46402270c28151973610ef250cf7f867fe0d4aee2d548`
  * `dataset_version`: `whybench_v1`
  * `db_snapshot_sha256`: `26bd603a325232bd25e2e0fce3ef17daf916629f61bc25324b2afdd1ed8cc63d`
  * `drift_cases_sha256`: `1c9ee61e648ef1508faca6c00d7536ce0acb3447597cb91ab0cfb66998722f71`
  * `precision_labels_sha256`: `55e7a53f5c5af86e9948abaa80c7d8fc406ea8f6d49f6fb97411aa609e68fbce`
  * `questions_sha256`: `1e46e50dd8a35f6d6a7c33b7b5472521e982b4ff907cd91584a0bb962f9d94ab`
