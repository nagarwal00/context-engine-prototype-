# Professor-Level Evaluation Report

Written from the point of view of a strict examiner who will run the code. Ratings refer to the
`audit-and-fixes` branch, not the original submission.

## 1. Overall verdict
**Demonstrable and defensible, with clearly stated limits.** Before this audit the project would
very likely have failed a hostile live examination (anyone could sign in as anyone; one web page
could wipe the database; the UI invented commit history when the backend failed). Those defects are
fixed and covered by tests that run through the real HTTP server. The remaining weaknesses are
mostly about *evaluation depth* and *code structure*, not about correctness or honesty.

| Area | Rating (1–5) | Evidence |
|---|---|---|
| Problem framing & novelty | 4 | Clear "why was this written" problem; lifecycle + refusal + CI guard is more than RAG |
| Architecture | 3 | Three tiers exist; `api.py` is a god class; one import cycle |
| Implementation correctness | 4 | 409 tests; HTTP-level security tests; browser E2E |
| Security | 4 | All reproduced P0/P1 issues fixed; residual P2/P3 documented |
| Data integrity | 4 | Invariant enforced in code **and** by DB triggers; ungrounded view empty |
| Evaluation rigour | 2.5 | Honest numbers, frozen test split, CIs — but N=26, curated events, precision unmeasured, no real user study |
| Documentation | 2.5 | Very extensive but contradictory historical reports; `audit/` is now the source of truth |
| Demo readiness | 4 | Reproducible clean install; scripted demo; static fallback |

## 2. Technical strengths (with evidence)
1. **Evidence grounding is real**: every stored decision cites ≥1 event; enforced in `save_decision`, by triggers (`backend/integrity.py`), and checked by `v_ungrounded_decisions` (0 rows after seed, after real-repo ingest, after the benchmark).
2. **Lifecycle model**: illegal transitions are refused (HTTP 409 observed for accepted→rejected).
3. **Abstention**: the system answers "insufficient evidence" instead of inventing (64.4 % refusal accuracy on 45 negatives — honest, not great).
4. **CI guard rules**: hold-out drift set 16/16, reproducible byte-for-byte.
5. **Reproducible evaluation**: frozen split with hash check; headline reproduced exactly (80.8 % / 100 % / 64.4 %).
6. **Security engineering**: hashed sessions and OAuth state, HMAC webhooks, CSRF/Origin checks, per-repo authorization, rate limiting.

## 3. Weaknesses an examiner will find
1. **Extraction is keyword heuristics with hand-set confidences** (0.95 ADR, 0.90 commit, 0.85 PR, 0.65 issue). These are *not* probabilities; calibration is "not measured".
2. **Benchmark size and realism**: 26 positive questions (95 % CI 62–92 %); events are curated subsets (~12 KB per repo), so precision on noisy real histories is not measured. The extractor fixes in this audit changed **nothing** on WhyBench — proof that the benchmark cannot see that class of error.
3. **Keyword BM25 baseline beats CIF on evidence retrieval** (92.3 % vs 80.8 %) — already admitted in the README; be ready to explain why CIF's value is state classification, refusal and CI guarding.
4. **Conflict detection** uses 7 generic word pairs plus 2 pairs written for the demo data.
5. **Only Python code is parsed** into function entities.
6. **User study**: protocol only; the "N=6" numbers printed by the test suite are synthetic test fixtures, not results. Do not present them as findings.
7. **Code structure**: 2,500-line `api.py`; three copies of the frontend.
8. **Pre-existing test gap**: CI never exercised local ingestion because `demo_sample_repo` is a broken submodule pointer (empty in clones). A real failure existed in your folder that CI could not see.

## 4. Likely examiner questions — and honest answers
| Question | Answer you can defend |
|---|---|
| Why not just RAG over commits? | RAG retrieves text; CIF stores *decisions* with lifecycle state, refuses when no evidence exists, and turns accepted decisions into CI rules that block regressions. BM25 retrieves more raw evidence (92 % vs 81 %) but cannot say "rejected", "superseded" or "unknown". |
| What does "grounded" mean precisely? | A decision in tested/accepted/rejected/superseded must link ≥1 stored event; enforced by `save_decision`, DB triggers, and an integrity view. |
| Can the DB still contain an ungrounded decision? | Via a raw SQL INSERT, yes (SQLite has no commit-time checks); the app path cannot create one and `v_ungrounded_decisions` detects it. |
| Are your confidence scores calibrated? | No. They are heuristic priors; calibration needs ≥100 labelled decisions and is reported as "not measured". |
| How was the test set protected from overfitting? | Frozen before tuning, SHA-256 recorded, runner refuses to re-run without `--final --force`; dev/test question texts verified disjoint (0 overlap). |
| What is the temporal reasoning? | Decisions/edges carry `valid_from`; "as-of" queries reconstruct what was known at a date, which prevents using later evidence to explain earlier code. |
| How does drift detection work? | Diffs are parsed line by line; guard rules synthesized from accepted/rejected decisions (forbid/require import, forbidden pattern, config value) are matched against added lines, ignoring comments; findings cite the governing decision. |
| What happens if GitHub is down? | The API returns GitHub's real error; the UI shows it. (Before the audit the UI fabricated commits.) |
| Biggest limitation? | Extraction precision on real, noisy histories is unmeasured and the benchmark is small. |
| What did AI tools do? | See `AI_ASSISTANCE.md`; this audit is documented in `audit/`. Be ready to explain each fix yourself. |

## 5. Features needing extra explanation in the viva
Evidence invariant (three layers) · lifecycle transitions · as-of queries · guard-rule synthesis
· refusal/abstention · why confidence ≠ probability · static vs live mode · repo-level authorization.

## 6. Demonstration readiness
Ready, provided you (1) rotate the leaked OAuth secret, (2) follow `DEMO_GUIDE_FINAL.md`
(not the older demo docs), and (3) present the evaluation numbers with their confidence intervals.
