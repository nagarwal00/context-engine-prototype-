# Context Intelligence Framework — Empirical Evaluation Results

> **Important**: In accordance with Capstone Project guidelines and `docs/process/ANTIGRAVITY_HANDOFF_V2.md`, **no metric, percentage, or baseline in this report is fabricated or hand-edited**. All numbers are automatically generated from reproducible run manifests.

> **Benchmark Notice**: **Synthetic benchmark — see LIMITATIONS**. WhyBench-Synth is a hand-authored benchmark designed to test internal decision lifecycle tracking, evidence grounding invariants, and abstention behavior.

## 1. WhyBench-Synth (Hand-Authored Synthetic Benchmark)

Evaluated via `tools/run_whybench.py --split dev` (Manifest: `results/dev_20261118_015631/manifest.json`).

- **Split**: `dev`
- **Total Questions Evaluated**: 63
- **Standard Positive Questions**: 18
- **Negative Refusal Questions**: 45
- **Database Snapshot SHA-256**: `29103efda94c9debd4880ebebc42ce2ea76cfe1fa60a9ccff6362012417471dc`
- **Git Commit**: `1a27baf892a1ff89fc930f5bcbab5d0ea1e4abaa` (dirty)

### 1.1 Task 1 — Evidence Retrieval ("Find the sources that explain X")
*Comparable across CIF and search baselines evaluated on identical positive questions (`expected_state != 'none'`).*

| System / Baseline | Method | Input Received | Task 1 Top-5 Hit Rate | Refusal (Abstention) | Status |
|---|---|---|:---:|:---:|:---:|
| **CIF (Context Intelligence)** | Provenance Graph Traversal | Natural language question | **100.0%** (18/18) | **64.4%** (29/45 abstained) | Measured |
| **Baseline A** | Keyword Token Overlap (BM25) | Natural language question | **100.0%** | *n/a (always answers)* | Measured |
| **Baseline B** | Docs-Only Search (`adr, doc`) | Natural language question | **50.0%** | *n/a (always answers)* | Measured |
| **Baseline C** | Plain LLM over Repo Text | Natural language question | *not measured* | *not measured* | `CIF_LLM_API_KEY` unset |
| **Baseline D** | GitHub Copilot Manual Labels | Natural language question | *not measured* | *not measured* | No manual labels |

#### Task 1 Per-Repository Breakdown

| Repository | Questions (Std / Refusal) | CIF Event Hit Rate | Baseline A (BM25) | Baseline B (Docs) |
|---|:---:|:---:|:---:|:---:|
| `acme-ecommerce/payment-core` | 6 / 15 | **100.0%** (6/6) | 100.0% | 50.0% |
| `cli/cli` | 6 / 15 | **100.0%** (6/6) | 100.0% | 50.0% |
| `cloud-hypervisor/cloud-hypervisor` | 6 / 15 | **100.0%** (6/6) | 100.0% | 50.0% |

### 1.2 Task 2 — Decision Reconstruction (Lifecycle State, Rationale, Alternatives, Supersession)
*Evaluates structured architectural model extraction and lifecycle fidelity. Search baselines cannot perform this task and are marked `n/a`.*

| System / Baseline | Method | Task 2 Strict Recall (1-to-1) | Task 2 Lenient Recall | State Accuracy | Refusal Accuracy | Status |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **CIF (Context Intelligence)** | Reconciled Lifecycle + Invariants | **100.0%** (18/18) | **100.0%** (18/18) | **100.0%** (18/18, small n) | **64.4%** (29/45) | Measured |
| **Baseline A** | Keyword Search (Grep/BM25) | **n/a** | **n/a** | **n/a** | **n/a (always answers)** | Unstructured search only |
| **Baseline B** | Docs-Only Search | **n/a** | **n/a** | **n/a** | **n/a (always answers)** | Unstructured search only |
| **Baseline C** | Plain LLM over Repo Text | *not measured* | *not measured* | *not measured* | *not measured* | `CIF_LLM_API_KEY` unset |
| **Baseline D** | GitHub Copilot Manual Labels | *not measured* | *not measured* | *not measured* | *not measured* | No manual labels |

#### Task 2 Per-Repository Breakdown

| Repository | Strict Recall (1-to-1) | Lenient Recall | State Accuracy | Refusal Accuracy | Decision Precision |
|---|:---:|:---:|:---:|:---:|:---:|
| `acme-ecommerce/payment-core` | **100.0%** (6/6) | 100.0% | **100.0%** (6/6) | **66.7%** (10/15) | not measured |
| `cli/cli` | **100.0%** (6/6) | 100.0% | **100.0%** (6/6) | **53.3%** (8/15) | not measured |
| `cloud-hypervisor/cloud-hypervisor` | **100.0%** (6/6) | 100.0% | **100.0%** (6/6) | **73.3%** (11/15) | not measured |

