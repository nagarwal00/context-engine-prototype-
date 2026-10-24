# CIF Privacy, Redaction, and Data Retention Architecture

This document describes the privacy controls, data minimization policies, automated redaction mechanisms, and repository retention controls implemented in the **Context Intelligence Framework (CIF)**.

---

## 1. Core Privacy Principles

1. **Defense-in-Depth Redaction**: Secrets, API keys, credentials, and tokens are scrubbed *before* indexing, graph edge formation, metadata hashing, persistent database storage, and console/system logging.
2. **Deterministic Token Replacement**: Sensitive tokens are replaced with standardized non-reversible markers (`[REDACTED:<type>]`), preserving text structure to ensure that raw secret strings never touch disk or external services.
3. **Local-Only Invariant**: In environments where network traffic or third-party AI models are restricted, `CIF_LOCAL_ONLY=1` strictly disables outbound network calls and LLM integrations.
4. **Complete Right-to-Forget**: The administrator endpoint `POST /api/purge-repo` immediately cascades deletion across all tables, traces, graph edges, and historical state logs associated with a repository.

---

## 2. Automated Redaction Engine (`backend/ingestion/sanitizer.py`)

All ingestion adapters (`GitAdapter`, `GitHubAdapter`, `ADRAdapter`, and direct `Database.upsert_event` calls) route event content through `sanitize_event()` prior to database insertion.

### Redacted Secret Categories

| Secret Type | Detection Pattern / Signatures | Replacement Token |
| :--- | :--- | :--- |
| **GitHub Tokens** | `ghp_`, `gho_`, `ghs_`, `ghr_`, `github_pat_` | `[REDACTED:GITHUB_TOKEN]` |
| **AWS Access Key ID** | `AKIA[0-9A-Z]{16}` | `[REDACTED:AWS_KEY]` |
| **AWS Secret Access Key** | Assignments with 40-character base64 keys | `[REDACTED:AWS_SECRET]` |
| **Slack Tokens** | `xoxb-`, `xoxa-`, `xoxp-`, `xoxr-`, `xoxs-`, `xapp-` | `[REDACTED:SLACK_TOKEN]` |
| **Google API Keys** | `AIza[0-9A-Za-z\-_]{35}` | `[REDACTED:GOOGLE_KEY]` |
| **Provider API Keys** | `sk-`, `sk-ant-` (≥20 url-safe chars) | `[REDACTED:API_KEY]` |
| **Stripe API Keys** | `sk_live_`, `rk_live_` (≥20 chars) | `[REDACTED:STRIPE_KEY]` |
| **GitLab Tokens** | `glpat-` (≥20 url-safe chars) | `[REDACTED:GITLAB_TOKEN]` |
| **npm Access Tokens** | `npm_` (36 alphanumeric chars) | `[REDACTED:NPM_TOKEN]` |
| **Private Keys** | `-----BEGIN [A-Z ]*PRIVATE KEY-----...-----END...-----` | `[REDACTED:PRIVATE_KEY]` |
| **JSON Web Tokens (JWT)** | Three-part base64url signed tokens (`eyJ...`) | `[REDACTED:JWT]` |
| **Authorization Bearer** | `Authorization: Bearer <token>` or `Bearer <token>` | `Bearer [REDACTED:BEARER_TOKEN]` |
| **Basic Authentication** | `Authorization: Basic <credentials>` | `Authorization: Basic [REDACTED:BASIC_AUTH]` |
| **Secret / Password Assigns** | `password`, `secret`, `token`, `api_key`, `access_key` assignments | `[REDACTED:SECRET_ASSIGNMENT]` |
| **URL Query Parameters** | Query string parameter values in `source_url` | `[REDACTED:QUERY_PARAM]` |
| **URL Basic Auth** | `http(s)://user:password@host` | `[REDACTED:CREDENTIALS]` |

### Optional Personally Identifiable Information (PII)

PII redaction is off by default to preserve developer author attribution (emails stay opt-in), but can be enabled on-demand via environment flags:

- **`CIF_REDACT_PII=1`**: Redacts email addresses (`[REDACTED:EMAIL]`) and phone numbers (`[REDACTED:PHONE]`).
- **`CIF_REDACT_AUTHOR=1`**: Redacts author display names (`[REDACTED:AUTHOR]`).

---

## 3. What is Stored in the Local Database

CIF only stores data necessary to reconstruct architectural decision context:
- **Repository Identifiers**: Canonical repo strings (e.g. `org/repo`).
- **Commit Metadata**: Git commit hashes (SHAs), commit timestamps, and sanitized commit titles/messages.
- **Issue & Pull Request History**: Public issue/PR numbers, sanitized titles, descriptions, and discussion comments.
- **ADR & Architecture Docs**: Document filenames, structural sections (Status, Context, Decision, Consequences).
- **Extracted Decision Graphs**: Decision nodes, lifecycle states (`proposed`, `tested`, `accepted`, `rejected`, `superseded`, `reopened`), evidence event links, claim passages, and temporal validity intervals (`valid_from`, `valid_to`).

---

## 4. What is Never Sent to an LLM

