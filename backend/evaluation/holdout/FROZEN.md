# Frozen Drift Hold-Out Evaluation Set

This directory contains the immutable drift evaluation hold-out set created in Step 3.2a of the evaluation-review plan, frozen strictly **before** generalizing the guard rule synthesis engine.

## Domain
Repository: `acme-eng/job-queue-service`  
Subsystem: Distributed Task Queue & Worker Execution (disjoint from thermal control, cache service, and payment processing).

## Dataset Files & SHA-256 Hashes

| File | Records | Description | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| `decisions.json` | 4 | Hand-authored architectural decisions with rationale and rejected alternatives | `eb6ba569119c3039a984c55cbdf26b9f02f5711459e12a7b5db29cafcbaa907c` |
| `cases.json` | 16 | Diff test cases (8 violations, 8 negatives including comment/deletion/substring tests) | `c769a0aeb0101ee823d72e048942b62929a8ca38056ba05f45258ff4bb993918` |

## Ground Truth Guarantees
- Created before any modifications to `guard_rules.py` or `rejected_idea_guard.py`.
- No evaluation against this dataset is performed until the synthesizer is fully generalized and verified.
- Measurement will be executed exactly once in Step 3.2c via `tools/run_holdout.py`.
