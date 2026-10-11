# GitHub App Integration & Webhook Setup Guide

This document describes how to configure a GitHub App and connect it to the Context Intelligence Framework (CIF) to enforce architectural Decision Guard Rules on pull requests.

> [!NOTE]
> **Testing Status**: The webhook receiver and PR feedback posting logic have been verified using mock payloads and automated test suites (`tests/test_webhook.py`). A live end-to-end run against an external GitHub organization requires an active tunnel and public IP; live production deployment has not been executed in this offline academic environment.

---

## 1. Creating the GitHub App

1. In GitHub, navigate to **Settings** > **Developer settings** > **GitHub Apps** > **New GitHub App**.
2. Fill in the basic configuration:
   - **GitHub App name**: `CIF-Decision-Guard` (or unique name).
   - **Homepage URL**: `http://localhost:8080` (or your hosted dashboard URL).
   - **Webhook URL**: `https://<your-tunnel-domain>/api/webhook/github` (see §3 below).
   - **Webhook secret**: Generate a secure random token (e.g., using `openssl rand -hex 20`).
3. Set **Permissions**:
   - **Repository permissions**:
     - **Pull requests**: Read and write (required to inspect diffs and post review comments).
     - **Repository contents**: Read-only (required to inspect repository files and configuration).
     - **Issues**: Read-only (required to correlate PRs with linked issue context).
4. Set **Subscribe to events**:
   - Check **Pull request** (triggers on `opened`, `synchronize`, and `reopened`).
5. Save the App and install it into your target repository.

---

## 2. Environment Configuration

Set the required environment variables in your deployment environment or local shell:

```powershell
# PowerShell (Windows)
$env:CIF_WEBHOOK_SECRET = "your-generated-webhook-secret"
$env:GITHUB_TOKEN = "ghp_your_github_personal_access_token_or_app_token"
```

```bash
# Bash (Linux / macOS)
export CIF_WEBHOOK_SECRET="your-generated-webhook-secret"
export GITHUB_TOKEN="ghp_your_github_personal_access_token_or_app_token"
```

- `CIF_WEBHOOK_SECRET`: Used to cryptographically verify incoming `X-Hub-Signature-256` HMAC signatures. Unsigned requests or signature mismatches are rejected with HTTP 401.
- `GITHUB_TOKEN`: Used to fetch pull request unified diffs via the GitHub REST API and post violation comments.

---

## 3. Exposing the Local Server for Testing

To test incoming webhooks on a development machine:

1. Start the CIF server:
   ```bash
   python server.py
   ```
2. In a separate terminal, start an HTTP tunnel (e.g., via `cloudflared` or `ngrok`):
   ```bash
   ngrok http 8080
   # or
   cloudflared tunnel --url http://127.0.0.1:8080
   ```
3. Copy the public HTTPS forwarding URL and configure it as the **Webhook URL** in your GitHub App settings:
   `https://<subdomain>.ngrok-free.app/api/webhook/github`

---

## 4. Confirming Delivery and Verifying Enforcement

1. Open a pull request in the installed repository.
2. In the GitHub App settings, click **Advanced** > **Recent Deliveries**:
   - Confirm that the `pull_request` event was delivered with response code `200 OK`.
3. If the PR diff introduces an architectural violation (e.g., importing a forbidden library governed by an active guard rule):
   - The CIF webhook receiver automatically logs the violation in `drift_findings`.
   - If `GITHUB_TOKEN` is present, CIF posts a formatted PR comment linking directly to the original architectural decision and evidence records.

---

## 5. Serverless CI Alternative (No Webhook Required)

For environments without a publicly accessible server, CIF provides a direct command-line GitHub Actions workflow:
- Workflow definition: `.github/workflows/cif-check.yml`
- Local CLI check: `python tools/ci_check.py --base <base_sha> --head <head_sha>`
- Uses stdlib git diff and committed rules snapshot (`cif_rules.json`).