#### Honest Task Analysis
1. **Task 1 (Evidence Retrieval)**: CIF achieves **100.0%** event retrieval vs **100.0%** for BM25 and **50.0%** for Docs-only.
2. **Task 2 (Decision Reconstruction)**: Baseline A and B cannot classify states (`accepted` vs `rejected`), extract alternatives, or abstain on unrecorded topics (returning 0% refusal). CIF achieves **100.0% (18/18 matched decisions, small n)** State Accuracy and abstains correctly on 29/45 (64.4%) of unrecorded-topic questions; 16/45 receive an unsupported decision — see LIMITATIONS.
3. **Overcounting Gap**: Under audited one-to-one strict matching (Step 4.1), CIF achieves **100.0%** strict recall vs **100.0%** lenient recall (gap: `+0.0%`).

---

### 1.3 Confidence Quality and Calibration (Step 4.7)

> **Status**: *not measured* (not enough labels for calibration).
> Labelled predictions: **0** / 100 required for calibration. Heuristic scores remain explicitly marked as **uncalibrated** in UI and API (`Heuristic score (uncalibrated): XX%`).

---

## 2. Decision Guard Rules Evaluation (Step 3.4 & 3.5)

### 2.1 Authored Demo Drift Cases
Evaluated against `backend/evaluation/drift_cases.json` (20 labelled test cases across thermal and cache demo domains):

| Configuration | Test Cases | True Positives (TP) | False Positives (FP) | True Negatives (TN) | False Negatives (FN) | Precision | Recall |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Without Guard Rules** (Heuristic drift only) | 20 | 8 | 1 | 9 | 2 | **88.9%** | **80.0%** |
| **With Active Guard Rules** (`forbid_import`, `pattern`, etc.) | 20 | 10 | 0 | 10 | 0 | **100.0%** | **100.0%** |

> *original 20 cases use authored demo rules; hold-out measures generalisation*

### 2.2 Untouched Hold-Out Drift Evaluation (Third Domain)
Evaluated against `backend/evaluation/holdout/cases.json` (16 cases in `acme-eng/job-queue-service`) using generic guard rules synthesized from `backend/evaluation/holdout/decisions.json` without domain keywords:

| Suite / Domain | Test Cases | True Positives (TP) | False Positives (FP) | True Negatives (TN) | False Negatives (FN) | Precision | Recall | Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Hold-Out (Generic Rules)** | 16 | 8 | 0 | 8 | 0 | **100.0%** | **100.0%** | Measured |

- **Synthesized Rules Enforced**: 13 generic rules.
- **Generalisation Invariant**: Zero domain keywords hard-coded in engine source; all rules extracted from decision syntax and links.

### Key Findings
1. **Zero False Negatives in Demo Suite**: Guard rules provide 100.0% recall on forbidden import additions (`forbid_import`) across the 20 authored demo drift cases, ensuring that previously rejected libraries cannot be silently reintroduced.
2. **Generalisation on Hold-Out Set**: The generic rule synthesizer extracts clean boundaries on the hold-out domain, correctly identifying all violations while ignoring comments, deletions, and near-miss substrings.
3. **Deterministic Enforcement**: Guard rules execute on added lines (`+`) in pull request diffs using deterministic AST and regex matching.

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
| **Full Unit Test Suite** | **352 Tests Passed** | Verified via `python -m unittest discover -s tests -v` |

---

## 4. Reproducibility Manifest (Step 4.8)

- **Manifest File**: `results/dev_20261118_015631/manifest.json`
- **Run Timestamp**: `2026-11-18T01:56:34.492580`
- **Python Version**: `3.11.6`
- **Git Commit HEAD**: `1a27baf892a1ff89fc930f5bcbab5d0ea1e4abaa`
- **Working Tree Clean**: `False`
- **Extractor Mode**: `heuristic`
- **Decision Threshold**: `0.85`
- **Random Seed**: `1234`
- **Cryptographic Hashes (SHA-256)**:
  * `conflict_cases_sha256`: `80f9337b9e01a7bad2c46402270c28151973610ef250cf7f867fe0d4aee2d548`
  * `dataset_version`: `whybench_v1`
  * `db_snapshot_sha256`: `29103efda94c9debd4880ebebc42ce2ea76cfe1fa60a9ccff6362012417471dc`
  * `drift_cases_sha256`: `1c9ee61e648ef1508faca6c00d7536ce0acb3447597cb91ab0cfb66998722f71`
  * `precision_labels_sha256`: `1790af198b129afa2991aaa5aff44a207d37bf52bc4a667f8d1e3afa2e695254`
  * `questions_sha256`: `6d33ebbcf613f870a99fd755b2ebb371e66520ea1615f33ea87750f6c151deed`
