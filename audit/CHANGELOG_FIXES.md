# Changelog of Fixes (branch `audit-and-fixes`)

All fixes are local commits on top of `a2a1839`. Nothing has been pushed.
"Verification" names the test that fails on the old code and passes on the new code, or the
manual/browser check performed.

| Issue | File(s) | Root cause | Correction | Verification |
|---|---|---|---|---|
| SEC-01 password-less login | `server.py`, `backend/auth/local_accounts.py` (new), migration 008 | `/auth/login` looked up the username and issued a session; the password field was ignored | PBKDF2-SHA256 (200k iterations, random salt) password hashes; constant-time compare; OAuth/demo accounts have no password and cannot be password-logged-in; local accounts get negative `github_id` | `test_http_security`: 5 login/register tests; browser registration flow |
| SEC-02 cross-site DB wipe in dev mode | `server.py` `_guard_request` | Origin check only for cookie auth; dev mode = admin for any loopback caller; `text/plain` bodies parsed as JSON | Same-origin check for every state-changing request without `Authorization`; cookie POST without Origin refused; non-empty POST must be `application/json` (415); dev-mode Host must be loopback (DNS rebinding) | `HTTPDevModeTests` (4 tests) |
| SEC-03 cross-repo IDOR | `backend/auth/repo_access.py`, `backend/security.py` | Authorization used the `repo` parameter, handler used the object id | Repo resolved from the object (decision/rule/finding/event/artifact); mismatch → 404 | `test_object_id_cannot_be_read/modified_through_another_repo` |
| SEC-12 list endpoints leak | `backend/api.py` `handle_get` / `_scope_to_repos` | No-`repo` requests authorised against demo repo but returned all rows | Rows filtered to the caller's accessible repositories | `test_list_endpoints_without_repo_do_not_leak_private_repos` |
| APP-01 DELETE crash | `server.py` | Call to undefined `enforce_csrf_for_cookie` | Removed; CSRF handled by `_guard_request` | `test_delete_returns_json_instead_of_crashing`, `test_cross_origin_delete_with_cookie_is_rejected` |
| APP-02 empty replies on exceptions | `server.py` `_safe_dispatch` | No top-level handler | JSON 500 with `error_code` + `request_id`; traceback logged server-side only | `test_invalid_numeric_input_returns_400_not_empty_reply`, `test_error_responses_are_json_with_request_id` |
| SEC-04 demo-login open redirect | `server.py` | `next` not validated | `validate_next_path`; `CIF_DEMO_LOGIN=0` disables | `test_demo_login_does_not_redirect_off_site` |
| SEC-05 rate-limit bypass | `server.py` `_get_client_key` | Bucket keyed by any presented token string | Per-user bucket only for a valid session/admin token, else IP | `test_fake_tokens_share_the_ip_bucket` |
| SEC-06 bind check shadowed | `server.py` | Duplicate print-only definition overrode the enforcing one | One definition; refuses non-loopback bind when `CIF_DEV_MODE=1` | `test_public_bind_with_dev_mode_is_refused` |
| SEC-07 public GitHub proxy | `backend/api.py` | Unauthenticated, unvalidated `repo` | Sign-in required; strict `owner/name` validation (also in `parse_repo_identifier`) | `test_github_proxy_requires_sign_in`, `..._rejects_malformed_repo` |
| SEC-08 secrets in Docker image | `.dockerignore` (new) | `COPY . /app` with no ignore file | Excludes `.env`, `*.db`, logs, `.git` | Reviewed |
| SEC-10 job ownership | `backend/api.py` | No ownership check on job status/cancel | Only requester or admin; others get 404 | Code review + existing job tests |
| SEC-11 diagnostics disclosure | `backend/api.py` | DB path and user/session counts public | Public: status only; details for admin token / in-process callers | `test_public_diagnostics_do_not_disclose_paths_or_user_counts` |
| AUD-01 forgeable audit trail | `backend/api.py` `_actor_for` | Actor was a role name or a client-supplied string | Verified `user:<login>`; optional display name appended as unverified label | `test_review_actions` (unchanged tests still pass); browser check: history shows `user:actions_…` |
| INT-01 frontend fabrication | `web/app.js`, `login.html`, `landing.js` | Live errors switched the session to a mock engine that invented commits | Live mode reports errors ("Backend unreachable"); ~600 lines of fabrication removed; static mode refuses ingestion | Browser: backend killed mid-session → badge "Backend unreachable" + notice; static snapshot ingest → `STATIC_MODE` error |
| INT-02 hard-coded commits (backend) | `backend/ingestion/live_github.py`, `backend/api.py` | Fallback list for repos named "breathwise" | Removed; GitHub's real error is returned | grep: no `breathwise` in backend |
| INT-03 citation URL rewriting | `web/app.js` `safeUrl` | Map of substrings → team's commits | Scheme validation only | Code review |
| INT-04 / ALG-05 invented local metadata | `live_github.py`, `backend/ingestion/urls.py` (new), adapters | Fixed issue #5 / author / date / file for every local file; `github.com/local/…` links; ADR linked to every function; separate keyword extractor | git history when present, fixture otherwise, "unknown" when neither; `local://` locators; links only to mentioned files; `DecisionExtractor` for every source; standard ADR folders | `test_local_ingest` (5 tests); real repo `npryce/adr-tools` ingested with real authors/dates |
| ALG-05 background job extractor | `backend/ingestion/job_runner.py` | Third ad-hoc keyword extractor; the created `DecisionExtractor` was unused | Uses `DecisionExtractor` (the benchmarked algorithm) | `test_job_runner`, `test_add_repo` |
| DB-01 invariant not in DB | `backend/integrity.py` (new), migration 008, `backend/db.py` | Python-only enforcement; cascade stripped evidence | Triggers + `v_ungrounded_decisions`; `save_decision` links evidence before state update; re-asserted at start-up | `test_db_integrity` (7 tests) |
| DB-02 global wipe on re-ingest | `live_github.py` | `clear_existing` called `clear_database()` | `purge_repo(repo)` | Code review + `test_local_ingest` re-ingest test |
| FE-01 port-8080 dependence | `web/cif-mode.js` (new), 5 pages, `tools/build_static.py` | Mode guessed from port; localStorage flag trusted in live mode | One detector; only the Pages build sets the static flag; localStorage only in static mode | Browser E2E on port 8095: all 10 surfaces live |
| ALG-01/02/03 extractor false positives | `backend/engine/extractor.py`, `adr_adapter.py` | Broad keywords; bare "rejects"; status substring order | Weak verbs need architectural context; rejection must target a proposal; status order fixed | `test_extractor_precision` (5 tests); WhyBench dev/test unchanged |
| Drift UI bugs | `drift_detector.py`, `web/app.js` | Finding had no `decision_title`; crash when only rejected-idea findings | Title included; safe fallback; shows uncalibrated signal strength | Browser drift check |
| Guard-rule false success | `backend/api.py`, `web/app.js` | "success" even if rule missing; UI ignored response | 404 for unknown rule; UI checks result | `test_guard_rules` |
| TOOL-01 CRLF freeze hash | `tools/validate_whybench.py` | Hash recorded on CRLF checkout | Line-ending-independent comparison; tampering still detected | Validator passes; tampered copy fails |
| TOOL-02 JS checker | `tools/check_js.py` | Hand-written brace counter | `node --check` on 20 files | `[OK] 20/20` |
| Test isolation | `tests/test_failure_analysis.py` | Test opened the project's real `whybench.db` | Uses a temp DB | DB checksums unchanged after full suite |
| Rate-limit default | `backend/rate_limiter.py` | 60/min ≈ 4 dashboard loads | 300/min (auth 10, ingest 5, expensive 15 unchanged) | Latency run |
| Static latency | `tools/build_static.py` | Fixed `15.0 ms` published as a metric | "not measured" | Code review |

## Tests changed (and why)
| Test | Change | Reason |
|---|---|---|
| `test_auth_flow._http_request` | adds `Content-Type: application/json` when sending a body | Helper sent JSON labelled as form data; real clients send JSON; server now refuses mislabelled bodies (415) |
| `test_repo_isolation._request` | same | same |
| `test_backend_api_exhaustive.test_17` | declares JSON content type | Intent ("malformed JSON → 400") preserved; undeclared bodies now get 415 earlier |
| `test_failure_analysis` | temp DB path | It was writing to the real benchmark DB |
No assertion was weakened. Old-behaviour tests for review-actor names still pass unchanged.
