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
