# REST API Documentation
## Context Intelligence Framework (CIF)

All endpoints accept and return UTF-8 encoded JSON unless otherwise specified.
Requests must send and receive standard request correlation IDs (`X-Request-ID`).

---

## 1. Global Conventions

### Response Envelope
Successful responses return HTTP 200 with standard envelopes:
```json
{
  "status": "success",
  "data": { ... },
  "request_id": "8d12ab8f-ff0f-41c6-94f4-f999b755182c"
}
```

Error responses return standard HTTP 4xx/5xx with error codes:
```json
{
  "status": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded for category 'api'. Please wait 60 seconds.",
  "retry_after": 60,
  "request_id": "f4e55489-32c5-4c97-9cb1-7e732aa1be0d"
}
```

### Rate Limit Headers (RFC Compliant)
Every API response includes rate limiting metadata:
- `X-RateLimit-Limit`: Maximum requests permitted in the sliding window.
- `X-RateLimit-Remaining`: Remaining requests before throttling.
- `X-RateLimit-Reset`: Seconds remaining until sliding window quota refreshes.
- `Retry-After`: (On HTTP 429 only) Number of seconds client must wait.

---

## 2. Public & System Endpoints

### `GET /healthz` | `GET /api/healthz`
- **Role**: Public
- **Description**: Lightweight health probe for load balancers and orchestrators.
- **Response**:
```json
{
  "status": "ok",
  "mode": "live",
  "db": "ok",
  "request_id": "uuid"
}
```

### `GET /api/diagnostics` | `GET /api/system/status`
- **Role**: Public
- **Description**: Comprehensive system telemetry, database status, table row counts, rate limiter statistics, and uptime.
- **Response**:
```json
{
  "status": "success",
  "backend_status": "online",
  "uptime_seconds": 128.4,
  "database": {
    "status": "connected",
    "path": "c:\\Users\\HP\\Desktop\\SE_project\\context_intelligence.db",
    "tables": {
      "events": 9,
      "decisions": 7,
      "entities": 9,
      "edges": 21,
      "guard_rules": 10,
      "users": 4,
      "sessions": 11,
      "repos": 2
    },
    "authoritative": true
  },
  "rate_limiter": {
    "enabled": true,
    "window_seconds": 60,
    "configured_limits": {
      "auth": 10,
      "ingest": 5,
      "expensive": 15,
      "api": 60
    },
    "total_requests_checked": 42,
    "total_requests_blocked": 1,
    "active_rate_limit_keys": 3
  },
  "version": "1.0.0",
  "timestamp": "2026-11-20T11:52:00Z",
  "request_id": "uuid"
}
```

### `GET /api/repos`
- **Role**: Public
- **Description**: Returns list of all indexed repositories in the database.
- **Response**:
```json
{
  "status": "success",
  "data": [
    "acme-ecommerce/payment-core",
    "cloud-hypervisor/cloud-hypervisor"
  ],
  "request_id": "uuid"
}
```

---

## 3. Decision Intelligence Endpoints

### `GET /api/timeline`
- **Role**: `ROLE_REPO_READ`
- **Query Parameters**:
  - `repo` (optional): Filter by repository name.
  - `start` (optional): ISO 8601 start timestamp.
  - `end` (optional): ISO 8601 end timestamp.
- **Response**: Array of chronological decisions with evidence count, state, author, and timestamp.

### `GET /api/graph`
- **Role**: `ROLE_REPO_READ`
- **Query Parameters**: `repo` (optional)
- **Response**: Nodes (`decisions`, `events`, `entities`) and directed causal `edges` (`affects`, `derives_from`, `supersedes`).

### `GET /api/decisions`
- **Role**: `ROLE_REPO_READ`
- **Query Parameters**: `repo` (optional), `state` (optional)
- **Response**: Full decision list including rationale, assumptions, ADR file path, and confidence scores.

### `GET /api/as-of`
- **Role**: `ROLE_REPO_READ`
- **Query Parameters**:
  - `repo` (required)
  - `date` (required): ISO 8601 point-in-time timestamp.
- **Response**: Point-in-time state of the repository showing active decisions and active entities as of the specified historical date.

### `GET /api/bus-factor`
- **Role**: `ROLE_REPO_READ`
- **Query Parameters**: `repo` (optional)
- **Response**: High-risk concentration analysis, per-module contributor distributions, and overall bus factor metric.

### `GET /api/onboarding`
- **Role**: `ROLE_REPO_READ`
- **Query Parameters**: `repo` (required), `role` (optional), `task` (optional)
- **Response**: Tailored architectural reading list, critical invariant decisions, and domain checklist for newly onboarded engineers.

---

## 4. Review & Governance Endpoints

### `POST /api/review-action`
- **Role**: `ROLE_REPO_REVIEW`
- **Headers**: `Authorization: Bearer <token>` or valid session cookie.
- **Payload**:
```json
{
  "action": "confirm" | "dismiss" | "correct",
  "target_id": "dec_pilot_001",
  "item_type": "decision",
  "title": "Optional new title on correction",
  "state": "Optional new state",
  "rationale": "Audit explanation"
}
```
- **Response**: `{"status": "success", "message": "Decision updated successfully."}`

### `POST /api/drift-check`
- **Role**: `ROLE_REPO_REVIEW`
- **Payload**:
```json
{
  "repo": "acme-ecommerce/payment-core",
  "diff_text": "--- a/src/thermal.py\n+++ b/src/thermal.py\n+if temp > 80: shutoff()",
  "files": ["src/thermal.py"]
}
```
- **Response**: Evaluates git diff against accepted decisions and returns any architectural drift or guard-rule violations.

---

## 5. Administration Endpoints

### `POST /api/reseed`
- **Role**: `ROLE_ADMIN`
- **Payload**: `{"confirm": "context_intelligence.db"}`
- **Description**: Reinitializes the pilot repositories to known ground-truth seed decisions.

### `POST /api/clear-db`
- **Role**: `ROLE_ADMIN`
- **Payload**: `{"confirm": "context_intelligence.db"}`
- **Description**: Clears all operational records for a clean-room demonstration.
