# CIF Privacy, Redaction, and Data Retention Architecture

This document describes the privacy guarantees, data minimization policies, automated redaction mechanisms, and repository retention controls implemented in the **Context Intelligence Framework (CIF)**.

---

## 1. Core Privacy Principles

1. **Defense-in-Depth Redaction**: Secrets, API keys, credentials, and tokens are scrubbed *before* indexing, graph edge formation, metadata hashing, persistent database storage, and console/system logging.
2. **Deterministic Token Replacement**: Sensitive tokens are replaced with standardized non-reversible markers (`[REDACTED:<type>]`), preserving text structure while guaranteeing that raw secret strings never touch disk or external services.
3. **Local-Only Guarantee**: In environments where network traffic or third-party AI models are restricted, `CIF_LOCAL_ONLY=1` strictly disables outbound network calls and LLM integrations.
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
| **Slack Tokens** | `xoxb-`, `xoxa-`, `xoxp-`, `xoxr-`, `xoxs-` | `[REDACTED:SLACK_TOKEN]` |
| **Google API Keys** | `AIza[0-9A-Za-z\-_]{35}` | `[REDACTED:GOOGLE_KEY]` |
| **Private Keys** | `-----BEGIN [A-Z ]*PRIVATE KEY-----...-----END...-----` | `[REDACTED:PRIVATE_KEY]` |
| **JSON Web Tokens (JWT)** | Three-part base64url signed tokens (`eyJ...`) | `[REDACTED:JWT]` |
| **Authorization Bearer** | `Authorization: Bearer <token>` or `Bearer <token>` | `Bearer [REDACTED:BEARER_TOKEN]` |
| **Secret / Password Assigns** | `password`, `secret`, `token`, `api_key`, `access_key` assignments | `[REDACTED:SECRET_ASSIGNMENT]` |
| **URL Query Parameters** | Query string parameter values in `source_url` | `[REDACTED:QUERY_PARAM]` |
| **URL Basic Auth** | `http(s)://user:password@host` | `[REDACTED:CREDENTIALS]` |

### Optional Personally Identifiable Information (PII)

PII redaction is off by default to preserve developer author attribution, but can be enabled on-demand via environment flags:

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

## 6. Repository Purge & Data Retention (`POST /api/purge-repo`)

Administrators can completely remove all traces of a repository from the database at any time.

### Endpoint: `POST /api/purge-repo`
- **Authorization**: Required Role `admin` (`Authorization: Bearer <CIF_ADMIN_TOKEN>`).
- **Payload**:
  ```json
  {
    "repo": "acme-ecommerce/payment-core",
    "confirm": "acme-ecommerce/payment-core"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Successfully purged all records for repository 'acme-ecommerce/payment-core'",
    "deleted_counts": {
      "claim_evidence": 12,
      "decision_claims": 8,
      "guard_rules": 4,
      "state_history": 15,
      "decision_evidence": 20,
      "decision_artifacts": 10,
      "finding_feedback": 3,
      "edges": 35,
      "decisions": 6,
      "entities": 14,
      "events": 28
    }
  }
  ```

---

## 7. Logging & Error Scrubbing

The `SanitizingLogFilter` class (`backend.ingestion.sanitizer.SanitizingLogFilter`) intercepts all logging records and exception tracebacks, scrubbing sensitive tokens before console or file emission. API error responses never echo authentication tokens or raw secret payloads.