When an LLM client is enabled (`CIF_LLM_API_KEY` configured and `CIF_LOCAL_ONLY=0`):
1. **Unredacted Text**: Raw text is never sent to the LLM. Only pre-sanitized text is passed.
2. **Access Tokens and Secrets**: Internal authorization tokens (`CIF_ADMIN_TOKEN`, `CIF_REVIEWER_TOKEN`, `GITHUB_TOKEN`) are strictly excluded from prompts.
3. **Repository Files Outside Scope**: Arbitrary workspace files, environment configuration files (`.env`), and database binaries are never sent.
4. **Complete Local Fallback**: When `CIF_LOCAL_ONLY=1` is set, LLM client invocations are entirely short-circuited (`available() -> False`, `complete_json() -> None`).

---

## 5. Local-Only Mode (`CIF_LOCAL_ONLY=1`)

To operate CIF in air-gapped, high-compliance, or offline local development environments:
```bash
set CIF_LOCAL_ONLY=1
python server.py
```
When `CIF_LOCAL_ONLY=1`:
- Outbound GitHub API network requests are blocked (`RuntimeError` on attempt).
- Ingestion endpoints (`/api/ingest-repo`) refuse remote URL targets and only allow local directory paths.
- LLM clients are completely deactivated.
- Decision extraction operates purely via deterministic rule-based algorithms.

---

## 6. Repository Deletion & Right to Forget (`DELETE /api/repos/{owner}/{repo}`)

CIF implements an automated, cascading deletion mechanism to fulfill the user's right to forget repository data at any time.

### Informed User Consent (Pre-Ingestion)
Before a user adds a repository to CIF, the user interface and API contract explicitly disclose:
1. **What CIF reads**: Commit history (author, message, diffs), pull requests (titles, bodies, reviews, comments), issues (descriptions, discussion comments), architectural decision documentation (`docs/adr`, `adr`, `docs/decisions`, `rfcs`), and code snapshots of the default branch.
2. **Where data is stored**: In the local, encrypted/isolated SQLite database `context_intelligence.db` on the host machine.
3. **Pre-persistence Redaction**: All incoming texts pass through the multi-pattern privacy sanitizer *before* storage. Secrets (tokens, keys, passwords, credentials) are never written to disk.
4. **How to delete**: Users can delete all stored repository data at any time via the web interface or via `DELETE /api/repos/{owner}/{repo}`.

### Endpoint: `DELETE /api/repos/{owner}/{repo}`
- **Authorization**: The user who added the repository (`added_by_user_id`), or an administrator (`Authorization: Bearer <CIF_ADMIN_TOKEN>`).
  - Unauthenticated calls return `401 Unauthorized`.
  - Non-owner users who did not add the repository return `403 Forbidden`.
  - Non-existent repositories return `404 Not Found`.
- **Cascading Deletion Scope**:
  Deleting a repository permanently purges all associated records across every table:
  - `events`: Commit records, PR events, review comments, issue records.
  - `entities`: File and AST function entities.
  - `decisions`: Extracted and recorded architectural decisions.
  - `edges`: Directed relationships between entities, decisions, and evidence.
  - `decision_claims`: Reconstructed architectural claims.
  - `claim_evidence` & `decision_evidence`: Event citations supporting claims.
  - `decision_artifacts`: File linkage associations.
  - `state_history`: Chronological lifecycle transitions.
  - `guard_rules` & `decision_assumptions`: Active lint/guard invariants.
  - `finding_feedback`: User review confirmations and dismissals.
  - `ingest_jobs`: Historical and active background ingestion jobs.
  - `repo_access` & `repo_reviewers`: Cached permission mappings and assigned reviewers.
  - `repos`: Repository registry entry.
- **Physical Disk Expungement (`VACUUM`)**:
  Following table deletion, CIF triggers an immediate SQLite `VACUUM;` operation. This rebuilds the database file, overwriting free pages and ensuring that raw-byte scans of the database file on disk contain zero residual text or fragments of the deleted repository.
- **Response Format**:
  ```json
  {
    "status": "success",
    "message": "Successfully deleted repository 'owner/repo' and expunged all records",
    "repo": "owner/repo",
    "deleted_counts": {
      "claim_evidence": 12,
      "decision_claims": 8,
      "guard_rules": 4,
      "decision_assumptions": 2,
      "state_history": 15,
      "decision_evidence": 20,
      "decision_artifacts": 10,
      "finding_feedback": 3,
      "edges": 35,
      "decisions": 6,
      "entities": 14,
      "events": 28,
      "ingest_jobs": 2,
      "repo_access": 3,
      "repo_reviewers": 1,
      "repos": 1
    }
  }
  ```

---

## 7. Administrative Repository Purge (`POST /api/purge-repo`)

In addition to user-initiated repository deletion, administrators can purge repositories using `POST /api/purge-repo` with explicit confirmation name matching.

---

## 8. Logging & Error Scrubbing

The `SanitizingLogFilter` class (`backend.ingestion.sanitizer.SanitizingLogFilter`) intercepts all logging records and exception tracebacks, scrubbing sensitive tokens before console or file emission. API error responses never echo authentication tokens or raw secret payloads.
