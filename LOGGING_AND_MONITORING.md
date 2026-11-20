# Logging & Monitoring Architecture
## Context Intelligence Framework (CIF)

The Context Intelligence Framework implements structured, rotating logging and end-to-end observability adhering to modern production standards.

---

## 1. Structured Logging Hierarchy (`backend/logging_config.py`)

All logging configuration is centralized in `backend/logging_config.py`. Rotating file handlers protect disk storage by capping individual log files at **5 MB** with **5 backups** each.

### Dedicated Log Files in `logs/`
| File | Logger Hierarchy | Minimum Level | Purpose |
|---|---|---|---|
| `logs/application.log` | Root / `cif.*` | `INFO` | General application lifecycle, initialization, and component health. |
| `logs/api.log` | `cif.api`, `cif.server` | `INFO` | HTTP requests, route dispatches, response codes, latency (ms), client IPs. |
| `logs/error.log` | Root / `cif.*` | `WARNING` | Errors, unhandled exceptions, failed invariants, stack traces. |
| `logs/database.log` | `cif.database` | `INFO` | Relational transactions, migrations, connection pool events, query errors. |
| `logs/security.log` | `cif.security` | `INFO` | RBAC decisions, token validation, CSRF checks, CORS violations. |
| `logs/rate_limit.log` | `cif.rate_limit` | `INFO` | Quota checks, throttling occurrences, sliding-window resets. |

---

## 2. Request Correlation & Context Tracing

Every incoming request is tagged with a unique **UUID4 Correlation ID**:
1. If the client provides an `X-Request-ID` header, it is adopted.
2. Otherwise, `server.py` generates a fresh UUID4.
3. The request ID is stored in thread-local storage (`set_request_id(uuid)`).
4. `RequestIdFilter` automatically attaches `%(request_id)s` to every log record.
5. The request ID is echoed in the response headers (`X-Request-ID: <uuid>`) and injected into the response JSON body (`"request_id": "<uuid>"`).

### Console Output Format
Terminal output is clean, informative, and un-silenced:
```
[11:52:10] [INFO ] [8d12ab8f-ff0f-41c6-94f4-f999b755182c] 127.0.0.1 - "GET /api/repos HTTP/1.1" 200 -
[11:52:10] [INFO ] [8d12ab8f-ff0f-41c6-94f4-f999b755182c] GET /api/repos -> 200 (6.04ms) [client=127.0.0.1]
[11:52:10] [WARNING] [f4e55489-32c5-4c97-9cb1-7e732aa1be0d] Rate limit exceeded for key=[REDACTED] on category='api'. Count=2/2. Retry after 60s.
[11:52:10] [INFO ] [f4e55489-32c5-4c97-9cb1-7e732aa1be0d] 127.0.0.1 - "GET /api/repos HTTP/1.1" 429 -
```

---

## 3. Secret Redaction Filter (`SecretRedactionFilter`)

To prevent credential leakage into log files or console streams, a regex-based redaction filter intercepts every log entry:
- **GitHub Personal Access Tokens**: Matches `ghp_...`, `gho_...`, `github_pat_...` and replaces with `[REDACTED_GH_TOKEN]`.
- **Bearer Tokens**: Matches `Bearer <token>` and replaces with `Bearer [REDACTED_TOKEN]`.
- **Session Tokens**: Matches `cif_session=<token>` and replaces with `cif_session=[REDACTED_SESSION]`.
- **Sensitive Parameters**: Matches `password=`, `secret=`, `key=` and redacts values.

---

## 4. Diagnostics & System Telemetry (`/api/diagnostics`)

The framework exposes a live observability endpoint at `/api/diagnostics` (aliased as `/api/system/status`):
- **Server Health**: Online status, uptime seconds, process ID.
- **Database Status**: Relational connectivity state, authoritative database file path, row counts for all core tables (`events`, `decisions`, `entities`, `edges`, `guard_rules`, `users`, `sessions`, `repos`).
- **Rate Limiter Metrics**: Active sliding windows, total requests checked, total requests throttled, configured category quotas.
- **Timestamp**: Current UTC ISO 8601 server timestamp.
