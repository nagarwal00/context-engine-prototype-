# Centralized Rate Limiting Specification
## Context Intelligence Framework (CIF)

The Context Intelligence Framework incorporates an in-memory, thread-safe **Sliding-Window Rate Limiter** implemented in `backend/rate_limiter.py`.

---

## 1. Sliding Window Algorithm

Unlike naive fixed-window counters that suffer from burst boundary vulnerabilities (where twice the limit can be sent across the boundary of two minutes), CIF tracks timestamped hit histories per `(category, key)` tuple.

### Execution Flow:
1. When a request arrives, `window_start = now - window_seconds`.
2. Existing timestamps strictly `< window_start` are pruned.
3. If `len(timestamps) >= limit`:
   - Request is throttled.
   - `retry_after = max(1, int(oldest_hit + window_seconds - now + 0.99))`.
   - Returns `(False, retry_after, 0, limit)`.
4. If `len(timestamps) < limit`:
   - Timestamp is appended to history.
   - Returns `(True, 0, limit - len(timestamps), limit)`.

---

## 2. Quota Categories & Default Limits

End-points are categorized dynamically by `RateLimiter.get_category_for_path(path, method)`:

| Category | Default Window | Default Limit | Endpoints Protected |
|---|---|---|---|
| `auth` | 60 seconds | 10 requests | `/auth/login`, `/auth/register`, `/auth/token/exchange`, `/auth/logout` |
| `ingest` | 60 seconds | 5 requests | `/api/ingest`, `/api/ingest-repo`, `/api/purge-repo`, `/api/webhook/github` |
| `expensive` | 60 seconds | 15 requests | `/api/reseed`, `/api/clear-db`, `/api/benchmark`, `/api/drift-check`, `/api/query` |
| `api` | 60 seconds | 60 requests | `/api/repos`, `/api/timeline`, `/api/graph`, `/api/decisions`, `/api/bus-factor`, etc. |

*Exempt Endpoints*: `/healthz`, `/api/healthz`, `/api/diagnostics`, `/api/system/status`, and static assets (`.css`, `.js`, `.html`).

---

## 3. Client Identification Strategy

The rate limiter isolates usage by client identity:
- **Authenticated Users**: If the request carries an `Authorization: Bearer <token>` or `cif_session=<token>` cookie, the key is derived from a SHA-256 hash of the token: `user:<hash[:16]>`. This ensures individual user quotas are enforced even behind corporate proxies.
- **Unauthenticated Users**: If no credentials exist, the key falls back to the client IP address: `ip:<client_ip>`.

---

## 4. Configuration & Environment Variables

All rate limiter parameters are configurable via environment variables in `.env` without modifying code:

```bash
# Enable or disable rate limiting ("true" / "false")
CIF_RATE_LIMIT_ENABLED=true

# Sliding window duration in seconds (default: 60)
CIF_RATE_LIMIT_WINDOW=60

# Category caps per window
CIF_RATE_LIMIT_AUTH_MAX=10
CIF_RATE_LIMIT_INGEST_MAX=5
CIF_RATE_LIMIT_EXPENSIVE_MAX=15
CIF_RATE_LIMIT_API_MAX=60
```

---

## 5. HTTP 429 Protocol Compliance

When a client exceeds its allocation, CIF responds with HTTP 429:

### Headers:
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json; charset=utf-8
Retry-After: 60
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 60
X-Request-ID: f4e55489-32c5-4c97-9cb1-7e732aa1be0d
```

### JSON Body:
```json
{
  "status": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded for category 'api'. Please wait 60 seconds before retrying.",
  "retry_after": 60,
  "category": "api",
  "limit": 60,
  "request_id": "f4e55489-32c5-4c97-9cb1-7e732aa1be0d"
}
```

