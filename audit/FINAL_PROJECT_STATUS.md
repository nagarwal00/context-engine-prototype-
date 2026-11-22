# Final Project Status — 2026-11-21 (branch `audit-and-fixes`, not pushed)

## Verified working (exercised live or by tests I ran)
- Clean install from a fresh clone: `init_db.py --seed` → `server.py` → register → dashboard → restart → login.
- Local accounts with real passwords; logout; demo login (validated redirect).
- All 10 dashboard surfaces with live data on **any port** (tested 8080, 8095, random ports).
- Timeline, graph, decisions, evidence, explanations, review queue, onboarding, bus factor, metrics.
- Review actions with lifecycle enforcement (409 on illegal transitions) and verified actor identity.
- Live CI drift check (violation and clean presets); guard-rule approve/disable with honest results.
- Evidence invariant: `save_decision` + DB triggers + `v_ungrounded_decisions` (0 everywhere checked).
- Per-repository authorization incl. object-level checks; list endpoints scoped per user.
- CSRF/Origin, JSON content-type, dev-mode Host checks; rate limiting with 429 + `Retry-After` + UI countdown.
- Local-folder ingestion with real git history (tested on real public repo `npryce/adr-tools`), from API and from the dashboard.
- Static GitHub Pages snapshot: read-only, labelled, refuses ingestion.
- Benchmarks reproduced exactly; hold-out drift set 16/16.
- 409 automated tests (2 skipped), `run_demo.py` 21/21, docs/EOL/JS/WhyBench validators.

## Partially working
| Feature | Limitation |
|---|---|
| Decision extraction | Keyword heuristics; hand-set confidences; precision on noisy histories unmeasured |
| Conflict detection | 7 generic term pairs + 2 demo-specific pairs |
| Background ingest job (`POST /api/repos`) | Now extracts with `DecisionExtractor`, but creates no explicit graph edges (P2) |
| Entity resolution | Python files only |
| Evidence invariant in DB | Raw SQL INSERT can bypass it (detected by the view, not prevented) |
| Architecture | `api.py` god class; one import cycle; three frontend copies |

## Blocked by external credentials / services
| Feature | What is needed |
|---|---|
| GitHub REST ingestion against real GitHub | Internet + ideally `GITHUB_TOKEN` (this audit environment's proxy blocked REST calls; mocked tests pass) |
| GitHub OAuth sign-in | OAuth App credentials and callback URL |
| Webhook / PR comments | Public URL + `CIF_WEBHOOK_SECRET` + GitHub App |
| LLM extractor | API key |

## Not tested
Chrome/VS Code extensions inside their hosts · Firefox/Edge/mobile layouts · Docker build ·
Python 3.11 specifically (3.13 used) · large repositories / load.

## Not implemented
Real user study (protocol only; synthetic fixture numbers must not be reported) · password reset /
account lockout · decision precision and confidence calibration measurement.

## Failed verification
None outstanding. (Every failure found during the audit was fixed and re-verified.)

---

## Decisions I need from you (nothing below has been done)
1. **Rotate secrets (strongly recommended).** The `.env` inside the ZIP you shared contains a real
   GitHub OAuth client secret and a session secret. Regenerate the client secret at
   GitHub → Settings → Developer settings → OAuth Apps, and set a new `CIF_SESSION_SECRET`.
   (They were never in Git history and I did not copy or transmit them.)
2. **Delete `new_frontend/`?** It is a stale third copy of the UI that still contains the old
   fabrication code. Nothing serves it.
3. **Fix `demo_sample_repo`?** It is committed as a broken submodule pointer, so it is empty for
   anyone who clones from GitHub (and CI never tested it). Option: commit its files normally.
4. **Stray databases** `cif.db` (empty schema) and `cif_dashboard.db` (0 bytes) look unused — delete?
5. **Push** the `audit-and-fixes` branch (5 commits + reports) to GitHub and open a pull request?
6. **Old reports** (~40 root `.md` files) contain outdated claims. Keep them as history with a
   pointer to `audit/`, or move them to `docs/history/`?

## Existing user data
Your `context_intelligence.db` (4 users, 11 sessions) was never modified; originals are backed up
with SHA-256 in `../db_backups_original/`. When you next start the server on it, migration 008 is
applied automatically: it adds a nullable column, triggers, a view and one `schema_migrations` row.
Verified on a copy of your database: every data table keeps identical row counts, integrity check OK,
0 foreign-key violations, 0 ungrounded decisions. Existing
users have no password and must re-register or use GitHub/demo sign-in.
