# Re-evaluation: Context Intelligence Framework (v4 fixes)

Professor-style review of the updated SE_project.zip, dated 24 October 2026.

## Verdict

**Score now: about 24.5/30** (my range is 23 to 26). Last time it was 21. The jump is real, and I checked it by running things, not by trusting the audit file.

| Area | Marks | Before | Now |
|---|---|---|---|
| Problem and positioning | 4 | 3.0 | 3.5 |
| Design and architecture | 5 | 4.5 | 4.5 |
| Implementation | 7 | 5.5 | 6.0 |
| Testing and engineering practice | 4 | 2.5 | 3.5 |
| Evaluation rigour | 6 | 3.0 | 4.0 |
| Demo, hosting and docs | 4 | 2.5 | 3.0 |
| **Total** | **30** | **21.0** | **24.5** |

The weights are assumed from the approved project scope, because the official rubric was not available.

## What is now genuinely fixed (each item verified)

- **Version control:** Phase 7–9 is committed (86 commits, tags in place). The private key is out of `scratch/` and nothing secret is tracked.
- **Tests:** 329 tests (up from 279). The time-bomb test is gone, and `run_demo.py` passes 21/21. Edges have 0 NULL `repo_full_name`. `verify_db_untouched.py` confirms the tests no longer modify the databases.
- **Fair comparison:** On the same 26 questions BM25 scores 92.3% against CIF's 80.8%, with 95% intervals, and the report says so plainly.
- **Honest labelling:** WhyBench is now labelled synthetic everywhere, and the frozen files are untouched (`validate_whybench.py` passes).
- **Engine:** No domain words (PID, Redis, etc.) remain in `backend/engine`, and conflict matching now uses word boundaries. A hold-out drift set in a third domain was added, frozen before the fix.
- **Disclosure:** `AI_ASSISTANCE.md` and `CONTRIBUTIONS.md` now exist, and the presenter coaching moved out of the README.

## Bugs and problems still present

1. **One flaky test.** Of 5 full runs, 1 failed with `Broken pipe` in a test that starts a local HTTP server. It is probably in `test_feedback.py` or `test_api_auth.py`, but I did not isolate which. A flaky test can fail during a demo or in CI.
2. **Stale numbers in the docs.**
   - `evaluation_results.md` says "173 Tests Passed" (the real count is 329).
   - `print_facts.py` reports 174, so the tool meant to prevent drift is itself wrong.
   - `check_docs.py` passes anyway.
3. **`STATUS_AUDIT.md` Phase 10 describes things that do not exist.**
   - It cites `baseline_c_llm.py`, `generate_copilot_sheet.py`, `docs/user_study/SURVEY.md`, `docs/process/AI_ASSISTANCE.md` and `test_security_sanitizer.py`. The real files have different names or are missing.
   - It claims Wilcoxon and Mann-Whitney tests plus an "IRB-ready" package. The analyzer only computes means, medians and paired differences.
   - The audit is supposed to be the evidence document, so fix this before an examiner opens it.
4. **The hold-out 100%/100% is weak evidence.** It was written by the same author, so its 16 cases show the mechanism works when rejected options are written in backticks. It does not show generalisation to ordinary prose.
5. **Clutter in the zip.**
   - `temp_ci.db` and its journal.
   - `backups/` (old databases).
   - `dist/` (three zips).
   - Three placeholder-titled decisions in the shipped DB ("Architectural Decision dec_thermal_pid_01").
6. **Still not measured:**
   - Baselines C (LLM) and D (Copilot).
   - Precision (all 80 labels are empty).
   - Calibration.
   - The user study.
   - A real-repo corpus.
   - A live GitHub App deployment.
7. **The professor's objection is still unanswered with data.** "AI agents can do this" needs Baseline C, and the instructor-named benchmarks (Continuum, Warrant, Context Graph) appear nowhere in the docs or report. Both `TODO(human)` files are also still empty.

## Is it worth a 17-week project?

**Scope: yes, and then some.** The repo has about 17k lines of backend and 13.7k lines of tests, 329 tests, 11 UI surfaces, 7 migrations, a GitHub App flow, and Chrome and VS Code extensions. That is well above what a typical course project delivers.

**Process: this is the weak spot.** The commit history shows 2 commits in September, then 50 commits across Oct 10–14, then 34 across Oct 23–24. That is about 7 active days, not 17 weeks of steady progress. If the course checks weekly progress, this will show. Also, `AI_ASSISTANCE.md` calls the AI an "autonomous implementation agent" while the author sections are empty, so be ready to explain every module in a viva.

## Is it worth 30 marks?

It is worth the upper band, about 24 to 26 today. Engineering volume is no longer what separates it from full marks, so more code will not help. The last 3–4 marks come from evidence and honesty:

1. Run Baseline C with a real API key. This directly answers the professor's objection.
2. Label the 80 precision items (about 3 hours).
3. Run a 5-person user study.
4. Deploy live and save screenshots.
5. Fill both `TODO(human)` files truthfully.
6. Ingest one real repo and label about 15 real decisions.
7. Add a short qualitative table comparing against Continuum, Warrant and Context Graph.

I did not audit whether formal SDLC artefacts exist (SRS, UML, test plan, project plan). If the rubric rewards those, confirm they exist, because they are often worth easy marks in a Software Engineering course.
