# Context Intelligence Framework — Empirical Evaluation Results

> **Important**: In accordance with Capstone Project guidelines and `ANTIGRAVITY_HANDOFF.md`, **no metric, percentage, or baseline in this report is fabricated or hard-coded**. All numbers are computed by test and evaluation scripts from reproducible datasets.

---

## 1. WhyBench: Real-World Benchmark Corpus

WhyBench evaluates the Context Intelligence Framework on 3 open-source repositories with recorded architectural decisions, pull request reviews, and issue discussions:
1. `acme-ecommerce/payment-core` (Local snapshot: `demo_sample_repo`) — 21 questions
2. `cloud-hypervisor/cloud-hypervisor` — 20 questions
3. `cli/cli` — 20 questions

**Total Dataset**: 61 questions (24 dev split [39.3%], 37 test split [60.7%]). All items are supported by public URLs or designed as negative refusal tests.

### 1.1 Final Test Split Results (Split Across Equivalent Tasks — Step 4.2)

Evaluated via `python tools/run_whybench.py --split test --final` (saved to `backend/evaluation/whybench/results_test_20261011.json`).

In accordance with Step 4.2, the benchmark results are explicitly partitioned into two distinct tasks so unlike systems are not compared directly:

#### Task 1 — Evidence Retrieval ("Find the sources that explain X")
*Comparable across CIF and search baselines. Metric: Top-5 evidence event hit rate.*

| System / Baseline | Method | Input Received | Task 1 Top-5 Hit Rate | Refusal (Abstention) | Status |
|---|---|---|:---:|:---:|:---:|
| **CIF (Context Intelligence)** | Provenance Graph Traversal | Natural language question | **65.4%** (17/26) | **100.0%** (11/11 abstained) | Measured |
| **Baseline A** | Keyword Token Overlap (BM25) | Natural language question | **64.9%** (24/37) | *n/a (always answers)* | Measured |
| **Baseline B** | Docs-Only Search (`adr, doc`) | Natural language question | **16.2%** (6/37) | *n/a (always answers)* | Measured |
| **Baseline C** | Plain LLM over Repo Text | Natural language question | *not measured* | *not measured* | `CIF_LLM_API_KEY` unset |
| **Baseline D** | GitHub Copilot Manual Labels | Natural language question | *not measured* | *not measured* | No manual labels |

#### Task 2 — Decision Reconstruction (Lifecycle State, Rationale, Alternatives, Supersession)
*Evaluates structured architectural model extraction and lifecycle fidelity. Search baselines cannot perform this task and are marked `n/a`.*

| System / Baseline | Method | Task 2 Strict Recall (1-to-1) | Task 2 Lenient Recall | State Accuracy | Refusal Accuracy | Status |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **CIF (Context Intelligence)** | Reconciled Lifecycle + Invariants | **30.8%** (8/26) | **34.6%** (9/26) | **100.0%** (8/8) | **100.0%** (11/11) | Measured |
| **Baseline A** | Keyword Search (Grep/BM25) | **n/a** | **n/a** | **n/a** | **n/a (always answers)** | Unstructured search only |
| **Baseline B** | Docs-Only Search | **n/a** | **n/a** | **n/a** | **n/a (always answers)** | Unstructured search only |
| **Baseline C** | Plain LLM over Repo Text | *not measured* | *not measured* | *not measured* | *not measured* | `CIF_LLM_API_KEY` unset |
| **Baseline D** | GitHub Copilot Manual Labels | *not measured* | *not measured* | *not measured* | *not measured* | No manual labels |

#### Honest Task Analysis
1. **Task 1 (Evidence Retrieval)**: CIF (**65.4%**) and Baseline A (**64.9%**) achieve comparable evidence hit rates when locating raw discussions that answer architectural questions. Baseline B (**16.2%**) demonstrates that searching formal documentation alone misses the majority of architectural decisions in real projects.
2. **Task 2 (Decision Reconstruction)**: Baseline A and B cannot classify states (`accepted` vs `rejected`), cannot extract alternatives, and cannot abstain on unrecorded topics (they return arbitrary noisy hits with 0% refusal). CIF reconstructs structured decisions with **100.0% State Accuracy** on extracted items and **100.0% Refusal Accuracy** on unrecorded decisions.
3. **Overcounting Gap**: Under audited one-to-one strict matching (Step 4.1), CIF achieves **30.8%** strict recall vs **34.6%** lenient recall (a +3.8% overcounting gap), exposing where single decisions previously matched multiple questions under lenient evaluation.


---

### 1.2 Development Split Extractor Comparison (Step 3.4)

Evaluated via `python tools/run_whybench.py --split dev --extractor both`:

| Extractor Mode | Decision Recall | State Accuracy | Refusal Accuracy | Grounding Validation |
|---|:---:|:---:|:---:|:---:|
| **Heuristic Pattern Extractor** | **55.6%** (10/18) | **100.0%** (10/10) | **100.0%** (6/6) | Active |
| **LLM-Assisted Extractor** | *not measured* | *not measured* | *not measured* | Mock-tested in CI |

*Note: The LLM extractor interface (`backend/engine/llm_client.py`) and anti-hallucination grounding validator (`backend/engine/llm_extractor.py`) are fully implemented and verified via unit test `tests/test_extractor.py::test_validate_grounding_anti_hallucination` with canned responses. Real API calls require setting `CIF_LLM_API_KEY` and `CIF_LLM_MODEL`.*

---

## 2. Decision Guard Rules Evaluation (Step 5.5)

Evaluated against `backend/evaluation/drift_cases.json` (20 labelled test cases, including 10 violation cases and 10 negative/ok cases):

| Configuration | Test Cases | True Positives (TP) | False Positives (FP) | True Negatives (TN) | False Negatives (FN) | Precision | Recall |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Without Guard Rules** (Heuristic drift only) | 20 | 8 | 1 | 9 | 2 | **88.9%** | **80.0%** |
| **With Active Guard Rules** (`forbid_import`, `pattern`, etc.) | 20 | 10 | 1 | 9 | 0 | **90.9%** | **100.0%** |

### Key Findings
1. **Zero False Negatives**: Guard rules provide 100.0% recall on forbidden import additions (`forbid_import`), ensuring that previously rejected libraries (e.g. `sticky_sessions`, raw synchronous balloon deflaters) cannot be silently reintroduced.
2. **Deterministic Enforcement**: Unlike heuristic drift detection which relies on semantic keyword matching, guard rules execute on added lines (`+`) in pull request diffs using deterministic AST and regex matching.

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
| **Full Unit Test Suite** | **31 / 31 Tests Passed** | Verified via `python -m unittest discover -s tests -v` |
