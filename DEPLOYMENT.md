# Complete GitHub Deployment Guide

This guide walks you through the complete process of organizing, committing, and deploying the **Context Intelligence Framework** to **GitHub** and **GitHub Pages** with live interactive functionality — with **no external hosting or third-party services** (no Vercel, no Netlify, no Heroku).

---

## 1. Project File Organization

The project is organized into clean separation between backend engines, the web application, deployment workflows, and documentation:

```text
SE_project/
├── .github/
│   └── workflows/
│       ├── deploy.yml              # Automated GitHub Pages CI/CD deployment workflow
│       └── cif-check.yml           # Automated serverless CI drift checker
├── .gitignore                      # Excludes Python bytecode, databases, caches, and dist/
├── DEPLOYMENT.md                   # This step-by-step deployment guide
├── EVALUATION.md                   # Benchmark methodology, splits, and reproduction guide
├── LIMITATIONS.md                  # Honest scope boundaries and known constraints
├── PRIVACY.md                      # Privacy guarantees, secret redaction, and purge docs
├── SECURITY_SCAN.md                # Secret scan audit report across git and SQLite
├── readme.md                       # Main project overview and demonstration guide
├── task.md                         # Project milestones and development task checklist
├── explanation.md                  # In-depth architectural breakdown of system
├── server.py                       # Native Python HTTP server for local development
├── run_demo.py                     # 21-feature automated verification test runner
│
├── tools/                          # Release and Evaluation Toolchain
│   ├── build_static.py             # Generates static snapshot for GitHub Pages
│   ├── init_db.py                  # Initializes database, runs migrations and seed data
│   ├── make_demo_repo.py           # Builds deterministic 11-commit demo git repo
│   ├── package_release.py          # Builds & verifies clean release ZIP package
│   ├── scan_secrets.py             # Scans Git history & database text columns
│   ├── run_whybench.py             # Reproducible evaluation runner
│   └── analyze_failures.py         # Categorizes benchmark misses in dev split
│
├── backend/                        # Core Python Engine & Logic
│   ├── api.py                      # REST API router & GitHub webhook receiver
│   ├── db.py                       # SQLite database interface & mechanical invariants
│   ├── migrations/                 # Versioned database schema migrations (v001-v007)
│   ├── models.py                   # Data models (Event, Decision, Entity, Edge)
│   ├── seed_data.py                # Deterministic seed data generator (thermal & cache)
│   ├── engine/                     # Brain (drift, graph, bus factor, onboarding)
│   └── ingestion/                  # Multi-source adapters (Git, GitHub, ADR, Slack, Sanitizer)
│
├── web/                            # Source Frontend Files (Used by server.py)
│   ├── index.html                  # Semantic UI with all surfaces & modals
│   ├── style.css                   # Polished dark-mode design system & animations
│   ├── app.js                      # UI controller + hybrid Local/GitHub Pages API adapter
│   └── static_data.js              # Seed dataset allowing standalone client-side execution
│
└── docs/                           # GitHub Pages Static Distribution Directory (Mirrors web/)
    ├── index.html                  # Web entry point for GitHub Pages
    ├── style.css                   # Stylesheet for GitHub Pages
    ├── app.js                      # Application controller for GitHub Pages
    └── static_data.js              # Standalone data store for GitHub Pages
```

---

## 2. Why & How It Deploys to GitHub Pages

GitHub Pages natively serves **static assets** (HTML, CSS, JavaScript) directly from your repository for free. It does not run continuous Python server processes in the cloud.

To make the application fully interactive on GitHub Pages without sacrificing local Python server capabilities, we implemented a **Hybrid API Layer** in `web/app.js`:

1. **When running locally (`localhost` / `127.0.0.1`):**  
   The frontend automatically connects to your local Python server (`server.py`) and queries SQLite.
2. **When running on GitHub Pages (`*.github.io`):**  
   The frontend seamlessly uses the embedded client-side engine (`static_data.js`), enabling:
   - Full navigation across all 11 interactive surfaces (`repositories`, `timeline`, `graph`, `code`, `decisions`, `evidence`, `review`, `onboarding`, `drift-test`, `benchmark`, `bus-factor`).
   - Interactive SVG Context Graph exploration.
   - Live Human Review Queue actions (**Confirm**, **Correct**, **Reject**).
   - Live CI Code Drift Checker with all 3 test presets.
   - Decision state filtering and keyword search.

---

## 3. Step-by-Step Deployment Steps

### Step 1: Open Command Prompt or Terminal
Navigate to your project directory:
```cmd
cd C:\Users\HP\Desktop\SE_project
```

---

### Step 2: Initialize Git and Make the Initial Commit
Run the following commands in order:

```cmd
git init
git add .
git commit -m "Initial commit: Context Intelligence Framework with GitHub Pages deployment"
```

---

