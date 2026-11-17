# Security and Secret Scan Report (Step 6.3)

- **Scan Date**: 2026-11-17
- **Scope**: Project Git history (including Phase 7–9 auth, extensions, and process docs), `demo_sample_repo/.git`, `context_intelligence.db`, `whybench.db`
- **Status**: CRITICAL: LEAK DETECTED

## Summary Breakdown

| Category | Count | Status |
|---|---|---|
| **Active / Unredacted Secrets** | **24** | FAILED ❌ |
| **Redacted Tokens (`[REDACTED:...]`)** | 0 | Expected (Privacy Sanitizer verified) |
| **Synthetic Unit Test Tokens** | 27 | Expected (Static test fixtures only) |
| **Total Patterns Inspected** | 484 | Complete |

## Target Details

1. **Main Repository Git History**: 24 real leaks.
2. **Demo Sample Repository Git History**: 0 real leaks.
3. **`context_intelligence.db`**: 0 real leaks.
4. **`whybench.db`**: 0 real leaks.

## Real Credential Verdict

> [!CAUTION]
> **Real credentials found! Action required.**
- Location: `project_repo commit:bfe46857c2 file:docs/app.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:bfe46857c2 file:web/app.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:595e20bac4 file:docs/landing.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:595e20bac4 file:docs/login.html` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:595e20bac4 file:new_frontend/context-engine-ui-refresh/landing.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:595e20bac4 file:new_frontend/context-engine-ui-refresh/login.html` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:595e20bac4 file:web/landing.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:595e20bac4 file:web/login.html` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:40e1fe7598 file:new_frontend/context-engine-ui-refresh/app.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:40e1fe7598 file:new_frontend/context-engine-ui-refresh/landing.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:40e1fe7598 file:new_frontend/context-engine-ui-refresh/landing.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:b0406127a2 file:new_frontend/context-engine-ui-refresh/login.html` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:b0406127a2 file:new_frontend/context-engine-ui-refresh/login.html` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:45358be5a2 file:tests/test_dashboard_auth_gate.py` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:22f9e3c581 file:docs/app.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:22f9e3c581 file:docs/landing.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:22f9e3c581 file:docs/landing.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:22f9e3c581 file:docs/login.html` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:22f9e3c581 file:docs/login.html` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:22f9e3c581 file:web/app.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:22f9e3c581 file:web/landing.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:22f9e3c581 file:web/landing.js` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:22f9e3c581 file:web/login.html` | Pattern: `SECRET_ASSIGNMENT`
- Location: `project_repo commit:22f9e3c581 file:web/login.html` | Pattern: `SECRET_ASSIGNMENT`
