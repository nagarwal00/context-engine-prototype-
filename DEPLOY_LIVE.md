# Live Deployment & Verification Guide (Step 6.1, Human Task H-7)

> **Deployment Status**: Automated server handlers, health checks (`/healthz`), Dockerfile specifications, and authentication routes are implemented and validated by unit tests (`tests/test_healthz.py`, `tests/test_api_auth.py`). Live deployment to a public internet host requires external platform accounts and credentials, marked as **Human Tasks** below.

---

## 1. Overview & Architecture

Context Intelligence Framework (CIF) is designed to run as a single-process service with zero third-party pip dependencies (pure Python standard library). In a production or publicly hosted deployment:

- **Web / API Server**: Runs `python server.py` binding to `0.0.0.0:${PORT}` (default port 8080).
- **Database**: SQLite3 database (`context_intelligence.db`). Requires a **persistent volume / disk mount** so that ingested repositories, decision records, and audit logs survive container restarts.
- **HTTPS & Public Routing**: Required for GitHub App OAuth redirects and incoming webhook deliveries.

---

## 2. Environment Variables Checklist

Set these variables in your hosting provider's dashboard (or `.env` file for local tunnels) based on [`.env.example`](file:///.env.example):

| Variable | Recommended Value | Purpose |
|---|---|---|
| `PORT` | `8080` (or host assigned) | HTTP server port |
| `CIF_BIND` | `0.0.0.0` | Bind address for containerized hosts |
| `CIF_MODE` | `live` | Enables live database access & dynamic endpoints |
| `CIF_DEV_MODE` | `0` | Disables permissive local CORS; enforces production origins |
| `CIF_DB_PATH` | `/app/data/context_intelligence.db` | Absolute path on persistent volume |
| `CIF_BASE_URL` | `https://your-app.example.com` | Public HTTPS base URL for OAuth callbacks & webhooks |
| `CIF_SESSION_SECRET` | `openssl rand -hex 32` | 32-byte secret for session token signing and state HMAC |
| `CIF_ADMIN_TOKEN` | `openssl rand -hex 24` | Token for admin routes (`/api/reseed`, management) |
| `CIF_CORS_ORIGINS` | `https://your-app.example.com` | Allowed browser origins |
| `CIF_EXTENSION_IDS` | `pmkcmkalbgefpllgfmhgieeajolmefpi` | Chrome extension ID allowlist |
| `GITHUB_APP_SLUG` | `context-intelligence-framework` | GitHub App slug from developer settings |
| `GITHUB_APP_ID` | e.g. `123456` | GitHub App ID |
| `GITHUB_APP_CLIENT_ID` | e.g. `Iv1.xxxxxxxxxxxx` | GitHub OAuth client ID |
| `GITHUB_APP_CLIENT_SECRET`| Secret from GitHub | GitHub OAuth client secret |
| `CIF_WEBHOOK_SECRET` | `openssl rand -hex 20` | Webhook HMAC verification secret |

---

## 3. Free Hosting Options & Step-by-Step Setup

### Option A: Render (Free Web Service + Persistent Disk)
> **TODO(human)**: Human Task H-7 requires logging into Render.

1. **Create Web Service**:
   - Connect repository or deploy from public Git repository.
   - Environment: **Docker** (uses repository [`Dockerfile`](file:///Dockerfile)).
2. **Attach Persistent Disk**:
   - In service settings, add a Disk:
     - Name: `cif-data`
     - Mount Path: `/app/data`
     - Size: 1 GB (sufficient for tens of thousands of commits and graph nodes).
3. **Configure Environment Variables**:
   - Enter all variables from §2 above.
4. **Deploy**:
   - Render automatically provisions TLS/HTTPS (e.g., `https://cif-framework.onrender.com`).

---

### Option B: Fly.io (Docker + Volume)
> **TODO(human)**: Human Task H-7 requires Fly.io CLI and account.

1. **Initialize App**:
   ```bash
   fly launch --no-deploy
   ```
2. **Create Persistent Volume**:
   ```bash
   fly volumes create cif_data --region iad --size 1
   ```
3. **Update `fly.toml`**:
   ```toml
   [mounts]
     source = "cif_data"
     destination = "/app/data"

   [env]
     PORT = "8080"
     CIF_BIND = "0.0.0.0"
     CIF_MODE = "live"
     CIF_DB_PATH = "/app/data/context_intelligence.db"
   ```
4. **Set Secrets & Deploy**:
   ```bash
   fly secrets set CIF_SESSION_SECRET="..." CIF_WEBHOOK_SECRET="..." ...
   fly deploy
   ```

---

### Option C: Cloudflare Tunnel / ngrok (from Developer Laptop)
> **TODO(human)**: Ideal for live demo presentations and examination defense.

1. **Run Local Server with Persistent DB**:
   ```bash
   python server.py
   ```
2. **Launch Cloudflare Tunnel (Free, no account needed for quick tunnels)**:
   ```bash
   cloudflared tunnel --url http://localhost:8080
   ```
   *Note the generated public URL (e.g., `https://random-word-name.trycloudflare.com`).*
3. **Export Environment Variables**:
   ```bash
   set CIF_BASE_URL=https://random-word-name.trycloudflare.com
   ```

---

## 4. GitHub App Configuration

Once your public HTTPS URL is live (e.g., `https://cif.example.com`), update the GitHub App settings per [`GITHUB_APP_SETUP.md`](file:///GITHUB_APP_SETUP.md):

1. **Homepage URL**: `https://cif.example.com`
2. **Setup URL**: `https://cif.example.com/repos?installed=1`
3. **User authorization callback URL**:
   - `https://cif.example.com/auth/github/callback`
   - `https://pmkcmkalbgefpllgfmhgieeajolmefpi.chromiumapp.org/` (Chrome extension)
   - `vscode://cif.cif-vscode/auth` (VS Code)
4. **Webhook URL**: `https://cif.example.com/api/webhook/github`
5. **Webhook Secret**: Must match `CIF_WEBHOOK_SECRET`.

---

## 5. Live Verification Runbook

Perform the following verification steps once deployed:

### Step 1: Healthz Probe
Verify public accessibility and database connectivity:
```bash
curl -s https://your-app.example.com/healthz
```
**Expected Response (HTTP 200)**:
```json
{"status": "ok", "mode": "live", "db": "ok"}
```

### Step 2: Auth Configuration Check
Verify the server exposes configured public App identities:
```bash
curl -s https://your-app.example.com/api/auth-config
```
**Expected Response (HTTP 200)**:
```json
{"auth_enabled": true, "github_app_slug": "context-intelligence-framework", "client_id": "Iv1.xxx..."}
```

### Step 3: Webhook Delivery Verification
1. In **GitHub Developer Settings** > **GitHub Apps** > **Advanced** > **Recent Deliveries**.
2. Find the ping event or push event.
3. Verify the HTTP response status code is **200 OK**.

### Step 4: Evidence Capture (Human Task H-7)
Capture screenshots and evidence for submission:
- Save `/healthz` browser or curl output screenshot to [`docs/evidence/`](file:///docs/evidence/).
- Save GitHub App "Recent Deliveries" green checkmark to [`docs/evidence/`](file:///docs/evidence/).
- Save live repository ingestion progress screenshot to [`docs/evidence/`](file:///docs/evidence/).
