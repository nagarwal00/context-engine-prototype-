# Deployment & Operational Guide
## Context Intelligence Framework (CIF)

This guide covers local startup, containerized execution, reverse-proxy integration, and GitHub Pages static synchronization.

---

## 1. Quick Start (Local Setup)

### Prerequisites
- Python 3.10+ (Standard library only; zero external pip dependencies required).
- Modern web browser (Chrome, Firefox, Safari, Edge).

### Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/nagarwal00/context-engine-prototype-.git
   cd context-engine-prototype-
   ```

2. **Configure Environment Variables (Optional)**:
   Copy `.env.example` to `.env` or set environment variables:
   ```bash
   cp .env.example .env
   ```

3. **Start the Web Server**:
   ```bash
   python server.py
   ```
   Output:
   ```
   ======================================================================
     Context Intelligence Framework -- Living Decision History Prototype
   ======================================================================
   [*] Serving all 9 UI surfaces, interactive Context Graph, and Review Queue.
   [SERVER LIVE] Prototype is live and running at: http://127.0.0.1:8080/
   ```

4. **Access the Dashboard**:
   Open `http://localhost:8080/dashboard.html` in your browser.
   To bypass authentication during local evaluation, visit `http://localhost:8080/auth/demo/login` or log in via GitHub App credentials.

---

## 2. GitHub Pages Static Snapshot Deployment

The live frontend is deployed on GitHub Pages:
`https://nagarwal00.github.io/context-engine-prototype-/dashboard.html`

### Syncing Changes from `web/` to `docs/`:
Whenever changes are made to the frontend in `web/`, run the deterministic snapshot generator:
```bash
python tools/build_static.py
```
This script:
1. Re-exports the authoritative database contents into `web/static_data.js`.
2. Verifies the SHA-256 database snapshot hash.
3. Mirrors `web/` cleanly into `docs/`.
4. Guarantees 100% parity between local dashboard and the deployed GitHub Pages site.

### GitHub Pages Settings Configuration
In GitHub Repository Settings -> **Pages**:
- **Build and deployment -> Source**: Choose **Deploy from a branch**.
- **Branch**: Select `main`, folder: `/docs`.
- Click **Save**.

---

## 3. Production Deployment with Reverse Proxy (NGINX)

When deploying behind NGINX or Caddy in production:

### Recommended NGINX Configuration:
```nginx
server {
    listen 80;
    server_name cif.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id; # Injects correlation ID
    }
}
```

---

## 4. Environment Variables Reference

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8080` | Port for the HTTP server to listen on. |
| `CIF_BIND` | `127.0.0.1` | Network interface to bind (`127.0.0.1` or `0.0.0.0`). |
| `CIF_DB_PATH` | `context_intelligence.db` | Path to SQLite operational database file. |
| `CIF_ADMIN_TOKEN` | *unset* | Bearer token required for administrative operations (`/api/reseed`, `/api/clear-db`). |
| `CIF_RATE_LIMIT_ENABLED` | `true` | Enables/disables sliding-window rate limiting. |
| `CIF_RATE_LIMIT_API_MAX` | `60` | Request quota per minute for general API endpoints. |
| `CIF_RATE_LIMIT_AUTH_MAX` | `10` | Request quota per minute for authentication endpoints. |
| `CIF_RATE_LIMIT_INGEST_MAX` | `5` | Request quota per minute for ingestion endpoints. |
| `CIF_RATE_LIMIT_EXPENSIVE_MAX`| `15` | Request quota per minute for heavy query/benchmark endpoints. |

