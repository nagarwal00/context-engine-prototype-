# GitHub App Integration & OAuth Setup Guide (Phases 7, 8, 9)

This document describes how to configure the **CIF GitHub App** to enable:
1. **GitHub Login & OAuth**: One-click authentication for Web, Chrome Extension, and VS Code.
2. **Whole-Repository Automatic Ingestion**: Ingest commits, PRs, issues, ADRs, and code without pasting personal access tokens.
3. **Live Sync Webhooks**: Incremental real-time updates when commits or pull requests are pushed.
4. **Chrome & VS Code In-Editor Context**: Architectural decision provenance and drift warnings.

> [!NOTE]
> **Testing Status**:
> All backend authentication flows, sliding sessions, token exchanges, CSRF protections, webhook event handling, and App JWT minting are covered by automated unit and integration tests using mocked payloads (`tests/test_auth_flow.py`, `tests/test_add_repo.py`, `tests/test_job_runner.py`, `tests/test_webhook_sync.py`).
> End-to-end operation against a live GitHub App requires public HTTPS hosting (Human Tasks H-A, H-B, H-C, H-D).

---

## 1. Registering the GitHub App (Human Task H-A)

Navigate to **GitHub Settings** > **Developer settings** > **GitHub Apps** > **New GitHub App** and configure:

### A. General Information
- **GitHub App name**: `Context-Intelligence-Framework` (or unique name).
- **Homepage URL**: `${CIF_BASE_URL}` (e.g. `http://127.0.0.1:8080` or your public domain).
- **Setup URL**: `${CIF_BASE_URL}/repos?installed=1` (redirects users back to the CIF repository manager upon installation).

### B. User Authorization & OAuth
- **Callback URLs** (add all that apply):
  - Web Dashboard: `http://127.0.0.1:8080/auth/github/callback` (or `${CIF_BASE_URL}/auth/github/callback`)
  - Chrome Extension: `https://pmkcmkalbgefpllgfmhgieeajolmefpi.chromiumapp.org/` (replace with your extension ID if different)
  - VS Code Extension: `vscode://cif.cif-vscode/auth`
- **Expire user authorization tokens**: Check **ON** (GitHub default for modern apps; tokens expire after 8 hours and use refresh tokens).
- **Request user authorization (OAuth) during installation**: Check **ON**.

### C. Webhook Configuration
- **Webhook URL**: `${CIF_BASE_URL}/api/webhook/github` (e.g. via Cloudflare tunnel or ngrok).
- **Webhook secret**: Generate a secure random token (`openssl rand -hex 20`).
- **SSL verification**: Enable SSL verification.

### D. Repository Permissions
- **Contents**: **Read-only** (inspect file paths, blobs, trees, and ADRs).
- **Metadata**: **Read-only** (inspect repository metadata and branches).
- **Issues**: **Read-only** (correlate PRs and issues with architectural decisions).
- **Pull requests**: **Read & write** (inspect pull request diffs and post review violation feedback comments).

### E. Account Permissions
- **Email addresses**: None (Rule R4: CIF does not collect or store user emails).

### F. Subscribe to Events
Check the following events:
- **Pull request**
- **Push**
- **Issues**
- **Issue comment**
- **Pull request review**
- **Installation**
- **Installation repositories**

### G. Private Key (RS256 JWT Minting)
- Scroll to **Private keys** and click **Generate a private key**.
- Save the downloaded `.pem` file to a secure directory (e.g., `keys/github_app.pem`).
- This key is used by `backend/auth/app_token.py` (Rule R1) to mint App installation tokens.

---

## 2. Environment Variables Configuration

Configure these variables in your `.env` file or production environment:

```bash
# Server & OAuth URLs
CIF_BASE_URL=http://127.0.0.1:8080
CIF_SESSION_SECRET=your-32-byte-hex-random-secret

# GitHub App Credentials (from App General page)
GITHUB_APP_SLUG=context-intelligence-framework
GITHUB_APP_ID=123456
GITHUB_APP_CLIENT_ID=Iv1.xxxxxxxxxxxx
GITHUB_APP_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_APP_PRIVATE_KEY_PATH=keys/github_app.pem

# Optional: Token encryption at rest (Rule R1)
CIF_TOKEN_ENC_KEY=32-byte-base64-or-hex-encryption-key

# Client Extension IDs
CIF_EXTENSION_IDS=pmkcmkalbgefpllgfmhgieeajolmefpi
CIF_VSCODE_EXT_IDS=cif.cif-vscode

# Webhook Secret (from App settings)
CIF_WEBHOOK_SECRET=your-generated-webhook-secret

# Admin token (Rule R2: operations only, never in regular UI)
CIF_ADMIN_TOKEN=your-cif-admin-token-here

# Ingestion Caps & Limits (Rule R6)
CIF_MAX_COMMITS=5000
CIF_MAX_PRS=1500
CIF_MAX_ISSUES=1500
CIF_MAX_TARBALL_MB=100
```

---

## 3. Human Tasks Reference Matrix

| Task | Description | Status |
|---|---|---|
| **H-A** | Register GitHub App, generate client secret, webhook secret, and private key | Human Task (requires GitHub account) |
| **H-B** | Run live login → install App → add repository walk-through; save screenshots | Human Task (requires live GitHub App) |
| **H-C** | Load unpacked Chrome extension in `chrome://extensions`, verify ID, run live PR panel test | Human Task (requires Chromium browser) |
| **H-D** | Setup public HTTPS tunnel or hosting for incoming webhooks beyond localhost | Human Task (requires network tunnel or VPS) |
| **H-E** | Prepare two demo PRs on a test repo (one violating, one clean) | Human Task (requires live test repo) |
| **H-F** | Confirm whether VS Code extension should be started | Completed (confirmed and implemented) |

---

## 4. Local Webhook Testing via Tunnel

To test incoming webhooks locally during development:
1. Start CIF server: `python server.py`
2. Start tunnel: `cloudflared tunnel --url http://127.0.0.1:8080` (or `ngrok http 8080`)
3. Set Webhook URL in GitHub App settings: `https://<tunnel-id>.trycloudflare.com/api/webhook/github`
4. Confirm deliveries in GitHub App **Advanced -> Recent Deliveries**.