### Step 3: Create a New Repository on GitHub
1. Log in to your GitHub account: [https://github.com](https://github.com).
2. In the top right corner, click the **`+`** icon and select **New repository**.
3. Fill in the repository details:
   - **Repository name:** `context-intelligence-framework` (or any name you prefer).
   - **Description:** `Living Decision History Prototype with Temporal Context Graph`.
   - **Visibility:** Choose **Public** (required for free GitHub Pages).
   - **Initialize with README / .gitignore:** **Leave UNCHECKED** (we already have both).
4. Click **Create repository**.

---

### Step 4: Link Your Local Code and Push to GitHub
Copy your repository URL from GitHub (e.g. `https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git`).

In your Command Prompt, run:
```cmd
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
git push -u origin main
```
*(Replace `<YOUR_USERNAME>` and `<YOUR_REPO_NAME>` with your actual GitHub username and repository name).*

---

### Step 5: Enable GitHub Pages

You can choose either of the two native methods below. **Method A is recommended** as it is completely automated.

#### Method A: Using GitHub Actions (Recommended)
1. On your GitHub repository page, click the **Settings** tab (the gear icon at the top).
2. In the left sidebar, click **Pages** (under "Code and automation").
3. Under **Build and deployment** > **Source**, change the dropdown from *Deploy from a branch* to **GitHub Actions**.
4. That's it! The pre-configured workflow at `.github/workflows/deploy.yml` will automatically build and deploy your site whenever code is pushed to `main`.
5. Click the **Actions** tab at the top to watch the deployment run (takes ~30-45 seconds).

#### Method B: Deploy from Branch (1-Click Alternative)
1. On your GitHub repository page, click **Settings** > **Pages**.
2. Under **Build and deployment** > **Source**, keep **Deploy from a branch**.
3. Under **Branch**:
   - Select **`main`** from the branch dropdown.
   - Select **`/docs`** from the folder dropdown (NOT `/ (root)`).
4. Click **Save**.

---

### Step 6: Access Your Live Deployed Website!
Once the deployment finishes (usually within 1 minute), GitHub Pages will give you a public URL:

👉 **`https://<YOUR_USERNAME>.github.io/<YOUR_REPO_NAME>/`**

You can paste this link in your README or share it directly with your professor or evaluators. Anyone in the world can open the link in their browser and interact with the full prototype with zero setup!

---

## 4. How to Update the Live Site Later

Whenever you edit files in the future, push the updates to GitHub with these 3 simple commands:

```cmd
git add .
git commit -m "Update project features"
git push
```

GitHub Pages will automatically update within seconds!

---

## 5. Live Backend Server Deployment (Phases 7 & 8)

While GitHub Pages provides a static client-side simulation, the complete multi-tenant product with GitHub OAuth login, automatic repository ingestion, webhook live-sync, and extension backends requires a live Python HTTP service.

### Prerequisites
- A Linux VPS, cloud container, or machine with a public HTTPS domain.
- Python 3.10+ (standard library only; optional `cryptography` for RS256 App JWT minting).
- Reverse proxy (Nginx, Caddy, or Cloudflare Tunnel) terminating TLS.

### Steps
1. Clone the repository and configure `.env`:
   ```bash
   cp .env.example .env
   # Populate CIF_BASE_URL (https://your-domain.com), GITHUB_APP_*, CIF_EXTENSION_IDS, etc.
   ```
2. Run database migration and seed:
   ```bash
   python tools/init_db.py
   ```
3. Start the production backend server:
   ```bash
   python server.py
   ```
4. Configure systemd service for automatic process supervision.
5. In GitHub App settings, set:
   - Homepage URL: `https://your-domain.com`
   - Callback URL: `https://your-domain.com/auth/github/callback`
   - Webhook URL: `https://your-domain.com/api/webhook/github`

---

## 6. Chrome Extension Distribution (Phase 8)

### Option A: Load Unpacked (Development & Evaluation)
1. Open Google Chrome and navigate to `chrome://extensions`.
2. Enable **Developer mode** in the top-right corner.
3. Click **Load unpacked** and select the `extension/` directory.
4. Verify extension ID matches `CIF_EXTENSION_IDS` in `.env` (default: `pmkcmkalbgefpllgfmhgieeajolmefpi`).

### Option B: Build Zip Distribution Package
```bash
python tools/build_extension.py
```
Output artifact: `dist/cif-extension.zip`.

---

## 7. VS Code Extension Distribution (Phase 9)

### Option A: Extension Development Host
1. Open the workspace root or `vscode-extension/` in VS Code.
2. Ensure the backend server is running (`python server.py`).
3. Press **F5** to launch the `[Extension Development Host]` with CIF active.

### Option B: VSIX Package Installation
```bash
cd vscode-extension
npx @vscode/vsce package
code --install-extension cif-vscode-1.0.0.vsix
```

