# Software Test Plan (STP)
## Context Intelligence Framework (CIF)

**Document Standard:** IEEE Std 829-2008 Compliant Test Plan  
**Project:** Context Intelligence Framework — Continuous Architectural Context Recovery & Drift Interception  
**Version:** 1.4.0  
**Status:** Approved / Baselined  
**Date:** October 2026  

---

## 1. Introduction and Objectives

### 1.1 Purpose
This Software Test Plan (STP) governs the verification and validation strategy for the Context Intelligence Framework (CIF). It defines the test hierarchy, tooling, execution criteria, pass/fail standards, and regression mechanisms required to ensure production-grade reliability, security, and architectural integrity.

### 1.2 Quality Goals
1. **Zero Flaky Tests**: Complete test deterministic execution across Windows, Linux, and macOS platforms.
2. **100% Invariant Enforcement**: Absolute verification that no ungrounded decision record can enter the database.
3. **Zero State Mutation**: Strict isolation ensuring test suites execute against temporary sandboxes and never modify reference databases.
4. **Zero Secret Leakage**: Continuous automated scanning of all codebase artifacts for credential, key, or token leakage.
5. **Full Traceability**: Every functional requirement defined in the [docs/sdlc/SRS.md](file:///c:/Users/HP/Desktop/SE_project/docs/sdlc/SRS.md) maps directly to automated test cases.

---

## 2. Test Hierarchy and Strategy

CIF employs a multi-tiered test pyramid comprising 5 distinct validation levels:

```
                  /\
                 /  \     Level 5: System Verification (run_demo.py - 21 Checks)
                /----\
               /      \    Level 4: Benchmarks & Hold-Out (WhyBench & Holdout Suite)
              /--------\
             /          \   Level 3: Integration & API (HTTP, Multi-Repo, Auth)
            /------------\
           /              \  Level 2: Invariants & Security (Secret Scanner, DB Untouched)
          /----------------\
         /                  \ Level 1: Unit & Component Tests (329 Tests in tests/)
        ----------------------
```

### Level 1: Unit & Component Tests
- **Framework**: Python Standard Library `unittest`.
- **Scope**: Models, sanitizers, heuristic extractors, lifecycle transition state machine, graph traversals, and calibration algorithms.
- **Count**: 329 tests executed via `python -m unittest discover -s tests`.
- **Execution Speed**: Sub-10 seconds total run time on standard hardware.

### Level 2: Invariant & Integrity Verification
- **Mechanical Grounding Check**: Validates that insertion attempts without evidence links throw `InvariantViolationError`.
- **Database Immutability Check**: `python tools/verify_db_untouched.py` computes pre- and post-test SHA-256 hashes of `context_intelligence.db` and `whybench.db` to verify zero mutation.
- **Referential Integrity**: Verifies SQLite foreign key pragma enforcement across all relational tables.

### Level 3: Integration & API Tests
- **HTTP Server Harness**: Tests REST endpoints in `backend/api.py` via ephemeral local sockets.
- **Flakiness Protection**: Handlers and test clients implement transient socket retry loops and unhandled `BrokenPipeError` / `ConnectionResetError` suppression.
- **Repository Isolation**: Multi-tenant tests ensure repository scopes (`acme-eng/thermal-control-system` vs `acme-eng/distributed-cache-service`) cannot cross-pollinate.

### Level 4: Benchmark Verification & Baseline Evaluation
- **WhyBench Suite**: 134-item benchmark evaluated via `python tools/validate_whybench.py`.
- **Hold-Out Generalization**: 16-case drift synthesis set evaluated in an independent third domain (`acme-eng/job-queue-service`).
- **Baseline Comparison**: Reproducible comparison reporting CIF vs BM25 with Wilson 95% confidence intervals.

### Level 5: System Verification Demo Suite
- **Verification Harness**: `python run_demo.py`.
- **Automated Checks**: 21 sequential end-to-end verification steps covering database bootstrapping, API response validation, guard synthesis, drift interception, and explainability output.

---

## 3. Test Suites and Tooling Inventory

| Tool / Test Script | Purpose | Execution Command | Target Threshold |
|---|---|---|---|
| Full Unit Suite | Component & integration testing | `python -m unittest discover -s tests -v` | 329 Passed, 0 Failed |
| System Demo Harness | End-to-end user journey verification | `python run_demo.py` | 21/21 Checks Passed |
| DB Untouched Verifier | Confirms test sandbox isolation | `python tools/verify_db_untouched.py` | Output: `DB UNTOUCHED` |
| WhyBench Validator | Cryptographic integrity of benchmark | `python tools/validate_whybench.py` | 134/134 Items Valid |
| Docs Integrity Checker | Validates factual claims & links | `python tools/check_docs.py` | 0 Banned, 0 Broken Links |
| Line Ending Verifier | Enforces clean LF line terminations | `python tools/check_eol.py` | Output: `EOL OK` |
| Secret Scanner | Audits codebase for credential leaks | `python tools/scan_secrets.py` | 0 Leaks Detected |

---

## 4. Test Environment and Isolation Strategy

1. **Sandboxed Directories**: Every test class inheriting from `unittest.TestCase` creates a dedicated temporary directory using `tempfile.mkdtemp()` in `setUp()` and safely deletes it using `shutil.rmtree(..., ignore_errors=True)` in `tearDown()`.
2. **Ephemeral Ports**: Integration tests dynamically bind to port 0 (OS-assigned free port) to avoid address collisions in CI environments.
3. **Socket Hardening**: Test clients wrap HTTP calls in a retry loop (1 retry, 100ms backoff) to gracefully absorb transient OS TCP teardown resets (`ConnectionResetError`).
4. **Deterministic Seeds**: Random seeds (`seed=1234`) are locked across benchmark evaluation runs to guarantee reproducible splits and calculations.

---

## 5. Pass/Fail Criteria & Release Gates

A build or release is marked **PASSED** if and only if all of the following conditions are simultaneously satisfied:

```
[ Gate 1: 329 Unit Tests Pass (0 Failures, 0 Errors) ]
                         |
[ Gate 2: 21 System Demo Checks Pass (100%) ]
                         |
[ Gate 3: DB Untouched Verifier Outputs "DB UNTOUCHED" ]
                         |
[ Gate 4: WhyBench Validator Confirms 134/134 Items Valid ]
                         |
[ Gate 5: Check Docs Confirms 0 Broken Links, 0 Drift Strings ]
                         |
[ Gate 6: Check EOL Confirms Clean LF Formatting ]
                         |
[ Gate 7: Scan Secrets Confirms 0 Credential Leaks ]
                         |
                      RELEASE READY
```
